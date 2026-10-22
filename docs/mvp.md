# MVP de Presto — guía única (backend + frontend)

Este repositorio es el **monorepo consolidado** de Presto: la API Django en la
raíz y el front React/Vite en [`frontend/`](../frontend/). Reemplaza a las copias
sueltas que estaban en el escritorio:

| Pieza | Origen | Por qué |
|---|---|---|
| Backend | `Desktop\PRESTOWEB\prestoweb-main` | Es la versión más nueva: app `payments`, `seed_demo`, refresh en cookie httpOnly, `/auth/logout/`, `compliance` y reintentos de avisos. |
| Frontend | `Desktop\PRESTOFRONT\frontend` | Única copia con el cliente HTTP contra cookies y el contrato actualizado. |

> Los originales **no se tocaron**. Todo lo nuevo vive en `Desktop\PRESTO-MVP`.

## 1. Arranque rápido (10 minutos)

Requisitos: Docker + Docker Compose, Node 20+ y `pnpm`.

```sh
# 1) Backend, base, Redis, worker y beat
docker compose up -d --build
docker compose ps

# 2) Datos de demo (usuarios, ofertas, préstamos, inversiones y gastos)
docker compose run --rm web python manage.py seed_demo

# 3) Front
cd frontend
pnpm install
pnpm dev            # http://localhost:5173
```

Usuarios de la demo (contraseña `Presto123!`):

| Email | Rol |
|---|---|
| `ana@presto.demo` | prestataria |
| `beto@presto.demo` | prestamista |
| `carla@presto.demo` | inversora |

La API queda en `http://localhost:8000`, Swagger en `/api/docs/` y el admin en
`/admin/`.

> Usá **`localhost`** en el front y en la API. Si el front corre en `localhost`
> y la API en `127.0.0.1`, el navegador los trata como sitios distintos y la
> cookie del refresh no viaja.

### 1.b Sin Docker (Windows, sin permisos de administrador)
Docker Desktop necesita virtualización habilitada en la BIOS, WSL2 y permisos de
administrador. Si eso no está disponible, el stack se puede correr nativo con
PostgreSQL y Redis portables (es lo que quedó instalado en esta máquina, en
`%LOCALAPPDATA%\presto`):

```powershell
# Una sola vez
.\scripts\install-services.ps1     # baja PostgreSQL 16 y Redis portables
.\scripts\setup-venv.ps1           # crea .venv e instala dependencias

# Cada vez que se trabaja
.\scripts\start-services.ps1
. .\scripts\env.ps1
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# Al terminar
.\scripts\stop-services.ps1
```

El worker y el beat también corren nativos:

```powershell
.\.venv\Scripts\python.exe -m celery -A config worker -l info
.\.venv\Scripts\python.exe -m celery -A config beat -l info --schedule .\celerybeat-schedule
```

### 1.c Docker (cuando la máquina lo permita)

Docker Desktop necesita **tres cosas**: sesión de administrador, virtualización
habilitada en la BIOS (SVM/AMD-V o VT-x) y WSL2. El instalador ya está
descargado en `%LOCALAPPDATA%\presto\installers`.

```powershell
# PowerShell como administrador, después de habilitar SVM/VT-x en la BIOS
.\scripts\install-docker.ps1
```

El script verifica los requisitos, instala WSL2 si falta y corre el instalador.
Si algo no está listo, lo explica y no toca nada. Después del reinicio:

```sh
docker run --rm hello-world
docker compose up -d --build
```

## 2. Guion de demo (5 minutos)

1. Entrar como **ana**: dashboard con saldo, préstamo activo y cuota próxima.
2. **Prestamos → detalle**: pagar la cuota 1 (pide `Idempotency-Key`; el pago
   mueve el ledger y actualiza el estado).
3. Entrar como **carla** en otra ventana: **Inversiones → abrir plazo fijo**.
4. **Billetera**: depósito simulado y transferencia a otra persona por alias.
5. **Presupuestos**: categoría + límite mensual + gasto.
6. **Reportes** (desde el dashboard): gasto por categoría y movimientos.
7. Volver a **beto**: el préstamo aparece como prestamista y ve el pago.

Todo el dinero es **simulado** (`DEMO_MODE=true`): no hay pasarela conectada.

