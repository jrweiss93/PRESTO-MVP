# Guía de código — frontend

SPA React + Vite + TypeScript. Consume la API por OpenAPI y se despliega en Vercel.

## Archivos

| Archivo | Qué hace |
|---|---|
| `package.json` | Dependencias, scripts y Node ≥ 24. |
| `vite.config.ts` | Vite, React, alias `@` y tests. |
| `tsconfig.json` | Configuración TypeScript. |
| `eslint.config.js` | Reglas de lint. |
| `playwright.config.ts` | Proyectos E2E mock/API. |
| `vercel.json` | Rewrites de SPA. |
| `index.html` | HTML base y script inline de tema. |
| `.env` | URL de API y flags locales. |
| `.env.example` | Plantilla de variables del front. |
| `README.md` | Guía del front y reglas de sesión. |
| `contract/openapi.yaml` | Contrato para generar tipos. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `src/` | Código de la SPA. |
| `mock/` | API en memoria para desarrollo. |
| `e2e/` | Specs de Playwright. |
| `contract/` | Contrato OpenAPI. |
| `docs/` | Decisiones del front. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
