# ADR 0011 — PLA/FT: mínimo viable en el MVP y umbral de monitoreo configurable

- **Estado:** aceptado (decisión de producto tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** apps `identity`, `ledger`, `payments`, `reports`
- **Resuelve:** O5 — umbrales de ROS, beneficiario final, screening, monitoreo, documentación, conservación y responsable

## Contexto

O5 tenía que definir: umbrales de Reporte de Operaciones Sospechosas (ROS),
identificación del beneficiario final, screening contra listas de sanciones,
reglas de monitoreo de patrones (velocidad, montos, estructuración),
documentación de la operatoria, plazos de conservación y responsable
asignado.

Lo que ya existe en el backend:

- `identity` tiene **KYC** con estados `pending|approved|rejected`, aprobado
  desde el admin (AGENTS §9.9). El KYC aprobado es **obligatorio** para
  depósitos, retiros, transferencias, creación de ofertas, aceptación de
  préstamos y apertura de posiciones.
- `identity` guarda `document_number` y los metadatos que manda el usuario
  (`submit_kyc`), pero **no hay subida de documentos** ni verificación
  automática.

Base normativa: `docs/regulatorio-bcra.md` (F6, F7, F8 y C8).

- Registro de **operaciones inusuales** con los campos del art. 32 de la
  Res. 43/2024 (nivel de riesgo, perfil del cliente, metodología de
  detección, tipo de inusualidad, medidas y decisión final).
- **ROS**: sin demora; el plazo más exigente es el de la **Res. UIF 56/2024**
  (**24 h** desde la conclusión, con tope de **90 días** desde la operación).
  El ROS tiene que ser **fundado**.
- **Conservación de la información: 10 años**.
- Umbrales de reporte sistemático para plataformas: **≥ 6 SMVM** (operaciones
  con activos virtuales) y **$50.000.000 / $30.000.000** (ingresos, egresos o
  saldo final de plataformas ante ARCA).

## Decisión

Se implementa el **mínimo viable de PLA/FT** que el producto necesita para
operar, con tres piezas concretas y el resto explícitamente diferido:

1. **KYC aprobado es condición para operar** (ya implementado, no se toca).
   **Se responde además la pregunta del frontend** (`PROYECTO_FRONT.md` §13):
   **sí, el KYC aprobado se exige también para depósitos y retiros**, además
   de ofertas, préstamos e inversiones.
2. **Registro de operaciones inusuales** (`identity`): se agrega el registro de
   operaciones que el backend detecta, con los campos del art. 32 de la
   Res. 43/2024. El **umbral y las reglas son configurables por entorno**
   (`PLA_FT_*`), con estos valores por defecto:
   - `PLA_FT_SINGLE_OPERATION_THRESHOLD`: **ARS 1.000.000** (o USD 1.000) en una
     operación;
   - `PLA_FT_DAILY_TOTAL_THRESHOLD`: **ARS 5.000.000** (o USD 5.000) en un día;
   - `PLA_FT_MAX_OPERATIONS_PER_DAY`: **10** operaciones de depósito o retiro;
   - `PLA_FT_STRUCTURING_THRESHOLD`: **3** operaciones por debajo del umbral
     diario dentro de una ventana de 24 h (patrón de estructuración).
   Una operación que supera un umbral **no se bloquea**: se **marca** y se
   registra. **El bloqueo lo decide una persona**, no una regla.
3. **Derivación de la decisión de reporte a una persona**: el registro de la
   operación inusual tiene un estado `open|reviewed` y un campo de decisión
   motivada. El **reporte a la UIF es una tarea humana con plazo de 24 h**
   (Res. 56/2024) y **no** lo automatiza el backend: el backend **no** reporta
   a la UIF. La documentación del procedimiento (quién decide, cómo, con qué
   plazo y dónde queda el legajo) la escribe el responsable que el cliente
   designe, que sigue siendo **[a validar]**.
4. **Conservación: 10 años** de la información de clientes y operaciones. Hoy
   el backend **no borra** nada (no hay purga de datos), así que el requisito
   se cumple por omisión: no se agrega ninguna tarea de borrado y queda
   prohibido agregarla sin decisión nueva.
5. **Beneficiario final y screening contra listas de sanciones**: **diferidos**.
    Requieren un proveedor de screening o un proceso propio, y datos que
   la app todavía no tiene (tipo de persona jurídica, país, actividad
   económica). No se implementa un screening casero. Queda como
   **[a validar]** con el profesional que defina el procedimiento.
6. **Subida de documentos del KYC**: se mantiene como **solo metadatos** (ya
   está decidido en `PROYECTO_FRONT.md` §4.2). El legajo en papel o digital es
   del responsable de compliance, fuera del backend por ahora.
7. **Lo que el backend nunca hace**: no bloquea por regla automática, no
   reporta a la UIF, no puntúa riesgo de forma automática, no inventa umbrales
   legales. Los umbrales por defecto son **criterios internos de detección**,
   no umbrales legales: se documentan como tales.

## Consecuencias

**Positivas**

- Se cubre la detección y el registro sin automatizar decisiones legales.
- Los umbrales por entorno permiten calibrar sin tocar código.
- Se responde la pregunta abierta del frontend (KYC en depósitos y retiros).

**Negativas / riesgos asumidos**

- **La parte que más importa (screening, beneficiario final, ROS) es la que
  queda para el responsable humano.** Sin ese responsable designado, el MVP
  no puede operar con dinero real: es un bloqueo de proyecto, no técnico.
- Los umbrales por defecto son arbitrarios: hay que calibrarlos con el
  profesor y el cliente, y revisar que no sirvan para discriminar de forma
  indebida.
- El registro de operaciones inusuales guarda datos del usuario: es dato
  sensible (AGENTS §9) y no puede ir a los emails de `notifications`.

**Pendiente**

- Designar el responsable de compliance y escribir el procedimiento (plazo de
  24 h, criterio de "fundado", legajo).
- Calibrar umbrales con datos reales.
- Screening de listas de sanciones y beneficiario final.
- Definir el reporte sistemático ante ARCA si los umbrales se alcanzan.
