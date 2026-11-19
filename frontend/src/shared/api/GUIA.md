# Guía de código — frontend/src/shared/api

Contrato y acceso a la API.

## Archivos

| Archivo | Qué hace |
|---|---|
| `client.ts` | Fetch centralizado: token en memoria, refresh cookie, 401, idempotencia, errores y paginación. |
| `endpoints.ts` | Funciones tipadas por recurso. |
| `types.ts` | Alias de tipos generados desde OpenAPI. |
| `schema.d.ts` | Generado con `pnpm gen:api`; no editar a mano. |
| `client.test.ts` | Tests de sesión/refresh/errores. |
| `endpoints.test.ts` | Tests de endpoints. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
