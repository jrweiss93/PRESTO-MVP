"""Tests del marco regulatorio del asistente."""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    user = UserFactory(email='presti@example.com')
    api = APIClient()
    token = RefreshToken.for_user(user)
    api.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return api


def test_regulations_require_authentication():
    """El marco legal no es público."""
    response = APIClient().get('/api/v1/assistant/regulations/')

    assert response.status_code == 401


def test_regulations_list_returns_disclaimer_categories_and_items(client):
    """El listado trae el aviso, las categorías y las fichas."""
    response = client.get('/api/v1/assistant/regulations/')

    assert response.status_code == 200
    assert 'no es asesoramiento legal' in response.data['disclaimer']
    assert len(response.data['categories']) >= 5
    assert len(response.data['items']) >= 5
    item = response.data['items'][0]
    assert item['id']
    assert item['category']
    assert item['key_points']
    assert item['norms']
    assert item['links']


def test_regulations_filter_by_category(client):
    """El filtro por categoría devuelve solo esa categoría."""
    response = client.get('/api/v1/assistant/regulations/?category=antilavado')

    assert response.status_code == 200
    assert response.data['items']
    assert all(item['category'] == 'antilavado' for item in response.data['items'])


def test_regulations_filter_by_text(client):
    """El filtro por texto busca en título, resumen y puntos."""
    response = client.get('/api/v1/assistant/regulations/?q=CNV')

    assert response.status_code == 200
    assert len(response.data['items']) == 1
    assert response.data['items'][0]['id'] == 'oferta-publica-cnv'


def test_regulations_reject_an_unknown_category(client):
    """Una categoría que no existe es un error de validación."""
    response = client.get('/api/v1/assistant/regulations/?category=inventada')

    assert response.status_code == 400
    assert response.data['error']['code'] == 'validation_error'


def test_regulation_detail_returns_one_card(client):
    """El detalle devuelve la ficha pedida con el aviso."""
    response = client.get('/api/v1/assistant/regulations/mutuo-entre-particulares/')

    assert response.status_code == 200
    assert response.data['item']['id'] == 'mutuo-entre-particulares'
    assert response.data['disclaimer']


def test_regulation_detail_returns_404(client):
    """Una ficha inexistente devuelve 404."""
    response = client.get('/api/v1/assistant/regulations/no-existe/')

    assert response.status_code == 404
    assert response.data['error']['code'] == 'not_found'
