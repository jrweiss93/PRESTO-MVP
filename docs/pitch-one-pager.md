# Presto en una página

**Presto** es una API de finanzas e inversiones con un marketplace de préstamos:
cada persona publica ofertas, las compara y elige la que le conviene; el dinero
que se mueve lo lleva un libro mayor de doble entrada. Hoy hay dos piezas
funcionando y verificadas: **el backend (Django + PostgreSQL)** y **el frontend
(React + TypeScript + Vite)**.

> Documento de pitch: qué es, cómo está armado, qué se puede mostrar en cinco
> minutos y qué falta. Las reglas del proyecto viven en
> [AGENTS.md](../AGENTS.md) y el detalle del trabajo en
> [HANDOFF.md](../HANDOFF.md).

---

## 1. Qué se puede mostrar hoy

| Pantalla | Qué resuelve |
|---|---|
| `/dashboard` | Resumen de la cuenta y de la actividad |
| `/billetera` | Saldos por moneda, movimientos y depósitos/retiros/transferencias |
| `/pagos` | Pagos (depósito, retiro, transferencia) con su estado y su comprobante |
| `/marketplace` | Ofertas de préstamo, filtros y comparación (TEA + costo total) |
| `/ofertas` | Publicar una oferta de préstamo |
| `/prestamos` | Préstamos tomados, cronograma de cuotas y pago de una cuota |
| `/inversiones` | Plazos fijos: catálogo y posiciones |
| `/presupuestos` | Categorías, presupuestos, umbral de alerta y gasto acumulado |
| `/asistente` | Asistente de demo (funciona contra el mock, no contra la API) |

**Datos de la demo** (`manage.py seed_demo`, idempotente):

| Persona | Rol | Usuario | Contraseña |
|---|---|---|---|
| Ana | prestataria | `ana@presto.demo` | `Presto123!` |
| Beto | prestamista | `beto@presto.demo` | `Presto123!` |
| Carla | inversora | `carla@presto.demo` | `Presto123!` |

## 2. Demo de cinco minutos

```sh
# 1. Backend (PostgreSQL + Redis + web + worker + beat)
docker compose up --build -d
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed_demo

# 2. Front
cd ../PRESTOFRONT/frontend
pnpm install
pnpm dev            # http://localhost:5173
```

Sin Docker, el front también tiene un **mock** con el mismo contrato:

```sh
pnpm mock           # API falsa en http://localhost:8001
```

Alternativa sin base de datos: `pnpm mock` y `VITE_API_URL=http://127.0.0.1:8001/api/v1`.

## 3. Cómo está armado

**Monolito modular**: un proyecto Django, una base PostgreSQL, un despliegue.
12 apps y una regla por app: **solo se entra a otra por su `services.py` y su
`selectors.py`** (nunca importando modelos, vistas ni serializers). 31 contratos
de `import-linter` lo vigilan.

```
identity   ledger   offers   matching   loans   investments
                          budgets   reports   notifications
                          payments  demo
```

- **identity**: usuarios, JWT, perfil y KYC.
- **ledger**: libro mayor de doble entrada (cuentas, movimientos, reversos).
- **offers / matching / loans**: oferta, búsqueda, comparación, préstamo y cuotas.
- **investments**: plazos fijos.
- **budgets / reports / notifications**: presupuestos y gastos, reportes (con CSV),
  avisos por email.
- **payments**: depósitos, retiros y transferencias detrás de la interfaz
  `PaymentProvider` (hoy: un proveedor simulado y el de Mercado Pago).
- **demo**: siembra el escenario de demostración. No tiene modelos.

### El dinero

- **Doble entrada**: cada movimiento genera un débito y un crédito; la **suma de
  los saldos por moneda da 0** y eso está garantizado por constraints y triggers
  en la base, no solo por el código.
- **Idempotencia**: toda operación de dinero exige la header `Idempotency-Key`.
  Repetir la misma clave con el mismo payload devuelve la misma operación (no se
  mueve el saldo dos veces); con un payload distinto, `409`.
