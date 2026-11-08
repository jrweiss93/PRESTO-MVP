"""Tests de los perfiles de Presto (prestatario, prestamista e inversor)."""

import uuid

import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.identity.models import PrestoProfile
from apps.identity.services import activate_profile, register_user
from apps.identity.tests.factories import PrestoProfileFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def authenticate(client, user):
    """Autentica al cliente con un access token del usuario dado."""
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


# ---- modelo ----


def test_register_creates_the_three_profiles_with_borrower_active():
    """Registrar un usuario crea los tres perfiles, con el prestatario activo."""
    user = register_user(email='perfiles@example.com', password='TestPass123!')

    profiles = PrestoProfile.objects.filter(user=user)
    assert {p.kind for p in profiles} == {'borrower', 'lender', 'investor'}
    assert profiles.get(kind='borrower').is_active is True
    assert profiles.get(kind='lender').is_active is False
    assert profiles.get(kind='investor').is_active is False


def test_profile_kind_is_unique_per_user():
    """Un usuario no puede tener dos veces el mismo perfil."""
    profile = PrestoProfileFactory()
    with pytest.raises(IntegrityError):
        PrestoProfileFactory(user=profile.user, kind=profile.kind)


def test_only_one_active_profile_per_user():
    """Activar un perfil desactiva el anterior (única activa por usuario)."""
    user = register_user(email='unica-activa@example.com', password='TestPass123!')
    activate_profile(user=user, kind='lender')

    actives = PrestoProfile.objects.filter(user=user, is_active=True)
    assert [p.kind for p in actives] == ['lender']


# ---- servicios ----


def test_activate_profile_switches_the_active_profile():
    """Activar un perfil cambia cuál está activo."""
    user = register_user(email='cambio-perfil@example.com', password='TestPass123!')

    profile = activate_profile(user=user, kind='investor')

    assert profile.kind == 'investor'
    assert PrestoProfile.objects.get(user=user, kind='investor').is_active is True
    assert PrestoProfile.objects.get(user=user, kind='borrower').is_active is False


def test_activate_profile_rejects_an_unknown_kind():
    """Un tipo de perfil que no existe levanta un error de dominio."""
    from apps.identity.exceptions import InvalidProfileKind

    user = register_user(email='perfil-invalido@example.com', password='TestPass123!')

    with pytest.raises(InvalidProfileKind):
        activate_profile(user=user, kind='administrador')


# ---- selectores ----


def test_get_active_profile_returns_none_without_profiles():
    """Sin perfiles no hay perfil activo."""
    user = UserFactory()

    from apps.identity.selectors import get_active_profile

    assert get_active_profile(user_id=user.id) is None


def test_get_active_profile_returns_the_active_kind():
    """El selector devuelve el perfil activo."""
    from apps.identity.selectors import get_active_profile

    user = register_user(email='selector-activo@example.com', password='TestPass123!')
    activate_profile(user=user, kind='lender')

    assert get_active_profile(user_id=user.id).kind == 'lender'


# ---- API ----


def test_me_returns_profiles_and_active_profile(client):
    """El perfil propio expone los perfiles y cuál está activo."""
    user = register_user(email='me-perfiles@example.com', password='TestPass123!')
    authenticate(client, user)

    response = client.get('/api/v1/auth/me/')

    assert response.status_code == 200
    assert response.data['active_profile'] == 'borrower'
    assert {p['kind'] for p in response.data['profiles']} == {
        'borrower',
        'lender',
        'investor',
    }
    active = [p for p in response.data['profiles'] if p['is_active']]
    assert [p['kind'] for p in active] == ['borrower']


def test_activate_profile_endpoint_switches_the_profile(client):
    """El endpoint activa un perfil y devuelve el usuario actualizado."""
    user = register_user(email='endpoint-perfil@example.com', password='TestPass123!')
    authenticate(client, user)

    response = client.post(
        '/api/v1/auth/me/activate-profile/',
        {'kind': 'investor'},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['active_profile'] == 'investor'


def test_activate_profile_endpoint_requires_authentication(client):
    """Activar un perfil exige autenticación."""
    response = client.post('/api/v1/auth/me/activate-profile/', {'kind': 'lender'}, format='json')

    assert response.status_code == 401
    assert response.data['error']['code'] == 'not_authenticated'


def test_activate_profile_endpoint_rejects_unknown_kind(client):
    """Un tipo de perfil inválido devuelve 400."""
    user = register_user(email='endpoint-invalido@example.com', password='TestPass123!')
    authenticate(client, user)

    response = client.post(
        '/api/v1/auth/me/activate-profile/',
        {'kind': 'administrador'},
        format='json',
    )

    assert response.status_code == 400


def test_openapi_schema_documents_the_activate_endpoint(client):
    """El esquema documenta el endpoint de activación de perfil."""
    response = client.get('/api/schema/')

    assert '/api/v1/auth/me/activate-profile/' in response.data['paths']


def test_me_payload_is_serializable_for_a_user_without_profiles(client):
    """Un usuario sin perfiles (ej. de una factory) se serializa sin romper."""
    user = UserFactory()
    authenticate(client, user)

    response = client.get('/api/v1/auth/me/')

    assert response.status_code == 200
    assert response.data['profiles'] == []
    assert response.data['active_profile'] is None
