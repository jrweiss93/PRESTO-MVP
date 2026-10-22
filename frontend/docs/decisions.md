# Decisiones del front

Registro corto de las decisiones tomadas al migrar el prototipo heredado
(`Documents/Default Project`) al repositorio `PRESTOFRONT/frontend`.
Referencia: `PROYECTO_FRONT.md` (contrato con el backend).

## Cumplido

| Regla                                      | Cómo se cumple                                                                                                                                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Todo dentro de `frontend/`                 | La app, el mock y el contrato viven en `frontend/`.                                                                                                                                                    |
| Tipos generados del contrato               | `pnpm gen:api` genera `src/shared/api/schema.d.ts`; `types.ts` solo hace alias.                                                                                                                        |
| Access token solo en memoria               | `src/shared/api/client.ts` lo guarda en una variable del módulo.                                                                                                                                       |
| Refresh por cookie httpOnly                | El backend deja la cookie `presto_refresh`; el front llama `POST /auth/token/refresh/` con `credentials: "include"`.                                                                                   |
| `Idempotency-Key` en operaciones de dinero | `apiPostWithIdempotency()` + `useIdempotencyKey()` (clave estable por intento).                                                                                                                        |
| Importes sin `parseFloat`                  | `formatMoney()` separa entero y decimal y agrupa los miles.                                                                                                                                            |
| Banner legal descartable                   | `ComplianceBanner` en el layout, oculto en modo demo.                                                                                                                                                  |
| CORS con credenciales                      | El front manda `credentials: "include"` en login, refresh y operaciones de dinero; la API responde con `Access-Control-Allow-Credentials: true` y permite el header `Idempotency-Key` en el preflight. |

## Desvíos (a revisar antes de producción)

### D-1 · Mock server propio en lugar de MSW

El spec propone **MSW** para interceptar la API en el navegador. Acá se usa
`mock/server.mjs`, un servidor Node con la API completa en memoria.

Motivos: el prototipo ya traía ese mock (870 líneas) con el asistente de
mercado, noticias y marco regulatorio ya resueltos; y el flujo de login
necesita una cookie httpOnly real, que MSW no reproduce bien.

Consecuencia: el front tiene dos modos (`VITE_API_URL` apunta al backend o
al mock). El modo MSW queda como deuda técnica a cerrar si se quiere el
`pnpm dev` sin proceso extra.

### D-2 · Sin TanStack Query ni Zod

El spec los propone para el manejo de datos y la validación de formularios.
Esta entrega mantiene `useState`/`useEffect` (el patrón del prototipo) y
valida con atributos HTML nativos. Es el desvío más grande: antes de
producción hay que migrar el fetching a TanStack Query y los formularios a
Zod + React Hook Form.

### D-3 · End-to-end fuera de la CI

Hay specs de Playwright en `e2e/` (auth, marketplace y wallet) contra el mock y
contra la API real, pero **no corren en la CI**: el pipeline solo ejecuta
`typecheck`, los tests unitarios de Vitest y el build. Además quedó registrado un
caso de marketplace con fallo (`test-results/`), así que antes de confiar en la
suite hay que correrla completa y arreglar ese caso.

### D-4 · Sin i18n

La interfaz está en español rioplatense y no usa librería de i18n (el spec
no la exige).

### D-5 · Presti pasó del mock al backend

La feature **Presti** (mercado, noticias, marco regulatorio y chat) nació como
mock. Ahora está implementada en el backend (`apps/assistant`) **sin LLM**:
mercado y noticias de fuentes externas con caché, fichas legales curadas y chat
por intenciones con datos reales del usuario. El mock sigue sirviendo para
trabajar offline (`pnpm mock`). Ver ADR 0017.
