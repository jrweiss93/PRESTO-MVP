# Mapa técnico del repositorio de Presto

**Qué hay en cada carpeta, qué hace cada archivo y por qué se decidió así**

> **Proyecto:** Presto — demo de finanzas e inversiones con dinero simulado.
> **Repositorio:** `jrweiss93/PRESTO-MVP`, rama `main`.
> **Backend:** Python 3.14 + Django 6 + Django REST Framework.
> **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS.
> **Base de datos:** PostgreSQL 16. **Cola:** Redis + Celery.
> **Fecha:** noviembre de 2026.

Este documento recorre el repositorio carpeta por carpeta y archivo por
archivo. No intenta reemplazar al código: sirve como mapa para entender dónde
está cada cosa, qué responsabilidad tiene y qué decisión de diseño hay detrás.
Cuando un archivo es generado o una migración histórica, se explica igual para
que no queden “cajas negras”.

## Cómo leer este documento

El repositorio separa cuatro tipos de contenido:

1. **Código fuente de producción:** archivos dentro de `apps/`, `config/`,
   `frontend/src/`, `deploy/` y `scripts/`. Es lo que se mantiene y se revisa.
2. **Pruebas:** `apps/*/tests/`, `tests/` y `frontend/src/**/*.test.*`,
   `frontend/e2e/`.
3. **Generado automáticamente:** migraciones, `frontend/src/shared/api/schema.d.ts`,
   `config/staticfiles/`, `dist/` y `tsconfig.tsbuildinfo`. No se editan a mano
   salvo que se regenere la fuente.
4. **Documentación y material de presentación:** `docs/`, `README.md`,
   `AGENTS.md`, `HANDOFF.md`.

La regla mental es: **las apps de Django no se importan entre sí por modelos**.
Cada app expone `services.py` para escribir y `selectors.py` para leer; el resto
es infraestructura. Esa regla explica casi todas las decisiones de carpetas que
vienen después.

---

## 1. Vista general del árbol

```
PRESTO-MVP/
├── apps/                 13 apps (core + 12 de dominio)
│   ├── core/             utilidades transversales
│   ├── identity/         usuarios, auth, KYC, respaldo
│   ├── ledger/           libro mayor de doble entrada
│   ├── payments/         intención de pago y proveedores
│   ├── offers/           ofertas de préstamo
│   ├── matching/         búsqueda y comparación
│   ├── loans/            préstamos, cuotas y chat
│   ├── investments/      plazos fijos
│   ├── budgets/          presupuestos y gastos
│   ├── reports/          reportes y CSV
│   ├── notifications/    avisos y preferencias
│   ├── assistant/        Presti sin LLM
│   └── demo/             seed y datos de demostración
├── config/               settings, URLs, Celery, WSGI/ASGI, admin
├── deploy/               entrypoint, Caddy y backup
├── frontend/             SPA React + Vite + TypeScript
├── scripts/              setup, demo local, smoke tests y presentaciones
├── tests/                prueba end-to-end global
├── docs/                 arquitectura, ADRs, guías y material
└── .github/workflows/    CI
```

En la raíz también viven `manage.py`, `pyproject.toml`, `Dockerfile`,
`render.yaml`, `docker-compose.yml`, `docker-compose.prod.yml`, `Makefile`,
`pytest.ini`, `AGENTS.md`, `README.md` y `HANDOFF.md`.

---

## 2. Archivos de la raíz

| Archivo | Qué hace | Decisión / por qué |
|---|---|---|
| `manage.py` | Punto de entrada de Django. Fija `config.settings.local` por defecto. | Permite `runserver`, migraciones, seeds y comandos sin configurar el módulo de settings a mano. |
| `pyproject.toml` | Metadatos, dependencias y configuración de ruff. | Un solo lugar para dependencias y estilo. Python ≥ 3.12; el Docker usa 3.14. |
| `pytest.ini` | Fija `config.settings.test` como settings de pytest. | Los tests nunca usan SQLite ni settings de producción: se prueban contra PostgreSQL real. |
| `Makefile` | Atajos para Docker: `up`, `test`, `lint`, `migrate`, `seed`, `front`, `worker`, `beat`. | Estandariza comandos para quien no recuerda la invocación larga de Compose. |
| `README.md` | Presentación, apps, endpoints, arranque, variables y reglas. | Es la puerta de entrada; un test (`apps/core/tests/test_readme.py`) falla si falta documentar un endpoint o una app. |
| `AGENTS.md` | Fuente de verdad de reglas de negocio, capas, seguridad y límites. | Separa “qué está permitido” de “cómo se implementa”. El código y los ADR remiten a este documento. |
| `HANDOFF.md` | Estado técnico, historia de commits y pendientes. | Facilita que otra persona continúe el proyecto sin reconstruir el contexto. |
| `COMO-USAR-LA-DEMO.txt` | Guía corta para abrir la demo local en Windows. | Pensada para alguien no técnico que solo necesita hacer doble clic. |
| `PRESTO-DEMO.cmd` / `PRESTO-DEMO-STOP.cmd` | Lanzan o detienen PostgreSQL, Redis, API y front. | La demo no depende de Docker ni de recordar comandos. |
| `Dockerfile` | Imagen multi-stage: base, runtime, development y production. | Runtime sin herramientas de test; código copiado después de las dependencias para cachear mejor. Corre como usuario `presto`, no root. |
| `docker-compose.yml` | Entorno local con db, redis, web, worker y beat. | Reproduce el stack completo y permite probar Celery. |
| `docker-compose.prod.yml` | Producción con imágenes fijadas a digest, Gunicorn, worker, beat, perfiles `proxy` y `backup`. | Reproducibilidad y separación de secretos por variables de entorno. |
| `render.yaml` | Blueprint de Render: PostgreSQL, Redis y web con imagen de GHCR. | El backend no construye en Render: usa la imagen que publica CI. Documenta el límite de worker/beat en free. |
| `.env.example` | Plantilla de variables para desarrollo. | Evita commitear secretos y deja documentado cada bloque. |
| `.env.prod.example` | Plantilla de producción con valores vacíos y advertencias. | Misma idea, pero con `SameSite=None`, SMTP y proveedor de pagos. |
| `.gitignore` / `.gitattributes` | Excluyen secretos, entornos y artefactos; fijan LF. | Evita subir `.venv`, `dist`, `.env` o binarios generados. |
| `.dockerignore` | Excluye front, tests, docs y entornos del contexto de build. | La imagen del backend no carga archivos innecesarios. |
| `.importlinter` | 32 contratos de límites entre apps y apps transversales. | La arquitectura no queda en un dibujo: CI falla si una app importa lo que no debe. |
| `.pre-commit-config.yaml` | Hooks de ruff e import-linter. | Detecta problemas antes del commit. |
| `.node-version` / `.nvmrc` | Fijan Node 24. | Coincide con `frontend/package.json` y CI. |

### Decisión de fondo

La raíz contiene **solo el proyecto Django y la orquestación**. El frontend vive
en `frontend/` y se despliega por separado. Se evitó mezclar el `package.json`
del front con la raíz para que la imagen Docker del backend no incluya
`node_modules` ni el build de React.

---

## 3. `apps/`: organización común

Cada app sigue el mismo esqueleto:

```
apps/<app>/
├── admin.py          registro en el admin de Django
├── apps.py           configuración de la app
├── exceptions.py     errores de dominio
├── models.py         entidades y constraints
├── permissions.py    permisos DRF (si aplica)
├── selectors.py      lecturas y agregados
├── serializers.py    validación de entrada y formato de salida
├── services.py       escritura, reglas y transacciones
├── signals.py        señales de dominio (si aplica)
├── tasks.py          adaptadores Celery (si aplica)
├── urls.py           rutas bajo /api/v1/
├── views.py          vistas finas
├── migrations/       historial de base de datos
└── tests/            tests de modelos, servicios, API, concurrencia, etc.
```

### Decisiones comunes

1. **Vista fina, servicio grueso.** La vista autentica, valida y delega. La
   regla de negocio y el `transaction.atomic()` viven en `services.py`.
2. **Lectura separada de escritura.** `selectors.py` no modifica estado; los
   selectores aíslan por usuario y evitan N+1 con `select_related` /
   `prefetch_related`.
3. **Serializers sin lógica financiera.** Validan campos y formatean; no mueven
   dinero ni consultan varias apps.
4. **Referencias cruzadas con UUID.** No hay `ForeignKey` entre apps de dominio;
   así se pueden extraer a futuro y no se acoplan modelos.
5. **`BaseModel`.** Todas las entidades heredan UUID, `created_at` y
   `updated_at`.
6. **`TextChoices`.** Los estados son enums tipados, no strings sueltos.
7. **Constraints en `Meta`.** La base también protege montos positivos, monedas,
   unicidad e idempotencia.
8. **Señales con IDs.** Las apps emisoras publican señales con identificadores;
   `notifications` conecta receptores y crea avisos sin acoplarse a la app
   emisora.
9. **Tasks delgadas.** Las tareas Celery llaman al mismo service que usa la API;
   no duplican reglas.

---

## 4. `apps/core` — utilidades transversales

No tiene endpoints de negocio; es la base de todo.

| Archivo | Qué hace / decisión |
|---|---|
| `models.py` | `BaseModel` abstracto con UUID, `created_at`, `updated_at`. Evita repetir campos y permite exponer IDs sin filtrar secuencias. |
| `money.py` | `round_two`, `money`, `monthly_rate_from_annual_tna`, `french_installment`, `simple_interest`, `french_total_interest`, `french_total_cost`, `effective_annual_rate`. Único lugar donde se redondea; todo con `Decimal`. |
| `exceptions.py` | `DomainError`, `InsufficientFunds`, `InvalidAmount`, `KYCNotCompleted`. Las apps convierten errores de dominio a respuestas HTTP en las vistas. |
| `exception_handler.py` | `api_exception_handler`: todos los errores salen como `{"error": {"code", "message", "details"}}`. El front puede mostrar mensajes homogéneos. |
| `pagination.py` | `StandardPagination` (100 por página, máximo 1000). Evita respuestas gigantes y permite `page_size` controlado. |
| `middleware.py` | `HealthCheckMiddleware` responde `/health/` antes de validar `Host` y TLS; `DemoModeHeaderMiddleware` agrega `X-Presto-Mode: demo`. Es clave en Render. |
| `checks.py` | `check_legal_review_acknowledged`: aviso `legal.W001` si no se reconoció la revisión legal. No bloquea la demo, pero sí un despliegue serio. |
| `compliance.py` | Fuente única de los pendientes legales/PLA-FT; alimenta `/api/v1/meta/` y el banner del front. |
| `serializers.py` | Serializers de `Meta` y compliance. |
| `views.py` | `health_check` (200/503 según base) y `MetaView` (modo demo, dinero simulado y compliance). |
| `tests/` | Tests de dinero, health, meta, OpenAPI, CORS, settings de seguridad, checks, README y documentación. |

**Decisión:** todo lo transversal vive en `core`, que no importa ninguna app de
dominio. Así no se crea un ciclo y cualquier app puede usarlo sin acoplarse a
otra.

---

## 5. `apps/identity` — usuarios, sesión, KYC y respaldo

### Modelos (`models.py`)

| Clase | Rol y decisión |
|---|---|
| `UserManager` | Crea usuarios usando email como identificador; no existe `username`. |
| `User` | Hereda `AbstractUser`; email único, `email_verified_at`, `terms_accepted_at`. Propiedad `email_verified`. |
| `Profile` | Datos personales: teléfono, fecha de nacimiento, país ISO-3166. |
| `PrestoProfile` | Perfil operativo `borrower/lender/investor` con `is_active`; el registro crea uno y los permisos leen el activo. |
| `KYCVerification` | Historial de KYC; una sola solicitud `pending` por usuario. |
| `BiometricCheck` | Validación biométrica simulada; guarda puntajes y hash, nunca imagen. |
| `BackupAccount` | Cuenta externa declarada como respaldo: proveedor, referencia enmascarada, moneda, saldo declarado y estado. No guarda credenciales. |

### Archivos

| Archivo | Qué hace / decisión |
|---|---|
| `services.py` | `register_user`, `set_profile`, `submit_kyc`, `resolve_kyc`, `run_biometric_check`, `update_profile`, `request_password_reset`, `confirm_password_reset`, `send_email_verification`, `confirm_email_verification`, `create_backup_account`, `verify_backup_account`, `delete_backup_account`, `require_repayment_source`, `close_account`, `change_password`, cookies y blacklist. Todo lo que escribe pasa por acá. |
| `selectors.py` | `get_profile`, `get_kyc_for_user`, `is_kyc_approved`, `get_active_profile`, `list_backup_accounts_for_user`, `has_verified_backup_account`, `has_active_loan_as_borrower`, `get_active_financial_operations`, `get_user_email`. Aíslan por usuario. |
| `serializers.py` | Registro, login, perfil, KYC, biometría, backup, cierre de cuenta, tokens y mensajes. Validan formato; no deciden reglas de dinero. |
| `views.py` | `RegisterView`, `LoginView`, `TokenRefreshView`, `LogoutView`, `MeView`, `KycView`, `KycBiometricView`, reset/verify/password change, backup accounts y `CloseAccountView`. |
| `permissions.py` | Throttles de login/registro/reset/verificación; `IsKycApproved`, `KycApprovedForUnsafeMethods`, `HasVerifiedBackupAccount`, `IsActiveProfile`, `ActiveProfileForUnsafeMethods`. |
| `tokens.py` | `encode_uid`, `decode_uid` y generador de token de email que no incluye `last_login`. |
| `emails.py` | Construye enlaces a `FRONTEND_URL` y envía emails de reset y verificación. |
| `signals.py` | Señal de KYC aprobado; `demo` la escucha para el bono de bienvenida. |
| `admin.py` | Admin de usuarios, perfiles, KYC, biometría y backup. |
| `urls.py` | Rutas `/auth/...`, `/kyc/...` y `/backup-accounts/...`. |

### Decisiones

- **Login por email** en lugar de usuario: menos fricción y menos datos.
- **Access token en memoria + refresh en cookie httpOnly**, con rotación y
  blacklist. Reduce el impacto de un XSS.
- **KYC como gate** para operaciones que mueven dinero; email verificado es
  informativo.
- **Perfil fijo en la demo**: el registro crea un perfil y `set_profile` existe
  para normalizar cuentas de demo; la API no permite cambiarlo.
