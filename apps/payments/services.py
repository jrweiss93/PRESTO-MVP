"""Servicios de escritura de la app payments (interfaz pública).

El `Payment` es la **intención** de mover dinero; el saldo del usuario lo
mueve el **ledger**, que es la fuente de verdad (AGENTS §6 y ADR 0008).

Flujo de un pago:

1. Se crea el `Payment` en estado `pending` (con la clave de idempotencia).
2. Se llama al proveedor. Si el proveedor confirma de inmediato (modo
   simulado o transferencia interna), el saldo se mueve en el mismo service.
3. Si el proveedor queda esperando (Mercado Pago), el saldo se mueve cuando
   llega el **webhook firmado** del proveedor.
"""

import hashlib
import json
import logging
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction

from apps.core.exceptions import InsufficientFunds, InvalidAmount, KYCNotCompleted
from apps.identity.selectors import get_user_email, is_kyc_approved
from apps.ledger import services as ledger_services
from apps.payments import providers
from apps.payments.exceptions import (
    DestinationAccountRequired,
    IdempotencyConflict,
    InvalidWebhookSignature,
    ProviderError,
    ProviderNotConfigured,
)
from apps.payments.models import Payment, WebhookEvent
from apps.payments.providers import ProviderResult, WebhookEventInfo

logger = logging.getLogger(__name__)


def build_request_hash(payload: dict) -> str:
    """Calcula un hash estable de un payload.

    Args:
        payload: datos de la operación.

    Returns:
        Hash SHA-256 hexadecimal del payload.
    """
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def create_payment(
    *,
    user_id: uuid.UUID,
    direction: str,
    amount: Decimal,
    currency: str,
    idempotency_key: str,
    description: str = '',
    destination_user_id: uuid.UUID | None = None,
    destination_account: str = '',
) -> Payment:
    """Crea un pago y, si el proveedor confirma, mueve el saldo.

    Args:
        user_id: usuario que ordena la operación.
        direction: `deposit`, `withdrawal` o `transfer`.
        amount: importe, mayor que cero.
        currency: código ISO de la moneda.
        idempotency_key: clave de idempotencia del usuario.
        description: descripción de la operación.
        destination_user_id: usuario que recibe la transferencia.
        destination_account: cuenta externa de destino (solo retiros).

    Returns:
        El pago creado, o el original si la clave ya se usó.

    Raises:
        InvalidAmount: si el importe no es positivo.
        KYCNotCompleted: si el usuario no tiene KYC aprobada.
        DestinationAccountRequired: si la transferencia no tiene destino.
        IdempotencyConflict: si la clave ya existe con otro payload.
        ProviderError: si el proveedor falla.
    """
    _assert_valid_amount(amount)
    _require_kyc(user_id)
    if direction == Payment.Direction.TRANSFER:
        if destination_user_id is None:
            raise DestinationAccountRequired('La transferencia necesita un usuario de destino.')
        if destination_user_id == user_id:
            raise DestinationAccountRequired('El destino no puede ser el mismo usuario.')
    request_hash = build_request_hash(
        {
            'direction': direction,
            'currency': currency,
            'amount': str(amount),
            'description': description,
            'destination_user_id': str(destination_user_id or ''),
        }
    )
    existing = _resolve_idempotent(user_id, idempotency_key, request_hash)
    if existing is not None:
        return existing
    provider = providers.get_provider()
    try:
        payment = Payment.objects.create(
            user_id=user_id,
            direction=direction,
            amount=amount,
            currency=currency,
            provider=provider.name,
            provider_reference=f'{provider.name}:{uuid.uuid4()}',
            status=Payment.Status.PENDING,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            destination_user_id=destination_user_id,
            payload={'description': description},
        )
    except IntegrityError:
        return _recover_from_idempotency_race(user_id, idempotency_key, request_hash)
    payment.payload = {**payment.payload, 'external_reference': str(payment.id)}
    payment.save(update_fields=['payload', 'updated_at'])
    try:
        result = _call_provider(
            provider=provider,
            payment=payment,
            user_email=get_user_email(user_id=user_id) or '',
            destination_account=destination_account,
        )
    except ProviderError as exc:
        _mark_failed(payment, str(exc))
        raise
    payment.provider_reference = result.external_id
    payment.payload = {**payment.payload, **result.payload}
    if result.checkout_url:
        payment.payload['checkout_url'] = result.checkout_url
    payment.save(update_fields=['provider_reference', 'payload', 'updated_at'])
    if result.status == providers.STATUS_CONFIRMED:
        confirm_payment(payment_id=payment.id)
        payment.refresh_from_db()
    return payment


