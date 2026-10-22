"""Proveedores de pagos.

El backend **no** habla con el proveedor directamente: habla con un
`PaymentProvider`. Así, cambiar de proveedor (o usar el simulado en el modo
demo y en los tests) no toca los servicios ni el ledger (ADR 0008).

Contrato de la interfaz:

- `create_deposit`: el usuario pone plata en la plataforma.
- `create_withdrawal`: el usuario saca plata de la plataforma.
- `create_transfer`: movimiento entre dos usuarios de Presto. El dinero no
  cruza la frontera del proveedor, así que se confirma de inmediato.
- `get_balance`: saldo de la cuenta del proveedor.
- `verify_webhook_signature`: valida la firma del webhook **antes** de
  parsearlo.
"""

import abc
import hashlib
import hmac
import json
import logging
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from apps.payments.exceptions import ProviderError, ProviderNotConfigured

logger = logging.getLogger(__name__)

SIMULATED = 'simulated'
MERCADO_PAGO = 'mercadopago'

#: Estados que devuelve un proveedor para una operación.
STATUS_CONFIRMED = 'confirmed'
STATUS_PENDING = 'pending'
STATUS_FAILED = 'failed'


@dataclass
class ProviderResult:
    """Resultado de una operación contra el proveedor.

    Attributes:
        external_id: identificador del pago en el proveedor.
        status: `confirmed`, `pending` o `failed`.
        payload: datos del proveedor (por ejemplo, el link de pago).
        checkout_url: link donde el usuario paga, si el proveedor lo da.
    """

    external_id: str
    status: str
    payload: dict = field(default_factory=dict)
    checkout_url: str = ''


@dataclass
class WebhookEventInfo:
    """Lo que el proveedor entiende de un evento de webhook.

    Attributes:
        external_id: identificador del evento en el proveedor.
        reference: referencia externa del pago (para encontrar el `Payment`).
        event_type: tipo del evento, ya traducido.
        status: `confirmed`, `failed` o `pending`.
        payload: cuerpo crudo del evento.
    """

    external_id: str
    reference: str
    event_type: str
    status: str
    payload: dict = field(default_factory=dict)


class PaymentProvider(abc.ABC):
    """Contrato que todo proveedor de pagos tiene que cumplir."""

    #: Código del proveedor, tal como se guarda en `Payment.provider`.
    name: str = ''

    @abc.abstractmethod
    def create_deposit(
        self,
        *,
        payment_id: uuid.UUID,
        user_email: str,
        amount: Decimal,
        currency: str,
        description: str = '',
    ) -> ProviderResult:
        """Crea un depósito a nombre de un usuario.

        Args:
            payment_id: identificador interno del pago.
            user_email: email del usuario, para la cuenta del proveedor.
            amount: importe del depósito.
            currency: moneda del depósito.
            description: descripción del depósito.

        Returns:
            El resultado con el identificador externo del pago.
        """

    @abc.abstractmethod
    def create_withdrawal(
        self,
        *,
        payment_id: uuid.UUID,
        user_email: str,
        amount: Decimal,
        currency: str,
        description: str = '',
        destination_account: str = '',
    ) -> ProviderResult:
        """Crea un retiro a nombre de un usuario.

        Args:
            payment_id: identificador interno del pago.
            user_email: email del usuario.
            amount: importe del retiro.
            currency: moneda del retiro.
            description: descripción del retiro.
            destination_account: cuenta externa donde se deposita el dinero.

        Returns:
            El resultado con el identificador externo del pago.
        """

    @abc.abstractmethod
    def create_transfer(
        self,
        *,
        payment_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        description: str = '',
    ) -> ProviderResult:
        """Crea una transferencia entre dos usuarios de Presto.

        Args:
            payment_id: identificador interno del pago.
            amount: importe de la transferencia.
            currency: moneda de la transferencia.
            description: descripción de la transferencia.

        Returns:
            El resultado con el identificador externo del pago.
        """

    @abc.abstractmethod
    def get_balance(self) -> Decimal:
        """Devuelve el saldo de la cuenta del proveedor.

        Returns:
            El saldo disponible en el proveedor.
        """

    @abc.abstractmethod
    def verify_webhook_signature(self, *, body: bytes, headers: dict[str, str]) -> bool:
        """Verifica la firma de un webhook.

        Args:
            body: cuerpo crudo del webhook (los bytes exactos).
            headers: headers de la petición.

        Returns:
            True si la firma es válida.
        """

    @abc.abstractmethod
    def parse_webhook_event(self, payload: dict) -> WebhookEventInfo:
        """Traduce el cuerpo de un webhook a la información del evento.

        Args:
            payload: cuerpo del webhook ya parseado.

        Returns:
            La información del evento con su estado.
        """


