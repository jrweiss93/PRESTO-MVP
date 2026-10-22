"""Tokens de un solo uso de la app identity."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def encode_uid(user_id) -> str:
    """Codifica el id del usuario para que viaje en un enlace.

    Args:
        user_id: identificador del usuario (UUID).

    Returns:
        El id codificado en base64 URL-safe.
    """
    return urlsafe_base64_encode(force_bytes(user_id))


def decode_uid(uid: str) -> str | None:
    """Decodifica el id de usuario de un enlace.

    Args:
        uid: identificador codificado en base64 URL-safe.

    Returns:
        El id como string, o None si el valor no es un base64 válido.
    """
    try:
        return urlsafe_base64_decode(uid).decode('utf-8')
    except (TypeError, ValueError, UnicodeDecodeError):
        return None


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Token para confirmar el email.

    A diferencia del token de reseteo de contraseña, **no** incluye
    `last_login`: el usuario puede iniciar sesión antes de confirmar el correo y
    el enlace tiene que seguir siendo válido. Se invalida al cambiar la
    contraseña o al verificar el email.
    """

    key_salt = 'apps.identity.tokens.EmailVerificationTokenGenerator'

    def _make_hash_value(self, user, timestamp: int) -> str:
        """Arma el valor que firma el token."""
        verified_at = (
            user.email_verified_at.replace(microsecond=0).isoformat()
            if user.email_verified_at
            else ''
        )
        return f'{user.pk}{user.password}{user.email}{verified_at}{timestamp}'


email_verification_token = EmailVerificationTokenGenerator()