def confirm_payment(payment_id: uuid.UUID) -> Payment:
    """Confirma un pago pendiente moviendo el saldo en el ledger.

    Es **idempotente**: si el pago ya está confirmado no vuelve a mover saldo.

    Args:
        payment_id: identificador del pago.

    Returns:
        El pago, confirmado o en su estado actual.

    Raises:
        ProviderError: si el pago no existe o no se puede confirmar.
    """
    payment = Payment.objects.filter(pk=payment_id).first()
    if payment is None:
        raise ProviderError('El pago no existe.')
    if payment.status != Payment.Status.PENDING:
        return payment
    ledger_transaction = _move_money(payment)
    payment.status = Payment.Status.CONFIRMED
    payment.ledger_transaction_id = ledger_transaction.id
    payment.error = ''
    payment.save(update_fields=['status', 'ledger_transaction_id', 'error', 'updated_at'])
    logger.info(
        'Pago confirmado: payment_id=%s ledger_transaction_id=%s',
        payment.id,
        ledger_transaction.id,
    )
    return payment


def fail_payment(payment_id: uuid.UUID, reason: str) -> Payment:
    """Marca un pago como fallido.

    Args:
        payment_id: identificador del pago.
        reason: motivo del fallo.

    Returns:
        El pago, fallido o en su estado actual.
    """
    payment = Payment.objects.filter(pk=payment_id).first()
    if payment is None:
        raise ProviderError('El pago no existe.')
    if payment.status != Payment.Status.PENDING:
        return payment
    _mark_failed(payment, reason)
    return payment


def handle_webhook(
    *,
    provider_name: str,
    body: bytes,
    headers: dict[str, str],
) -> WebhookEvent:
    """Procesa un webhook del proveedor de pagos.

    La firma se verifica **antes** de parsear el cuerpo: con la firma
    inválida no se toca el ledger (ADR 0008).

    Args:
        provider_name: nombre del proveedor que manda el evento.
        body: cuerpo crudo del webhook.
        headers: headers de la petición.

    Returns:
        El evento registrado y procesado.

    Raises:
        ProviderNotConfigured: si el proveedor no existe.
        InvalidWebhookSignature: si la firma no es válida.
        ProviderError: si el cuerpo no es JSON válido.
    """
    provider = _provider_by_name(provider_name)
    if not provider.verify_webhook_signature(body=body, headers=headers):
        raise InvalidWebhookSignature('La firma del webhook no es válida.')
    payload = _parse_json(body)
    if payload is None:
        raise ProviderError('El webhook no es un JSON válido.')
    info = provider.parse_webhook_event(payload)
    event, created = WebhookEvent.objects.get_or_create(
        provider=provider.name,
        external_id=info.external_id or info.reference,
        defaults={
            'event_type': info.event_type,
            'status': WebhookEvent.Status.RECEIVED,
            'payload': info.payload,
        },
    )
    if not created:
        logger.info(
            'Webhook repetido de %s: event_id=%s no se vuelve a procesar',
            provider.name,
            event.id,
        )
        return event
    payment = _find_payment(provider=provider.name, info=info)
    if payment is None:
        event.status = WebhookEvent.Status.IGNORED
        event.error = 'El evento no corresponde a ningún pago.'
        event.save(update_fields=['status', 'error', 'updated_at'])
        return event
    event.payment_id = payment.id
    try:
        if info.status == providers.STATUS_CONFIRMED:
            confirm_payment(payment_id=payment.id)
        elif info.status == providers.STATUS_FAILED:
            fail_payment(
                payment_id=payment.id, reason=f'Rechazado por el proveedor: {info.event_type}'
            )
    except ProviderError as exc:
        event.status = WebhookEvent.Status.FAILED
        event.error = str(exc)[:255]
        event.save(update_fields=['status', 'error', 'payment_id', 'updated_at'])
        raise
    event.status = WebhookEvent.Status.PROCESSED
    event.save(update_fields=['status', 'payment_id', 'updated_at'])
    return event


def _call_provider(
    *,
    provider,
    payment: Payment,
    user_email: str,
    destination_account: str,
) -> ProviderResult:
    """Le pide al proveedor la operación del pago.

    Args:
        provider: el proveedor configurado.
        payment: el pago a crear en el proveedor.
        user_email: email del usuario.
        destination_account: cuenta externa de destino (retiros).

    Returns:
        El resultado del proveedor.

    Raises:
        ProviderError: si el proveedor falla.
    """
    if payment.direction == Payment.Direction.DEPOSIT:
        return provider.create_deposit(
            payment_id=payment.id,
            user_email=user_email,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.payload.get('description', ''),
        )
    if payment.direction == Payment.Direction.WITHDRAWAL:
        return provider.create_withdrawal(
            payment_id=payment.id,
            user_email=user_email,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.payload.get('description', ''),
            destination_account=destination_account,
        )
    return provider.create_transfer(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.payload.get('description', ''),
    )


