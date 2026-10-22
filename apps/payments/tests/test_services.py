"""Tests de los servicios de payments."""

import hashlib
import hmac
import json
import time
from decimal import Decimal

import pytest

from apps.core.exceptions import InsufficientFunds, KYCNotCompleted
from apps.payments import providers
from apps.payments.exceptions import (
    DestinationAccountRequired,
    IdempotencyConflict,
    InvalidWebhookSignature,
    ProviderError,
)
from apps.payments.models import Payment, WebhookEvent
from apps.payments.services import create_payment, handle_webhook
from apps.payments.tests.factories import create_approved_user

pytestmark = pytest.mark.django_db


class PendingProvider(providers.PaymentProvider):
    """Proveidor de test: deja el pago pendiente hasta que llega el webhook."""

    name = 'simulated'

    def create_deposit(self, **kwargs):
        """Deja el depósito pendiente."""
        return providers.ProviderResult(external_id='pending-ref', status=providers.STATUS_PENDING)

    def create_withdrawal(self, **kwargs):
        """Deja el retiro pendiente."""
        return providers.ProviderResult(external_id='pending-ref', status=providers.STATUS_PENDING)

    def create_transfer(self, **kwargs):
        """Deja la transferencia pendiente."""
        return providers.ProviderResult(external_id='pending-ref', status=providers.STATUS_PENDING)

    def get_balance(self):
        """No hay saldo real en el proveedor de test."""
        return Decimal('0.00')

    def verify_webhook_signature(self, *, body, headers):
        """El proveedor de test no firma: acepta todo."""
        return True

    def parse_webhook_event(self, payload):
        """Traduce el webhook de test."""
        return providers.WebhookEventInfo(
            external_id=str(payload.get('id', '')),
            reference=str(payload.get('external_reference', '')),
            event_type=str(payload.get('action', '')),
            status=str(payload.get('status', providers.STATUS_PENDING)),
            payload=payload,
        )


@pytest.fixture
def user():
    """Usuario con KYC aprobada."""
    return create_approved_user()


def test_create_deposit_moves_the_money(user):
    """Un depósito simulado acredita la billetera del usuario."""
    payment = create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-1',
    )

    assert payment.status == Payment.Status.CONFIRMED
    assert payment.ledger_transaction_id is not None
    assert _balance(user.id, 'ARS') == Decimal('1000.00')


def test_create_deposit_is_idempotent(user):
    """La misma clave con el mismo payload devuelve el mismo pago."""
    first = create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-2',
    )
    second = create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-2',
    )

    assert first.id == second.id
    assert Payment.objects.count() == 1


def test_create_deposit_with_the_same_key_and_other_payload_conflicts(user):
    """La misma clave con otro payload es un conflicto."""
    create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-3',
    )

    with pytest.raises(IdempotencyConflict):
        create_payment(
            user_id=user.id,
            direction=Payment.Direction.DEPOSIT,
            amount=Decimal('2000.00'),
            currency=Payment.Currency.ARS,
            idempotency_key='dep-3',
        )


def test_create_deposit_requires_kyc():
    """Sin KYC no se puede mover dinero."""
    from apps.identity.services import register_user

    user = register_user(email='sin-kyc@example.com', password='TestPass123!')

    with pytest.raises(KYCNotCompleted):
        create_payment(
            user_id=user.id,
            direction=Payment.Direction.DEPOSIT,
            amount=Decimal('1000.00'),
            currency=Payment.Currency.ARS,
            idempotency_key='dep-4',
        )


def test_create_deposit_rejects_a_non_positive_amount(user):
    """El importe tiene que ser mayor que cero."""
    from apps.core.exceptions import InvalidAmount

    with pytest.raises(InvalidAmount):
        create_payment(
            user_id=user.id,
            direction=Payment.Direction.DEPOSIT,
            amount=Decimal('0.00'),
            currency=Payment.Currency.ARS,
            idempotency_key='dep-5',
        )


def test_create_withdrawal_without_funds_fails(user):
    """Un retiro sin saldo no se confirma."""
    with pytest.raises(InsufficientFunds):
        create_payment(
            user_id=user.id,
            direction=Payment.Direction.WITHDRAWAL,
            amount=Decimal('500.00'),
            currency=Payment.Currency.ARS,
            idempotency_key='ret-1',
        )


