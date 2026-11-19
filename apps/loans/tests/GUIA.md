# Guía de código — apps/loans/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_api.py` | Endpoints de préstamos/cuotas. |
| `test_services.py` | Aceptación, cuotas, pago, snapshot y estados. |
| `test_models.py` | Modelos y constraints. |
| `test_concurrency.py` | Aceptación concurrente. |
| `test_repayment_source.py` | Cuenta de respaldo. |
| `test_loan_breakdown.py` | Desglose de cuotas. |
| `test_commands.py` | Comando de vencimientos. |
| `test_tasks.py` | Tareas de vencimiento. |
| `test_notify_tasks.py` | Avisos de cuotas. |
| `test_messages.py` | Chat privado. |
| `test_reviews.py` | Reseñas y reputación. |
| `test_cancellation.py` | Cancelación y archivado. |
| `factories.py` | Fábricas de préstamos. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
