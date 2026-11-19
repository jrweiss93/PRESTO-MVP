# Guía de código — apps/ledger

Libro mayor de doble entrada: cuentas, transacciones, asientos, saldos, idempotencia, bloqueos y reversos.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Admin de cuentas y movimientos; los asientos no se editan, solo se consultan o reversan. |
| `checks.py` | `ledger.E001`: bloquea depósitos simulados en producción si no está `DEMO_MODE`. |
| `exceptions.py` | Errores de cuentas, moneda, idempotencia, saldo y depósitos simulados. |
| `models.py` | `Account`, `LedgerTransaction` y `LedgerEntry` con constraints de moneda, saldo e idempotencia. |
| `selectors.py` | Cuentas, saldos, movimientos, períodos, desglose y detalle de movimientos. |
| `serializers.py` | Cuentas, transacciones, creación y saldo. |
| `services.py` | Depósitos, retiros, transferencias, reversos, bloqueo de cuentas, doble entrada, idempotencia y KYC. |
| `urls.py` | Rutas de cuentas, saldo, transacciones y detalle. |
| `views.py` | Listado/creación de cuentas y movimientos; paginación por cursor. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Doble entrada, inmutable, triggers, saldo, concurrencia, idempotencia y API. |
| `migrations/` | Tablas del ledger, triggers de inmutabilidad/doble entrada y constraints de moneda/saldo. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
