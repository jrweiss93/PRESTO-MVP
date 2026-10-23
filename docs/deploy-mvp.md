# Desplegar la demo pública (Vercel + backend administrado)

Esta guía deja Presto publicado como **demo con dinero simulado**: usuarios de
ejemplo, todas las funciones disponibles y un aviso visible de que no se mueve
dinero real. **No es un despliegue para operar con fondos reales.**

La guía larga de Northflank está en [`deploy-northflank.md`](deploy-northflank.md)
y la de VPS + Caddy en [`deploy-demo.md`](deploy-demo.md). Acá está el camino
corto.

## 1. Antes de empezar

- El repositorio en GitHub (el backend y `frontend/` en el mismo repo).
- Una cuenta en Vercel y otra en un host con Docker (Northflank o Render).
- Un PostgreSQL y un Redis administrados (los dos hosts los ofrecen).
- Un dominio o subdominio para la API (el front puede quedar en `*.vercel.app`).

## 2. Backend

### Opción rápida: Render con el blueprint

El repo trae `render.yaml`. En Render: **New → Blueprint → elegir el repo**. Crea
la base PostgreSQL, el Redis y el servicio web desde el `Dockerfile`, con
`RUN_MIGRATIONS=1` (el entrypoint aplica las migraciones al arrancar).

Al crear el blueprint, dejá **vacías** `CORS_ALLOWED_ORIGINS` y `FRONTEND_URL`:
se completan cuando exista la URL de Vercel (paso 3). Después, en la **Shell**
del servicio:

```sh
python manage.py seed_demo
python manage.py createsuperuser
```

> El plan `free` de Render **no incluye Shell**. Si no querés pasar a `starter`,
> sembrá la base desde tu máquina con la *External Database URL*:
>
> ```powershell
> .\scripts\seed-remote.ps1
> ```
>
> El script pide la URL (Render → `presto-db` → **Connect** → **External
> Database URL**) y corre `seed_demo` contra esa base. El `initialDeployHook`
> del blueprint también siembra en la primera creación de un servicio nuevo.
>
> Para el **admin**, con la misma URL:
>
> ```powershell
> .\scripts\create-superuser-remote.ps1
> ```
>
> Pide email y contraseña (mínimo 12 caracteres) y crea o actualiza el
> superusuario. Queda disponible en `/admin/` de la API.

> El plan `free` duerme el servicio por inactividad: la primera visita puede
> tardar unos segundos. Para una demo en vivo, considerá `starter`.

#### La imagen se publica desde GitHub (GHCR)

El blueprint ya **no construye** la imagen en Render: usa la que publica GitHub
Actions en cada push a `main`:

```
ghcr.io/jrweiss93/presto-mvp:latest
```

1. En GitHub, entrá a **Packages → presto-mvp → Package settings → Change
   visibility → Public** (la primera vez). Sin eso, Render no puede bajarla.
2. En Render, **Manual Deploy → Deploy latest image** para tomar la última.
   Los servicios con imagen preconstruida no se redeployan solos cuando cambia
   el tag.

> Si preferís mantener el paquete privado, agregá un *registry credential* de
> GHCR en Render y sumá `image.creds.fromRegistryCreds` al blueprint.

### Opción manual (Northflank, Railway, VPS, etc.)

Crear un servicio desde el `Dockerfile` del repo, con el puerto **8000** y estas
variables (los valores entre `<>` se reemplazan):