- **Cuenta de respaldo**: salvaguarda de la fase 1; guarda solo datos
  enmascarados y exige saldo declarado suficiente para la primera cuota.
- **Cierre lógico** (`is_active=False`), bloqueado con préstamos o inversiones
  activas; el ledger es inmutable y se conserva para auditoría.

### Tests

`test_api`, `test_services`, `test_models`, `test_permissions`, `test_profiles`,
`test_selectors`, `test_backup_accounts`, `test_biometric`,
`test_email_verification`, `test_password_reset`, `test_admin`. Cubren login,
tokens, KYC, perfiles, respaldo, biometría simulada y cierre.

### Migraciones

`0001` inicial, `0002` manager/email, `0003` Profile, `0004` KYC, `0005`
email verificado, `0006` PrestoProfile, `0007` BiometricCheck, `0008` términos
aceptados, `0009` BackupAccount.

---

## 6. `apps/ledger` — el corazón del dinero

### Modelos

| Clase | Rol y decisión |
|---|---|
| `Account` | Billetera de usuario, custodia o sistema; saldo materializado. Constraints: una cuenta por usuario/moneda, moneda ARS/USD y saldo no negativo solo en `user_wallet`. |
| `LedgerTransaction` | Movimiento: tipo, idempotencia, hash del payload, usuario, descripción y reverso. |
| `LedgerEntry` | Asiento débito/crédito con cuenta, importe y moneda. |

### Archivos

| Archivo | Qué hace / decisión |
|---|---|
| `services.py` | `deposit`, `withdraw`, `transfer`, `transfer_between_users`, `transfer_to_counterpart`, `transfer_from_counterpart`, `reverse_transaction`, `_post_transaction`, `_lock_accounts`, `_apply_legs`, `_resolve_idempotent`, `_recover_from_idempotency_race`, validaciones de monto/saldo/KYC/demo. Todo movimiento pasa por acá. |
| `selectors.py` | Cuentas, saldos, transacciones, período, desglose y detalle de movimientos. |
| `serializers.py` | Cuenta, transacción, creación y saldo. |
| `views.py` | Listado/creación de cuentas y transacciones, saldo y detalle; paginación por cursor en movimientos. |
| `checks.py` | `ledger.E001`: bloquea depósitos simulados en producción si `DEMO_MODE` no está activo. |
| `admin.py` | Solo consulta y reverso desde admin; los asientos no se editan ni borran. |
| `urls.py` | `/ledger/accounts/`, `/transactions/`, detalle y saldo. |

### Decisiones

- **Doble entrada**: cada transacción tiene débitos y créditos que suman igual.
- **Inmutabilidad**: triggers de PostgreSQL bloquean `UPDATE` y `DELETE`; un
  error se corrige con un reverso.
- **Saldo materializado** en `Account.balance` para consultas rápidas, siempre
  actualizado dentro de una transacción y con bloqueo `select_for_update`.
- **Bloqueo ordenado por ID** para evitar deadlocks.
- **Idempotencia** por usuario + clave + hash; misma clave con otro payload da
  `409`.
- **KYC obligatorio** para mover dinero.

### Tests

`test_services`, `test_api`, `test_api_transactions`, `test_models`,
`test_triggers`, `test_concurrency`, `test_selectors`,
`test_period_selectors`, `test_movement_details`, `test_checks`, `test_admin`.
Verifican doble entrada, inmutabilidad, saldo, concurrencia e idempotencia.

### Migraciones

`0001` tablas, `0002` triggers de doble entrada e inmutabilidad, `0003`
constraints de moneda y saldo.

---

## 7. `apps/payments` — intención de pago y proveedores

| Archivo | Qué hace / decisión |
|---|---|
| `models.py` | `Payment` (dirección, monto, proveedor, estado, idempotencia, ledger) y `WebhookEvent` (evento externo único). El saldo no vive acá. |
| `providers.py` | `PaymentProvider` (ABC), `ProviderResult`, `WebhookEventInfo`, `SimulatedProvider`, `MercadoPagoProvider`, `get_provider`. Patrón estrategia / puerto-adaptador. |
| `services.py` | `create_payment`, `confirm_payment`, `fail_payment`, `handle_webhook`, `_call_provider`, `_move_money`, resolución de idempotencia y parseo de webhooks. El saldo lo mueve el ledger. |
| `selectors.py` | Pagos del usuario y eventos de webhook. |
| `serializers.py` | Pago, creación y webhook. |
| `views.py` | Listado/creación, detalle y webhook público con throttle. |
| `permissions.py` | `WebhookThrottle` (60/min). |
| `urls.py` | `/payments/`, `/{id}/`, `/webhooks/{provider}/`. |
| `admin.py` | Consulta de pagos y eventos. |

**Decisión:** el pago es una **intención** y una bitácora; el dinero se mueve
solo con el ledger. El proveedor real se cambia por settings sin tocar servicios
ni tests. El webhook valida firma antes de parsear.

**Tests:** `test_api`, `test_services`, `test_models`; cubren proveedor
simulado, idempotencia, webhook y estados.

**Migración:** `0001` inicial.

---

## 8. `apps/offers` — ofertas del prestamista

| Archivo | Qué hace / decisión |
|---|---|
| `models.py` | `Offer`: prestamista, monto, moneda, TNA, plazo, requisitos y estado `active/expired/accepted`. |
| `services.py` | `create_offer`, `update_offer`, `expire_offer`, `accept_offer`; valida KYC y que nadie acepte su propia oferta. Publicar no reserva fondos. |
| `selectors.py` | `get_offer`, `list_offers_for_lender`, `get_active_offer`, `get_offer_locked`, `get_own_offer_locked`, `search_active_offers`. |
| `serializers.py` | Oferta, creación y actualización. |
| `views.py` | Listado/creación y detalle/edición. |
| `permissions.py` | `HasApprovedKyc`. |
| `urls.py` | `/offers/` y `/offers/{id}/`. |
| `admin.py` | Solo consulta. |

**Decisión:** la oferta es intención, no reserva. El bloqueo y cambio de estado
se hacen al aceptar, dentro de la transacción de `loans`.

**Tests:** `test_api`, `test_services`, `test_models`, `test_selectors`,
`test_permissions`, `test_concurrency`.

**Migración:** `0001`.

---

## 9. `apps/matching` — búsqueda y comparación

No tiene modelos ni escrituras.

| Archivo | Qué hace / decisión |
|---|---|
| `selectors.py` | `search_offers` (moneda, rango, tasa, plazo, orden) y `compare_offers` (cuota, interés total, costo total, TEA). Usa `offers.selectors`, nunca modelos. |
| `serializers.py` | Query de búsqueda, oferta match, comparación y payload. |
| `views.py` | `MatchingOfferListView`, `OfferComparisonView`. |
| `urls.py` | `/matching/offers/`, `/matching/comparisons/`. |

**Decisión:** app de solo lectura. La lógica de cálculo reutiliza
`core.money`; no duplica fórmulas. Comparar no crea préstamos.

**Tests:** `test_selectors`, `test_api`.

---

## 10. `apps/loans` — préstamos, cuotas y chat

### Modelos