def test_create_transfer_moves_the_money_to_the_destination(user):
    """Una transferencia mueve el saldo a la billetera del otro usuario."""
    destination = create_approved_user(email='destino@example.com')
    create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-6',
    )

    payment = create_payment(
        user_id=user.id,
        direction=Payment.Direction.TRANSFER,
        amount=Decimal('250.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='tra-1',
        destination_user_id=destination.id,
    )

    assert payment.status == Payment.Status.CONFIRMED
    assert _balance(user.id, 'ARS') == Decimal('750.00')
    assert _balance(destination.id, 'ARS') == Decimal('250.00')


def test_create_transfer_without_destination_fails(user):
    """Una transferencia sin cuenta de destino es un error."""
    with pytest.raises(DestinationAccountRequired):
        create_payment(
            user_id=user.id,
            direction=Payment.Direction.TRANSFER,
            amount=Decimal('250.00'),
            currency=Payment.Currency.ARS,
            idempotency_key='tra-2',
        )


def test_create_payment_marks_the_payment_failed_when_the_provider_fails(user, monkeypatch):
    """Si el proveedor falla, el pago queda fallido."""

    class FailingProvider(providers.PaymentProvider):
        """Proveedor que siempre falla."""

        name = 'simulated'

        def create_deposit(self, **kwargs):
            """Falla siempre."""
            raise ProviderError('El proveedor no está disponible.')

        def create_withdrawal(self, **kwargs):
            """Falla siempre."""
            raise ProviderError('El proveedor no está disponible.')

        def create_transfer(self, **kwargs):
            """Falla siempre."""
            raise ProviderError('El proveedor no está disponible.')

        def get_balance(self):
            """No hay saldo."""
            return Decimal('0.00')

        def verify_webhook_signature(self, *, body, headers):
            """No firma."""
            return True

        def parse_webhook_event(self, payload):
            """No hay eventos."""
            return providers.WebhookEventInfo('', '', '', providers.STATUS_PENDING, payload)

    monkeypatch.setattr(providers, 'get_provider', lambda: FailingProvider())

    with pytest.raises(ProviderError):
        create_payment(
            user_id=user.id,
            direction=Payment.Direction.DEPOSIT,
            amount=Decimal('100.00'),
            currency=Payment.Currency.ARS,
            idempotency_key='dep-7',
        )

    payment = Payment.objects.get(idempotency_key='dep-7')
    assert payment.status == Payment.Status.FAILED
    assert payment.error


def test_webhook_confirms_the_payment_and_moves_the_money(user, monkeypatch):
    """El webhook firmado confirma el pago pendiente y mueve el saldo."""
    monkeypatch.setattr(providers, 'get_provider', lambda: PendingProvider())
    payment = create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-8',
    )
    assert payment.status == Payment.Status.PENDING

    body = json.dumps(
        {
            'id': 'evento-1',
            'action': 'payment.approved',
            'status': 'confirmed',
            'external_reference': str(payment.id),
        }
    ).encode('utf-8')
    event = handle_webhook(
        provider_name='simulated',
        body=body,
        headers={'content-type': 'application/json'},
    )

    assert event.status == WebhookEvent.Status.PROCESSED
    payment.refresh_from_db()
    assert payment.status == Payment.Status.CONFIRMED
    assert _balance(user.id, 'ARS') == Decimal('1000.00')


def test_webhook_repeated_does_not_move_the_money_twice(user, monkeypatch):
    """Un webhook repetido no mueve el saldo dos veces."""
    monkeypatch.setattr(providers, 'get_provider', lambda: PendingProvider())
    payment = create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-9',
    )
    body = json.dumps(
        {
            'id': 'evento-2',
            'action': 'payment.approved',
            'status': 'confirmed',
            'external_reference': str(payment.id),
        }
    ).encode('utf-8')

    handle_webhook(provider_name='simulated', body=body, headers={})
    handle_webhook(provider_name='simulated', body=body, headers={})

    assert _balance(user.id, 'ARS') == Decimal('1000.00')
    assert WebhookEvent.objects.filter(external_id='evento-2').count() == 1


