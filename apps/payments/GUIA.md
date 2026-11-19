# Guía de código — apps/payments

Intención de pago, webhooks y adaptadores de proveedor. El saldo real se mueve siempre en el ledger.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Consulta de pagos y eventos de webhook. |
| `exceptions.py` | Errores de pago, proveedor, webhook y cuenta destino. |
| `models.py` | `Payment` (intención/estado) y `WebhookEvent` (evento externo único). |
| `permissions.py` | `WebhookThrottle` (60/min). |
| `providers.py` | Interfaz `PaymentProvider`, `SimulatedProvider`, `MercadoPagoProvider` y `get_provider`. |
| `selectors.py` | Pagos del usuario y eventos de webhook. |
| `serializers.py` | Pago, creación y webhook. |
| `services.py` | Crear/confirmar/fallar pago, manejar webhook y mover dinero vía ledger. |
| `urls.py` | `/payments/`, detalle y webhook por proveedor. |
| `views.py` | Listado/creación, detalle y recepción pública de webhooks. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Proveedor simulado, idempotencia, estados, webhook y API. |
| `migrations/` | Tablas iniciales de pagos y eventos. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
