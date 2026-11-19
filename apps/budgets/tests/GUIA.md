# Guía de código — apps/budgets/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_api.py` | Endpoints de categorías, presupuestos, gastos y estado. |
| `test_services.py` | Creación y clasificación de movimientos. |
| `test_services_edges.py` | Casos borde de servicios. |
| `test_models.py` | Constraints y modelos. |
| `test_selectors.py` | Aislamiento y consultas. |
| `test_spending.py` | Regla de gasto derivada del ledger. |
| `test_categorization.py` | Categorización de movimientos. |
| `test_classification.py` | Clasificación de gastos. |
| `test_budget_alert.py` | Señal de alerta de presupuesto. |
| `test_concurrency.py` | Concurrencia. |
| `factories.py` | Fábricas de prueba. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
