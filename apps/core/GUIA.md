# Guía de código — apps/core

Utilidades transversales que no dependen de ninguna app de dominio. Acá viven el modelo base, el dinero, los errores HTTP y los endpoints operativos.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `checks.py` | System checks: aviso `legal.W001` si falta la revisión legal/PLA-FT. |
| `compliance.py` | Fuente única de los pendientes de compliance que alimentan `/meta/` y el banner del front. |
| `exception_handler.py` | Convierte errores de dominio y DRF al formato uniforme `{"error": {...}}`. |
| `exceptions.py` | Errores base: `DomainError`, `InsufficientFunds`, `InvalidAmount`, `KYCNotCompleted`. |
| `middleware.py` | Health check antes de validar `Host`/TLS y cabecera `X-Presto-Mode: demo`. |
| `models.py` | `BaseModel` abstracto con UUID, `created_at` y `updated_at`. |
| `money.py` | Único lugar de redondeo y fórmulas: cuota francesa, interés simple, TEA, costo total. |
| `pagination.py` | `StandardPagination`: 100 por página, máximo 1000. |
| `serializers.py` | Serializers de metadata y compliance. |
| `views.py` | `/health/` (estado de la base) y `/api/v1/meta/` (modo demo, dinero simulado y compliance). |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Pruebas de dinero, health, meta, OpenAPI, CORS, settings, checks y documentación. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
