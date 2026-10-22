"""Tests de mercado y noticias del asistente."""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Ambito</title>
<item>
  <title>El dolar blue subio hoy</title>
  <link>https://example.com/nota</link>
  <pubDate>Wed, 22 Oct 2026 12:00:00 GMT</pubDate>
</item>
<item><title>Sin link</title></item>
</channel></rss>
"""


@pytest.fixture
def client():
    return APIClient()


def authenticate(client):
    """Autentica al cliente con un usuario de prueba."""
    user = UserFactory(email='presti@example.com')
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return user


def test_market_requires_authentication(client):
    """El mercado no es público."""
    response = client.get('/api/v1/assistant/market/')

    assert response.status_code == 401
    assert response.data['error']['code'] == 'not_authenticated'


def test_market_returns_the_snapshot(client, monkeypatch):
    """El mercado devuelve dólar, cripto e índices con el formato del front."""
    from apps.assistant import market

    authenticate(client)
    monkeypatch.setattr(
        market,
        '_coins',
        lambda: [
            {
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'price_usd': 100000.5,
                'change_24h_pct': 1.25,
            }
        ],
    )
    monkeypatch.setattr(
        market,
        '_dollar',
        lambda: {
            'oficial': 1000.0,
            'oficial_avg': 1005.0,
            'blue': 1200.0,
            'blue_avg': 1205.0,
        },
    )

    response = client.get('/api/v1/assistant/market/')

    assert response.status_code == 200
    assert response.data['coins'][0]['symbol'] == 'BTC'
    assert response.data['dollar']['blue'] == 1200.0
    assert response.data['indices'] == []
    assert response.data['updated_at']


def test_market_degrades_when_the_sources_fail(client, monkeypatch):
    """Si las fuentes fallan, responde 200 con lo que haya (sin romper)."""
    from apps.assistant import market

    authenticate(client)
    monkeypatch.setattr(market, '_coins', lambda: [])
    monkeypatch.setattr(market, '_dollar', lambda: None)

    response = client.get('/api/v1/assistant/market/')

    assert response.status_code == 200
    assert response.data['coins'] == []
    assert response.data['dollar'] is None


def test_news_returns_the_feed_items(client, monkeypatch):
    """Las noticias se parsean del RSS configurado."""
    from apps.assistant import market

    authenticate(client)
    monkeypatch.setattr(market, '_fetch', lambda url, limit=None: RSS)

    response = client.get('/api/v1/assistant/news/')

    assert response.status_code == 200
    assert response.data['items'][0]['title'] == 'El dolar blue subio hoy'
    assert response.data['items'][0]['link'] == 'https://example.com/nota'
    assert response.data['items'][0]['source'] == 'Ambito'
    assert response.data['items'][1]['link'] is None


def test_news_returns_an_empty_feed_on_failure(client, monkeypatch):
    """Si el feed falla, responde 200 con la lista vacía."""
    from apps.assistant import market

    authenticate(client)
    monkeypatch.setattr(
        market,
        '_fetch',
        lambda url, limit=None: (_ for _ in ()).throw(OSError('sin red')),
    )

    response = client.get('/api/v1/assistant/news/')

    assert response.status_code == 200
    assert response.data['items'] == []
