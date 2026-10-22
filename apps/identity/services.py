"""Servicios de escritura de la app identity (interfaz pública)."""

import logging
import uuid
from typing import Any

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.identity.emails import send_email_verification_email, send_password_reset_email
from apps.identity.exceptions import (
    EmailAlreadyRegistered,
    InvalidDocuments,
    InvalidKYCResolution,
    InvalidProfileField,
    InvalidToken,
    KYCAlreadyResolved,
    PendingKYCExists,
    WeakPassword,
)
from apps.identity.models import KYCVerification, Profile, User
from apps.identity.tokens import decode_uid, email_verification_token, encode_uid

logger = logging.getLogger(__name__)

RESOLVABLE_STATUSES = (KYCVerification.Status.APPROVED, KYCVerification.Status.REJECTED)
PROFILE_FIELDS = ('phone_number', 'date_of_birth', 'country')


def set_refresh_cookie(response, refresh_token: str) -> None:
    """Deja el refresh token en una cookie httpOnly.

    El refresh token **no** vuelve en el cuerpo de la respuesta: viaja solo en
    la cookie, que el JavaScript del navegador no puede leer (ADR 0014).

    Args:
        response: la respuesta HTTP donde se setea la cookie.
        refresh_token: el refresh token a guardar.
    """
    response.set_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        path=settings.JWT_REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response) -> None:
    """Borra la cookie del refresh token.

    Args:
        response: la respuesta HTTP donde se borra la cookie.
    """
    response.delete_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


def get_refresh_token(request) -> str | None:
    """Devuelve el refresh token de la petición.

    Primero mira la cookie httpOnly; si no está, mira el cuerpo de la
    petición, que queda como compatibilidad para clientes que no son
    navegadores (ADR 0014).

    Args:
        request: la petición HTTP.

    Returns:
        El refresh token o None si la petición no trae ninguno.
    """
    cookie_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    body = request.data if hasattr(request, 'data') else {}
    token = body.get('refresh') if hasattr(body, 'get') else None
    return token or None


def register_user(email: str, password: str) -> User:
    """Registra un usuario y le crea su perfil vacío.

    Args:
        email: email único del usuario.
        password: contraseña en texto plano; se hashea antes de guardar.

    Returns:
        El usuario creado, con su perfil asociado.

    Raises:
        EmailAlreadyRegistered: si ya existe un usuario con ese email.
        WeakPassword: si la contraseña no pasa los validadores de Django.
    """
    if User.objects.filter(email__iexact=email).exists():
        raise EmailAlreadyRegistered('Ya existe un usuario registrado con ese email.')
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise WeakPassword('; '.join(exc.messages)) from exc
    with transaction.atomic():
        user = User.objects.create_user(email=email, password=password)
        Profile.objects.create(user=user)
    logger.info('Usuario registrado: user_id=%s', user.id)
    send_email_verification(user)
    return user


def submit_kyc(user: User, documents: dict[str, Any]) -> KYCVerification:
    """Registra una solicitud de verificación KYC para un usuario.

    Args:
        user: usuario que solicita la verificación.
        documents: metadata de los documentos (objeto JSON).

    Returns:
        La verificación creada, en estado pending.

    Raises:
        InvalidDocuments: si documents no es un objeto JSON.
        PendingKYCExists: si el usuario ya tiene una verificación pendiente.
    """
    if not isinstance(documents, dict):
        raise InvalidDocuments('Los documentos deben enviarse como objeto JSON de metadata.')
    try:
        with transaction.atomic():
            verification = KYCVerification.objects.create(user=user, documents=documents)
    except IntegrityError as exc:
        raise PendingKYCExists('El usuario ya tiene una verificación KYC pendiente.') from exc
    logger.info(
        'Verificación KYC solicitada: user_id=%s verification_id=%s', user.id, verification.id
    )
    return verification


def resolve_kyc(
    verification_id: uuid.UUID,
    status: str,
    resolved_by_user_id: uuid.UUID,
) -> KYCVerification:
    """Resuelve una verificación KYC aprobándola o rechazándola.

    Args:
        verification_id: identificador de la verificación a resolver.
        status: `approved` o `rejected`.
        resolved_by_user_id: identificador del usuario que decide.

    Returns:
        La verificación resuelta.

    Raises:
        InvalidKYCResolution: si el estado no es `approved` ni `rejected`.
        KYCAlreadyResolved: si la verificación ya había sido resuelta.
    """
    if status not in RESOLVABLE_STATUSES:
        raise InvalidKYCResolution(
            'Una verificación KYC solo puede resolverse como approved o rejected.'
        )
    with transaction.atomic():
        verification = KYCVerification.objects.select_for_update().get(pk=verification_id)
        if verification.status != KYCVerification.Status.PENDING:
            raise KYCAlreadyResolved('La verificación KYC ya fue resuelta.')
        verification.status = status
        verification.resolved_at = timezone.now()
        verification.resolved_by_user_id = resolved_by_user_id
        verification.save(update_fields=['status', 'resolved_at', 'resolved_by_user_id'])
    logger.info(
        'Verificación KYC resuelta: user_id=%s verification_id=%s status=%s resolved_by_user_id=%s',
        verification.user_id,
        verification.id,
        status,
        resolved_by_user_id,
    )
    return verification


