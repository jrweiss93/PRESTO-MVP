"""Errores de dominio de la app payments."""

from apps.core.exceptions import DomainError


class PaymentError(DomainError):
    """Error genérico de la app payments."""


class IdempotencyConflict(PaymentError):
    """Ya existe un pago con esa clave de idempotencia y otro payload."""


class ProviderNotConfigured(PaymentError):
    """El proveedor de pagos no está configurado."""


class ProviderError(PaymentError):
    """El proveedor de pagos falló o respondió algo inesperado."""


class InvalidWebhookSignature(PaymentError):
    """La firma del webhook no es válida."""


class WebhookNotFound(PaymentError):
    """El evento del webhook no corresponde a ningún pago."""


class DestinationAccountRequired(PaymentError):
    """La transferencia necesita una cuenta de destino."""
