"""Permisos de la app investments."""

from rest_framework.permissions import BasePermission

from apps.identity.selectors import get_active_profile


class IsInvestor(BasePermission):
    """Permite la lectura de inversiones solo con el perfil Inversor activo."""

    message = 'Para invertir necesitás activar el perfil Inversor.'

    def has_permission(self, request, view) -> bool:
        """Devuelve True solo si el perfil activo es `investor`."""
        user = request.user
        if not (user and user.is_authenticated):
            return False
        active = get_active_profile(user_id=user.id)
        return active is not None and active.kind == 'investor'
