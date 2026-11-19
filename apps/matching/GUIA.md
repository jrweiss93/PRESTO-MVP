# Guía de código — apps/matching

App de solo lectura para buscar y comparar ofertas sin crear préstamos ni modificar estado.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `exceptions.py` | Errores de comparación y oferta inexistente. |
| `selectors.py` | `search_offers` y `compare_offers` con cuota, interés total, costo y TEA. |
| `serializers.py` | Query de búsqueda, oferta match, comparación y payload. |
| `urls.py` | `/matching/offers/` y `/matching/comparisons/`. |
| `views.py` | Vistas de búsqueda y comparación. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Búsqueda, orden, filtros, comparación y API. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