## 3. Cómo está integrado

- **Sesión**: el login devuelve solo el `access` (en memoria) y deja el refresh
  en la cookie httpOnly `presto_refresh` (path `/api/v1/auth/`). El front
  refresca con `credentials: "include"`; `/auth/logout/` la borra y blacklistea
  el token.
- **CORS**: `CORS_ALLOWED_ORIGINS` incluye `localhost:5173` en desarrollo, con
  credenciales y el header `idempotency-key` permitido.
- **Contrato**: `frontend/contract/openapi.yaml` es la copia que consume el
  front; los tipos se regeneran con `pnpm gen:api`.
- **Asistente "Presti"**: solo existe en el mock (`frontend/mock`). Contra la
  API real está oculto por defecto (`VITE_ENABLE_ASSISTANT=false`). Para verlo:
  `pnpm mock` y `VITE_ENABLE_ASSISTANT=true`.

## 4. Verificación

```sh
# Backend
docker compose run --rm web python -m pytest -q
docker compose run --rm web ruff check .
docker compose run --rm web lint-imports --cache-dir /tmp/import-linter-cache

# Front
cd frontend
pnpm typecheck
pnpm test
pnpm build
```

Sin Docker, con el entorno nativo:

```powershell
. .\scripts\env.ps1
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

> CI, la imagen Docker y producción corren **Python 3.14 + Django 6.1**. El
> entorno local puede ser 3.12 o superior; el `.venv` de esta máquina quedó con
> 3.14.

## 5. Desplegar para mostrarlo

**Backend** (Render / Northflank / VPS con Docker): usar la imagen del
`Dockerfile`, `RUN_MIGRATIONS=1`, un PostgreSQL y un Redis administrados, y estas
variables:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<secreto largo>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api.tu-dominio.com
DATABASE_URL=postgres://...
REDIS_URL=redis://...
DEMO_MODE=true
CORS_ALLOWED_ORIGINS=https://tu-front.vercel.app
JWT_REFRESH_COOKIE_SAMESITE=None
JWT_REFRESH_COOKIE_SECURE=true
```

Después del primer arranque: `python manage.py seed_demo` y
`python manage.py createsuperuser`.

**Front** (Vercel): root `frontend/`, build `pnpm build`, salida `dist`, y
`VITE_API_URL=https://api.tu-dominio.com/api/v1`.

> Si el front y la API comparten dominio (por ejemplo `presto.com` y
> `api.presto.com`), alcanza con `SameSite=Lax`. Si el front está en Vercel y la
> API en otro sitio, **hacen falta** `SameSite=None` y `Secure`.

La guía larga de despliegue sigue en [`deploy-demo.md`](deploy-demo.md).

## 6. Qué falta antes de abrir al público con dinero real

Esto ya está resuelto: pagos simulados y con Mercado Pago detrás de una
interfaz, webhooks firmados, seed de demo, sesión con cookie, CORS y
notificaciones con reintento.

Sigue pendiente:

1. **Contrato con el proveedor de pagos** (credenciales y comisiones) y probar
   el flujo real en sandbox → producción.
2. **KYC con documentos**: hoy el KYC es metadata JSON aprobada a mano desde el
   admin. Hace falta subida de archivos y/o proveedor de identidad.
3. **Recuperación de contraseña y verificación de email**: ✅ implementadas
   (ADR 0016). El reseteo responde siempre 202 para no filtrar qué emails
   existen, cierra las sesiones abiertas al cambiar la clave y la verificación
   de email se muestra en el perfil. En la demo los correos salen por consola.
   La verificación es informativa: el requisito para mover dinero sigue siendo
   el KYC.
4. **Legal**: términos y condiciones, política de privacidad, aviso de "dinero
   simulado" en la demo y cierre de las definiciones regulatorias
   (`docs/regulatorio-bcra.md`).
5. **Operación**: Sentry, backups automáticos con prueba de restauración, HTTPS
   y dominio propio.
6. **Producto**: el asistente contra la API real y la cancelación anticipada de
   plazos fijos.

Las decisiones y su fundamento están en [`docs/adr/`](adr/) y en
[`audit-final.md`](audit-final.md).
