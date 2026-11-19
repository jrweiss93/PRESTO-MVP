# Guía de código — apps/investments/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_api.py` | Endpoints de productos y posiciones. |
| `test_services.py` | Apertura, interés y liquidación. |
| `test_models.py` | Modelos y constraints. |
| `test_concurrency.py` | Concurrencia. |
| `test_commands.py` | Comando de liquidación. |
| `test_tasks.py` | Tarea Celery. |
| `test_settlement_notification.py` | Aviso de liquidación. |
| `factories.py` | Fábricas de inversión. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