def _move_money(payment: Payment):
    """Mueve el saldo del ledger según la dirección del pago.

    Args:
        payment: el pago a confirmar.

    Returns:
        La transacción del ledger.

    Raises:
        ProviderError: si el movimiento no se puede hacer.
    """
    idempotency_key = f'payment:{payment.id}'
    description = payment.payload.get('description', '') or f'Pago {payment.direction}'
    try:
        if payment.direction == Payment.Direction.DEPOSIT:
            return ledger_services.deposit(
                user_id=payment.user_id,
                currency=payment.currency,
                amount=payment.amount,
                idempotency_key=idempotency_key,
                description=description,
            )
        if payment.direction == Payment.Direction.WITHDRAWAL:
            return ledger_services.withdraw(
                user_id=payment.user_id,
                currency=payment.currency,
                amount=payment.amount,
                idempotency_key=idempotency_key,
                description=description,
            )
        return ledger_services.transfer_between_users(
            source_user_id=payment.user_id,
            destination_user_id=payment.destination_user_id,
            currency=payment.currency,
            amount=payment.amount,
            idempotency_key=idempotency_key,
            initiated_by_user_id=payment.user_id,
            description=description,
        )
    except (InsufficientFunds, InvalidAmount, KYCNotCompleted):
        raise
    except Exception as exc:
        logger.exception('No se pudo mover el saldo del pago %s', payment.id)
        raise ProviderError('No se pudo mover el saldo del pago.') from exc


def _resolve_idempotent(
    user_id: uuid.UUID,
    idempotency_key: str,
    request_hash: str,
) -> Payment | None:
    """Devuelve el pago original si la clave ya existe con el mismo payload.

    Raises:
        IdempotencyConflict: si la clave existe con un payload distinto.
    """
    existing = Payment.objects.filter(
        user_id=user_id,
        idempotency_key=idempotency_key,
    ).first()
    if existing is None:
        return None
    if existing.request_hash != request_hash:
        raise IdempotencyConflict('Ya existe una operación con esa clave de idempotencia.')
    return existing


def _recover_from_idempotency_race(
    user_id: uuid.UUID,
    idempotency_key: str,
    request_hash: str,
) -> Payment:
    """Resuelve la carrera de idempotencia devolviendo el pago original."""
    existing = _resolve_idempotent(user_id, idempotency_key, request_hash)
    if existing is None:
        raise
    return existing


def _mark_failed(payment: Payment, reason: str) -> None:
    """Marca el pago como fallido y deja el motivo."""
    payment.status = Payment.Status.FAILED
    payment.error = reason[:255]
    payment.save(update_fields=['status', 'error', 'updated_at'])


def _provider_by_name(provider_name: str):
    """Devuelve el proveedor con ese nombre.

    Args:
        provider_name: nombre del proveedor.

    Returns:
        El proveedor configurado.

    Raises:
        ProviderNotConfigured: si el nombre no corresponde a un proveedor.
    """
    configured = (settings.PAYMENTS_PROVIDER or providers.SIMULATED).strip().lower()
    if provider_name.strip().lower() != configured:
        raise ProviderNotConfigured(f'El proveedor "{provider_name}" no está habilitado.')
    return providers.get_provider()


def _find_payment(*, provider: str, info: WebhookEventInfo) -> Payment | None:
    """Busca el pago al que corresponde un evento del proveedor.

    Args:
        provider: nombre del proveedor.
        info: información del evento.

    Returns:
        El pago, o None si el evento no corresponde a ningún pago.
    """
    payment = Payment.objects.filter(
        provider=provider,
        provider_reference=info.reference,
    ).first()
    if payment is not None:
        return payment
    return Payment.objects.filter(
        provider=provider,
        payload__external_reference=info.reference,
    ).first()


def _parse_json(body: bytes) -> dict | None:
    """Parsea el cuerpo del webhook.

    Args:
        body: cuerpo crudo.

    Returns:
        El cuerpo parseado, o None si no es JSON válido.
    """
    try:
        parsed = json.loads(body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _assert_valid_amount(amount: Decimal) -> None:
    """Verifica que el importe sea un Decimal positivo.

    Raises:
        InvalidAmount: si el importe no cumple la condición.
    """
    if not isinstance(amount, Decimal):
        raise InvalidAmount('El importe debe ser un Decimal.')
    if amount <= 0:
        raise InvalidAmount('El importe debe ser mayor que cero.')


def _require_kyc(user_id: uuid.UUID) -> None:
    """Exige KYC aprobada para operar con dinero (AGENTS §9.9).

    Raises:
        KYCNotCompleted: si el usuario no tiene KYC aprobada.
    """
    if not is_kyc_approved(user_id=user_id):
        raise KYCNotCompleted('Necesitás completar la verificación KYC para operar con dinero.')
