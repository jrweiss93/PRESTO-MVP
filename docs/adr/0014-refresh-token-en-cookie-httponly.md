# ADR 0014 — El refresh token viaja en una cookie httpOnly; el access token, solo en memoria

- **Estado:** aceptado (decisión técnica tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** app `identity`, contrato con el frontend
- **Resuelve:** la pregunta abierta de `PRESTOFRONT\PROYECTO_FRONT.md` §6.2.2 y §13
  ("transporte del refresh token", "pendiente de definir con Fer")

## Contexto

El frontend se desarrolla aparte, contra el esquema exportado, y su documento
de proyecto dice (sección 6.2.2):

> *"El refresh es rotativo. **Pendiente de definir con Fer cómo se
> transporta**: lo recomendado es una **cookie httpOnly, Secure y SameSite**
> gestionada por el backend. Si el backend lo devuelve en el cuerpo de la
> respuesta, **no lo guardes en almacenamiento del navegador**: consultá antes
> de implementar."*

Y (sección 13): *"Transporte del refresh token (cookie httpOnly recomendada).
Hay que definirlo con Fer antes de implementar la sesión real."*

Estado actual del backend:

- `POST /api/v1/auth/login/` devuelve **`access` y `refresh` en el cuerpo**.
- `POST /api/v1/auth/token/refresh/` recibe el refresh en el cuerpo y devuelve
  `access` y el refresh rotado en el cuerpo.
- La rotación ya está activa (`ROTATE_REFRESH_TOKENS=True`) y el refresh
  anterior se blacklista (`BLACKLIST_AFTER_ROTATION=True`).

Restricciones: AGENTS §9 (el token no se guarda en el navegador; nada sensible
en logs), y el frontend ya fijó su regla: access token **solo en memoria**.

## Decisión

1. **El refresh token se transporta en una cookie httpOnly**, no en el cuerpo
   de la respuesta. Es la opción que el propio frontend recomienda.
   - Nombre: `presto_refresh` (configurable con `JWT_REFRESH_COOKIE_NAME`).
   - `httponly=True`, `secure=True` en producción (configurable), `samesite=Lax`,
     `path=/api/v1/auth/`.
2. **La respuesta del login cambia**: devuelve `access` y `user`, y **ya no
   devuelve `refresh` en el cuerpo**. El `refresh` viaja solo en la cookie. El
   frontend regenera los tipos desde el esquema nuevo (que se le entrega con
   este cambio).
3. **El access token sigue siendo un token de corta duración (30 min) que se
   guarda en memoria**, y se manda en el header `Authorization: Bearer`.
4. **El endpoint de refresh lee la cookie**. Se acepta también el `refresh` en
   el cuerpo **como compatibilidad** para clientes no web (scripts, integración
   backend a backend), pero la cookie manda: la respuesta del refresh **no**
   devuelve el refresh en el cuerpo, solo rota la cookie.
5. **Se agrega `POST /api/v1/auth/logout/`**: blacklistea el refresh (cookie o
   cuerpo), borra la cookie y responde `204`. Sin logout no hay cierre de
   sesión real: el refresh seguiría vivo 7 días.
6. **El CSRF**: como la cookie es `SameSite=Lax` y el endpoint de refresh solo
   emite un access token (no ejecuta operaciones de dinero), el riesgo es
   acotado. Si en el futuro la cookie se usa para operaciones que mueven
   dinero, hace falta token CSRF: queda anotado.
7. **El CORS no usa credenciales**: la cookie viaja en la **misma** llamada
   que la authenticate (`credentials: 'include'`), y `CORS_ALLOW_CREDENTIALS`
   sigue en `False` porque la autenticación va en el header `Authorization`.

## Consecuencias

**Positivas**

- El refresh token **no es accesible desde JavaScript**: un XSS no lo roba.
- El frontend no necesita decidir dónde guardar el refresh: la cookie lo
  resuelve.
- Con el logout, la sesión se cierra de verdad y el refresh queda
  blacklisted.

**Negativas / riesgos asumidos**

- **Cambio incompatible en la respuesta del login**: el frontend tiene que
  regenerar los tipos. Es el punto del contrato: el esquema se entrega con el
  cambio.
- Con `SameSite=Lax` la cookie **no** viaja en un POST desde otro sitio: el
  refresh se renueva solo desde el frontend de Presto. Es lo correcto.
- El fallback por cuerpo deja la puerta abierta a que alguien lo use mal: está
  documentado como compatibilidad, no como camino recomendado.

**Pendiente**

- Confirmar con el frontend que el `fetch` de la API usa
  `credentials: 'include'`.
- Definir la política de dominio y `Secure` cuando haya HTTPS.
- Si el refresh se usa para operaciones de dinero: token CSRF.
