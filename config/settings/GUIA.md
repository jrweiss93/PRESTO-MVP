# Guía de código — config/settings

Settings separados por entorno. Los secretos llegan por variables de entorno.

## Archivos

| Archivo | Qué hace |
|---|---|
| `base.py` | Settings comunes y variables de entorno. |
| `local.py` | DEBUG, email por consola y throttles de desarrollo. |
| `production.py` | HTTPS, HSTS, cookies seguras y hosts explícitos. |
| `test.py` | Celery eager, email en memoria y depósitos simulados. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
