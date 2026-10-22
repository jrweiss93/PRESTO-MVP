"""Tests de la verificación de email."""

import re

import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.models import User
from apps.identity.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

PASSWORD = 'TestPass123!'


@pytest.fixture
def client():
    return APIClient()


def authenticate(client, user) -> APIClient:
    """Autentica al cliente con un access token del usuario dado."""
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


def extract_link_params(body: str) -> tuple[str, str]:
    """Saca el uid y el token del enlace que va en el cuerpo del email."""
    match = re.search(r'[?&]uid=([^&\s]+)&token=([^&\s]+)', body)
    assert match is not None, f'El email no trae un enlace con uid y token: {body}'
    return match.group(1), match.group(2)


def register(client, email: str = 'nuevo@example.com'):
    """Registra un usuario por la API."""
    return client.post(
        '/api/v1/auth/register/',
        {'email': email, 'password': PASSWORD},
        format='json',
    )


def verify(client, uid: str, token: str):
    """Confirma el email por la API."""
    return client.post(
        '/api/v1/auth/email/verify/',
        {'uid': uid, 'token': token},
        format='json',
    )


def test_registration_sends_the_verification_email(client):
    """Al registrarse se envía el enlace de verificación y el email queda sin verificar."""
    response = register(client)

    assert response.status_code == 201
    assert response.data['email_verified'] is False
    assert len(mail.outbox) == 1
    assert '/verificar?uid=' in mail.outbox[0].body
    uid, token = extract_link_params(mail.outbox[0].body)
    assert uid
    assert token


def test_verifying_the_email_marks_the_user_as_verified(client):
    """El token del email marca la cuenta como verificada."""
    register(client)
    uid, token = extract_link_params(mail.outbox[0].body)

    response = verify(client, uid, token)

    assert response.status_code == 200
    assert response.data == {'email': 'nuevo@example.com', 'email_verified': True}
    user = User.objects.get(email='nuevo@example.com')
    assert user.email_verified_at is not None


def test_verifying_twice_is_idempotent(client):
    """Confirmar dos veces el mismo email no falla."""
    register(client)
    uid, token = extract_link_params(mail.outbox[0].body)
    verify(client, uid, token)

    response = verify(client, uid, token)

    assert response.status_code == 200
    assert response.data['email_verified'] is True


def test_verification_rejects_an_invalid_token(client):
    """Un token que no corresponde devuelve 400."""
    register(client)
    uid, _ = extract_link_params(mail.outbox[0].body)

    response = verify(client, uid, 'token-invalido')

    assert response.status_code == 400
    assert 'token' in response.data['error']['details']


def test_verification_rejects_a_malformed_uid(client):
    """Un uid que no es base64 devuelve 400."""
    response = verify(client, 'no-es-base64', 'x')

    assert response.status_code == 400
    assert response.data['error']['code'] == 'validation_error'


def test_the_link_survives_a_login_before_verifying(client):
    """El enlace sigue valiendo aunque el usuario inicie sesión antes de confirmar."""
    register(client)
    uid, token = extract_link_params(mail.outbox[0].body)

    login = client.post(
        '/api/v1/auth/login/',
        {'email': 'nuevo@example.com', 'password': PASSWORD},
        format='json',
    )
    response = verify(client, uid, token)

    assert login.status_code == 200
    assert response.status_code == 200


def test_me_reports_the_email_verification_status(client):
    """`GET /auth/me/` informa si el email está verificado."""
    user = UserFactory(email='ana@example.com', password=PASSWORD)
    authenticate(client, user)
    before = client.get('/api/v1/auth/me/')
    user.email_verified_at = timezone.now()
    user.save(update_fields=['email_verified_at'])
    after = client.get('/api/v1/auth/me/')

    assert before.status_code == 200
    assert before.data['email_verified'] is False
    assert after.data['email_verified'] is True


def test_resending_the_verification_requires_authentication(client):
    """El reenvío es para usuarios autenticados."""
    response = client.post('/api/v1/auth/email/resend/', format='json')

    assert response.status_code == 401
    assert response.data['error']['code'] == 'not_authenticated'


def test_resending_the_verification_sends_another_email(client):
    """Un usuario sin verificar puede pedir el enlace de nuevo."""
    user = UserFactory(email='ana@example.com', password=PASSWORD)
    authenticate(client, user)

    response = client.post('/api/v1/auth/email/resend/', format='json')

    assert response.status_code == 202
    assert response.data['detail'] == 'Te enviamos el correo de verificación.'
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['ana@example.com']


def test_resending_when_already_verified_does_not_send_an_email(client):
    """Si el email ya está verificado, el reenvío lo informa y no manda nada."""
    user = UserFactory(email='ana@example.com', password=PASSWORD)
    user.email_verified_at = timezone.now()
    user.save(update_fields=['email_verified_at'])
    authenticate(client, user)

    response = client.post('/api/v1/auth/email/resend/', format='json')

    assert response.status_code == 202
    assert response.data['detail'] == 'Tu email ya está verificado.'
    assert mail.outbox == []
