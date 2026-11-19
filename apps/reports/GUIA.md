# Guía de código — apps/reports

Reportes de solo lectura y exportación CSV; no tiene modelos ni escribe estado.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin_site.py` | Sitio de admin con dashboard de métricas de solo lectura. |
| `exceptions.py` | Errores de parámetros y reporte demasiado grande. |
| `export.py` | Genera CSV con la stdlib y neutraliza inyección de fórmulas. |
| `selectors.py` | Validación de período/moneda y agregaciones de gastos, préstamos, inversiones y movimientos. |
| `serializers.py` | Filas y reportes. |
| `urls.py` | Rutas de los cuatro reportes. |
| `views.py` | Vistas finas con exportación CSV opcional. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Los cuatro reportes, parámetros, CSV, métricas y API. |
| `templates/admin/reports/` | Plantillas HTML del dashboard de métricas. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
