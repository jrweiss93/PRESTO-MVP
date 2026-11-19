# Guía de código — apps/ledger/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_services.py` | Depósitos, retiros, transferencias, reversos e idempotencia. |
| `test_api.py` | API de cuentas y saldo. |
| `test_api_transactions.py` | API de movimientos. |
| `test_models.py` | Modelos y constraints. |
| `test_triggers.py` | Doble entrada e inmutabilidad en PostgreSQL. |
| `test_concurrency.py` | Bloqueos y carreras. |
| `test_selectors.py` | Consultas y aislamiento. |
| `test_period_selectors.py` | Filtros por período. |
| `test_movement_details.py` | Detalle de movimientos. |
| `test_checks.py` | Check de depósitos simulados. |
| `test_admin.py` | Admin y reversos. |
| `factories.py` | Fábricas del ledger. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
