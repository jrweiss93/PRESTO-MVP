"""Selectores de la app payments (interfaz pública de lectura)."""

import uuid

from django.db.models import QuerySet

from apps.payments.models import Payment, WebhookEvent


def get_payment(payment_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Payment | None:
    """Devuelve un pago por su identificador.

    Args:
        payment_id: identificador del pago.
        user_id: si viene, el pago tiene que ser de ese usuario.

    Returns:
        El pago, o None si no existe o no es del usuario.
    """
    queryset = Payment.objects.filter(pk=payment_id)
    if user_id is not None:
        queryset = queryset.filter(user_id=user_id)
    return queryset.first()


def list_payments_for_user(user_id: uuid.UUID) -> QuerySet[Payment]:
    """Lista los pagos del usuario, del más nuevo al más viejo.

    Args:
        user_id: identificador del usuario.

    Returns:
        El queryset de pagos del usuario.
    """
    return Payment.objects.filter(user_id=user_id).order_by('-created_at', '-id')


def list_webhook_events(provider: str) -> QuerySet[WebhookEvent]:
    """Lista los eventos de webhook de un proveedor.

    Args:
        provider: nombre del proveedor.

    Returns:
        El queryset de eventos del proveedor.
    """
    return WebhookEvent.objects.filter(provider=provider).order_by('-created_at', '-id')
