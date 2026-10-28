# Presto — documento de la aplicación

## 1. Qué es Presto

Presto es una aplicación de finanzas personales, inversiones y préstamos entre
personas. Reúne en un solo lugar una **billetera en pesos y dólares**, un
**marketplace de préstamos**, **plazos fijos**, **presupuestos** y un asistente
que explica el mercado y el marco legal en lenguaje simple.

La aplicación está pensada para personas sin experiencia financiera que quieren
entender qué pasa con su dinero, cuánto van a pagar y qué opciones tienen, sin
depender de una planilla paralela ni de varias aplicaciones distintas.

> **Estado:** demo pública con **dinero simulado**. No es una oferta de
> inversión ni asesoramiento financiero. Fecha: octubre de 2026.

## 2. Problemática que busca resolver

- **El crédito es lento y poco claro.** Los requisitos cambian, los costos
  aparecen al final y el usuario no sabe con certeza cuánto va a pagar por mes.
- **Ahorrar e invertir parece difícil.** La jerga técnica y los requisitos de
  acceso alejan a quien tiene un saldo pequeño o poca experiencia.
- **Las herramientas están separadas.** Una app para la cuenta, otra para
  invertir, una planilla para los gastos y ningún lugar para prestar entre
  personas.
- **Quien presta no tiene un espacio simple.** Le falta un lugar con reglas
  claras para ofrecer su dinero y seguir el préstamo.

Presto no promete eliminar el riesgo financiero. Busca reducir la **fricción** y
la **falta de claridad** en cada paso.

## 3. Público objetivo

| Perfil | Situación | Qué necesita |
|---|---|---|
| **Ana, prestataria** | Necesita financiarse para un proyecto | Saber cuánto paga por mes, comparar opciones y pagar en cuotas |
| **Beto, prestamista** | Tiene saldo disponible | Ofrecer su dinero con reglas claras y seguir sus préstamos |
| **Carla, inversora** | Quiere que su saldo rinda | Entender la tasa, el plazo, el interés y el vencimiento |
| **Público general** | Personas sin experiencia financiera | Una interfaz simple, sin jerga y con todo en un lugar |

La propuesta es mobile-first: la mayoría de las personas va a entrar desde el
celular.

## 4. Operaciones que permite

| Área | Operaciones |
|---|---|
| **Identidad y acceso** | Registro, login, recuperación de contraseña, verificación de email y KYC |
| **Billetera** | Saldo en ARS y USD, depósitos, retiros y transferencias |
| **Préstamos** | Publicar una oferta, buscar y comparar, aceptar y pagar cuotas |
| **Inversiones** | Ver productos de plazo fijo, abrir una posición y seguir su vencimiento |
| **Control** | Categorías, presupuestos mensuales, gastos y reportes con exportación CSV |
| **Avisos** | Emails de cuota por vencer, cuota vencida, inversión liquidada y alerta de presupuesto |
| **Asistente** | Presti: saldo, cuotas, dólar, cripto, noticias y marco legal |
| **Administración** | Aprobar KYC, crear productos de inversión y revisar la operación |

El circuito principal es: **verificarse → cargar saldo → publicar o elegir una
oferta → pagar en cuotas → invertir el saldo**. Cada paso queda registrado.

## 5. Beneficios frente a otras alternativas

| Lo habitual | En Presto |
|---|---|
| Una app para la cuenta, otra para invertir y una planilla para los gastos | Todo el circuito en una sola aplicación |
| Costos que aparecen al final | Cuota, interés y costo total antes de aceptar |
| Inversión con jerga y requisitos altos | Tasas, plazos y vencimientos explicados en simple |
| Una sola moneda o conversión automática | ARS y USD separados, sin conversión implícita |
| Sin asistencia para entender | Presti explica el mercado y el marco legal |

Otros diferenciales:

- **Claridad antes de decidir:** la comparación muestra cuota, interés y costo
  total, no solo la tasa.
- **Presupuestos conectados al dinero real:** el gasto se deriva de los
  movimientos, sin cargar dos veces lo mismo.
- **Asistente sin humo:** Presti responde con reglas y datos reales; no inventa
  ni promete asesoramiento.
- **Dos monedas sin mezclas:** cada operación y cada reporte es de una moneda.

> La comparación es de **enfoque y experiencia de uso**. No compara precios ni
> condiciones de competidores.

## 6. Cómo funciona

1. **Identidad:** el usuario se registra y completa el KYC. Sin identidad
   verificada no se opera con dinero.
2. **Billetera:** carga saldo en ARS o USD. En la demo el depósito es simulado.
3. **Oferta:** un prestamista publica monto, moneda, plazo y tasa. Un prestatario
   puede buscar, comparar y aceptar.
4. **Préstamo:** al aceptar, se guardan las condiciones y se arma el cronograma
   de cuotas. El prestatario paga mes a mes.
