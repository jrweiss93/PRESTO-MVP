"""Tests del reseteo de contraseña."""

import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.identity.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

PASSWORD = 'TestPass123!'


@pytest.fixture
def client():
    return APIClient()


def extract_link_params(body: str) -> tuple[str, str]:
    """Saca el uid y el token del enlace que va en el cuerpo del email."""
    match = re.search(r'[?&]uid=([^&\s]+)&token=([^&\s]+)', body)
    assert match is not None, f'El email no trae un enlace con uid y token: {body}'
    return match.group(1), match.group(2)


def request_reset(client, email: str):
    """Pide el reseteo y devuelve la respuesta."""
    return client.post('/api/v1/auth/password-reset/', {'email': email}, format='json')


def test_password_reset_sends_an_email_for_a_registered_user(client):
    """Un email registrado recibe el enlace de reseteo."""
    UserFactory(email='ana@example.com', password=PASSWORD)

    response = request_reset(client, 'ana@example.com')

    assert response.status_code == 202
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['ana@example.com']
    assert '/restablecer?uid=' in mail.outbox[0].body
    uid, token = extract_link_params(mail.outbox[0].body)
    assert uid
    assert token


def test_password_reset_does_not_reveal_whether_the_email_exists(client):
    """Un email desconocido recibe la misma respuesta y no se envía nada."""
    response = request_reset(client, 'nadie@example.com')

    assert response.status_code == 202
    assert mail.outbox == []
    assert 'Si el email está registrado' in response.data['detail']


def test_password_reset_returns_the_same_message_for_both_cases(client):
    """La respuesta no distingue entre cuenta existente y cuenta inexistente."""
    UserFactory(email='ana@example.com', password=PASSWORD)
    payload_email_ok = request_reset(client, 'ana@example.com').data
    payload_email_unknown = request_reset(client, 'nadie@example.com').data

    assert payload_email_ok == payload_email_unknown


def test_password_reset_confirmation_changes_the_password(client):
    """Con el token del email la contraseña cambia y la anterior deja de servir."""
    user = UserFactory(email='ana@example.com', password=PASSWORD)
    request_reset(client, 'ana@example.com')
    uid, token = extract_link_params(mail.outbox[0].body)

    response = client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'uid': uid, 'token': token, 'new_password': 'NewPass456!'},
        format='json',
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password('NewPass456!')
    assert not user.check_password(PASSWORD)


def test_password_reset_token_cannot_be_used_twice(client):
    """El token se invalida al cambiar la contraseña."""
    UserFactory(email='ana@example.com', password=PASSWORD)
    request_reset(client, 'ana@example.com')
    uid, token = extract_link_params(mail.outbox[0].body)
    payload = {'uid': uid, 'token': token, 'new_password': 'NewPass456!'}

    first = client.post('/api/v1/auth/password-reset/confirm/', payload, format='json')
    second = client.post('/api/v1/auth/password-reset/confirm/', payload, format='json')

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.data['error']['code'] == 'validation_error'


def test_password_reset_rejects_an_invalid_token(client):
    """Un token que no corresponde devuelve 400."""
    UserFactory(email='ana@example.com', password=PASSWORD)
    request_reset(client, 'ana@example.com')
    uid, _ = extract_link_params(mail.outbox[0].body)

    response = client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'uid': uid, 'token': 'token-invalido', 'new_password': 'NewPass456!'},
        format='json',
    )

    assert response.status_code == 400
    assert 'token' in response.data['error']['details']


def test_password_reset_rejects_an_expired_token(client, settings):
    """Un enlace vencido devuelve 400."""
    UserFactory(email='ana@example.com', password=PASSWORD)
    request_reset(client, 'ana@example.com')
    uid, token = extract_link_params(mail.outbox[0].body)
    settings.PASSWORD_RESET_TIMEOUT = -1

    response = client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'uid': uid, 'token': token, 'new_password': 'NewPass456!'},
        format='json',
    )

    assert response.status_code == 400
    assert 'token' in response.data['error']['details']


def test_password_reset_rejects_a_weak_password(client):
    """La contraseña nueva pasa por los validadores de Django."""
    UserFactory(email='ana@example.com', password=PASSWORD)
    request_reset(client, 'ana@example.com')
    uid, token = extract_link_params(mail.outbox[0].body)

    response = client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'uid': uid, 'token': token, 'new_password': '12345678'},
        format='json',
    )

    assert response.status_code == 400
    assert 'new_password' in response.data['error']['details']


def test_password_reset_rejects_a_malformed_uid(client):
    """Un uid que no es base64 devuelve 400 y no rompe la vista."""
    response = client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'uid': 'no-es-base64', 'token': 'x', 'new_password': 'NewPass456!'},
        format='json',
    )

    assert response.status_code == 400
    assert response.data['error']['code'] == 'validation_error'


def test_password_reset_blacklists_the_open_sessions(client):
    """Al restablecer la contraseña, los refresh tokens vigentes dejan de servir."""
    UserFactory(email='ana@example.com', password=PASSWORD)
    login = client.post(
        '/api/v1/auth/login/',
        {'email': 'ana@example.com', 'password': PASSWORD},
        format='json',
    )
    refresh = login.cookies['presto_refresh'].value
    request_reset(client, 'ana@example.com')
    uid, token = extract_link_params(mail.outbox[0].body)

    client.post(
        '/api/v1/auth/password-reset/confirm/',
        {'uid': uid, 'token': token, 'new_password': 'NewPass456!'},
        format='json',
    )
    fresh_client = APIClient()
    response = fresh_client.post(
        '/api/v1/auth/token/refresh/',
        HTTP_COOKIE=f'presto_refresh={refresh}',
        format='json',
    )

    assert response.status_code == 401


def test_password_reset_is_throttled(client):
    """El pedido de reseteo tiene un límite de 5 por hora."""
    for _ in range(5):
        assert request_reset(client, 'nadie@example.com').status_code == 202

    response = request_reset(client, 'nadie@example.com')

    assert response.status_code == 429
    assert response.data['error']['code'] == 'throttled'