- **KYC obligatorio** antes de operar con dinero.
- **Nada de datos de tarjetas**: el cobro lo delega a un proveedor de pagos.
- El saldo lo mueve **el ledger**, no el proveedor: el webhook firmado del
  proveedor es el que confirma el pago.

### Decisiones que sostienen el diseño

| Decisión | Qué significa |
|---|---|
| O1 | El proveedor de pagos es **Mercado Pago**, detrás de la interfaz `PaymentProvider` |
| O2 | Presto **no es custodio**: cuentas segregadas y solo mueve dinero entre sus usuarios |
| O3 | El plazo fijo **no tiene garantía de capital** |
| O6 | Se compara con **TEA + costo total**, no solo con la tasa |
| D-10 | El refresh token viaja en una **cookie httpOnly**; el token de acceso nunca se persiste en el front |

## 4. Front

React 18 + TypeScript + Vite, con la estructura `src/app` (rutas y layout),
`src/features/*` (pantallas por dominio) y `src/shared/*` (API, UI y utilidades).

- **Tipos generados del contrato**: `openapi-typescript` sobre el
  `openapi.yaml` que genera el backend (`pnpm gen:api`). El esquema del backend
  y el del front son el mismo archivo, byte a byte.
- **El token de acceso vive solo en memoria**; la sesión se recupera con la
  cookie httpOnly (`credentials: "include"`), que es también lo que exige el
  CORS con credenciales.
- **Idempotencia en el front**: cada acción de dinero manda `Idempotency-Key` con
  una clave estable por intento, para que un doble clic no duplique el movimiento.
- **Importes sin pérdida**: los `Decimal` del backend llegan como strings y se
  formatean sin `parseFloat`.
- **Banner de cumplimiento**: el front muestra un recordatorio interno de que la
  revisión legal y de PLA/FT está pendiente (se puede ocultar en demo con
  `VITE_HIDE_COMPLIANCE_BANNER`).

## 5. Evidencia

| Chequeo | Resultado |
|---|---|
| Tests del backend | **750 passed** |
| Tests del front (Vitest) | **25 passed** (4 archivos) |
| Lint y formato | `ruff check` sin findings, `ruff format --check` 293 archivos, `pnpm lint` 0 errores |
| Tipos y build del front | `pnpm typecheck` y `pnpm build` en verde |
| Límites entre apps | **31 contratos, 0 rotos** |
| OpenAPI | 37 paths, 0 errores y 0 warnings |
| Migraciones | `makemigrations --check` sin cambios |
| `check --deploy` | Sin problemas (el único aviso es el recordatorio legal) |
| Flujo real por HTTP | Registro → login → KYC → depósito → oferta → comparación → préstamo → cuota → inversión → presupuesto → reportes → avisos → pagos |
| Invariante del ledger | **Suma de saldos ARS 0 y USD 0** al final del flujo |
| CORS | Preflight con `access-control-allow-credentials` e `idempotency-key` permitido |

## 6. Qué falta

| Tema | Estado |
|---|---|
| Mercado Pago real | La integración está escrita (webhook con firma HMAC, idempotencia) pero falta el **contrato comercial y las credenciales**; hoy corre el proveedor simulado |
| Revisión legal y de PLA/FT | La implementación es la mínima viable. Lo que depende de un profesional queda **pendiente de validación** (documentado en [docs/regulatorio-bcra.md](regulatorio-bcra.md)); el backend lo recuerda con `legal.W001` y con `GET /api/v1/meta/` |
| Cobertura end-to-end del front | El front se verifica con tests unitarios y de integración; falta una suite E2E en navegador |
| Despliegue | La guía de **Oracle Cloud (ARM) + DuckDNS + Vercel** está en [docs/deploy-demo.md](deploy-demo.md) |

## 7. Enlaces

- Reglas del proyecto: [AGENTS.md](../AGENTS.md)
- Estado del trabajo y decisiones: [HANDOFF.md](../HANDOFF.md)
- Mapa del backend: [docs/architecture.md](architecture.md)
- Decisiones de arquitectura: [docs/adr/](adr/)
- Marco regulatorio a validar: [docs/regulatorio-bcra.md](regulatorio-bcra.md)
- Esquema OpenAPI: `/api/schema/` (Swagger UI en `/api/docs/`)
