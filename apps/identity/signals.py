"""Señales de la app identity (AGENTS §5.3).

Las define la app emisora: los receptores de otras apps (p. ej. `demo`) se
conectan a estas señales. Solo llevan identificadores, nunca datos del negocio.
"""

from django.dispatch import Signal

# Verificación KYC aprobada (la recibe quien quiera reaccionar a una identidad
# verificada, p. ej. para acreditar el regalo de bienvenida).
kyc_approved = Signal()
