# ADR 0008 — Proveedor de pagos: Mercado Pago detrás de una interfaz de proveedor

- **Estado:** aceptado (decisión de producto tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** app `payments` (Bloque 7), `HANDOFF.md` §11.1 decisión **O1**
- **Resuelve:** O1 — qué proveedor de pagos usa Presto

## Contexto

Los depósitos y los retiros del backend son **simulados**: `ledger.deposit` y
`ledger.withdraw` mueven el saldo contra la cuenta de contrapartida `custody` y
están bloqueados en producción por el system check `ledger.E001`
(`LEDGER_SIMULATED_DEPOSITS_ENABLED`). El bloqueo de producción es correcto:
sin un proveedor real no se puede mover dinero.

Lo que había que definir (O1):

1. Qué proveedor (PSP, banco o pasarela) y si opera en Argentina.
2. Qué operaciones soporta: depósito, retiro, transferencia.
3. Si hay **webhooks firmados** para reconciliar.
4. Comisiones y tiempos de liquidación.
5. Si el saldo del ledger **se replica** contra la cuenta del proveedor.

Restricciones del proyecto:

- AGENTS §5.2: entre apps solo `services.py` y `selectors.py`; el `payments`
  no puede tocar `ledger.models`.
- AGENTS §6: todo importe es `Decimal` y se redondea solo en `core/money.py`.
- AGENTS §9: **la idempotencia es obligatoria** en toda operación que mueve
  dinero (header `Idempotency-Key`).
- `docs/regulatorio-bcra.md` (C7): el proveedor tiene que **segregar los
  fondos** y entregar saldos conciliables.

Evidencia del cliente (escrita, no inferida):

- `PRESENTACIÓN DEL PROYECTO - PRESTO.docx`: *"aplicar el mismo tipo de
  dinámica que ciertas billeteras virtuales como **Mercado Pago** y la propia
  app del Banco, sumando interés por monto de capital ingresado"*.
- `PITCH\pitch.md`, Fase 2: *"con capital → **pagos reales, integraciones
  bancarias, tarjetas**, KYC y métricas de negocio"*.

## Decisión

1. **Proveedor: Mercado Pago (PSP regulado, opera en Argentina).** Es el que el
   cliente ya nombró, y es el único de la lista que cubre en el mismo contrato
   depósito, retiro, transferencia y pago de préstamos.
2. **Presto habla con el proveedor detrás de una interfaz**, no directamente.
   La app `payments` define un contrato `PaymentProvider` (`apps/payments/providers.py`)
   con las operaciones `create_deposit`, `create_withdrawal`, `create_transfer`,
   `get_balance`, `verify_webhook_signature` y `parse_webhook_event`. Hay dos
   implementaciones:
   - `MercadoPagoProvider`: la real (API de Mercado Pago por HTTP con
     `urllib`, webhooks firmados con HMAC-SHA256).
   - `SimulatedProvider`: la que ya existe hoy (movimiento contra la cuenta de
     contrapartida del ledger), para el modo demo y los tests.
   Cambiar de proveedor **no toca** los servicios ni el ledger. El proveedor se
   elige por entorno con `PAYMENTS_PROVIDER` (`simulated` por defecto).
3. **El ledger sigue siendo la fuente de verdad.** El saldo del ledger es el
   saldo del usuario; el saldo del proveedor es el saldo de Presto. Se
   **concilian** (no se replaces), con el proveedor como cuenta de
   contrapartida. Las dos sumas tienen que cuadrar (invariante ya probada:
   `custody + system == -suma de las wallets`).
4. **Solo el service de `payments` mueve saldo, y lo hace a través de
   `ledger.services`.** La API de pagos **no** mueve el saldo de una operación
   del proveedor por su cuenta: con el proveedor real, la operación queda
   `pending` (con `checkout_url` para que el usuario pague) y **el webhook
   firmado es el que dispara el movimiento** del ledger. La firma se verifica
   **antes** de parsear el evento; si no valida, la respuesta es `401` y **no**
   se toca el ledger. El movimiento hereda la misma idempotencia
   (`Idempotency-Key`) que la API, y cada evento se registra una sola vez en
   `WebhookEvent` (único por `(provider, external_id)`), así que reenviar el
   mismo webhook no duplica el movimiento.
5. **Las transferencias entre dos usuarios de Presto son internas**: el dinero no
   cruza la frontera del proveedor, así que se resuelven con
   `ledger.services.transfer_between_users` y se confirman de inmediato. El
   campo `Payment.destination_user_id` las identifica (a propósito, para que
   nadie lo confunda con una cuenta externa del proveedor).
6. **Comisiones y tiempos de liquidación** no se modelan todavía: no hay campo
   de comisión en el ledger y agregar uno abre el CFT (ver ADR 0012). Se
   registran en la documentación del proveedor y se modelan cuando el cliente
   defina el modelo de negocio de la comisión.
7. **La cuenta del proveedor es una cuenta de Presto**, no una cuenta a nombre
   del usuario: los fondos de los usuarios **no están cubiertos por el Seguro
   de Garantía de Depósitos** (ver ADR 0009). La web del producto no puede
   prometer garantía de capital.

## Consecuencias

**Positivas**

- El `ledger` no se toca: el proveedor entra por un borde (HTTP) y el dinero
  siempre pasa por `ledger.services`.
- Los tests siguen corriendo sin red: `SimulatedProvider` es el doble por
  defecto.
- El frontend no cambia: los endpoints de `payments` hablan con la misma
  semántica de idempotencia y error.
- Queda abierta la puerta a otro proveedor sin refactor.

**Negativas / riesgos asumidos**

- **Dependencia de un tercero**: una caída o un cambio del proveedor impacta
  depósitos y retiros. Mitigación: el webhook es la fuente de la
  confirmación, y el saldo del ledger no se toca hasta que llega.
- **Un solo proveedor**: no hay failover. Se acepta para el MVP.
- **La cuenta segregada en el proveedor no está garantizada** por el SGD: es un
  riesgo del cliente que hay que declarar (ADR 0009, ADR 0010).
- **Falta el contrato comercial**: comisiones, liquidación y requisitos
  mínimos los tiene que cerrar el cliente con el proveedor. Mientras tanto, el
  `payments` real queda **sin producción**.

**Estado de la implementación (2026-10-22)**

- `apps/payments/` existe: modelos `Payment` y `WebhookEvent`, `providers.py`
  (interfaz + los dos proveedores), `services.py` (creación idempotente y
  aplicación del webhook), `selectors.py`, serializers, vistas, permisos,
  URLs, admin y la migración `0001_initial`.
- La API expone `GET/POST /api/v1/payments/`, `GET /api/v1/payments/{id}/` y
  `POST /api/v1/payments/webhooks/{provider}/`. Todo `POST` exige
  `Idempotency-Key` y KYC aprobado.
- La firma del webhook de Mercado Pago se valida sobre el manifest
  `id:<data.id>;request-id:<x-request-id>;ts:<ts>;` más el cuerpo crudo, con
  una ventana de `PAYMENTS_WEBHOOK_MAX_AGE_SECONDS` (30 s por defecto).
- **37 tests** cubren la app y **737** la suite completa.

**Pendiente**

- Alta de la cuenta en Mercado Pago, credenciales y certificado de producción.
- Definir el modelo de la comisión (desbloquea el CFT, ADR 0012).
- Conciliación automática de saldos (job diario que compare ledger vs.
  proveedor y avise la diferencia).
- Multimoneda: el proveedor opera en ARS; el saldo en USD sigue siendo interno.
