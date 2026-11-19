# Guía de código — apps/assistant

Presti: mercado, noticias, marco legal curado y chat por reglas, sin LLM.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `market.py` | Dólar/cripto y noticias con timeout, caché y degradación a vacío. |
| `permissions.py` | `AssistantThrottle` (120/h). |
| `regulations.py` | Fichas legales curadas con normas y enlaces oficiales. |
| `selectors.py` | Resúmenes del usuario usando selectores de otras apps. |
| `serializers.py` | Mercado, noticias, regulaciones, chat y respuestas. |
| `services.py` | Intenciones del chat: saldo, cuotas, inversiones, ofertas, mercado, legal y tutoriales. |
| `urls.py` | Mercado, noticias, regulaciones y chat. |
| `views.py` | Vistas de Presti y chat. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Intenciones del chat, mercado/noticias y fichas legales. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
