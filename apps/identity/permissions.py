"""Permisos y límites de tasa de la app identity."""

from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.throttling import ScopedRateThrottle

from apps.identity.selectors import (
    get_active_profile,
    has_verified_backup_account,
    is_kyc_approved,
)


class LoginThrottle(ScopedRateThrottle):
    """Limita los intentos de login a 5 por minuto (AGENTS §9.6).

    El scope lo define la vista con `throttle_scope = 'login'`.
    """


class RegisterThrottle(ScopedRateThrottle):
    """Limita los registros a 5 por hora (AGENTS §9.6).

    El scope lo define la vista con `throttle_scope = 'register'`.
    """


class PasswordResetThrottle(ScopedRateThrottle):
    """Limita los pedidos de reseteo de contraseña por IP.

    El scope lo define la vista con `throttle_scope = 'password_reset'`.
    """


class EmailVerificationThrottle(ScopedRateThrottle):
    """Limita los pedidos y reenvíos de verificación de email por IP.

    El scope lo define la vista con `throttle_scope = 'email_verification'`.
    """


class IsKycApproved(BasePermission):
    """Permite el acceso solo a usuarios con verificación KYC aprobada (AGENTS §9.9)."""

    message = 'Necesitás completar la verificación KYC para realizar esta operación.'

    def has_permission(self, request, view) -> bool:
        """Devuelve True solo si el usuario autenticado tiene KYC aprobada."""
        user = request.user
        return bool(user and user.is_authenticated and is_kyc_approved(user_id=user.id))


class KycApprovedForUnsafeMethods:
    """Exige KYC aprobada en las operaciones que mueven dinero.

    Las lecturas no cambian: siguen exigiendo solo autenticación. El control
    equivalente en la capa de services sigue vigente (defense in depth): este
    permiso da el `403` temprano y explícito de AGENTS §9.9, antes de tocar
    el saldo.
    """

    def get_permissions(self):
        """Agrega `IsKycApproved` a los métodos que no son de lectura."""
        permissions = list(super().get_permissions())
        if self.request.method not in SAFE_METHODS:
            permissions.append(IsKycApproved())
        return permissions


class HasVerifiedBackupAccount(BasePermission):
    """Exige una cuenta de respaldo verificada para aceptar un préstamo."""

    message = 'Vinculá y verificá una cuenta de respaldo antes de aceptar un préstamo.'

    def has_permission(self, request, view) -> bool:
        """Devuelve True si la exigencia está apagada o hay una cuenta verificada."""
        if not settings.REPAYMENT_SOURCE_REQUIRED:
            return True
        user = request.user
        return bool(user and user.is_authenticated and has_verified_backup_account(user_id=user.id))


class IsActiveProfile(BasePermission):
    """Permite operar solo con un perfil de Presto concreto activo.

    El chequeo de KYC corre antes (ver `ActiveProfileForUnsafeMethods`): si el
    usuario no tiene KYC aprobada, recibe el `403` de KYC; recién con KYC se
    valida que el perfil activo sea el adecuado para la operación.
    """

    messages = {
        'borrower': 'Para pedir préstamos necesitás activar el perfil Prestatario.',
        'lender': 'Para prestar necesitás activar el perfil Prestamista.',
        'investor': 'Para invertir necesitás activar el perfil Inversor.',
    }

    def __init__(self, profile_kind: str):
        """Guarda el tipo de perfil que exige la operación.

        Args:
            profile_kind: tipo de perfil (`borrower`, `lender` o `investor`).
        """
        self.profile_kind = profile_kind
        self.message = self.messages.get(
            profile_kind, 'El perfil activo no permite realizar esta operación.'
        )

    def has_permission(self, request, view) -> bool:
        """Devuelve True solo si el perfil activo es el que exige la operación."""
        user = request.user
        if not (user and user.is_authenticated):
            return False
        active = get_active_profile(user_id=user.id)
        return active is not None and active.kind == self.profile_kind


class ActiveProfileForUnsafeMethods(KycApprovedForUnsafeMethods):
    """Exige KYC y un perfil activo concreto en las operaciones que mueven dinero.

    Hereda de `KycApprovedForUnsafeMethods` para conservar el orden: primero
    `IsAuthenticated`, después `IsKycApproved` y recién al final el perfil. Así
    el mensaje de KYC (AGENTS §9.9) sigue teniendo prioridad sobre el de perfil.

    La subclase define `profile_kind` con el perfil que necesita la operación.
    """

    profile_kind: str | None = None

    def get_permissions(self):
        """Agrega `IsActiveProfile` después del chequeo de KYC en no-lectura."""
        permissions = list(super().get_permissions())
        if self.request.method not in SAFE_METHODS and self.profile_kind:
            permissions.append(IsActiveProfile(self.profile_kind))
        return permissions
