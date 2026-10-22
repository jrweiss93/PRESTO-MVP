"""System checks de la app core."""

from django.conf import settings
from django.core.checks import Warning


def check_legal_review_acknowledged(app_configs, **kwargs):
    """Avisa mientras la revisión legal y de PLA/FT esté pendiente.

    Es el **recordatorio de engineering**: no bloquea la aplicación (es un
    warning, no un error) pero aparece en `manage.py check`, en los logs del
    arranque y en el despliegue.

    Cuando el equipo terminó la revisión, se marca con
    `LEGAL_REVIEW_ACKNOWLEDGED=1` en el entorno y el aviso desaparece.
    """
    if settings.LEGAL_REVIEW_ACKNOWLEDGED:
        return []
    return [
        Warning(
            'La revisión legal y de PLA/FT está pendiente.',
            hint=(
                'Quedan puntos que necesitan validación profesional: '
                'PLA/FT, encuadre de custodia, copy del plazo fijo, CFT y '
                'registro en la CNV (ver docs/regulatorio-bcra.md). Cuando estén '
                'revisados, poné LEGAL_REVIEW_ACKNOWLEDGED=1 en el entorno.'
            ),
            id='legal.W001',
        )
    ]