| Clase | Rol y decisión |
|---|---|
| `Loan` | Préstamo aceptado; nace `active`, estados `active/paid/defaulted/cancelled`; guarda idempotencia, desembolso y marcas de cancelación/archivado por parte. |
| `OfferTermsSnapshot` | Copia JSON inmutable de las condiciones aceptadas. |
| `Installment` | Cuota con capital, interés, vencimiento y estado (`pending/paid/overdue/cancelled`). |
| `LoanMessage` | Mensaje privado entre las partes del préstamo; el chat es del préstamo, no global. |
| `LoanReview` | Recomendación (`recommended`) y comentario de una parte sobre la otra; una por préstamo y revisor. |

### Archivos

| Archivo | Qué hace / decisión |
|---|---|
| `services.py` | `build_installment_schedule`, `accept_offer`, `pay_installment`, `change_loan_status`, `mark_overdue`, `send_loan_message`, `create_loan_review`, `cancel_loan`, `archive_loan`. `accept_offer` es atómico; `cancel_loan` revierte el desembolso solo si no hay cuotas pagadas/vencidas; `archive_loan` oculta el préstamo para una parte. |
| `selectors.py` | `get_loan_for_party`, `list_loans_for_user` (excluye los archivados por el usuario), mensajes, reseñas/reputación, cuotas y desglose de movimientos. |
| `serializers.py` | Snapshot, cuota, préstamo, detalle, mensajes, reseñas, reputación y aceptación. |
| `views.py` | `LoanListCreateView`, `LoanDetailView`, `LoanCancelView`, `LoanArchiveView`, `LoanMessageListCreateView`, `LoanReviewView`, `UserReputationView`, `InstallmentPayView`. Terceros reciben 404. |
| `signals.py` | `loan_created`, `installment_paid`; `notifications` los escucha. |
| `tasks.py` | `mark_overdue_loans`, `notify_installments_due_soon`, `notify_overdue_installments`; delegan en services. |
| `management/commands/mark_overdue_loans.py` | Ejecuta el mismo service desde consola. |
| `urls.py` | `/loans/`, `/{id}/`, `/{id}/cancel/`, `/{id}/archive/`, `/{id}/messages/`, `/{id}/review/`, `/reviews/users/{id}/`, `/{id}/installments/{n}/pay/`. |
| `admin.py` | Consulta de préstamos, snapshot y cuotas; botón para marcar vencidas. |

**Decisiones:**

- **Snapshot inmutable** para que editar o borrar la oferta no cambie el
  préstamo.
- **Amortización francesa** con última cuota ajustada para que la suma de
  capital sea exacta.
- **Pago en orden y por la cuota completa**, solo por el prestatario.
- **Chat solo entre las partes**, con polling cada 8 s en el front.
- **Atomicidad total**: si el desembolso falla, no queda préstamo ni cuotas.

**Tests:** `test_services`, `test_api`, `test_models`, `test_concurrency`,
`test_loan_breakdown`, `test_repayment_source`, `test_commands`, `test_tasks`,
`test_notify_tasks`, `test_messages`, `test_reviews`, `test_cancellation`.

**Migraciones:** `0001` inicial, `0002` `ledger_transaction_id` en cuotas,
`0003` `LoanMessage`, `0004` `LoanReview`, `0005` cancelación y archivado.

---

## 11. `apps/investments` — plazos fijos

| Archivo | Qué hace / decisión |
|---|---|
| `models.py` | `InvestmentProduct` (tipo, nombre, descripción, moneda, plazo, TNA, mínimo, estado) y `Position` (usuario, producto, monto, vencimiento, interés, idempotencia). |
| `services.py` | `open_position` (mueve dinero a la cuenta sistema y calcula interés simple), `settle_matured_positions`, `_settle_position` (idempotente). |
| `selectors.py` | Productos activos y posiciones del usuario. |
| `serializers.py` | Producto, posición, detalle y apertura. |
| `views.py` | Productos y posiciones; perfil inversor para todas las operaciones. |
| `permissions.py` | `IsInvestor`. |
| `tasks.py` | `settle_investments`; adaptador delgado. |
| `management/commands/settle_investments.py` | Misma liquidación desde consola. |
| `signals.py` | `investment_settled` para notificaciones. |
| `urls.py` | `/investments/products/`, `/positions/`, `/{id}/`. |
| `admin.py` | Alta de productos solo staff y liquidación manual. |

**Decisión:** producto creado solo por staff; interés simple; sin cancelación
anticipada; liquidación idempotente.

**Tests:** `test_services`, `test_api`, `test_models`, `test_concurrency`,
`test_commands`, `test_tasks`, `test_settlement_notification`.

**Migraciones:** `0001` inicial, `0002` nombre/descripción del producto.

---

## 12. `apps/budgets` — presupuestos y gastos

| Archivo | Qué hace / decisión |
|---|---|
| `models.py` | `Category`, `Expense` (solo clasifica un movimiento del ledger) y `Budget` (límite mensual por categoría/moneda, umbral de alerta). |
| `services.py` | `create_category`, `create_budget`, `categorize_movement`, `_alert_budgets`. |
| `selectors.py` | Categorías, presupuestos, gastos, `analyze_movement_spending`, `get_monthly_spending`, `get_budget_status`; deriva importes del ledger. |
| `serializers.py` | Categoría, presupuesto, gasto y estado. |
| `views.py` | CRUD de categorías/presupuestos, estado y gastos. |
| `signals.py` | `budget_alert` para notificaciones. |
| `urls.py` | `/budgets/`, `/categories/`, `/expenses/`, `/{id}/status/`. |
| `admin.py` | Solo consulta. |

**Decisión:** no duplicar importes. El gasto se calcula desde el ledger; el
desembolso de un préstamo no es gasto, y el pago de una cuota solo cuenta por el
interés. Nunca se suman ARS y USD.

**Tests:** `test_services`, `test_services_edges`, `test_api`, `test_models`,
`test_selectors`, `test_spending`, `test_categorization`, `test_classification`,
`test_budget_alert`, `test_concurrency`.

**Migraciones:** `0001` inicial, `0002` Expense.

---

## 13. `apps/reports` — reportes y CSV

| Archivo | Qué hace / decisión |
|---|---|
| `selectors.py` | Validación de período/moneda y agregaciones de gastos, préstamos, inversiones y movimientos. |
| `export.py` | CSV con `csv` de la stdlib y neutralización de fórmulas (`=`, `+`, `-`, `@`). |
| `serializers.py` | Filas y reportes. |
| `views.py` | Cuatro reportes; `?export=csv` devuelve archivo. |
| `urls.py` | `/reports/spending|loans|investments|movements/`. |
| `admin_site.py` | `PrestoAdminSite` reemplaza el admin por defecto y muestra un dashboard de métricas de solo lectura. |
| `templates/admin/reports/` | Plantillas HTML del dashboard de métricas. |

**Decisión:** solo lectura, sin modelos. El CSV escapa fórmulas para evitar
inyección al abrirlo en una planilla.

**Tests:** `test_api`, `test_spending_api`, `test_loans_api`,
`test_investments_api`, `test_export`, `test_parameters`,
`test_admin_metrics`.

---

## 14. `apps/notifications` — avisos y preferencias

