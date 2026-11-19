# Guía de código — apps/notifications/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_services.py` | Creación, preferencias y lectura. |
| `test_receivers.py` | Señales y avisos. |
| `test_tasks.py` | Reintentos y backoff. |
| `test_emails.py` | Plantillas de email. |
| `test_api.py` | API de avisos. |
| `test_loan_created.py` | Aviso de préstamo creado. |
| `test_installment_paid.py` | Aviso de cuota pagada. |
| `factories.py` | Fábricas de avisos. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
