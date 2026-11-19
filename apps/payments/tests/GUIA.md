# Guía de código — apps/payments/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_services.py` | Crear/confirmar/fallar pago y webhook. |
| `test_api.py` | API de pagos y webhook. |
| `test_models.py` | Modelos y constraints. |
| `factories.py` | Fábricas de pagos. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
