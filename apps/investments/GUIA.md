# Guía de código — apps/investments

Productos de plazo fijo y posiciones de inversión, con apertura, interés simple y liquidación idempotente.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Alta de productos solo staff y liquidación manual de posiciones. |
| `exceptions.py` | Errores de producto y monto mínimo. |
| `models.py` | `InvestmentProduct` y `Position` con constraints de plazo, tasa, monto e idempotencia. |
| `permissions.py` | `IsInvestor` para operar con perfil inversor. |
| `selectors.py` | Productos activos y posiciones del usuario. |
| `serializers.py` | Producto, posición, detalle y apertura. |
| `services.py` | Abrir posición, mover dinero al sistema, calcular interés y liquidar vencidas. |
| `signals.py` | `investment_settled` para notificaciones. |
| `tasks.py` | Tarea Celery `settle_investments`; adaptador delgado del service. |
| `urls.py` | Productos y posiciones. |
| `views.py` | Listado de productos, posiciones y detalle. |
| `management/commands/settle_investments.py` | Liquida vencidas desde consola. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Apertura, intereses, liquidación, comandos, tareas, concurrencia y API. |
| `migrations/` | Tablas iniciales y nombre/descripción de producto. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
