"""Regalo de bienvenida: acredita dinero simulado a la persona prestataria.

Vive en la app `demo` porque necesita hablar con `identity` y con `ledger`
(ver el contrato `demo-only-services-and-selectors` en `.importlinter`): la
app `identity` no puede importar `ledger`, así que el servicio que mueve el
dinero se orquesta acá.
"""

import logging
from decimal import Decimal

from django.conf import settings

from apps.identity import selectors as identity_selectors
from apps.ledger import services as ledger_services

logger = logging.getLogger(__name__)

#: Importe del regalo de bienvenida (solo para el perfil prestatario).
WELCOME_BONUS_AMOUNT = Decimal('100000.00')
WELCOME_BONUS_CURRENCY = 'ARS'


def grant_welcome_bonus(user_id) -> bool:
    """Acredita el regalo de bienvenida a una persona prestataria, una sola vez.

    Es **idempotente**: usa una clave fija (`welcome-bonus-{user_id}`), así que
    volver a llamarlo no duplica el crédito. Solo se acredita en **modo demo**
    (con depósitos simulados habilitados) y solo al perfil prestatario. Nunca
    propaga errores: un fallo acá no debe romper la aprobación de KYC ni los
    tests.

    Args:
        user_id: identificador de la persona.

    Returns:
        True si se acreditó (o ya estaba acreditado); False si no corresponde.
    """
    if not getattr(settings, 'DEMO_MODE', False):
        return False
    if not settings.LEDGER_SIMULATED_DEPOSITS_ENABLED:
        return False
    try:
        active = identity_selectors.get_active_profile(user_id)
        if active is None or active.kind != 'borrower':
            return False
        ledger_services.deposit(
            user_id=user_id,
            currency=WELCOME_BONUS_CURRENCY,
            amount=WELCOME_BONUS_AMOUNT,
            idempotency_key=f'welcome-bonus-{user_id}',
            description='Regalo de bienvenida',
        )
        return True
    except Exception:
        logger.warning(
            'No se pudo acreditar el regalo de bienvenida: user_id=%s', user_id, exc_info=True
        )
        return False
