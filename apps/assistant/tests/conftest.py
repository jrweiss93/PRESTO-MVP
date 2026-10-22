"""Fixtures de los tests del asistente."""

import pytest


@pytest.fixture(autouse=True)
def clear_cache():
    """Limpia la caché entre tests (mercado y noticias)."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
