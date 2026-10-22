# ADR 0013 — Los avisos por email se reintentan con backoff exponencial y no se agrupan

- **Estado:** aceptado (decisión técnica tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** app `notifications`
- **Resuelve:** D-6 — qué hacer cuando el envío de un aviso falla

## Contexto

D-6 (de `docs/audit-final.md` §5) tenía que definir: si un envío que falla se
reintenta, con qué backoff, y si se agrupan varios avisos en un mismo email.

Estado actual (`apps/notifications`):

- `send_notification_email` es una tarea Celery **idempotente**: un aviso en
  estado `sent` no se vuelve a mandar.
- Un fallo de SMTP marca el aviso como `failed` con el motivo en `error` y la
  tarea **no** levanta una excepción: el ledger y la transacción de la app
  emisora no se ven afectados (ADR 0004, punto 5).
- **Los correos no se reintentan**: un aviso fallido queda en `failed` y no
  vuelve a encolarse solo (ADR 0004, "Pendiente").

## Decisión

1. **Sí se reintenta, con backoff exponencial y un máximo de 3 intentos en
   total** (el envío original más 2 reintentos). Es lo que recomendaba la
   auditoría: "Reintentar con backoff exponencial (3 intentos)".
2. **Backoff:** `60 s` para el primer reintento y `120 s` para el segundo
   (`base * 2^intento`). Son valores de arranque; se pueden ajustar con
   `NOTIFICATIONS_RETRY_BASE_SECONDS`.
3. **No se agrupan avisos en un mismo email.** Un aviso por email: es más
   simple de auditar, el usuario puede leer cada aviso por separado y un
   aviso roto no oculta a los demás. **No hay resumen diario** de avisos
   pendientes: la decisión es no agrupar.
4. **El contador de intentos vive en el modelo** (`Notification.attempts`), no
   solo en el estado interno de Celery: si el worker se reinicia, el contador no
   se pierde y el aviso no se reintenta para siempre.
5. **El estado sigue siendo `pending` mientras quedan reintentos.** El aviso
   pasa a `failed` **solo** cuando se agotan los 3 intentos (o cuando el
   error no es reintentable, por ejemplo: el usuario no tiene email). Durante
   los reintentos, el aviso **no** se considera enviado ni fallido.
6. **El reintento se hace con la tarea de Celery** (`self.retry`), no con un
   `sleep`: el worker queda libre y el reintento sobrevive a un reinicio.
7. **Un error no reintentable no se reintenta**: la falta de email del
   usuario es definitiva y el aviso queda `failed` de una vez.
8. **El email sigue siendo un aviso, no un comprobante:** no se manda el
   detalle del error al usuario (AGENTS §9), el `error` queda solo en el
   backend.

## Consecuencias

**Positivas**

- Un corte de SMTP de un minuto ya no deja al usuario sin su aviso de cuota.
- El contador persistido evita reintentos infinitos.
- El comportamiento es auditable: `attempts` y `error` quedan en el aviso.

**Negativas / riesgos asumidos**

- Un aviso puede tardar hasta 3 minutos en llegar (60 s + 120 s de espera).
- La tarea queda "en vuelo" durante los reintentos: con `CELERY_TASK_TIME_LIMIT`
  de 15 minutos no hay problema, pero el reintento cuenta como task activo.
- El estado `pending` durante los reintentos puede confundir a quien mira el
  admin: queda el campo `attempts` para distinguirlo de un aviso recién creado.

**Pendiente**

- Métrica de avisos fallidos (no hay observabilidad más allá del log).
- Alertas al responsable cuando un aviso agota los 3 intentos.
