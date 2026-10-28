# Presto — resumen ejecutivo

**Finanzas personales, inversiones y préstamos entre personas, en ARS y USD.**

> **Demo pública:** <https://presto-mvp-alpha.vercel.app>
> **API:** <https://presto-api-r8vc.onrender.com>
> **Usuarios demo:** `ana@presto.demo` · `beto@presto.demo` · `carla@presto.demo` — contraseña `Presto123!`
>
> Demo con **dinero simulado**. No es una oferta de inversión ni asesoramiento
> financiero. Fecha: 2026-10-28.

## La propuesta

Presto conecta a personas que necesitan financiarse con personas que tienen
saldo para prestar o invertir. Todo ocurre en una sola aplicación: billetera en
pesos y dólares, marketplace de ofertas, préstamos con cuotas, plazos fijos,
presupuestos, reportes y un asistente que explica el mercado y el marco legal.

El dinero no se calcula en el front: lo lleva un **libro mayor de doble entrada**
en el backend, con idempotencia, reversos y saldos que nunca quedan negativos en
las billeteras de los usuarios.

## Qué está implementado

| Área | Estado | Qué incluye |
|---|---|---|
| Identidad | Completo | Registro/login por email, JWT con rotación, refresh en cookie httpOnly, logout, reseteo de contraseña, verificación de email, perfil y KYC |
| Ledger | Completo | Cuentas ARS/USD, depósitos, retiros, transferencias, asientos, reversos, saldo desnormalizado y triggers en PostgreSQL |
| Pagos | Completo (simulado) | Intención de pago, webhooks firmados e interfaz con Mercado Pago; el saldo lo mueve el ledger |
| Marketplace | Completo | Publicación de ofertas, búsqueda con filtros y comparación de cuota, interés y costo total |
| Préstamos | Completo | Aceptación atómica con snapshot de condiciones, cronograma francés, pago de cuotas en orden y marcado de mora |
| Inversiones | Completo | Productos de plazo fijo (solo staff), apertura contra la cuenta `system`, interés simple y liquidación automática |
| Presupuestos | Completo | Categorías, límites mensuales por moneda, gasto derivado del ledger y alertas por umbral |
| Reportes | Completo | Gasto, préstamos, inversiones y movimientos, con exportación CSV |
| Notificaciones | Completo | Cuatro eventos por email, preferencias por usuario y reintentos con backoff |
| Presti | Completo | Mercado (dólar y cripto), noticias, marco legal curado y chat por reglas, sin LLM |
| Admin | Completo | Django admin con estilos, aprobación de KYC y superusuario creado por script |

La demo incluye un comando **`seed_demo`** idempotente que arma un escenario
completo: tres personas con KYC aprobado, saldos, una oferta aceptada, un
préstamo con una cuota pagada, un plazo fijo, un presupuesto con alerta y pagos
de prueba.

## Arquitectura

| Capa | Tecnología |
|---|---|
| Backend | Python 3.14 · Django 6.1 · Django REST Framework 3.18 · PostgreSQL 16 |
| Async | Celery 5.6 + Redis (cuatro tareas diarias) |
| API | OpenAPI generado y versionado; contrato validado en CI |
| Frontend | React 18 · Vite 5 · TypeScript · Tailwind, mobile-first |
| Infra | Docker multi-stage · Render (API + PostgreSQL + Redis) · Vercel (front) · GHCR · GitHub Actions |
| Calidad | 800 tests con PostgreSQL real · 32 contratos de límites entre apps · ruff · smoke test |

Es un **monolito modular**: 13 apps de dominio con capas estrictas
(`views` → `services`/`selectors` → `models`), sin ForeignKeys entre apps y con
acceso cruzado únicamente por servicios y selectores. `import-linter` verifica
esas reglas en cada push.

## Por qué es sólido

- **Dinero con invariantes, no solo fórmulas.** Doble entrada garantizada por un
  trigger diferido de PostgreSQL, inmutabilidad de asientos, saldo no negativo
  en billeteras, suma cero por moneda y bloqueos para concurrencia.
- **Idempotencia real.** Toda operación de dinero exige `Idempotency-Key`; la
  misma clave con otro payload devuelve `409`, y una carrera concurrente
  devuelve la operación original.
- **Sesión segura.** Access token en memoria, refresh en cookie httpOnly con
  rotación y blacklist; el reseteo de contraseña cierra todas las sesiones.
- **Calidad automatizada.** 800 tests, cobertura con umbrales, migraciones
  verificadas, esquema OpenAPI validado, auditoría de dependencias, `check
  --deploy`, imagen Docker construida y publicada en cada push a `main`.

## Qué se puede mostrar hoy

1. Login con una cuenta demo y navegación completa desde el celular.
2. Depósito simulado, transferencia y saldo en ARS/USD.
3. Oferta de préstamo, comparación y aceptación con cronograma de cuotas.
4. Pago de una cuota y actualización del estado del préstamo.
5. Apertura de un plazo fijo y liquidación al vencimiento.
6. Presupuesto con alerta y reportes con exportación CSV.
7. Presti: mercado real, noticias y marco legal.
8. Admin para aprobar KYC y revisar la operación.

## Límites actuales

- **Dinero simulado:** falta el contrato y las credenciales del proveedor de
  pagos para operar con fondos reales.
- **KYC manual:** hoy se aprueba desde el admin con metadata; falta subida de
  documentos o proveedor de identidad.
- **Legal:** términos, privacidad y encuadre CNV/BCRA/PLA-FT están pendientes de
  revisión profesional. La página `/legal` es un borrador de alcance.
- **Emails:** sin SMTP configurado salen por consola (logs).
- **Operación:** falta Sentry, backups automáticos probados y E2E del front en
  CI. El plan free de Render duerme la API (30–60 s de cold start).

## Próximos pasos

1. **Pagos reales:** Mercado Pago en sandbox y luego producción, con webhooks y
   conciliación.
2. **KYC con documentos:** subida y validación (propia o proveedor).
3. **Legal y regulatorio:** TyC, privacidad, PLA/FT y encuadre de custodia.
4. **Operación:** Sentry, backups con restauración probada, dominio propio.
5. **Producto:** Presti con RAG sobre las fichas legales, si se decide sumar LLM.

## Cómo probar la demo (3 minutos)

1. Entrá a la demo con `ana@presto.demo` / `Presto123!`.
2. Mirá el dashboard: saldo en ARS, préstamo activo y próxima cuota.
3. Pagá una cuota desde **Préstamos**.
4. Entrá con `carla@presto.demo` y abrí un plazo fijo en **Inversiones**.
5. Preguntale a Presti por el dólar, tu saldo o el marco legal.
6. Si querés ver el backoffice, entrá al admin con el superusuario.

## Enlaces

- Repositorio: <https://github.com/jrweiss93/PRESTO-MVP>
- Guía técnica completa: `docs/implementacion.md` (PDF y Word en `docs/`)
- Entrega y accesos: `docs/entrega.md`
- Deploy: `docs/deploy-mvp.md`
