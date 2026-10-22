"""Fuentes externas del asistente: mercado y noticias.

Todo es de solo lectura y con caché. Si una fuente externa falla, el asistente
devuelve la parte que sí pudo armar (o una lista vacía) en vez de romper la
pantalla.
"""

import json
import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

MARKET_CACHE_KEY = 'assistant:market'
NEWS_CACHE_KEY = 'assistant:news'
MAX_FEED_BYTES = 512 * 1024
USER_AGENT = 'PrestoAssistant/1.0'

COINS = (
    ('bitcoin', 'BTC', 'Bitcoin'),
    ('ethereum', 'ETH', 'Ethereum'),
)
COINGECKO_URL = (
    'https://api.coingecko.com/api/v3/simple/price'
    '?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true'
)
DOLLAR_URL = 'https://api.bluelytics.com.ar/v2/latest'


def _now_iso() -> str:
    """Devuelve la fecha actual en ISO 8601 UTC."""
    return datetime.now(UTC).isoformat(timespec='seconds')


def _fetch(url: str, *, limit: int | None = None) -> bytes:
    """Descarga una URL con timeout y User-Agent propio."""
    request = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(request, timeout=settings.ASSISTANT_HTTP_TIMEOUT) as response:
        return response.read(limit) if limit else response.read()


def _fetch_json(url: str):
    """Descarga y parsea un JSON."""
    return json.loads(_fetch(url).decode('utf-8'))


def _round(value):
    """Convierte a float con dos decimales, o None si no es un número."""
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _coins() -> list[dict]:
    """Cotizaciones de cripto desde CoinGecko."""
    try:
        data = _fetch_json(COINGECKO_URL)
    except (OSError, URLError, ValueError):
        logger.warning('No se pudo obtener el mercado de cripto.', exc_info=True)
        return []
    if not isinstance(data, dict):
        return []
    coins = []
    for coin_id, symbol, name in COINS:
        item = data.get(coin_id)
        if not isinstance(item, dict):
            continue
        coins.append(
            {
                'symbol': symbol,
                'name': name,
                'price_usd': _round(item.get('usd')),
                'change_24h_pct': _round(item.get('usd_24h_change')),
            }
        )
    return coins


def _dollar() -> dict | None:
    """Cotizaciones del dólar oficial y blue desde Bluelytics."""
    try:
        data = _fetch_json(DOLLAR_URL)
    except (OSError, URLError, ValueError):
        logger.warning('No se pudo obtener la cotización del dólar.', exc_info=True)
        return None
    if not isinstance(data, dict):
        return None
    oficial = data.get('oficial') if isinstance(data.get('oficial'), dict) else {}
    blue = data.get('blue') if isinstance(data.get('blue'), dict) else {}
    return {
        'oficial': _round(oficial.get('value_sell')),
        'oficial_avg': _round(oficial.get('value_avg')),
        'blue': _round(blue.get('value_sell')),
        'blue_avg': _round(blue.get('value_avg')),
    }


def get_market_snapshot() -> dict:
    """Devuelve el snapshot de mercado, cacheado unos segundos.

    Returns:
        Dict con `updated_at`, `coins`, `indices` y `dollar`.
    """
    cached = cache.get(MARKET_CACHE_KEY)
    if cached is not None:
        return cached

    coins: list[dict] = []
    dollar = None
    if settings.ASSISTANT_MARKET_ENABLED:
        coins = _coins()
        dollar = _dollar()

    snapshot = {
        'updated_at': _now_iso(),
        'coins': coins,
        'indices': [],
        'dollar': dollar,
    }
    # Si no vino nada, no se cachea: el próximo pedido reintenta.
    if coins or dollar:
        cache.set(MARKET_CACHE_KEY, snapshot, settings.ASSISTANT_MARKET_CACHE_SECONDS)
    return snapshot


def _clean_text(value: str | None) -> str:
    """Colapsa los espacios de un texto de RSS."""
    return ' '.join((value or '').split())


def _safe_url(value: str | None) -> str | None:
    """Devuelve la URL solo si es http o https."""
    url = (value or '').strip()
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return None
    return url


def _published_at(value: str | None) -> str | None:
    """Convierte la fecha de un RSS a ISO 8601, o None."""
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat(timespec='seconds')


def _parse_news(raw: bytes) -> list[dict]:
    """Parsea un feed RSS y devuelve hasta 8 noticias."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        logger.warning('El feed de noticias no es XML válido.')
        return []

    channel = root.find('channel')
    source = _clean_text(channel.findtext('title')) if channel is not None else ''
    items = []
    for item in root.findall('.//item')[:8]:
        title = _clean_text(item.findtext('title'))
        if not title:
            continue
        items.append(
            {
                'title': title,
                'link': _safe_url(item.findtext('link')),
                'published_at': _published_at(item.findtext('pubDate')),
                'source': source or 'RSS',
            }
        )
    return items


def get_news_feed() -> dict:
    """Devuelve las últimas noticias del feed configurado, cacheadas.

    Returns:
        Dict con `updated_at` e `items`. Sin feed configurado, `items` va vacío.
    """
    cached = cache.get(NEWS_CACHE_KEY)
    if cached is not None:
        return cached

    items: list[dict] = []
    feed_url = settings.ASSISTANT_NEWS_FEED_URL
    if feed_url:
        try:
            items = _parse_news(_fetch(feed_url, limit=MAX_FEED_BYTES))
        except (OSError, URLError):
            logger.warning('No se pudo obtener el feed de noticias.', exc_info=True)

    feed = {'updated_at': _now_iso(), 'items': items}
    if items:
        cache.set(NEWS_CACHE_KEY, feed, settings.ASSISTANT_NEWS_CACHE_SECONDS)
    return feed
