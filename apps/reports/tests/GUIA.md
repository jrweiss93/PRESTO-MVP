# Guía de código — apps/reports/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_api.py` | API de reportes. |
| `test_spending_api.py` | Reporte de gastos. |
| `test_loans_api.py` | Reporte de préstamos. |
| `test_investments_api.py` | Reporte de inversiones. |
| `test_export.py` | Exportación CSV. |
| `test_parameters.py` | Validación de parámetros. |
| `test_admin_metrics.py` | Dashboard de métricas. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
