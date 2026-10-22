# ADR 0016 — Reseteo de contraseña y verificación de email

- **Estado:** aceptado
- **Fecha:** 2026-10-22

## Contexto

La API no tenía forma de recuperar una cuenta: si el usuario olvidaba la
contraseña, quedaba afuera. Tampoco se confirmaba que el email fuera real, así
que los avisos de cuotas e inversiones podían ir a direcciones inexistentes sin
que nadie se enterara.

El front ya tenía el contrato de sesión (access en memoria + refresh en cookie
httpOnly) y la app necesitaba dos flujos públicos, sin exponer qué emails están
registrados.

## Decisión

1. **`User.email_verified_at`** (nullable) y la propiedad `email_verified`. Se
   expone `email_verified` en `GET /api/v1/auth/me/` y en el registro.
2. **Tokens sin estado** con las utilidades de Django:
   - reseteo: `django.contrib.auth.tokens.default_token_generator`;
   - verificación: un generador propio que **excluye `last_login`** del hash,
     porque el usuario puede iniciar sesión antes de confirmar el correo y el
     enlace tiene que seguir valiendo. Se invalida al cambiar la contraseña o al
     verificar.
3. **Enlaces al front** con `FRONTEND_URL` (`/restablecer` y `/verificar`) y
   vencimiento de una hora (`PASSWORD_RESET_TIMEOUT`).
4. **Sin enumeración de cuentas**: `POST /auth/password-reset/` responde
   **202** siempre, exista o no el email, y con el mismo mensaje. Los dos
   endpoints públicos tienen throttle de 5 por hora por IP.
5. **Al restablecer la contraseña se blacklistean todos los refresh tokens
   vigentes** del usuario: una sesión abierta deja de poder renovar el access.
   El access token sigue siendo válido hasta que vence (30 minutos), que es el
   compromiso asumido con JWT sin estado.
6. **El envío de emails no rompe la operación**: si SMTP falla, se registra el
   error y el registro (o el pedido de reseteo) responde igual. En modo demo el
   backend es de consola y los correos salen en los logs.
7. **La verificación de email no bloquea operaciones**: el requisito para mover
   dinero sigue siendo el **KYC aprobado**. La verificación es informativa y
   permite avisar al usuario; convertirla en un gate es una decisión de producto
   que puede hacerse después con un permiso nuevo, sin tocar los datos.

## Consecuencias

- Hace falta un SMTP real en producción (`EMAIL_HOST`); sin él, los enlaces solo
  aparecen en los logs (modo demo).
- Los enlaces vencen en una hora; el usuario puede pedir otro (mismo throttle).
- No hay flujo para **cambiar el email** de una cuenta ya verificada: si se
  agrega, tiene que invalidar `email_verified_at` y volver a pedir confirmación.
- El token de verificación queda inválido después de usarlo, pero el endpoint es
  idempotente: si la cuenta ya está verificada, responde 200 sin cambiar nada.