| Archivo | Qué hace / decisión |
|---|---|
| `models.py` | `Notification` (evento, referencia, estado, `read_at`, intentos) y `NotificationPreference` (opt-out por evento). |
| `services.py` | `create_notification`, `set_preference`, `get_preferences`, `register_notification_attempt`, `mark_notification_sent/failed/read`, `mark_all_notifications_read`. |
| `selectors.py` | Listado, obtención, preferencias y contador de no leídos. |
| `receivers.py` | Conecta señales de loans/investments/budgets; crea aviso y encola email con `transaction.on_commit`. |
| `emails.py` | Arma emails de texto plano sin datos sensibles. |
| `tasks.py` | `send_notification_email` con 3 intentos y backoff exponencial. |
| `views.py` | Notificaciones, preferencias, no leídos, marcar leído/todos. |
| `urls.py` | `/notifications/...`. |
| `admin.py` | Solo consulta. |

**Decisión:** la notificación in-app se crea en la transacción; el email es
best-effort y nunca rompe la operación financiera. La unicidad por evento evita
duplicados.

**Tests:** `test_services`, `test_api`, `test_receivers`, `test_tasks`,
`test_emails`, `test_loan_created`, `test_installment_paid`.

**Migraciones:** `0001` inicial, `0002` intentos, `0003` `read_at`, `0004` y
`0005` ampliación de tipos de evento.

---

## 15. `apps/assistant` — Presti sin LLM

| Archivo | Qué hace / decisión |
|---|---|
| `market.py` | Dólar (Bluelytics) y cripto (CoinGecko) con timeout, caché y degradación a vacío; noticias RSS con caché. |
| `regulations.py` | Fichas legales curadas con normas y enlaces oficiales. No se generan con un modelo. |
| `selectors.py` | Resúmenes del usuario usando selectores de ledger, loans, investments, offers e identity. |
| `services.py` | Chat por intenciones: saldo, cuotas, inversiones, KYC, ofertas, dólar, cripto, mercado, legal, tutorial de inversión, checklist, riesgos, liquidez y respaldo. Si no entiende, devuelve `fallback` con sugerencias. |
| `serializers.py` | Mercado, noticias, regulaciones, chat y respuestas. |
| `views.py` | `MarketView`, `NewsView`, regulaciones, `ChatView` y `AssistantView`. |
| `permissions.py` | `AssistantThrottle` (120/h). |
| `urls.py` | `/assistant/market|news|regulations|chat/`. |

**Decisión:** respuestas deterministas, sin costo por token y sin inventar
datos. Las fuentes externas pueden fallar sin romper la pantalla. El contenido
legal está versionado con el código.

**Tests:** `test_chat`, `test_market_news`, `test_regulations`.

---

## 16. `apps/demo` — datos y comandos de demostración

| Archivo | Qué hace / decisión |
|---|---|
| `seeds.py` | `seed_demo` idempotente: crea Ana, Beto y Carla, KYC, emails, depósitos, oferta, préstamo, cuotas, inversión, presupuesto y pagos. Usa services/selectors y, donde no hay interfaz pública, `django_apps.get_model`. |
| `welcome.py` | `grant_welcome_bonus`: acredita dinero simulado al prestatario cuando se aprueba el KYC. Vive en demo porque cruza identity y ledger. |
| `receivers.py` | Escucha KYC aprobado y dispara el bono. |
| `management/commands/seed_demo.py` | Comando que ejecuta el seed. |
| `management/commands/create_demo_superuser.py` | Crea/actualiza el superusuario desde variables de entorno. |

**Decisión:** el escenario es reproducible y no duplica dinero al correrlo de
nuevo. Las credenciales son públicas a propósito y la demo no debe usarse con
datos reales.

**Tests:** `test_seed_demo`, `test_welcome_bonus`, `test_create_superuser`.

---

## 17. `config/` — configuración de Django

| Archivo | Qué hace / decisión |
|---|---|
| `settings/base.py` | Settings comunes: apps, DRF, JWT, CORS, Celery, email, demo, assistant, pagos, logging y seguridad. Todo lo sensible por entorno. |
| `settings/local.py` | `DEBUG=True`, email por consola, throttles de login más altos para demo/E2E. |
| `settings/production.py` | `DEBUG=False`, HTTPS, HSTS, cookies seguras, `ALLOWED_HOSTS` explícito, `SameSite=None` cuando front/API están en dominios distintos. |
| `settings/test.py` | Celery eager, email en memoria, depósitos simulados, `DEMO_MODE=False`; tests contra PostgreSQL. |
| `urls.py` | Une admin, health, meta, `/api/v1/` de cada app, schema y Swagger. |
| `celery.py` | Broker Redis, sin result backend, beat schedule de vencimientos y liquidaciones. |
| `asgi.py` / `wsgi.py` | Puntos de entrada ASGI/WSGI; Gunicorn usa WSGI. |
| `admin.py` | `PrestoAdminConfig` usa `PrestoAdminSite` con dashboard de métricas. |
| `staticfiles/` | CSS/JS/imágenes del admin y DRF ya recolectados. **Generado**: no editar a mano; se regenera con `collectstatic`. |

**Decisión:** settings separados por entorno, sin secretos en el repo. El
middleware de health se ejecuta antes de `Host`/TLS para que Render pueda
considerar sano el servicio.

---

## 18. `deploy/` y contenedores

| Archivo | Qué hace / decisión |
|---|---|
| `deploy/entrypoint.sh` | Espera/reintenta migraciones si `RUN_MIGRATIONS=1` y arranca Gunicorn. |
| `deploy/Caddyfile` | Proxy inverso con TLS automático para el perfil `proxy` de producción. |
| `deploy/backup-postgres.sh` | Backup diario con `pg_dump`; documenta restauración. Perfil `backup`. |
| `Dockerfile` | Multi-stage, usuario no root, dependencias antes del código, `collectstatic`. |
| `docker-compose.yml` | Stack local completo: db, redis, web, worker y beat. |
| `docker-compose.prod.yml` | Producción: imágenes por digest, healthchecks, Gunicorn, perfiles opcionales. |
| `render.yaml` | Blueprint de Render con DB, Redis y web; worker/beat documentados como plan pago. |

**Decisión:** el backend se despliega como imagen inmutable, no compilando en
producción. Migraciones automáticas al arrancar, pero con reintentos.

---

## 19. `scripts/` — automatización

| Script | Qué hace |
|---|---|
| `setup-venv.ps1` | Crea `.venv` e instala dependencias del backend. |
| `install-services.ps1` | Descarga PostgreSQL 16 y Redis portables en `%LOCALAPPDATA%\presto`. |
| `start-services.ps1` / `stop-services.ps1` | Arrancan/paran PostgreSQL y Redis portables. |
| `env.ps1` | Carga variables de desarrollo (DB, Redis, CORS, demo). |
| `run_server.ps1`, `run-api.ps1`, `run-front.ps1` | Levantan backend/front en ventanas separadas. |
| `run-demo.ps1`, `stop-demo.ps1` | Orquestan la demo local completa. |
| `install-docker.ps1` | Instala Docker Desktop si la máquina cumple requisitos. |
| `create-demo-shortcuts.ps1` | Crea accesos directos en el escritorio. |
| `seed-remote.ps1` | Siembra la demo en la base de Render usando la URL externa. |
| `create-superuser-remote.ps1` | Crea/actualiza el admin en Render sin Shell. |
| `smoke-demo.ps1` | 11 chequeos: health, demo, CORS, login, cookie, refresh, Presti y rutas del front. |
| `demo_flow.py` | Recorrido completo contra la API local. |
| `build_presentation.py` / `build_short_presentation.py` | Generan las presentaciones PPTX/HTML. |