class SimulatedProvider(PaymentProvider):
    """Proveedor simulado: el que se usa en el modo demo y en los tests.

    No llama a nadie: devuelve una referencia externa ficticia. El movimiento
    del saldo lo hace `services.py` a través del ledger, igual que con el
    proveedor real.
    """

    name = SIMULATED

    def create_deposit(
        self,
        *,
        payment_id: uuid.UUID,
        user_email: str,
        amount: Decimal,
        currency: str,
        description: str = '',
    ) -> ProviderResult:
        """Devuelve una referencia simulada de depósito.

        Args:
            payment_id: identificador interno del pago.
            user_email: email del usuario.
            amount: importe del depósito.
            currency: moneda del depósito.
            description: descripción del depósito.

        Returns:
            El resultado simulado, confirmado de inmediato.
        """
        del user_email, description
        return ProviderResult(
            external_id=f'sim-{payment_id}',
            status=STATUS_CONFIRMED,
            payload={'simulated': True, 'amount': str(amount), 'currency': currency},
        )

    def create_withdrawal(
        self,
        *,
        payment_id: uuid.UUID,
        user_email: str,
        amount: Decimal,
        currency: str,
        description: str = '',
        destination_account: str = '',
    ) -> ProviderResult:
        """Devuelve una referencia simulada de retiro.

        Args:
            payment_id: identificador interno del pago.
            user_email: email del usuario.
            amount: importe del retiro.
            currency: moneda del retiro.
            description: descripción del retiro.
            destination_account: cuenta externa de destino.

        Returns:
            El resultado simulado, confirmado de inmediato.
        """
        del user_email, description, destination_account
        return ProviderResult(
            external_id=f'sim-{payment_id}',
            status=STATUS_CONFIRMED,
            payload={'simulated': True, 'amount': str(amount), 'currency': currency},
        )

    def create_transfer(
        self,
        *,
        payment_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        description: str = '',
    ) -> ProviderResult:
        """Devuelve una referencia simulada de transferencia.

        Args:
            payment_id: identificador interno del pago.
            amount: importe de la transferencia.
            currency: moneda de la transferencia.
            description: descripción de la transferencia.

        Returns:
            El resultado simulado, confirmado de inmediato.
        """
        del description
        return ProviderResult(
            external_id=f'sim-{payment_id}',
            status=STATUS_CONFIRMED,
            payload={'simulated': True, 'amount': str(amount), 'currency': currency},
        )

    def get_balance(self) -> Decimal:
        """Devuelve el saldo simulado.

        Returns:
            Un saldo simulado de cero.
        """
        return Decimal('0.00')

    def verify_webhook_signature(self, *, body: bytes, headers: dict[str, str]) -> bool:
        """Valida la firma del webhook simulado.

        Args:
            body: cuerpo crudo del webhook.
            headers: headers de la petición.

        Returns:
            True: el proveedor simulado no firma.
        """
        del body, headers
        return True

    def parse_webhook_event(self, payload: dict) -> WebhookEventInfo:
        """Traduce el cuerpo de un webhook simulado.

        Args:
            payload: cuerpo del webhook ya parseado.

        Returns:
            La información del evento.
        """
        external_id = str(payload.get('id', '') or payload.get('external_id', ''))
        reference = str(payload.get('external_reference', '') or external_id)
        event_type = str(payload.get('action', '') or payload.get('event_type', ''))
        status = str(payload.get('status', STATUS_PENDING) or STATUS_PENDING)
        if status not in (STATUS_CONFIRMED, STATUS_FAILED, STATUS_PENDING):
            status = STATUS_PENDING
        return WebhookEventInfo(
            external_id=external_id,
            reference=reference,
            event_type=event_type,
            status=status,
            payload=payload,
        )


