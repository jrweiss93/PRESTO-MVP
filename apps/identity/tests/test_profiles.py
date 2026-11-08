"""Tests de los perfiles de Presto fijos (prestatario, prestamista e inversor)."""

import pytest
from rest_framework.test import APIClient

from apps.identity.exceptions import InvalidProfileKind
from apps.identity.models import PrestoProfile
from apps.identity.services import register_user, set_profile
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


# ---- registro con perfil fijo ----


def test_register_creates_a_single_borrower_profile_by_default():
    """Registrar sin indicar perfil crea un único perfil prestatario."""
    user = register_user(email='fijo@example.com', password='TestPass123!')

    profiles = list(PrestoProfile.objects.filter(user=user))
    assert len(profiles) == 1
    assert profiles[0].kind == 'borrower'
    assert profiles[0].is_active is True


def test_register_creates_the_requested_profile():
    """Registrar con profile_kind crea un único perfil de ese tipo."""
    user = register_user(
        email='lender-fijo@example.com', password='TestPass123!', profile_kind='lender'
    )

    assert PrestoProfile.objects.filter(user=user).count() == 1
    assert PrestoProfile.objects.get(user=user).kind == 'lender'


def test_register_rejects_an_unknown_profile():
    """Un perfil que no existe levanta un error de dominio."""
    with pytest.raises(InvalidProfileKind):
        register_user(
            email='invalido@example.com', password='TestPass123!', profile_kind='administrador'
        )


# ---- fijar el perfil de un usuario existente ----


def test_set_profile_leaves_a_single_fixed_profile():
    """set_profile borra otros perfiles y deja solo el indicado."""
    user = UserFactory()
    PrestoProfileFactory(user=user, kind='borrower', is_active=True)
    PrestoProfileFactory(user=user, kind='lender')
    PrestoProfileFactory(user=user, kind='investor')

    profile = set_profile(user=user, kind='lender')

    assert profile.kind == 'lender'
    assert profile.is_active is True
    assert [p.kind for p in PrestoProfile.objects.filter(user=user)] == ['lender']


def test_set_profile_rejects_an_unknown_kind():
    """Un perfil que no existe levanta un error de dominio."""
    user = UserFactory()

    with pytest.raises(InvalidProfileKind):
        set_profile(user=user, kind='administrador')


# ---- selectores ----


def test_get_active_profile_returns_none_without_profiles():
    """Sin perfiles no hay perfil activo."""
    from apps.identity.selectors import get_active_profile

    user = UserFactory()

    assert get_active_profile(user_id=user.id) is None


def test_get_active_profile_returns_the_fixed_profile():
    """El selector devuelve el perfil fijo activo."""
    from apps.identity.selectors import get_active_profile

    user = register_user(
        email='selector-fijo@example.com', password='TestPass123!', profile_kind='investor'
    )

    assert get_active_profile(user_id=user.id).kind == 'investor'


def test_list_profiles_returns_the_single_profile():
    """El selector lista el único perfil del usuario."""
    from apps.identity.selectors import list_profiles_for_user

    user = register_user(
        email='lista-fijo@example.com', password='TestPass123!', profile_kind='lender'
    )

    profiles = list_profiles_for_user(user.id)
    assert [p.kind for p in profiles] == ['lender']


# ---- API ----


def test_me_returns_the_fixed_profile(client):
    """El perfil propio expone el perfil fijo activo."""
    user = register_user(
        email='me-fijo@example.com', password='TestPass123!', profile_kind='borrower'
    )
    authenticate(client, user)

    response = client.get('/api/v1/auth/me/')

    assert response.status_code == 200
    assert response.data['active_profile'] == 'borrower'
    assert [p['kind'] for p in response.data['profiles']] == ['borrower']


def test_register_endpoint_accepts_a_profile(client):
    """El registro acepta profile_kind y devuelve el perfil activo."""
    response = client.post(
        '/api/v1/auth/register/',
        {
            'email': 'nuevo-inversor@example.com',
            'password': 'TestPass123!',
            'profile_kind': 'investor',
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['active_profile'] == 'investor'


def test_register_endpoint_defaults_to_borrower(client):
    """Sin profile_kind el registro crea un prestatario."""
    response = client.post(
        '/api/v1/auth/register/',
        {'email': 'nuevo-prestatario@example.com', 'password': 'TestPass123!'},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['active_profile'] == 'borrower'


def test_register_endpoint_rejects_unknown_profile(client):
    """Un profile_kind inválido devuelve 400."""
    response = client.post(
        '/api/v1/auth/register/',
        {
            'email': 'nuevo-invalido@example.com',
            'password': 'TestPass123!',
            'profile_kind': 'admin',
        },
        format='json',
    )

    assert response.status_code == 400


def test_me_payload_is_serializable_for_a_user_without_profiles(client):
    """Un usuario sin perfiles (ej. de una factory) se serializa sin romper."""
    user = UserFactory()
    authenticate(client, user)

    response = client.get('/api/v1/auth/me/')

    assert response.status_code == 200
    assert response.data['profiles'] == []
    assert response.data['active_profile'] is None
