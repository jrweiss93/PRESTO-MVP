"""Selectores de lectura de la app identity (interfaz pública)."""

import uuid

from apps.identity.models import BiometricCheck, KYCVerification, PrestoProfile, Profile, User


def get_profile(user_id: uuid.UUID) -> Profile | None:
    """Devuelve el perfil del usuario, o None si no tiene.

    Args:
        user_id: identificador del usuario.

    Returns:
        El Profile del usuario o None.
    """
    return Profile.objects.filter(user_id=user_id).first()


def get_kyc_for_user(user_id: uuid.UUID) -> KYCVerification | None:
    """Devuelve la verificación KYC más reciente del usuario.

    Args:
        user_id: identificador del usuario.

    Returns:
        La KYCVerification más reciente o None.
    """
    return KYCVerification.objects.filter(user_id=user_id).order_by('-requested_at').first()


def get_kyc_by_id(verification_id: uuid.UUID, user_id: uuid.UUID) -> KYCVerification | None:
    """Devuelve una verificación KYC solo si pertenece al usuario indicado.

    Args:
        verification_id: identificador de la verificación.
        user_id: identificador del usuario propietario.

    Returns:
        La KYCVerification o None si no existe o es de otro usuario.
    """
    return KYCVerification.objects.filter(pk=verification_id, user_id=user_id).first()


def is_kyc_approved(user_id: uuid.UUID) -> bool:
    """Indica si la verificación KYC vigente del usuario está aprobada.

    Args:
        user_id: identificador del usuario.

    Returns:
        True solo si la verificación más reciente está en estado approved.
    """
    verification = get_kyc_for_user(user_id=user_id)
    return verification is not None and verification.status == KYCVerification.Status.APPROVED


def list_profiles_for_user(user_id: uuid.UUID) -> list[PrestoProfile]:
    """Lista los perfiles de Presto del usuario.

    Args:
        user_id: identificador del usuario.

    Returns:
        Los perfiles del usuario (prestatario, prestamista e inversor).
    """
    return list(PrestoProfile.objects.filter(user_id=user_id).order_by('kind'))


def get_active_profile(user_id: uuid.UUID) -> PrestoProfile | None:
    """Devuelve el perfil de Presto activo del usuario, o None si no tiene.

    Args:
        user_id: identificador del usuario.

    Returns:
        El PrestoProfile activo o None.
    """
    return PrestoProfile.objects.filter(user_id=user_id, is_active=True).first()


def get_profile_for_kind(user_id: uuid.UUID, kind: str) -> PrestoProfile | None:
    """Devuelve el perfil del usuario para el tipo indicado, o None.

    Args:
        user_id: identificador del usuario.
        kind: tipo de perfil (`borrower`, `lender` o `investor`).

    Returns:
        El PrestoProfile del tipo pedido o None.
    """
    return PrestoProfile.objects.filter(user_id=user_id, kind=kind).first()


def get_latest_biometric_check(
    user_id: uuid.UUID,
    verification_id: uuid.UUID | None = None,
) -> BiometricCheck | None:
    """Devuelve la validación biométrica más reciente del usuario.

    Args:
        user_id: identificador del usuario.
        verification_id: filtra por una verificación KYC concreta (opcional).

    Returns:
        El BiometricCheck más reciente o None.
    """
    queryset = BiometricCheck.objects.filter(user_id=user_id)
    if verification_id is not None:
        queryset = queryset.filter(kyc_verification_id=verification_id)
    return queryset.order_by('-created_at').first()


def list_biometric_checks(
    user_id: uuid.UUID,
    verification_id: uuid.UUID,
) -> list[BiometricCheck]:
    """Lista las validaciones biométricas de una verificación KYC del usuario.

    Args:
        user_id: identificador del usuario.
        verification_id: verificación KYC dueña de los checks.

    Returns:
        Los BiometricCheck de la verificación, del más reciente al más antiguo.
    """
    return list(
        BiometricCheck.objects.filter(
            user_id=user_id, kyc_verification_id=verification_id
        ).order_by('-created_at')
    )


def get_user_email(user_id: uuid.UUID) -> str | None:
    """Devuelve el email del usuario, o None si no tiene.

    Es el único selector de la app que cruza apps: lo usan las notificaciones
    para enviarle el aviso por email.

    Args:
        user_id: identificador del usuario.

    Returns:
        El email del usuario o None.
    """
    email = User.objects.filter(id=user_id).values_list('email', flat=True).first()
    return email or None