5. **Inversión:** el usuario abre un plazo fijo y cobra el interés al vencimiento.
6. **Control:** presupuestos por categoría y reportes de lo que pasó.

## 7. Presti, el asistente

Presti responde preguntas sobre:

- **Tu cuenta:** saldo, cuota próxima y resumen de préstamos e inversiones.
- **El mercado:** dólar oficial y blue, bitcoin y ethereum.
- **El marco legal:** préstamo entre particulares, BCRA, CNV, tasas, PLA/FT y
  derechos del consumidor, con enlaces oficiales.
- **Cómo operar:** qué necesitás para prestar o invertir.

**No es IA generativa.** Usa reglas, datos de la cuenta y contenido legal curado.
Si no entiende una pregunta, propone opciones. Eso reduce el riesgo de
respuestas inventadas en un tema sensible como el dinero.

## 8. Confianza y seguridad

- **Identidad verificada** antes de mover dinero (KYC).
- **Libro contable de doble entrada:** cada movimiento se registra dos veces;
  si sale de una cuenta, entra en otra.
- **Sin cobros duplicados:** cada operación de dinero tiene una clave única; si
  se reintenta, no se ejecuta dos veces.
- **Saldos de usuario no negativos:** el sistema impide que una billetera quede
  en rojo.
- **Monedas separadas:** ARS y USD nunca se suman ni se convierten solos.
- **Todo queda registrado:** movimientos, cuotas, inversiones y avisos.

## 9. Tecnología elegida y por qué

| Herramienta | Por qué se eligió |
|---|---|
| **Python + Django** | Framework maduro, seguro y ordenado; ideal para reglas de negocio, permisos y admin. Permite avanzar rápido sin sacrificar claridad. |
| **Django REST Framework + OpenAPI** | API consistente, documentada y con un contrato que el front puede consumir sin adivinar. |
| **PostgreSQL** | Datos financieros necesitan transacciones, restricciones y consistencia. Además permite triggers y tipos decimales exactos. |
| **Redis + Celery** | Tareas diarias (cuotas vencidas, liquidaciones, avisos) sin bloquear la aplicación. |
| **React + Vite + TypeScript** | Interfaz rápida, tipada y mobile-first; el equipo detecta errores antes de publicar. |
| **Docker + Render + Vercel + GitHub Actions** | Despliegue reproducible, demo accesible y controles automáticos en cada cambio. |
| **pytest + factory_boy + import-linter + ruff** | Pruebas contra PostgreSQL real, límites entre módulos y estilo consistente. |

La prioridad fue **seguridad, mantenibilidad y claridad**, no usar la tecnología
de moda. La arquitectura es un monolito modular: 13 módulos con capas estrictas y
comunicación solo por servicios y selectores.

## 10. Estado actual

La demo pública ya muestra el circuito completo:

- Registro, login, recuperación de contraseña y verificación de email.
- KYC y perfil.
- Billetera en ARS y USD, depósitos, retiros y transferencias.
- Ofertas, búsqueda, comparación, préstamo y pago de cuotas.
- Plazos fijos y liquidación.
- Presupuestos, gastos y reportes con CSV.
- Avisos por email y preferencias.
- Presti (mercado, noticias, marco legal y chat).
- Admin para aprobar KYC y revisar datos.

**Números:** 13 módulos, 800 pruebas automáticas, 5 controles en cada cambio y
una demo pública.

## 11. Límites y próximos pasos

**Límites de la demo**

- Dinero simulado: no hay pasarela de pagos conectada.
- KYC manual: se aprueba desde el admin; no hay subida de documentos.
- Emails por consola si no se configura SMTP.
- Legal: la página `/legal` es un borrador de alcance.
- El plan free de Render duerme la API (30–60 segundos en la primera visita).

**Próximos pasos**

1. **Pagos reales:** Mercado Pago en sandbox y luego producción, con webhooks y
   conciliación.
2. **KYC con documentos:** subida y validación propia o con un proveedor.
3. **Legal y regulatorio:** términos, privacidad, PLA/FT y encuadre de custodia.
4. **Operación:** Sentry, backups con restauración probada y dominio propio.
5. **Producto:** valoraciones, notificaciones in-app y, si se decide, Presti con
   un modelo de lenguaje sobre las fichas legales.

## 12. Demo y acceso

- **Front:** <https://presto-mvp-alpha.vercel.app>
- **API:** <https://presto-api-r8vc.onrender.com>
- **Swagger:** <https://presto-api-r8vc.onrender.com/api/docs/>
- **Usuarios demo:** `ana@presto.demo`, `beto@presto.demo`, `carla@presto.demo`
- **Contraseña:** `Presto123!`

El código, la documentación técnica y la guía de despliegue están en
<https://github.com/jrweiss93/PRESTO-MVP>.
