"""Modelos de la app payments.

El `Payment` es la **intención** de mover dinero hacia adentro (depósito) o
hacia afuera (retiro) de la plataforma, y el registro de lo que el proveedor
confirmó. El saldo del usuario **no** vive acá: vive en el ledger, que es la
fuente de verdad (ADR 0008).
"""

from decimal import Decimal

from django.db import models

from apps.core.models import BaseModel


class Payment(BaseModel):
    """Intención de pago de un usuario contra un proveedor externo.

    La fila se crea **antes** de llamar al proveedor: es la bitácora de la
    operación y garantiza que un webhook pueda encontrar el pago aunque el
    cliente haya cerrado la conexión.
    """

    class Direction(models.TextChoices):
        DEPOSIT = 'deposit', 'Depósito'
        WITHDRAWAL = 'withdrawal', 'Retiro'
        TRANSFER = 'transfer', 'Transferencia'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        CONFIRMED = 'confirmed', 'Confirmado'
        FAILED = 'failed', 'Fallido'
        REVERSED = 'reversed', 'Reversado'

    class Currency(models.TextChoices):
        ARS = 'ARS', 'Peso argentino'
        USD = 'USD', 'Dólar'

    class Provider(models.TextChoices):
        SIMULATED = 'simulated', 'Simulado'
        MERCADO_PAGO = 'mercadopago', 'Mercado Pago'

    user_id = models.UUIDField()
    direction = models.CharField(max_length=16, choices=Direction.choices)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    provider = models.CharField(max_length=16, choices=Provider.choices)
    provider_reference = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=100)
    request_hash = models.CharField(max_length=64)
    ledger_transaction_id = models.UUIDField(null=True, blank=True)
    destination_user_id = models.UUIDField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    error = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_id', 'idempotency_key'],
                name='payments_payment_idempotency_per_user',
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='payments_payment_amount_positive',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Devuelve una descripción legible del pago."""
        return f'{self.direction} {self.amount} {self.currency} ({self.status})'


class WebhookEvent(BaseModel):
    """Evento recibido de un proveedor de pagos.

    Guarda el evento **antes** de procesarlo: la única
    `UniqueConstraint` por `(provider, external_id)` hace que un webhook
    repetido no mueva el saldo dos veces (ADR 0008).
    """

    class Status(models.TextChoices):
        RECEIVED = 'received', 'Recibido'
        PROCESSED = 'processed', 'Procesado'
        IGNORED = 'ignored', 'Ignorado'
        FAILED = 'failed', 'Fallido'

    provider = models.CharField(max_length=16)
    external_id = models.CharField(max_length=128)
    event_type = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    payment_id = models.UUIDField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    error = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'external_id'],
                name='payments_webhook_event_unique_per_provider',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Devuelve una descripción legible del evento."""
        return f'{self.provider}:{self.external_id} ({self.status})'