def test_webhook_with_an_invalid_signature_is_rejected(user, monkeypatch):
    """Con la firma inválida no se toca el ledger."""

    class StrictProvider(PendingProvider):
        """Proveidor que exige una firma concreta."""

        def verify_webhook_signature(self, *, body, headers):
            """Solo acepta la firma `ok`."""
            return headers.get('x-signature') == 'ok'

    monkeypatch.setattr(providers, 'get_provider', lambda: StrictProvider())
    payment = create_payment(
        user_id=user.id,
        direction=Payment.Direction.DEPOSIT,
        amount=Decimal('1000.00'),
        currency=Payment.Currency.ARS,
        idempotency_key='dep-10',
    )
    body = json.dumps(
        {
            'id': 'evento-3',
            'action': 'payment.approved',
            'status': 'confirmed',
            'external_reference': str(payment.id),
        }
    ).encode('utf-8')

    with pytest.raises(InvalidWebhookSignature):
        handle_webhook(provider_name='simulated', body=body, headers={'x-signature': 'mala'})

    assert _balance(user.id, 'ARS') == Decimal('0.00')
    payment.refresh_from_db()
    assert payment.status == Payment.Status.PENDING


def test_mercado_pago_signature_is_validated(settings):
    """La firma de Mercado Pago se valida con HMAC-SHA256 sobre el manifest."""
    settings.MERCADO_PAGO_ACCESS_TOKEN = 'token-de-prueba'
    settings.PAYMENTS_WEBHOOK_MAX_AGE_SECONDS = 300
    provider = providers.MercadoPagoProvider(
        access_token='token-de-prueba',
        webhook_secret='secreto-de-prueba',
    )
    body = json.dumps({'action': 'payment.approved', 'data': {'id': '12345'}}).encode('utf-8')
    timestamp = int(time.time())
    manifest = f'id:12345;request-id:req-1;ts:{timestamp};'
    expected = hmac.new(
        b'secreto-de-prueba',
        (manifest + body.decode('utf-8')).encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        'x-signature': f'ts={timestamp},v1={expected}',
        'x-request-id': 'req-1',
    }

    assert provider.verify_webhook_signature(body=body, headers=headers) is True


def test_mercado_pago_signature_with_a_wrong_secret_is_rejected(settings):
    """Una firma hecha con otro secreto no se acepta."""
    provider = providers.MercadoPagoProvider(
        access_token='token-de-prueba',
        webhook_secret='secreto-de-prueba',
    )
    body = json.dumps({'action': 'payment.approved', 'data': {'id': '12345'}}).encode('utf-8')
    timestamp = int(time.time())
    expected = hmac.new(
        b'otro-secreto',
        f'id:12345;request-id:req-1;ts:{timestamp};'.encode(),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        'x-signature': f'ts={timestamp},v1={expected}',
        'x-request-id': 'req-1',
    }

    assert provider.verify_webhook_signature(body=body, headers=headers) is False


def test_mercado_pago_signature_with_an_old_timestamp_is_rejected(settings):
    """Una firma vieja no se acepta: evita que alguien la reenvíe."""
    provider = providers.MercadoPagoProvider(
        access_token='token-de-prueba',
        webhook_secret='secreto-de-prueba',
    )
    body = json.dumps({'action': 'payment.approved', 'data': {'id': '12345'}}).encode('utf-8')
    timestamp = int(time.time()) - 3600
    expected = hmac.new(
        b'secreto-de-prueba',
        f'id:12345;request-id:req-1;ts:{timestamp};'.encode(),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        'x-signature': f'ts={timestamp},v1={expected}',
        'x-request-id': 'req-1',
    }

    assert provider.verify_webhook_signature(body=body, headers=headers) is False


def test_mercado_pago_provider_needs_credentials(settings):
    """Sin token de acceso el proveedor real no se puede construir."""
    from apps.payments.exceptions import ProviderNotConfigured

    with pytest.raises(ProviderNotConfigured):
        providers.MercadoPagoProvider(access_token='')


def _wallet_id(user_id):
    """Devuelve el id de la billetera del usuario en pesos."""
    from apps.ledger.selectors import list_accounts_for_user

    accounts = list_accounts_for_user(user_id=user_id).filter(currency='ARS')
    return accounts.first().id


def _balance(user_id, currency):
    """Devuelve el saldo de la billetera del usuario en esa moneda."""
    from apps.ledger.selectors import get_user_wallet

    wallet = get_user_wallet(user_id=user_id, currency=currency)
    return wallet.balance if wallet is not None else Decimal('0.00')