**Decisión:** Windows sin Docker es un camino de primera clase porque es el
entorno de la demo; los scripts evitan depender de WSL o de conocimientos de
Compose.

---

## 20. `tests/` — prueba end-to-end global

| Archivo | Qué hace |
|---|---|
| `tests/test_end_to_end.py` | Recorre el flujo completo en ARS y USD: registro, KYC, fondos, oferta, préstamo, cuotas, inversión, presupuestos y reportes; verifica el invariante de suma cero del ledger. |

**Decisión:** los tests de cada app prueban piezas; este test prueba que el
sistema completo siga siendo coherente. Corre contra PostgreSQL real.

---

## 21. `.github/workflows/ci.yml` — integración continua

5 jobs:

1. **quality:** ruff check/format, import-linter, OpenAPI, pip-audit y
   `check --deploy`.
2. **migrations:** `makemigrations --check`.
3. **tests:** PostgreSQL 16, migraciones, pytest y gates de cobertura.
4. **frontend:** Node 24, typecheck, tests y build.
5. **docker:** construye la imagen, verifica la app y publica en GHCR en
   `main` (`latest` y SHA corto).

**Decisión:** la arquitectura y el contrato se validan automáticamente. El
deploy de Render usa la imagen publicada por CI, por lo que no se despliega
código sin pasar los checks.

---

## 22. `frontend/` — SPA React

### 22.1 Archivos de configuración

| Archivo | Qué hace / decisión |
|---|---|
| `package.json` | Dependencias, scripts (`dev`, `build`, `mock`, `gen:api`, `typecheck`, `lint`, `test`, `test:e2e`) y Node ≥ 24. |
| `vite.config.ts` | Vite + React + alias `@` y configuración de tests. |
| `tsconfig.json` | TypeScript estricto; incluye `src` y `e2e`. |
| `eslint.config.js` | Reglas de React, hooks y refresh. |
| `.prettierrc.json` / `.prettierignore` | Formato consistente. |
| `playwright.config.ts` | Proyectos `mock` y `api` para E2E. |
| `vercel.json` | Rewrites de SPA para rutas profundas. |
| `index.html` | HTML base y script inline que aplica el tema oscuro antes de renderizar (evita flash). |
| `.env` / `.env.example` | URL de API local, asistente y banners. |
| `pnpm-lock.yaml` / `pnpm-workspace.yaml` | Versiones fijadas y workspace. |
| `contract/openapi.yaml` | Copia del contrato usado para generar tipos. |
| `README.md` | Guía del front y reglas de sesión. |
| `docs/decisions.md` | Decisiones y desvíos del front (mock, sin TanStack, E2E fuera de CI). |

### 22.2 `src/app` — composición de la aplicación

| Archivo | Qué hace / decisión |
|---|---|
| `main.tsx` | Monta React con `ThemeProvider`, `BrowserRouter` y `AuthProvider`. |
| `App.tsx` | Rutas públicas y privadas; `Protected` y `ProfileOnly` restringen por sesión y perfil. |
| `layout/AppLayout.tsx` | Shell con sidebar, header, banners y `Outlet`. |
| `layout/AppHeader.tsx` | Menú mobile, campana, toggle de tema y menú de usuario. |
| `layout/AppSidebar.tsx` | Navegación según perfil activo, marca y tarjeta de Presti. |
| `layout/Backdrop.tsx` | Fondo del menú mobile. |
| `layout/NotificationsBell.tsx` | Polling de no leídos cada 20 s y al enfocar; badge y link. |
| `layout/DemoModeBanner.tsx` | Aviso de dinero simulado según `/meta/`; descartable. |
| `layout/ComplianceBanner.tsx` | Aviso interno de revisión legal; oculto en demo por defecto. |
| `providers/ThemeContext.tsx` | Tema claro/oscuro, `localStorage`, `prefers-color-scheme`. |
| `providers/SidebarContext.tsx` | Estado de sidebar expandido/mobile/hover. |

**Decisión:** contextos pequeños en lugar de un store global; el estado
compartido real es sesión, tema y sidebar.

### 22.3 `src/features` — una carpeta por dominio

| Feature / archivo | Qué hace / decisión |
|---|---|
| `auth/AuthContext.tsx` | Usuario, login, registro, logout, refresh y perfil activo. Access token solo en memoria. |
| `auth/components/AuthShell.tsx` | Layout compartido de login, reset y verificación; incluye toggle de tema. |
| `auth/pages/Login.tsx`, `Register.tsx` | Formularios de acceso y alta; perfil fijo y términos. |
| `auth/pages/ForgotPassword.tsx`, `ResetPassword.tsx`, `VerifyEmail.tsx` | Flujo de recuperación y verificación. |
| `auth/pages/Profile.tsx` | Perfil, KYC, biometría simulada, cuentas de respaldo, seguridad y cierre. |
| `wallet/pages/Dashboard.tsx` | Resumen, saldo, préstamos del rol, respaldo, inversiones y refresco cada 15 s. |
| `wallet/pages/Wallet.tsx` | Cuentas, saldo, movimientos y alta de movimientos. |
| `payments/pages/Payments.tsx` | Depósitos, retiros y transferencias con idempotencia. |
| `budgets/pages/Budgets.tsx` | Categorías, presupuestos, estado y gastos. |
| `marketplace/pages/Marketplace.tsx` | Tablero de ofertas, filtros colapsables, comparación y aceptación. |
| `marketplace/pages/Offers.tsx` | Ofertas propias del prestamista, publicación y estado. |
| `loans/pages/Loans.tsx` | Lista filtrada por rol, contraparte y acceso al chat. |
| `loans/pages/LoanDetail.tsx` | Condiciones, cuotas, pago, banner de chat, snapshot y `LoanChat`. |
| `loans/components/LoanChat.tsx` | Chat privado con polling cada 8 s y envío de mensajes. |
| `investments/pages/Investments.tsx` | Productos, posiciones, apertura y liquidación visible. |
| `notifications/pages/Notifications.tsx` | Avisos, marcar leído y preferencias. |
| `assistant/pages/Assistant.tsx` | Presti: chat, mercado, noticias y marco legal. |
| `marketing/pages/Landing.tsx` | Landing pública con demo, cuentas y propuesta. |
| `marketing/pages/Legal.tsx` | Términos, privacidad y alcance de la demo. |

**Decisión:** cada feature contiene sus páginas y componentes; lo compartido va
a `shared`. No hay un `components/` global con archivos sin relación.

### 22.4 `src/shared`

