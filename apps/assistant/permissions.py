"""Permisos y límites de tasa del asistente."""

from rest_framework.throttling import ScopedRateThrottle


class AssistantThrottle(ScopedRateThrottle):
    """Limita el uso de Presti por usuario/IP.

    El scope lo define cada vista con `throttle_scope = 'assistant'`.
    """
