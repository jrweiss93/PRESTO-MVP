"""Receptores de las señales de las apps emisoras (AGENTS §5.3).

Cada receptor hace una sola cosa y delega en un servicio. Acá solo se escucha la
aprobación de KYC para acreditar el regalo de bienvenida al prestatario.
"""

import logging

from django.dispatch import receiver

from apps.demo.welcome import grant_welcome_bonus
from apps.identity.signals import kyc_approved

logger = logging.getLogger(__name__)


@receiver(kyc_approved)
def grant_welcome_bonus_on_kyc_approved(sender, user_id, **kwargs):
    """Acredita el regalo de bienvenida al prestatario cuya identidad se verificó.

    `grant_welcome_bonus` es idempotente y solo actúa sobre el perfil prestatario
    en modo demo: no hace nada (ni falla) para prestamistas, inversores o fuera
    del modo demo. El receptor nunca propaga errores: la señal no debe romper el
    flujo que aprobó el KYC.
    """
    try:
        grant_welcome_bonus(user_id)
    except Exception:
        logger.warning(
            'Fallo al procesar el bono de bienvenida en el receptor: user_id=%s',
            user_id,
            exc_info=True,
        )
