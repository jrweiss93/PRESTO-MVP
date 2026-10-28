# Entrega de Presto (demo pública)

Este documento es el mapa para pasar el proyecto a otra persona: dónde está el
código, dónde corre, qué accesos hacen falta y qué límites tiene la demo.

> **Estado:** demo pública funcionando con **dinero simulado**. No es una
> instancia para operar con fondos reales.
> **Última actualización:** 2026-10-22 · rama `main` · commit `eaf7ec5`.

## 1. Dónde está cada cosa

| Pieza | Ubicación |
|---|---|
| Código fuente | <https://github.com/jrweiss93/PRESTO-MVP> (público, `main`) |
| Copia local | `C:\Users\Leonel\Desktop\PRESTO-MVP` (backend en la raíz + `frontend/`) |
| Front | <https://presto-mvp-alpha.vercel.app> |
| API | <https://presto-api-r8vc.onrender.com> |
| Swagger | <https://presto-api-r8vc.onrender.com/api/docs/> |
| Admin | <https://presto-api-r8vc.onrender.com/admin/> |
| Imagen Docker | `ghcr.io/jrweiss93/presto-mvp:latest` (pública) |

La API corre en **Render** (servicios `presto-api`, `presto-db`,
`presto-redis`, blueprint `presto-mvp`) y el front en **Vercel**. Las dos
cuentas pertenecen al dueño actual del proyecto.

**Los datos de la demo viven en el Postgres de Render, no en el repo.** Se
pueden recrear con `seed_demo`.

## 2. Usuarios de la demo

| Rol | Email | Contraseña |
|---|---|---|
| Prestataria | `ana@presto.demo` | `Presto123!` |
| Prestamista | `beto@presto.demo` | `Presto123!` |
| Inversora | `carla@presto.demo` | `Presto123!` |

Son credenciales **públicas a propósito**. No las reutilices en una instancia
real ni cargues datos personales en la demo.

El superusuario del admin **no tiene contraseña por defecto**: se crea con
`scripts/create-superuser-remote.ps1` y la elige quien lo ejecuta.

## 3. Qué contiene el repositorio

- **Backend Django** (`apps/`): `identity`, `ledger`, `payments`, `offers`,
  `matching`, `loans`, `investments`, `budgets`, `reports`, `notifications`,
  `assistant`, `demo` y `core`.
- **Frontend React + Vite** (`frontend/`): landing, auth, billetera, pagos,
  presupuestos, marketplace, préstamos, inversiones, perfil/KYC, Presti y legal.
- **Documentación** (`docs/`):
  - `mvp.md` — arranque local y guion de demo.
  - `deploy-mvp.md` — despliegue, variables, checklist y troubleshooting.
  - `implementacion.md` — detalle técnico del código (modelos, servicios, endpoints, front, infra).
  - `implementacion.pdf` / `implementacion.docx` — las mismas versiones para compartir.
  - `resumen-ejecutivo.md` / `.pdf` / `.docx` — resumen de 3 páginas para presentar.
  - `guia-para-mostrar.md` / `.pdf` / `.docx` — guion sin tecnicismos para explicar la demo.
  - `presentacion-presto.pptx` / `.pdf` — presentación de 13 slides con notas del orador.
  - `presentacion-corta.pptx` / `.pdf` — versión de 8 slides para una exposición de 5 minutos.
  - `documento-presto.md` / `.pdf` / `.docx` — documento de producto: problema, público, operaciones, beneficios y stack.
  - `architecture.md` y `adr/` — decisiones técnicas.
  - `audit-final.md`, `regulatorio-bcra.md`, `pitch-one-pager.md`.
- **Reglas y estado:** `AGENTS.md` (fuente de verdad) y `HANDOFF.md`.
- **Infraestructura:** `Dockerfile`, `docker-compose*.yml`, `render.yaml`,
  `frontend/vercel.json`, `.github/workflows/ci.yml`.
- **Scripts** (`scripts/`): setup de venv, servicios portables de Windows,
  seed local, seed remoto, superusuario, smoke test y flujo end-to-end.

## 4. Levantarlo en local

**La forma más simple (Windows):** doble clic en `PRESTO-DEMO.cmd` o en el
acceso directo **Presto Demo** del escritorio. El lanzador levanta PostgreSQL,
Redis, la API y el front, siembra la demo y abre el navegador. Para detenerlo:
`PRESTO-DEMO-STOP.cmd`.

**Con Docker** (requiere Docker + WSL2 y virtualización):

```sh
docker compose up -d --build
docker compose run --rm web python manage.py seed_demo
cd frontend && pnpm install && pnpm dev
```

**En Windows sin Docker** (PostgreSQL y Redis portables):

