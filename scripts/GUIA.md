# Guía de código — scripts

Automatización para desarrollo, demo local, despliegue y presentaciones.

## Archivos

| Archivo | Qué hace |
|---|---|
| `build_presentation.py` | Genera la presentación larga en PPTX/HTML. |
| `build_short_presentation.py` | Genera la presentación corta en PPTX/HTML. |
| `create-demo-shortcuts.ps1` | Crea accesos directos de la demo en el escritorio. |
| `create-superuser-remote.ps1` | Crea el admin en la base remota de Render. |
| `demo_flow.py` | Recorrido funcional completo contra la API local. |
| `env.ps1` | Carga variables de entorno de desarrollo. |
| `install-docker.ps1` | Instala Docker Desktop si la máquina cumple requisitos. |
| `install-services.ps1` | Descarga PostgreSQL 16 y Redis portables. |
| `run_server.ps1` | Levanta el backend local. |
| `run-api.ps1` | Ventana de API para la demo. |
| `run-demo.ps1` | Orquesta la demo local completa. |
| `run-front.ps1` | Levanta el front de Vite. |
| `seed-remote.ps1` | Siembra la demo en la base remota. |
| `setup-venv.ps1` | Crea el entorno virtual e instala dependencias. |
| `smoke-demo.ps1` | Smoke test de 11 chequeos sobre la demo desplegada. |
| `start-services.ps1` | Arranca PostgreSQL y Redis portables. |
| `stop-demo.ps1` | Detiene la demo local. |
| `stop-services.ps1` | Detiene PostgreSQL y Redis portables. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
