"""Armado y envío de los emails de la app identity."""

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _frontend_link(path: str, params: dict[str, str]) -> str:
    """Arma un enlace al front con sus parámetros de query.

    Args:
        path: ruta del front (por ejemplo `/restablecer`).
        params: parámetros de la query string.

    Returns:
        La URL completa.
    """
    base = settings.FRONTEND_URL.rstrip('/')
    return f'{base}{path}?{urlencode(params)}'


def build_password_reset_link(uid: str, token: str) -> str:
    """Devuelve el enlace que abre el formulario de nueva contraseña."""
    return _frontend_link('/restablecer', {'uid': uid, 'token': token})


def build_email_verification_link(uid: str, token: str) -> str:
    """Devuelve el enlace que confirma el email."""
    return _frontend_link('/verificar', {'uid': uid, 'token': token})


def send_password_reset_email(user, uid: str, token: str) -> None:
    """Envía el email con el enlace para restablecer la contraseña.

    Args:
        user: usuario destinatario.
        uid: id del usuario codificado.
        token: token de reseteo.
    """
    link = build_password_reset_link(uid=uid, token=token)
    send_mail(
        subject='Presto: restablecé tu contraseña',
        message=(
            'Hola,\n\n'
            'Recibimos un pedido para restablecer la contraseña de tu cuenta.\n'
            'Abrí este enlace para elegir una nueva:\n\n'
            f'{link}\n\n'
            'Si no fuiste vos, ignorá este mensaje: tu contraseña no cambia.\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_email_verification_email(user, uid: str, token: str) -> None:
    """Envía el email con el enlace para confirmar la dirección.

    Args:
        user: usuario destinatario.
        uid: id del usuario codificado.
        token: token de verificación.
    """
    link = build_email_verification_link(uid=uid, token=token)
    send_mail(
        subject='Presto: confirmá tu email',
        message=(
            'Hola,\n\n'
            'Gracias por registrarte en Presto.\n'
            'Confirmá tu email abriendo este enlace:\n\n'
            f'{link}\n\n'
            'Si no creaste esta cuenta, ignorá este mensaje.\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
