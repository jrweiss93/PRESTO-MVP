# Guía de código — apps/assistant/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_chat.py` | Intenciones, saldo, cuotas, ofertas, mercado, legal y fallback. |
| `test_market_news.py` | Mercado, noticias, caché y degradación. |
| `test_regulations.py` | Fichas legales y búsqueda por id. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