| Archivo | Qué hace / decisión |
|---|---|
| `api/client.ts` | `fetch` centralizado: token en memoria, refresh con cookie, reintento 401, `Idempotency-Key`, errores y paginación. |
| `api/endpoints.ts` | Funciones tipadas por recurso; ninguna pantalla llama `fetch` directo. |
| `api/types.ts` | Alias de los tipos generados; no se escriben respuestas a mano. |
| `api/schema.d.ts` | **Generado** con `pnpm gen:api` desde OpenAPI. No editar. |
| `lib/format.ts` | Moneda, tasa, fecha y etiquetas; sin `parseFloat`. |
| `lib/decimal.ts` | Sumas/comparaciones exactas con `bigint`. |
| `lib/profiles.ts` | Tipos y etiquetas de perfil. |
| `lib/features.ts` | Flag de Presti por variable de entorno. |
| `lib/useIdempotencyKey.ts` | Clave estable por intento. |
| `lib/index.ts` | `cn` (clsx + tailwind-merge). |
| `ui/icons.tsx` | Íconos SVG. |
| `ui/Mascot.tsx` | Mascota de Presti. |
| `ui/ThemeToggle.tsx` | Botón sol/luna reutilizable. |
| `index.css` | Tailwind, tema, clases semánticas, landing, dark mode, tablero y chat. |
| `test/setup.ts` | Configuración de Testing Library. |

**Decisiones:** tipos generados desde el contrato, cliente HTTP único, montos
como texto decimal y access token fuera de `localStorage`. El tema oscuro usa
`.dark` en `<html>`, `localStorage` y `prefers-color-scheme`, con script inline
para evitar flash.

### 22.5 `frontend/mock`, `e2e` y `docs`

| Archivo | Qué hace |
|---|---|
| `mock/server.mjs` | API completa en memoria, con login, cookie, idempotencia, préstamos, inversiones y asistente. |
| `mock/assistant.mjs`, `mock/regulations.mjs` | Datos del asistente para el mock. |
| `e2e/auth.spec.ts`, `marketplace.spec.ts`, `wallet.spec.ts` | Playwright de flujos principales. |
| `e2e/helpers.ts` | Utilidades de login/navegación. |
| `docs/decisions.md` | Decisiones y deuda del front. |

**Decisión:** el mock permite trabajar sin backend y probar la cookie httpOnly
real; por eso se prefirió un servidor Node antes que MSW. Los E2E están fuera de
CI por tiempo/estabilidad (deuda documentada).

---

## 23. `docs/` — documentación y ADRs

| Archivo | Contenido |
|---|---|
| `architecture.md` | Mapa del backend, apps, capas, dinero, entornos. |
| `implementacion.md` | Detalle de modelos, servicios, endpoints, front, infra y tests. |
| `decisiones-tecnicas.md` / `.pdf` / `.docx` | Documento narrativo de decisiones de código y POO. |
| `mvp.md` | Arranque local y guion de demo. |
| `deploy-demo.md` / `deploy-mvp.md` | Despliegue, variables, checklist y troubleshooting. |
| `entrega.md` | Mapa para pasar el proyecto a otra persona. |
| `resumen-ejecutivo.md` / `.pdf` / `.docx` | Resumen de producto. |
| `documento-presto.md` / `.pdf` / `.docx` | Documento de producto. |
| `guia-para-mostrar.md` / `.pdf` / `.docx` | Guion de demo sin tecnicismos. |
| `presentacion-*.pptx/pdf/html` | Presentaciones y versiones imprimibles. |
| `regulatorio-bcra.md` | Pendientes legales/PLA-FT y encuadre. |
| `audit-final.md` | Auditoría técnica y hallazgos. |
| `pitch-one-pager.md` | Resumen de una página. |
| `assets/` | Logo PNG/SVG. |
| `adr/0001..0017` | Decisiones puntuales: Celery, presupuestos, reportes, notificaciones, saldo, doble entrada, orden de apps, pagos, custodia, rendimiento, PLA/FT, CFT, reintentos, cookie httpOnly, digests, reset/verificación y Presti sin LLM. |

**Decisión:** la documentación vive junto al código y se versiona. Los ADR
explican el contexto y las consecuencias; no son solo “qué hace” sino “por qué”.

---

## 24. Decisiones transversales que explican el repositorio

| Decisión | Por qué |
|---|---|
| Monolito modular | Menos complejidad operativa y transacciones simples; los límites se sostienen con apps e import-linter. |
| `services.py` + `selectors.py` | Casos de uso explícitos, lecturas aisladas y tests más simples. |
| UUID sin FK entre apps | Desacople y posibilidad de extraer una app; la integridad se refuerza con servicios y tests. |
| `Decimal` y un solo redondeo | Evita diferencias de centavos entre cálculo, ledger y pantalla. |
| Ledger de doble entrada inmutable | Auditoría y corrección por reverso, no por edición. |
| Idempotencia | Un doble clic, un reintento o un webhook repetido no duplican dinero. |
| Snapshot de oferta | El préstamo conserva las condiciones aceptadas aunque la oferta cambie. |
| Perfil fijo en la demo | Reglas claras: prestatario no publica, prestamista no invierte. |
| Cuenta de respaldo y cierre bloqueado | Salvaguardas de fase 1 antes de operar con dinero real. |
| Presti sin LLM | Respuestas deterministas, sin costo por token ni alucinaciones. |
| Proveedor de pagos abstracto | Simulado y Mercado Pago intercambiables sin tocar dominio. |
| Access token en memoria + refresh httpOnly | Menor exposición a XSS; el refresh no lo lee JavaScript. |
| OpenAPI + tipos generados | El contrato se detecta en typecheck, no en la demo. |
| Polling en dashboard/préstamos/chat | “Casi tiempo real” sin WebSockets, suficiente para la demo y barato en Render. |
| Worker/beat en plan pago | En free no hay procesos de fondo; los emails y tareas programadas quedan documentados como límite. |

---

## 25. Cómo extender el repositorio (guía rápida)

- **Nueva regla de negocio:** va en `apps/<app>/services.py`, dentro de
  `transaction.atomic()` si escribe.
- **Nueva lectura o filtro:** va en `apps/<app>/selectors.py`.
- **Nuevo endpoint:** serializer → view fina → `urls.py`; actualizar README y
  OpenAPI.
- **Nuevo modelo:** `models.py` + migración + constraints + tests; si cruza
  apps, usar UUID y selectores.
- **Nueva pantalla:** `features/<feature>/pages`, ruta en `app/App.tsx`,
  endpoint en `shared/api/endpoints.ts`.
- **Nuevo tipo de API:** regenerar `schema.d.ts` con `pnpm gen:api`; no escribirlo
  a mano.
- **Nuevo evento:** señal en la app emisora, receptor en `notifications`, aviso
  in-app y email best-effort.
- **Nueva tarea programada:** service idempotente + task delgada + entrada en
  `config/celery.py` + README.

---

## 26. Glosario mínimo

| Término | Significado |
|---|---|
| App | Módulo Django con una responsabilidad de dominio. |
| Service | Función que escribe y aplica reglas; dueña de la transacción. |
| Selector | Función de lectura; no modifica estado. |
| Ledger | Libro mayor de débitos y créditos. |
| Asiento | Cada débito o crédito de una transacción. |
| Idempotencia | Repetir una operación no la duplica. |
| Snapshot | Copia congelada de condiciones aceptadas. |
| TNA / TEA | Tasa nominal anual / tasa efectiva anual. |
| KYC | Verificación de identidad. |
| PLA/FT | Prevención de lavado y financiamiento del terrorismo. |
| Mock | API en memoria para desarrollar sin backend. |
| ADR | Registro de una decisión de arquitectura. |

---

## Anexo A. Inventario de archivos de prueba

La suite backend tiene **910 tests** al cierre de este documento. Los archivos se
agrupan por app y por tipo de garantía:

| App | Archivo de test | Qué cubre |
|---|---|---|
| assistant | `test_chat.py` | Intenciones del chat, saldo, cuotas, ofertas, mercado, legal y fallback. |
| assistant | `test_market_news.py` | Mercado/noticias, caché y degradación si falla la fuente. |
| assistant | `test_regulations.py` | Fichas legales curadas y búsqueda por id. |
| budgets | `test_api.py` | Endpoints de categorías, presupuestos, gastos y estado. |
| budgets | `test_services.py` / `test_services_edges.py` | Creación, clasificación y casos borde. |
| budgets | `test_models.py` / `test_selectors.py` | Constraints, aislamiento y derivación del ledger. |
| budgets | `test_spending.py` / `test_categorization.py` / `test_classification.py` | Regla de gasto, categorías y clasificación. |
| budgets | `test_budget_alert.py` / `test_concurrency.py` | Señal de alerta y concurrencia. |
| core | `test_money.py` | Redondeo, cuota francesa, interés simple, TEA y costos. |
| core | `test_health.py` / `test_meta.py` | Health y metadata pública. |
| core | `test_exception_handler.py` / `test_openapi.py` | Formato de errores y contrato. |
| core | `test_cors.py` / `test_security_settings.py` | CORS, cookies, HSTS y settings. |
| core | `test_demo_mode.py` / `test_compliance_checks.py` | Modo demo y revisión legal. |
| core | `test_readme.py` / `test_docs.py` | Documentación sincronizada con endpoints/apps. |
| core | `test_celery.py` / `test_email_backend.py` / `test_deployment.py` | Tareas, email y despliegue. |
| demo | `test_seed_demo.py` | Seed idempotente y escenario completo. |
| demo | `test_welcome_bonus.py` / `test_create_superuser.py` | Bono de bienvenida y admin. |
| identity | `test_api.py` | Registro, login, refresh, logout, perfil, KYC y backup. |
| identity | `test_services.py` | Registro, reseteo, verificación, cierre y contraseña. |
| identity | `test_models.py` / `test_selectors.py` | Usuarios, perfiles y consultas. |
| identity | `test_profiles.py` / `test_permissions.py` | Perfil fijo, gates de KYC y respaldo. |
| identity | `test_backup_accounts.py` / `test_biometric.py` | Respaldo, verificación y biometría simulada. |
| identity | `test_email_verification.py` / `test_password_reset.py` / `test_admin.py` | Emails, tokens y admin. |
| investments | `test_api.py` / `test_services.py` | Productos, apertura, interés y liquidación. |
| investments | `test_models.py` / `test_concurrency.py` | Constraints y carreras. |
| investments | `test_commands.py` / `test_tasks.py` / `test_settlement_notification.py` | Comando, Celery y aviso. |
| ledger | `test_services.py` | Depósitos, retiros, transferencias, reversos e idempotencia. |
| ledger | `test_api.py` / `test_api_transactions.py` | Cuentas, saldo y movimientos. |
| ledger | `test_triggers.py` | Doble entrada e inmutabilidad en PostgreSQL. |
| ledger | `test_concurrency.py` | Bloqueos y carreras de saldo. |
| ledger | `test_selectors.py` / `test_period_selectors.py` / `test_movement_details.py` | Consultas, períodos y detalle. |
| ledger | `test_models.py` / `test_checks.py` / `test_admin.py` | Constraints, check de demo y admin. |
| loans | `test_services.py` | Aceptación, cuotas, pago, estados y snapshot. |
| loans | `test_api.py` / `test_messages.py` / `test_reviews.py` / `test_cancellation.py` | Endpoints, permisos, chat, reputación, cancelación y archivado. |
| loans | `test_concurrency.py` / `test_repayment_source.py` | Aceptación concurrente y respaldo. |
| loans | `test_loan_breakdown.py` / `test_models.py` | Cronograma, constraints y modelos. |
| loans | `test_commands.py` / `test_tasks.py` / `test_notify_tasks.py` | Vencimientos y avisos. |
| matching | `test_selectors.py` / `test_api.py` | Filtros, orden, comparación y endpoints. |
| notifications | `test_services.py` / `test_receivers.py` | Creación, preferencias y señales. |
| notifications | `test_tasks.py` / `test_emails.py` | Reintentos, backoff y plantillas. |
| notifications | `test_loan_created.py` / `test_installment_paid.py` | Avisos de préstamo y cuota. |
| offers | `test_services.py` / `test_api.py` | Publicar, editar, expirar y aceptar. |
| offers | `test_models.py` / `test_selectors.py` / `test_permissions.py` / `test_concurrency.py` | Constraints, filtros, KYC y bloqueo. |
| payments | `test_services.py` / `test_api.py` / `test_models.py` | Proveedor simulado, webhook, estados e idempotencia. |
| reports | `test_api.py` / `test_spending_api.py` / `test_loans_api.py` / `test_investments_api.py` | Los cuatro reportes y parámetros. |
| reports | `test_export.py` / `test_parameters.py` / `test_admin_metrics.py` | CSV, validaciones y dashboard. |
| global | `tests/test_end_to_end.py` | Flujo completo ARS/USD y suma cero del ledger. |
| frontend | `client.test.ts` / `endpoints.test.ts` | Sesión, refresh, 401, idempotencia y endpoints. |
| frontend | `format.test.ts` / `decimal.test.ts` | Formato sin float y aritmética exacta. |
| frontend | `ComplianceBanner.test.tsx` | Visibilidad del banner legal. |
| frontend E2E | `auth.spec.ts` / `marketplace.spec.ts` / `wallet.spec.ts` | Flujos de Playwright contra mock/API. |

---

## Anexo B. ADRs y decisión registrada

| ADR | Decisión |
|---|---|
| 0001 | Celery + Redis como cola y scheduler. |
| 0002 | El gasto de presupuestos se deriva del ledger. |
| 0003 | Los reportes son de solo lectura. |
| 0004 | Notificaciones por email desde una cola. |
| 0005 | Saldo de cuentas desnormalizado y bloqueado. |
| 0006 | Doble entrada validada con trigger diferido. |
| 0007 | Orden y dependencias entre apps. |
| 0008 | Proveedor de pagos detrás de una interfaz (Mercado Pago). |
| 0009 | Cuenta segregada: Presto no custodia el dinero. |
| 0010 | Plazos fijos sin garantía de capital. |
| 0011 | Mínimo viable de PLA/FT. |
| 0012 | Costo total y CFT. |
| 0013 | Reintentos de avisos por email con backoff. |
| 0014 | Refresh token en cookie httpOnly. |
| 0015 | Imágenes de producción fijadas a digest. |
| 0016 | Reseteo de contraseña y verificación de email. |
| 0017 | Presti como asistente por reglas, sin LLM. |

---

**Cierre.** El repositorio está organizado para que el camino crítico del
dinero sea fácil de encontrar: `identity` dice quién es el usuario, `ledger`
mueve y registra el dinero, `offers` y `loans` modelan el crédito,
`investments` los plazos fijos, y `notifications` comunica lo que pasó. El
frontend refleja las mismas reglas con Tipos generados, sesión segura y una
interfaz por perfil. Las carpetas no son decorativas: cada una tiene un límite,
un dueño y una razón para existir.
