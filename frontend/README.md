# Presto Front

Front de **Presto** (finanzas e inversión con marketplace de préstamos).
React + Vite + TypeScript + Tailwind. Consume la API Django/DRF de Presto
mediante el contrato OpenAPI (`contract/openapi.yaml`).

## Requisitos

- Node.js 20+ y pnpm (`npm i -g pnpm`)
- La API de Presto corriendo (por defecto `http://localhost:8000/api/v1`)
  o el mock local (`pnpm mock`, puerto 8001)

> Este front vive dentro del monorepo, en `frontend/`. El arranque completo
> (backend + datos de demo + front) está en [`../docs/mvp.md`](../docs/mvp.md).

## Puesta en marcha

```bash
pnpm install
cp .env.example .env      # ajustar VITE_API_URL si hace falta
pnpm dev                  # http://localhost:5173
```

Usuarios de la demo (backend con `manage.py seed_demo`):

| Email               | Rol         | Contraseña   |
| ------------------- | ----------- | ------------ |
| `ana@presto.demo`   | prestataria | `Presto123!` |
| `beto@presto.demo`  | prestamista | `Presto123!` |
| `carla@presto.demo` | inversora   | `Presto123!` |

## Scripts

| Script           | Qué hace                                         |
| ---------------- | ------------------------------------------------ |
| `pnpm dev`       | servidor de desarrollo (Vite, puerto 5173)       |
| `pnpm build`     | typecheck + build de producción en `dist/`       |
| `pnpm preview`   | sirve el build                                   |
| `pnpm mock`      | mock server de la API en memoria (puerto 8001)   |
| `pnpm gen:api`   | regenera los tipos desde `contract/openapi.yaml` |
| `pnpm typecheck` | `tsc --noEmit`                                   |
| `pnpm lint`      | ESLint                                           |
| `pnpm format`    | Prettier                                         |
| `pnpm test`      | Vitest                                           |

## Estructura

```
src/
  app/
    App.tsx                  # rutas y guarda de sesión
    main.tsx                 # punto de entrada
    layout/                  # layout, sidebar, header y banner de cumplimiento
    providers/               # contexto del sidebar
  features/
    auth/                    # AuthContext + login, registro y perfil/KYC
    wallet/                  # dashboard y billetera
    payments/                # pagos
    budgets/                 # presupuestos y categorías de gasto
    marketplace/             # búsqueda de ofertas y ofertas propias
    loans/                   # préstamos y detalle con pago de cuotas
    investments/             # productos y posiciones
    assistant/               # Presti: mercado, noticias, marco legal y chat
  shared/
    api/
      client.ts              # fetch: token en memoria, refresh por cookie, idempotencia
      endpoints.ts           # funciones tipadas por recurso
      types.ts               # alias de los tipos generados
      schema.d.ts            # GENERADO con `pnpm gen:api` (no editar)
    lib/                     # formato de moneda, hooks, utilidades
    ui/                      # íconos y mascot
mock/                        # mock server de la API (node, sin dependencias)
contract/openapi.yaml        # copia del contrato para generar los tipos
```

## Reglas de sesión (importantes)

- El **access token vive solo en memoria**: nunca se guarda en `localStorage`
  ni `sessionStorage`.
- El **refresh token no lo ve el front**: viaja en la cookie httpOnly
  `presto_refresh` que deja el backend. El refresh se pide con
  `credentials: "include"`.
- Toda operación que **mueve dinero** manda el header `Idempotency-Key`
  (depósitos/retiros/transferencias, aceptar oferta, invertir, pagar). El
  backend responde 400 si falta.
- Los importes se formatean **sin `parseFloat`**: se separa la parte entera
  de la decimal y se agrupan los miles, así el número mostrado es
  exactamente el que devolvió la API.

### Lo que la API tiene que permitir

Para que el navegador acepte las peticiones del front, la API necesita:

- `CORS_ALLOWED_ORIGINS` con el origen del front (por ejemplo
  `http://localhost:5173`), separado por comas y **nunca** `*`;
- **credenciales permitidas** (`CORS_ALLOW_CREDENTIALS=True`): el refresh se
  pide con `credentials: "include"` y viaja en cookie httpOnly;
- el header **`Idempotency-Key`** permitido en el preflight, porque lo manda
  toda operación de dinero;
- si el front y la API viven en dominios distintos, la cookie de refresh tiene
  que ir con `SameSite=None` (siempre con `Secure`).

## Pantallas

Dashboard, billetera, pagos, presupuestos, marketplace, ofertas propias,
préstamos (con detalle y pago de cuotas), inversiones, perfil/KYC y el asistente
**Presti**. La raíz `/` es una **landing pública** con las cuentas de demo y
`/legal` explica el alcance (dinero simulado, sin asesoramiento).

Presti está implementado en el backend (`apps/assistant`): mercado (dólar y
cripto), noticias, marco legal curado y chat por reglas, **sin LLM**. Se puede
ocultar con `VITE_ENABLE_ASSISTANT=false`.

## Recordatorio interno de revisión legal

`GET /api/v1/meta/` devuelve el bloque `compliance` con los puntos que
todavía necesitan validación legal o profesional. La app lo muestra como
banner descartable **solo fuera del modo demo**, porque no es un mensaje
para el usuario final:

- `VITE_HIDE_COMPLIANCE_BANNER=true` lo oculta siempre.
- `VITE_SHOW_COMPLIANCE_BANNER=true` lo fuerza, aunque la API esté en demo.

## Mock

`pnpm mock` levanta una API falsa en memoria (puerto 8001) con usuarios de
prueba (`demo@presto.com` / `demo123456`). Sirve para trabajar sin el
backend y para el demo offline. Respeta el mismo contrato: login con
refresh en cookie httpOnly y `Idempotency-Key` obligatorio en las
operaciones de dinero.

## Decisiones y desvíos

Ver `docs/decisions.md`.