```powershell
.\scripts\install-services.ps1   # una vez
.\scripts\setup-venv.ps1         # una vez
.\scripts\start-services.ps1
. .\scripts\env.ps1
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

cd frontend
pnpm install
pnpm dev
```

Detalle completo: [`mvp.md`](mvp.md).

## 5. Desplegar una copia propia

Guía completa: [`deploy-mvp.md`](deploy-mvp.md). Resumen:

1. **Backend en Render**: **New → Blueprint → este repo**. El `render.yaml`
   crea base, Redis y web. La imagen se publica desde GitHub Actions en
   `ghcr.io/jrweiss93/presto-mvp:latest`; el paquete es público.
2. **Front en Vercel**: importar el repo con **Root Directory `frontend`**,
   `VITE_API_URL=https://<api>/api/v1` y `VITE_ENABLE_ASSISTANT=true`.
3. En Render, completar `CORS_ALLOWED_ORIGINS` y `FRONTEND_URL` con el dominio
   del front.
4. Sembrar la base y crear el admin (ver abajo).
5. Verificar con el smoke test.

Si se hace **fork**, el workflow publica la imagen en la cuenta del fork; hay
que actualizar la URL `image.url` de `render.yaml` y los dominios de CORS.

## 6. Accesos y secretos

- **GitHub:** el repo es público (clonar no requiere permiso). Para pushear,
  agregar a la persona en **Settings → Collaborators**.
- **Render:** invitar al **Team/Workspace** para operar el deploy actual, o
  desplegar una copia propia desde el blueprint.
- **Vercel:** invitar al **Team** del proyecto, o importar el repo en una cuenta
  propia.
- **Secretos:** viven en **Render → Environment** y **Vercel → Environment
  Variables**. No están en el repo. **No compartas** la *External Database URL*,
  tokens ni contraseñas por chat; usá las invitaciones de cada plataforma.
- Si la instancia cambia de dueño, conviene **rotar** `DJANGO_SECRET_KEY` y la
  contraseña del admin.

## 7. Verificación

```powershell
.\scripts\smoke-demo.ps1 `
  -ApiUrl https://presto-api-r8vc.onrender.com `
  -FrontUrl https://presto-mvp-alpha.vercel.app
```

Debe dar **11/11**: health, modo demo, CORS con credenciales, login, cookie
httpOnly, refresh, Presti (mercado y chat) y las rutas del front.

Chequeos rápidos:

- `GET /health/` → `{"status":"ok"}`
- `GET /api/v1/meta/` → `{"mode":"demo","simulated_money":true,...}`
- `GET /static/admin/css/base.css` → 200 `text/css`

La CI de GitHub corre calidad, migraciones, tests, frontend e imagen Docker
(5 jobs).

## 8. Límites conocidos

- **Dinero simulado**: no hay pasarela de pagos conectada.
- **KYC manual**: metadata JSON aprobada desde el admin; no hay subida de
  documentos ni proveedor de identidad.
- **Emails por consola**: sin SMTP configurado, los correos de auth y avisos
  salen en los logs de Render.
- **Legal**: la página `/legal` es un borrador de alcance, no TyC definitivos.
  Faltan PLA/FT, encuadre de custodia y CNV (`docs/regulatorio-bcra.md`).
- **Plan free de Render**: el servicio duerme; la primera visita puede tardar
  30–60 segundos. Para una demo en vivo, despertarlo antes.
- **Superusuario**: se crea con el script; no hay uno por defecto.
- **Presti sin LLM**: responde por reglas; mercado y noticias dependen de
  fuentes externas y pueden venir vacíos.
- **Sin Sentry ni backups automáticos probados** en esta instancia.
- Los tests E2E del front no corren en CI.

## 9. Checklist de entrega

- [ ] Agregar a la persona como collaborator en GitHub (si va a pushear).
- [ ] Invitarla a Render y Vercel (o desplegar una copia propia).
- [ ] Compartir el link del front y las credenciales demo.
- [ ] Confirmar que el seed y el superusuario estén creados.
- [ ] Correr el smoke test y que dé 11/11.
- [ ] Leer `docs/mvp.md` (local) y `docs/deploy-mvp.md` (deploy).
- [ ] No compartir secretos ni la URL externa de la base.

## 10. Para seguir el desarrollo

- Reglas del proyecto: [`AGENTS.md`](../AGENTS.md).
- Estado técnico y pendientes: [`HANDOFF.md`](../HANDOFF.md).
- Arquitectura y ADRs: [`architecture.md`](architecture.md) y [`adr/`](adr/).
- Próximos pasos de producto: pagos reales, KYC con documentos, legales,
  Sentry y E2E en CI.