class MercadoPagoProvider(PaymentProvider):
    """Proveedor real: Mercado Pago.

    Habla con la API de Mercado Pago por HTTP. La firma de los webhooks se
    valida con HMAC-SHA256 sobre el manifest `id;request-id;ts` y el cuerpo
    crudo, tal como la documenta Mercado Pago.

    **No hay contrato comercial cerrado**: las credenciales llegan por
    variables de entorno y, sin ellas, el proveedor no se puede construir
    (ADR 0008).
    """

    name = MERCADO_PAGO

    def __init__(self, access_token: str = '', webhook_secret: str = '', base_url: str = ''):
        """Construye el proveedor con sus credenciales.

        Args:
            access_token: token de acceso a la API de Mercado Pago.
            webhook_secret: secreto de firma de los webhooks.
            base_url: raíz de la API.

        Raises:
            ProviderNotConfigured: si falta el token de acceso.
        """
        if not access_token:
            raise ProviderNotConfigured(
                'Falta MERCADO_PAGO_ACCESS_TOKEN: el proveedor real no está configurado.'
            )
        self.access_token = access_token
        self.webhook_secret = webhook_secret
        self.base_url = base_url or 'https://api.mercadopago.com'

    def create_deposit(
        self,
        *,
        payment_id: uuid.UUID,
        user_email: str,
        amount: Decimal,
        currency: str,
        description: str = '',
    ) -> ProviderResult:
        """Crea un checkout de Mercado Pago para que el usuario deposite.

        Args:
            payment_id: identificador interno del pago.
            user_email: email del usuario.
            amount: importe del depósito.
            currency: moneda del depósito.
            description: descripción del depósito.

        Returns:
            El resultado con la preferencia creada y el link de pago.

        Raises:
            ProviderError: si la API de Mercado Pago responde con un error.
        """
        payload = {
            'items': [
                {
                    'title': description or 'Depósito en Presto',
                    'quantity': 1,
                    'unit_price': str(amount),
                    'currency_id': currency,
                }
            ],
            'payer': {'email': user_email},
            'external_reference': str(payment_id),
            'notification_url': settings.MERCADO_PAGO_WEBHOOK_URL,
        }
        response = self._request('POST', '/v1/payments/preference', payload)
        return ProviderResult(
            external_id=str(response.get('id', payment_id)),
            status=STATUS_PENDING,
            payload=response,
            checkout_url=str(response.get('init_point', '')),
        )

    def create_withdrawal(
        self,
        *,
        payment_id: uuid.UUID,
        user_email: str,
        amount: Decimal,
        currency: str,
        description: str = '',
        destination_account: str = '',
    ) -> ProviderResult:
        """Pide un retiro (cash out) en Mercado Pago.

        Args:
            payment_id: identificador interno del pago.
            user_email: email del usuario.
            amount: importe del retiro.
            currency: moneda del retiro.
            description: descripción del retiro.
            destination_account: cuenta externa donde se deposita el dinero.

        Returns:
            El resultado con el identificador del retiro.

        Raises:
            ProviderError: si la API de Mercado Pago responde con un error.
            ProviderNotConfigured: si el retiro no tiene cuenta de destino.
        """
        if not destination_account:
            raise ProviderNotConfigured(
                'El retiro necesita la cuenta externa de destino del usuario.'
            )
        payload = {
            'amount': str(amount),
            'currency_id': currency,
            'description': description or 'Retiro de Presto',
            'destination_id': destination_account,
            'external_reference': str(payment_id),
        }
        response = self._request('POST', '/v1/cashout', payload)
        return ProviderResult(
            external_id=str(response.get('id', payment_id)),
            status=STATUS_PENDING,
            payload=response,
        )

    def create_transfer(
        self,
        *,
        payment_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        description: str = '',
    ) -> ProviderResult:
        """Confirma la transferencia interna entre dos usuarios de Presto.

        Los dos usuarios están dentro de la plataforma: el dinero no cruza la
        frontera del proveedor, así que no hay llamada externa.

        Args:
            payment_id: identificador interno del pago.
            amount: importe de la transferencia.
            currency: moneda de la transferencia.
            description: descripción de la transferencia.

        Returns:
            El resultado, confirmado de inmediato.
        """
        del description
        return ProviderResult(
            external_id=f'transfer-{payment_id}',
            status=STATUS_CONFIRMED,
            payload={'internal': True, 'amount': str(amount), 'currency': currency},
        )

    def get_balance(self) -> Decimal:
        """Devuelve el saldo de la cuenta de Mercado Pago.

        Returns:
            El saldo disponible en el proveedor.

        Raises:
            ProviderError: si la API de Mercado Pago responde con un error.
        """
        response = self._request('GET', '/v1/account/balance', None)
        balance = response.get('balance')
        if balance is None:
            return Decimal('0.00')
        return Decimal(str(balance))

    def verify_webhook_signature(self, *, body: bytes, headers: dict[str, str]) -> bool:
        """Valida la firma HMAC-SHA256 de un webhook de Mercado Pago.

        La firma viene en el header `x-signature` con el formato
        `ts=<unix>,v1=<hmac>`. El HMAC se calcula sobre el manifest
        `id:<data.id>;request-id:<x-request-id>;ts:<ts>;` y, si el `data.id`
        es alfanumérico, también sobre el cuerpo crudo.

        Args:
            body: cuerpo crudo del webhook.
            headers: headers de la petición.

        Returns:
            True si la firma es válida.
        """
        if not self.webhook_secret:
            logger.error('No hay secreto de webhook configurado: se rechaza el evento.')
            return False
        signature_header = ''
        for key, value in headers.items():
            if key.lower() == 'x-signature':
                signature_header = value
                break
        if not signature_header:
            return False
        parts = dict(piece.split('=', 1) for piece in signature_header.split(',') if '=' in piece)
        timestamp = parts.get('ts', '')
        received_signature = parts.get('v1', '')
        if not timestamp or not received_signature:
            return False
        try:
            timestamp_value = int(timestamp)
        except ValueError:
            return False
        max_age = settings.PAYMENTS_WEBHOOK_MAX_AGE_SECONDS
        if abs(int(time.time()) - timestamp_value) > max_age:
            logger.warning('Webhook de Mercado Pago con timestamp vencido: %s', timestamp)
            return False
        data = self._parse_body(body)
        data_id = self._extract_data_id(data)
        request_id = ''
        for key, value in headers.items():
            if key.lower() == 'x-request-id':
                request_id = value
                break
        manifest = f'id:{data_id};request-id:{request_id};ts:{timestamp};'
        if data_id.isalnum():
            manifest += body.decode('utf-8', errors='replace')
        expected = hmac.new(
            self.webhook_secret.encode('utf-8'),
            manifest.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, received_signature)

    def _parse_body(self, body: bytes) -> dict:
        """Parsea el cuerpo del webhook sin fallar.

        Args:
            body: cuerpo crudo del webhook.

        Returns:
            El cuerpo parseado, o un diccionario vacío si no es JSON válido.
        """
        try:
            parsed = json.loads(body.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _extract_data_id(payload: dict) -> str:
        """Devuelve el identificador del pago de un webhook de Mercado Pago.

        Mercado Pago manda el id del pago dentro de `data.id`; el `id` de la
        raíz es el del **evento**.

        Args:
            payload: cuerpo del webhook ya parseado.

        Returns:
            El identificador del pago, o una cadena vacía.
        """
        data = payload.get('data')
        if isinstance(data, dict) and data.get('id') is not None:
            return str(data['id'])
        return str(payload.get('id', '') or '')

    def parse_webhook_event(self, payload: dict) -> WebhookEventInfo:
        """Traduce un webhook de Mercado Pago a la información del evento.

        Mercado Pago manda el evento con un `action` (`payment.approved`,
        `payment.rejected`, `cashout.approved`, ...) y los datos del pago en
        `data`. La referencia externa (`external_reference`) es la que
        identifica el pago de Presto.

        Args:
            payload: cuerpo del webhook ya parseado.

        Returns:
            La información del evento con su estado.
        """
        data = payload.get('data')
        data = data if isinstance(data, dict) else {}
        attributes = data.get('attributes')
        attributes = attributes if isinstance(attributes, dict) else {}
        action = str(payload.get('action', '') or attributes.get('status', ''))
        external_id = self._extract_data_id(payload)
        reference = str(attributes.get('external_reference', '') or external_id)
        return WebhookEventInfo(
            external_id=external_id,
            reference=reference,
            event_type=action,
            status=self._status_from_action(action),
            payload=payload,
        )

    @staticmethod
    def _status_from_action(action: str) -> str:
        """Traduce la acción del webhook al estado del pago.

        Args:
            action: acción del webhook de Mercado Pago.

        Returns:
            `confirmed`, `failed` o `pending`.
        """
        normalized = action.strip().lower()
        if normalized in ('payment.approved', 'cashout.approved', 'payment.completed'):
            return STATUS_CONFIRMED
        if normalized in (
            'payment.rejected',
            'payment.cancelled',
            'payment.canceled',
            'payment.refunded',
            'cashout.rejected',
        ):
            return STATUS_FAILED
        return STATUS_PENDING

    def _request(self, method: str, path: str, payload: dict | None) -> dict:
        """Llama a la API de Mercado Pago.

        Args:
            method: método HTTP.
            path: ruta relativa a la raíz de la API.
            payload: cuerpo JSON, o None para un GET.

        Returns:
            La respuesta parseada.

        Raises:
            ProviderError: si la API responde con un error o no se puede llamar.
        """
        url = f'{self.base_url}{path}'
        data = json.dumps(payload).encode('utf-8') if payload is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header('Authorization', f'Bearer {self.access_token}')
        request.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(
                request, timeout=settings.PAYMENTS_HTTP_TIMEOUT
            ) as response:
                body = response.read().decode('utf-8')
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='replace')
            logger.error('Mercado Pago respondió %s en %s: %s', exc.code, path, detail)
            raise ProviderError(f'Mercado Pago respondió un error ({exc.code}).') from exc
        except urllib.error.URLError as exc:
            logger.error('No se pudo llamar a Mercado Pago en %s: %s', path, exc)
            raise ProviderError('No se pudo contactar al proveedor de pagos.') from exc
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError('Mercado Pago devolvió una respuesta ilegible.') from exc
        return parsed if isinstance(parsed, dict) else {}


def get_provider() -> PaymentProvider:
    """Devuelve el proveedor de pagos configurado.

    Returns:
        El proveedor según `PAYMENTS_PROVIDER`.

    Raises:
        ProviderNotConfigured: si el nombre del proveedor no es conocido.
    """
    name = (settings.PAYMENTS_PROVIDER or SIMULATED).strip().lower()
    if name == SIMULATED:
        return SimulatedProvider()
    if name == MERCADO_PAGO:
        return MercadoPagoProvider(
            access_token=settings.MERCADO_PAGO_ACCESS_TOKEN,
            webhook_secret=settings.MERCADO_PAGO_WEBHOOK_SECRET,
            base_url=settings.MERCADO_PAGO_BASE_URL,
        )
    raise ProviderNotConfigured(f'El proveedor de pagos "{name}" no existe.')
