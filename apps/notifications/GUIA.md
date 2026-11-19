# Guía de código — apps/notifications

Avisos in-app y por email, preferencias y reintentos. No guarda datos financieros.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Consulta de avisos y preferencias. |
| `emails.py` | Emails de texto plano sin datos sensibles. |
| `exceptions.py` | Errores de evento y aviso. |
| `models.py` | `Notification` y `NotificationPreference` con unicidad por evento. |
| `receivers.py` | Conecta señales de loans/investments/budgets y encola el email. |
| `selectors.py` | Listado, preferencias y contador de no leídos. |
| `serializers.py` | Avisos, preferencias y contadores. |
| `services.py` | Crear aviso, preferencias, intentos, envío/fallo y lectura. |
| `tasks.py` | `send_notification_email` con reintentos y backoff. |
| `urls.py` | Avisos, preferencias, lectura y contador. |
| `views.py` | Vistas de avisos, preferencias y lectura. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Avisos, señales, emails, tareas, préstamo creado y cuota pagada. |
| `migrations/` | Tablas iniciales, intentos, lectura y ampliación de eventos. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