def update_profile(user: User, changes: dict[str, Any]) -> Profile:
    """Actualiza los campos del perfil de un usuario, creándolo si no existe.

    Args:
        user: usuario dueño del perfil.
        changes: campos a actualizar (phone_number, date_of_birth, country).

    Returns:
        El perfil actualizado.

    Raises:
        InvalidProfileField: si se intenta modificar un campo ajeno al perfil.
    """
    unknown_fields = set(changes) - set(PROFILE_FIELDS)
    if unknown_fields:
        raise InvalidProfileField('Ese campo no pertenece al perfil del usuario.')
    profile, _ = Profile.objects.get_or_create(user=user)
    for field, value in changes.items():
        setattr(profile, field, value)
    profile.full_clean()
    profile.save()
    return profile


def request_password_reset(email: str) -> bool:
    """Envía el enlace para restablecer la contraseña, si el email existe.

    No revela si el email está registrado: la vista responde siempre lo mismo.
    Si el envío falla se registra el error y la respuesta no cambia (no se
    filtra información ni se rompe el request).

    Args:
        email: email de la cuenta que quiere recuperar la contraseña.

    Returns:
        True si se encontró la cuenta y se intentó enviar el email.
    """
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        logger.info('Pedido de reseteo para un email no registrado: no se envía nada.')
        return False
    uid = encode_uid(user.pk)
    token = default_token_generator.make_token(user)
    try:
        send_password_reset_email(user=user, uid=uid, token=token)
    except Exception:
        logger.exception('No se pudo enviar el email de reseteo: user_id=%s', user.id)
        return False
    logger.info('Email de reseteo enviado: user_id=%s', user.id)
    return True


def confirm_password_reset(uid: str, token: str, new_password: str) -> User:
    """Cambia la contraseña con un token válido y cierra las sesiones abiertas.

    Args:
        uid: id del usuario codificado en el enlace.
        token: token de reseteo emitido por `request_password_reset`.
        new_password: contraseña nueva en texto plano.

    Returns:
        El usuario con la contraseña actualizada.

    Raises:
        InvalidToken: si el enlace no es válido o venció.
        WeakPassword: si la contraseña no pasa los validadores de Django.
    """
    user = _get_user_from_uid(uid)
    if user is None or not default_token_generator.check_token(user, token):
        raise InvalidToken('El enlace no es válido o venció. Pedí uno nuevo.')
    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise WeakPassword('; '.join(exc.messages)) from exc
    with transaction.atomic():
        user.set_password(new_password)
        user.save(update_fields=['password'])
        _blacklist_refresh_tokens(user)
    logger.info('Contraseña restablecida: user_id=%s', user.id)
    return user


def send_email_verification(user: User) -> bool:
    """Envía (o reenvía) el enlace para confirmar el email.

    Args:
        user: usuario destinatario.

    Returns:
        True si se intentó enviar; False si ya estaba verificado o si el envío
        falló.
    """
    if user.email_verified_at is not None:
        return False
    uid = encode_uid(user.pk)
    token = email_verification_token.make_token(user)
    try:
        send_email_verification_email(user=user, uid=uid, token=token)
    except Exception:
        logger.exception('No se pudo enviar el email de verificación: user_id=%s', user.id)
        return False
    logger.info('Email de verificación enviado: user_id=%s', user.id)
    return True


def confirm_email_verification(uid: str, token: str) -> User:
    """Marca el email del usuario como confirmado.

    Es idempotente: si el email ya estaba verificado, devuelve el usuario sin
    cambios.

    Args:
        uid: id del usuario codificado en el enlace.
        token: token de verificación emitido por `send_email_verification`.

    Returns:
        El usuario con el email verificado.

    Raises:
        InvalidToken: si el enlace no es válido o venció.
    """
    user = _get_user_from_uid(uid)
    if user is None:
        raise InvalidToken('El enlace no es válido o venció. Podés pedir otro.')
    if user.email_verified_at is not None:
        return user
    if not email_verification_token.check_token(user, token):
        raise InvalidToken('El enlace no es válido o venció. Podés pedir otro.')
    user.email_verified_at = timezone.now()
    user.save(update_fields=['email_verified_at'])
    logger.info('Email verificado: user_id=%s', user.id)
    return user


def _get_user_from_uid(uid: str) -> User | None:
    """Devuelve el usuario activo del `uid` de un enlace, o None."""
    user_id = decode_uid(uid)
    if not user_id:
        return None
    try:
        return User.objects.filter(pk=user_id, is_active=True).first()
    except (DjangoValidationError, ValueError):
        return None


def _blacklist_refresh_tokens(user: User) -> int:
    """Invalida todos los refresh tokens vigentes del usuario.

    Se usa al restablecer la contraseña: si alguien tenía una sesión abierta,
    deja de poder renovar el access token.
    """
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    count = 0
    for outstanding in OutstandingToken.objects.filter(user=user).iterator():
        _, created = BlacklistedToken.objects.get_or_create(token=outstanding)
        count += int(created)
    return count
