"""Permisos y límites de tasa de la app payments."""

from rest_framework.throttling import ScopedRateThrottle


class WebhookThrottle(ScopedRateThrottle):
    """Limita los webhooks del proveedor a 60 por minuto.

    El scope lo define la vista con `throttle_scope = 'webhook'`. Un
    proveedor manda varios eventos juntos (aprobado, actualizado, fallido):
    un límite muy bajo los rechazaría.
    """
