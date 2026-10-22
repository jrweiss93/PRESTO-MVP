"""Tareas Celery de la app notifications.

El envío es una tarea: un fallo de SMTP no rompe la transacción de la app
que originó el evento ni el ledger.

Si el envío falla, la tarea **se reintenta con backoff exponencial** hasta
`MAX_SEND_ATTEMPTS` intentos en total. Mientras quedan reintentos, el aviso
sigue en `pending`; pasa a `failed` cuando se agotan (ADR 0013).
"""

import logging
import uuid

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.identity.selectors import get_user_email
from apps.notifications.emails import build_email
from apps.notifications.models import Notification
from apps.notifications.selectors import get_notification
from apps.notifications.services import (
    mark_notification_failed,
    mark_notification_sent,
    register_notification_attempt,
)

logger = logging.getLogger(__name__)

MAX_SEND_ATTEMPTS = 3
DEFAULT_RETRY_BASE_SECONDS = 60


def retry_countdown(attempts: int) -> int:
    """Calcula la espera del próximo reintento, en segundos.

    El backoff es exponencial: el primer reintento espera el base y el
    siguiente el doble (60 s y 120 s con el base por defecto).

    Args:
        attempts: cantidad de intentos ya realizados.

    Returns:
        La cantidad de segundos a esperar antes del próximo intento.
    """
    base = getattr(
        settings,
        'NOTIFICATIONS_RETRY_BASE_SECONDS',
        DEFAULT_RETRY_BASE_SECONDS,
    )
    return int(base) * (2 ** max(attempts - 1, 0))


@shared_task(
    bind=True,
    name='apps.notifications.tasks.send_notification_email',
    max_retries=MAX_SEND_ATTEMPTS - 1,
)
def send_notification_email(self, notification_id: str) -> bool:
    """Envía el email de un aviso pendiente.

    Es **idempotente**: un aviso que ya está enviado no se vuelve a mandar.

    Ante un fallo de SMTP reintenta con backoff exponencial hasta
    `MAX_SEND_ATTEMPTS` intentos; cuando se agotan, el aviso queda `failed`
    con el motivo.

    Args:
        notification_id: identificador del aviso.

    Returns:
        True si el email se envió, False si no había nada que enviar.
    """
    notification = get_notification(uuid.UUID(str(notification_id)))
    if notification is None:
        return False
    if notification.status != Notification.Status.PENDING:
        return False
    recipient = get_user_email(user_id=notification.user_id)
    if not recipient:
        mark_notification_failed(notification, 'El usuario no tiene un email registrado.')
        return False
    subject, body = build_email(notification)
    register_notification_attempt(notification)
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('No se pudo enviar el aviso %s', notification.id)
        if notification.attempts < MAX_SEND_ATTEMPTS:
            logger.warning(
                'Aviso %s: reintento %s/%s en %s segundos',
                notification.id,
                notification.attempts + 1,
                MAX_SEND_ATTEMPTS,
                retry_countdown(notification.attempts),
            )
            raise self.retry(
                exc=exc,
                countdown=retry_countdown(notification.attempts),
            ) from exc
        mark_notification_failed(notification, str(exc))
        return False
    logger.info(
        'Aviso enviado: notification_id=%s event_type=%s attempts=%s',
        notification.id,
        notification.event_type,
        notification.attempts,
    )
    mark_notification_sent(notification)
    return True