| Variable | Valor |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `DJANGO_SECRET_KEY` | secreto de 50+ caracteres (`python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `<api.mi-dominio.com>` |
| `DATABASE_URL` | la del PostgreSQL administrado (si exige SSL, agregá `?sslmode=require` al final de la URL) |
| `REDIS_URL` | la del Redis administrado |
| `DEMO_MODE` | `true` |
| `LEDGER_SIMULATED_DEPOSITS_ENABLED` | `true` |
| `CORS_ALLOWED_ORIGINS` | `https://<mi-front>.vercel.app` |
| `FRONTEND_URL` | `https://<mi-front>.vercel.app` |
| `JWT_REFRESH_COOKIE_SAMESITE` | `None` |
| `JWT_REFRESH_COOKIE_SECURE` | `true` |
| `RUN_MIGRATIONS` | `1` |
| `ASSISTANT_MARKET_ENABLED` | `true` |
| `ASSISTANT_NEWS_FEED_URL` | `https://www.ambito.com/rss/pages/economia.xml` (o vacío) |

Sin `EMAIL_HOST` los correos de auth salen por consola (logs del servicio). Para
la demo alcanza; si querés que lleguen de verdad, configurá el SMTP.

### Primer arranque

```sh
# En la consola del servicio (o un job one-off)
python manage.py seed_demo
python manage.py createsuperuser
```

`seed_demo` es idempotente: se puede volver a correr sin duplicar datos.

> Los estáticos del admin los sirve **WhiteNoise**; la imagen corre
> `collectstatic` en el build. No hace falta un servidor de estáticos aparte.

### Verificar

```sh
curl -s https://<api.mi-dominio.com>/health/
# {"status": "ok"}
curl -s https://<api.mi-dominio.com>/api/v1/meta/
# {"mode":"demo","simulated_money":true,...}
```

## 3. Front en Vercel

- Importar el repo y elegir **`frontend`** como *Root Directory*.
- Framework: **Vite** (lo detecta; también está en `vercel.json`).
- Build: `pnpm build` · Output: `dist`.
- Variable de entorno (Production y Preview):

| Variable | Valor |
|---|---|
| `VITE_API_URL` | `https://<api.mi-dominio.com>/api/v1` |
| `VITE_ENABLE_ASSISTANT` | `true` |

`vercel.json` ya deja los *rewrites* para que `/dashboard`, `/asistente` y
`/legal` funcionen al refrescar (sin eso, Vercel devuelve 404).

## 4. Smoke test

Desde el repo, con la demo ya publicada:

```powershell
.\scripts\smoke-demo.ps1 -ApiUrl https://api.mi-dominio.com -FrontUrl https://mi-front.vercel.app
```

Verifica salud, modo demo, CORS con credenciales, login, cookie httpOnly,
refresh, Presti (mercado y chat) y las rutas profundas del front.

## 5. Checklist para mostrar

- [ ] `/health/` responde 200 por HTTPS.
- [ ] `/api/v1/meta/` dice `mode: demo` y `simulated_money: true`.
- [ ] El banner azul “Estás en la demo” aparece al entrar.
- [ ] Landing pública en `/` con las cuentas demo y el aviso de dinero simulado.
- [ ] `/legal` abre y explica el alcance.
- [ ] Login con `ana@presto.demo` / `Presto123!`.
- [ ] Refrescar el panel mantiene la sesión (cookie).
- [ ] Depósito simulado y transferencia funcionan.
- [ ] Préstamo y pago de cuota funcionan.
- [ ] Inversión y reportes funcionan.
- [ ] Presti muestra mercado y responde “¿cuál es mi saldo?”.
- [ ] El admin (`/admin/`) abre con estilos.
- [ ] No hay errores 500 en los logs.
- [ ] Nadie usa datos personales reales.

## 6. Problemas típicos

| Síntoma | Causa | Solución |
|---|---|---|
| El login funciona pero al refrescar se pierde la sesión | Cookie `SameSite`/`Secure` o CORS sin credenciales | `JWT_REFRESH_COOKIE_SAMESITE=None`, `JWT_REFRESH_COOKIE_SECURE=true`, `CORS_ALLOWED_ORIGINS` exacto (sin `/` final) |
| `403 CSRF` en el admin | `CSRF_TRUSTED_ORIGINS` sin el dominio | agregarlo con `https://` |
| 404 al refrescar `/dashboard` | falta el rewrite de SPA | `vercel.json` en `frontend/` |
| `DisallowedHost` | `DJANGO_ALLOWED_HOSTS` sin el dominio | agregar el host de la API |
| 502/503 al arrancar | migraciones o DB/Redis mal configurados | revisar logs, `RUN_MIGRATIONS=1`, `DATABASE_URL` y `REDIS_URL` |
| Correos que no llegan | backend de consola | configurar `EMAIL_HOST`/SMTP |
| Presti sin mercado/noticias | fuente externa caída o bloqueada | es degradable: la pantalla sigue; revisar logs |

## 7. Límites de esta demo

- Dinero simulado, KYC manual y sin contrato de pagos: **no usar con usuarios
  reales ni con datos personales**.
- Las credenciales de demo son públicas a propósito; no las reutilices en una
  instancia real.
- Antes de abrir al público con dinero real: pagos, KYC con documentos, TyC,
  privacidad, PLA/FT y encuadre regulatorio (ver `docs/regulatorio-bcra.md`).
