# Guía de código — raíz del repositorio

Este archivo es el índice de documentación local. Cada carpeta de código tiene su propio `GUIA.md` con el detalle de sus archivos.

## Archivos

| Archivo | Qué hace |
|---|---|
| `manage.py` | Entrada de Django; usa `config.settings.local` por defecto. |
| `pyproject.toml` | Dependencias y configuración de ruff. |
| `pytest.ini` | Settings de pytest (`config.settings.test`). |
| `Makefile` | Atajos de Docker: up, test, lint, migrate, seed, front, worker, beat. |
| `README.md` | Presentación, endpoints, arranque y reglas. |
| `AGENTS.md` | Fuente de verdad de reglas de negocio, capas y seguridad. |
| `HANDOFF.md` | Estado técnico, historia y pendientes. |
| `COMO-USAR-LA-DEMO.txt` | Guía corta para abrir la demo local. |
| `PRESTO-DEMO.cmd` | Lanza la demo local completa. |
| `PRESTO-DEMO-STOP.cmd` | Detiene la demo local. |
| `Dockerfile` | Imagen multi-stage con usuario no root. |
| `docker-compose.yml` | Stack local: db, redis, web, worker y beat. |
| `docker-compose.prod.yml` | Stack de producción con perfiles proxy/backup. |
| `render.yaml` | Blueprint de Render. |
| `.env.example` | Plantilla de variables de desarrollo. |
| `.env.prod.example` | Plantilla de variables de producción. |
| `.gitignore` | Archivos que no se versionan. |
| `.gitattributes` | Normalización de fin de línea. |
| `.dockerignore` | Exclusiones del contexto Docker. |
| `.importlinter` | 32 contratos de límites entre apps. |
| `.pre-commit-config.yaml` | Hooks de ruff e import-linter. |
| `.node-version` | Versión de Node para el front. |
| `.nvmrc` | Versión de Node para nvm. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `apps/` | Backend Django dividido por dominio. |
| `config/` | Configuración, rutas, Celery y settings. |
| `deploy/` | Entrypoint, proxy y backup. |
| `frontend/` | SPA React + Vite. |
| `scripts/` | Automatización local, demo y presentaciones. |
| `tests/` | Prueba end-to-end global. |
| `docs/` | Documentación, ADRs y material. |
| `.github/workflows/` | CI. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
