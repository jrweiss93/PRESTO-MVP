# Guía de código — config

Configuración central de Django, Celery, rutas, admin y settings por entorno.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Importa Celery para que el worker use el mismo settings. |
| `admin.py` | Configura `PrestoAdminSite` como admin por defecto. |
| `asgi.py` | Punto de entrada ASGI. |
| `celery.py` | Broker Redis y beat schedule. |
| `urls.py` | Admin, health, meta, APIs, schema y Swagger. |
| `wsgi.py` | Punto de entrada WSGI para Gunicorn. |
| `settings/base.py` | Settings comunes y variables de entorno. |
| `settings/local.py` | DEBUG, email por consola y throttles de desarrollo. |
| `settings/production.py` | HTTPS, HSTS, cookies seguras y hosts explícitos. |
| `settings/test.py` | Celery eager, email en memoria y depósitos simulados. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `settings/` | Base, local, producción y test. |
| `staticfiles/` | Estáticos generados por `collectstatic`; no editar a mano. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
