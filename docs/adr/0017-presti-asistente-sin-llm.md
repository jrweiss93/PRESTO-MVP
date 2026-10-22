# ADR 0017 — Presti: asistente por reglas, sin LLM

- **Estado:** aceptado
- **Fecha:** 2026-10-22

## Contexto

El front traía un asistente ("Presti") que solo funcionaba contra el mock:
mercado, noticias, marco regulatorio y chat. Contra la API real no había
endpoints, y encenderlo con un modelo generativo en una app que mueve dinero
abre tres frentes: costo por token, latencia y **riesgo de que invente datos
financieros o legales**.

Para el MVP se necesita que la pantalla funcione, que los datos sean reales y
que ninguna respuesta pueda confundirse con asesoramiento.

## Decisión

1. **Sin LLM.** El chat responde con **intenciones por reglas** sobre datos
   reales del usuario y contenido curado. Si no entiende, lo dice y propone
   opciones (`intent: fallback`), nunca improvisa.
2. **Endpoints de solo lectura** en una app nueva, `assistant`:
   - `GET /assistant/market/`: dólar (Bluelytics) y cripto (CoinGecko), con
     timeout y caché de 60 s.
   - `GET /assistant/news/`: primeras 8 noticias de un RSS configurable
     (`ASSISTANT_NEWS_FEED_URL`), cacheadas 5 min. Sin feed, lista vacía.
   - `GET /assistant/regulations/` y `GET /assistant/regulations/{id}/`:
     fichas **curadas y versionadas** en el código, con normas y enlaces
     oficiales. Siempre con el aviso de que no es asesoramiento legal.
   - `POST /assistant/chat/`: saldo, préstamos, inversiones, KYC, mercado y
     marco legal.
3. **Datos del usuario por selectores.** La app no importa modelos de otras
   apps: usa sus `selectors.py` (AGENTS §5.2) y devuelve primitivos. La
   restricción queda en `.importlinter`.
4. **Degradación explícita.** Si una fuente externa falla, el endpoint responde
   200 con la parte disponible (o vacía) y el chat lo dice. Nunca un 500 por un
   proveedor caído.
5. **Autenticación y throttle.** Todo Presti exige sesión y tiene un límite de
   120 pedidos por hora.

## Consecuencias

- Las respuestas son deterministas y testeables; no hay costo por token.
- El mercado y las noticias dependen de servicios externos: pueden venir
  vacíos. La UI ya contempla ese caso.
- Las fichas regulatorias hay que **mantenerlas a mano** cuando cambie una
  norma; no se actualizan solas.
- Si más adelante se quiere un chat generativo, el camino es RAG sobre estas
  mismas fichas + *tool calls* de solo lectura, con el aviso y los límites
  definidos en este ADR. No se reemplaza el modo por reglas: se suma.
