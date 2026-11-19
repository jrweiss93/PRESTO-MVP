# Guía de código — apps/budgets

Categorías, presupuestos y clasificación de gastos. El importe se deriva del ledger; no se duplica.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Consulta de categorías, presupuestos y gastos. |
| `exceptions.py` | Errores de categoría, presupuesto, movimiento y duplicados. |
| `models.py` | `Category`, `Expense` (solo clasifica) y `Budget` (límite mensual y umbral). |
| `selectors.py` | Categorías, presupuestos, gastos, gasto mensual y estado; derivan del ledger. |
| `serializers.py` | Categoría, presupuesto, gasto y estado. |
| `services.py` | Crear categoría/presupuesto, categorizar movimiento y disparar alertas. |
| `signals.py` | Señal `budget_alert` para notificaciones. |
| `urls.py` | Presupuestos, categorías, gastos y estado. |
| `views.py` | CRUD de categorías/presupuestos, estado y clasificación de movimientos. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | API, servicios, modelos, selectores, gasto, clasificación, alertas y concurrencia. |
| `migrations/` | Tablas iniciales y modelo Expense. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
