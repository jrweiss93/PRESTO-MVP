# Guía de código — apps/offers

Ofertas de préstamo publicadas por prestamistas: monto, moneda, TNA, plazo, requisitos y estado.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Consulta de ofertas desde el admin. |
| `exceptions.py` | Errores de oferta desaparecida, no editable, no aceptable o propia. |
| `models.py` | `Offer` con estados `active/expired/accepted` y constraints de montos/tasas. |
| `permissions.py` | `HasApprovedKyc` para publicar o modificar ofertas. |
| `selectors.py` | Lectura, bloqueo y búsqueda de ofertas activas. |
| `serializers.py` | Oferta, creación y actualización. |
| `services.py` | Publicar, actualizar, expirar y aceptar; bloqueo de la oferta al aceptar. |
| `urls.py` | `/offers/` y `/offers/{id}/`. |
| `views.py` | Listado/creación y detalle/edición de ofertas. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Servicios, API, modelos, filtros, permisos y aceptación concurrente. |
| `migrations/` | Tabla inicial de ofertas. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
