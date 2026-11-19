# Guía de código — apps/offers/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_services.py` | Publicar, editar, expirar y aceptar. |
| `test_api.py` | Endpoints de ofertas. |
| `test_models.py` | Modelo y constraints. |
| `test_selectors.py` | Búsqueda/bloqueo. |
| `test_permissions.py` | KYC para publicar. |
| `test_concurrency.py` | Aceptación concurrente. |
| `factories.py` | Fábricas de ofertas. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
