# Investigación regulatoria para Presto (BCRA, UIF, defensa del consumidor)

- **Estado:** documento de trabajo interno (no es asesoramiento legal)
- **Fecha:** 2026-10-22
- **Origen:** pedido explícito del cliente en `PRESENTACIÓN DEL PROYECTO - PRESTO.docx`:
  *"Realizar una investigación sobre las regulaciones del Banco Central para con
  los intereses, para aplicar el mismo tipo de dinámica que ciertas billeteras
  virtuales como Mercado Pago y la propia app del Banco, sumando interés por
  monto de capital ingresado."*
- **Para qué sirve:** es la base factual de las decisiones O1, O2, O3, O5 y O6
  (`HANDOFF.md` §11.1) y de los ADR 0008 a 0012.

> **Alcance y límites.** Esto resume normativa pública y explica qué implica
> para el producto. **No reemplaza la validación de un abogado o contador en
> materia de PLA/FT y de defensa del consumidor**, que sigue pendiente antes de
> operar con dinero real. Cada conclusión que dependa de esa validación está
> marcada como **[a validar]**.

---

## 1. Fuentes consultadas

| # | Fuente | Qué regula | Fecha |
|---|---|---|---|
| F1 | BCRA, Comunicación "A" 8407 (TO del Sistema de Seguro de Garantía de los Depósitos) | cobertura y exclusiones del seguro de depósitos | 05/03/2026, vigente desde 01/04/2026 |
| F2 | Ley 24.485 y Decreto 540/95 (Fondo de Garantía de Depósitos, SEDESA) | garantía de los depósitos constituidos en entidades financieras | sistema vigente |
| F3 | BCRA, Comunicación "A" 6541/2018 (punto 3.2.4) y "A" 7645 (puntos 2.3.3 y 3.2) | tasas de interés y CFT en operaciones de crédito | 2018 / 2024 |
| F4 | Ley 24.240 de Defensa del Consumidor, art. 36 | datos que deben consignarse en el crédito para consumo | vigente |
| F5 | Resolución 12/2024 de la Secretaría de Industria y Comercio | información obligatoria en la publicidad de precios financiados | 23/04/2024 |
| F6 | UIF, Resolución 56/2024 y FAQ de ROS | plazos de reporte de operaciones sospechosas | 2024 |
| F7 | UIF, Resolución 43/2024 (arts. 32 y 33) | registro de operaciones inusuales y ROS de otros sujetos obligados | 2024 |
| F8 | ARCA, regímenes informativos de plataformas electrónicas | declaración jurada informativa de cuentas de plataformas | desde 04/2026 |

---

## 2. Seguro de Garantía de Depósitos (F1, F2)

Puntos clave:

1. **Cobertura:** desde el **01/04/2026**, hasta **$50.000.000 (ARS cincuenta
   millones) por persona, por cuenta y por depósito** en cada entidad
   financiera, y hasta **USD 100.000** en moneda extranjera. Cubre capital,
   intereses, actualizaciones (CER/UVA, ICC/UVI) y diferencias de cotización.
2. **Alcance:** alcanza a cuentas corrientes, cajas de ahorro, **plazo fijo** e
   inversiones a plazo constituidas **en entidades financieras**.
3. **Exclusiones relevantes para Presto:**
   - depósitos en **otros intermediarios** (es decir, los que no son una entidad
     financiera con licencia);
   - **depósitos a plazo fijo de títulos valores, aceptaciones o garantías**
     (5.2.5) y CEDIPs transmitidos por la propia entidad (5.2.7);
   - depósitos de **personas vinculadas** a la entidad;
   - **tasa por encima de la de referencia**: los depósitos a plazo que superen
     **1,3 veces la tasa de referencia** o la **tasa de referencia + 5 puntos
     porcentuales** (la mayor de las dos) **quedan fuera de la garantía**.
4. **Leyenda obligatoria:** "Los depósitos en pesos y en moneda extranjera
   cuentan con la garantía de hasta $50.000.000…" o, cuando el depósito está
   excluido, **"Depósito sin garantía"**.

**Implicancia para Presto (O2):** Presto **no es una entidad financiera**: no
tiene licencia del BCRA, no integra el SGD y **no puede emitir un CDBC ni
ofrecer un "plazo fijo" propio con garantía**. Si Presto ofrece un producto
llamado "plazo fijo", el capital **no está garantizado por Presto**; solo lo
estaría si el depósito se constituye **directamente en el banco** del usuario y
queda cubierto por el SGD hasta el límite del punto 1 (y con tasa dentro del
límite del punto 3.3). En cualquier otro caso corresponde la leyenda
**"Depósito sin garantía"**.

---

## 3. Intereses sobre el capital ingressado (lo que pidió el cliente)

La "dinámica de Mercado Pago y la app del Banco" es **saldo remunerado**: una
tasa pasiva que se acredita sobre el saldo depositado. Hay dos mecanismos distintos:

| | Saldo remunerado en cuenta | Plazo fijo / CDBC |
|---|---|---|
| Quién lo emite | La entidad financiera donde está la cuenta | La entidad financiera emisora |
| Quién paga la tasa | La entidad financiera | La entidad financiera |
| Plazo | Variable, se liquida daily o al cierre | Fijo, con fecha de vencimiento |
| Garantía del capital | SGD hasta $50.000.000 por persona/cuenta/depósito | SGD hasta $50.000.000 (si cumple los límites de tasa) |
| Tasa máxima para estar garantizado | Tasa de referencia (Com. B) | 1,3× la tasa de referencia o tasa + 5 pp, la mayor |
| Puede hacerlo Presto | **No**, salvo si Presto es el titular de la cuenta y expone el saldo de un socio | **No** |

**Implicancia para Presto (O2/O3):**

- El modelo que hoy tiene el backend (`Account.kind = custody` como cuenta de
  contrapartida) se interpreta como **"cuenta de Presto en el banco/PSP
  proveedor"**, no como "custodia de Presto": es una cuenta **segregada** del
  proveedor donde los fondos de todos los usuarios están juntos por moneda y
  **no están garantizados por el SGD** (no es un depósito en entidad
  financiera a nombre del usuario).
- El "plazo fijo" que muestra `investments` es, en el MVP, **una promesa
  matemática sobre el capital que Presto no garantiza**. La tasa que se publica
  es una **TNA** y el resultado depende de que Presto cumpla.
- Cuando exista el proveedor real (O1), los fondos del usuario en el proveedor
  **no están cubiertos por el SGD** mientras no estén en una cuenta a nombre
  del usuario en un banco. **[a validar]**

---

## 4. PLA/FT (F6, F7)

1. **Identificación del cliente:** todo sujeto obligado debe identificar al
   cliente y **conocerlo** (art. 13/14 de la Ley 25.246 y resoluciones UIF
   vigentes); la información se guarda en **legajo** y se conserva **10 años**
   desde la última operación.
2. **Registro de operaciones inusuales:** hay que llevar un registro de **todas
   las operaciones inusuales** con nivel de riesgo, perfil del cliente,
   metodología de detección, tipo de inusualidad, medidas y decisión final
   (art. 32 de la Res. 43/2024).
3. **Reporte de operaciones sospechosas (ROS):**
   - **Res. UIF 56/2024**: se reporta **sin demora**, en un plazo de **24 horas**
     desde que el sujeto obligado concluye que la operación es sospechosa, y la
     fecha de reporte **no puede superar los 90 días corridos** desde la
     operación (o su tentativa).
   - **Res. UIF 43/2024** (otros sujetos obligados): **15 días corridos** desde
     la conclusión, con tope de **150 días** desde la operación; **48 horas**
     para Financiamiento del Terrorismo.
   - El ROS debe ser **fundado**: describe las razones por las que la operación
     reviste ese carácter. No es un formulario en blanco.
4. **Umbrales de reporte sistemático (F6, F8):**
   - **Proveedores de Servicios de Activos Virtuales** (Res. UIF 49/2024):
     reporte mensual de altas y bajas de clientes y de operaciones **≥ 6 SMVM**.
   - **Plataformas electrónicas ante ARCA (F8):** declaración jurada informativa
     mensual de cuentas; desde el período fiscal **04/2026** se informa **la
     totalidad de las cuentas** de la plataforma (ingresos, egresos y saldo
     final) cuando los ingresos o egresos totales o el saldo final Reachen
     **$50.000.000** (persona humana) o **$30.000.000** (persona jurídica).

**Implicancia para Presto (O5):** en el MVP, Presto es una plataforma que
**moviliza fondos de terceros** (el prestamista y el deudor). Aunque hoy los
depósitos sean simulados, la estructura ya es la de un sujeto obligado en el
plazo. El mínimo viable razonable es: (a) KYC obligatorio ya implementado,
(b) registro de operaciones inusuales con los campos del art. 32, (c) umbral de
monitoreo por velocidad/estructuración, (d) un **registro de operaciones** y la
conservación de los datos, y (e) el procedimiento ROS con el plazo más corto
(24 h de la Res. 56/2024) por ser el más exigente. **[a validar con el
profesional que defina el procedimiento]**

---

## 5. Información al usuario en el crédito (F3, F4, F5)

La **Ley 24.240, art. 36** obliga a consignar de modo claro, **bajo pena de
nulidad**, en las operaciones de crédito para consumo:

- b) el precio al contado;
- c) el importe a desembolsar inicialmente y el **monto financiado**;
- d) la **tasa de interés efectiva anual**;
- e) el **total de los intereses a pagar o el costo financiero total**;
- f) el **sistema de amortización** del capital y la cancelación de los
  intereses;
- g) la **cantidad, periodicidad y monto** de los pagos;
- h) los **gastos extras, seguros o adicionales**, si los hubiera.

Además: si se omite la tasa, la obligación de pagar intereses se ajusta a la
**tasa pasiva anual promedio del mercado** difundida por el BCRA.

La **Resolución 12/2024** (art. 2.b) exige que la **publicidad** de precios
financiados incluya: anticipo, cantidad y monto de las cuotas, **tasa de
interés efectiva anual**, **costo financiero total** y gastos extras, seguros
y adicionales.

El BCRA (F3) define el **CFT** como el que resulta de la **tasa de interés, las
comisiones y los cargos** vigentes al momento de la contratación, indicando si
esos conceptos pueden modificarse; y fija el tope de aplicar, como máximo, el
CFT, la tasa promedio de depósitos a plazo fijo de 30 a 59 días informada por el
BCRA si la documentación no incluye la tasa y/o el CFT.

**Implicancia para Presto (O6):**

1. El art. 36.e) admite **"el total de los intereses a pagar"** *o* el CFT:
   mientras el producto **no tenga comisiones, seguros ni gastos extra**, el
   total de intereses cumple la/info exigida. **Hoy Presto no cobra comisiones
   ni seguros**: por eso **no hay CFT que exponer**.
2. En cuanto se agregue **cualquier comisión** (por ejemplo, una comisión de
   apertura o un fee de la plataforma), el CFT pasa a ser **obligatorio** y debe
   incluirse en la comparación **y** en la publicidad.
3. Falta hoy exponer la **tasa de interés efectiva anual** (art. 36.d): el
   modelo guarda la **TNA**. Se resuelve exponiendo la **TEA equivalente** en
   la comparación de ofertas y en el préstamo.
4. El "costo total" que ya devuelve `matching.compare_offers` es
   **capital + interés**, **no** es el CFT: la API lo documenta como
   `total_cost` y el frontend lo muestra con esa etiqueta.

---

## 6. Resumen de conclusiones

| # | Conclusión | Decisión que habilita |
|---|---|---|
| C1 | Presto **no es entidad financiera**: no puede emitir CDBC ni garantizar el capital de un plazo fijo | O2, O3 |
| C2 | Los fondos de los usuarios viven en una **cuenta segregada en el proveedor** (banco/PSP) y **no están cubiertos por el SGD** | O2 |
| C3 | El "plazo fijo" del MVP es una **promesa matemática de Presto**, con TNA variable y sin garantía de capital | O3 |
| C4 | El producto de **saldo remunerado** (interés sobre el capital ingressado, como pide el cliente) es un producto **del banco/PSP**, no de Presto: Presto lo muestra y lo liquida, no lo capta | O2, O3 |
| C5 | El CFT solo es exigible cuando hay **comisiones o gastos extra**; hoy Presto no los tiene → se expone **interés total** y **costo total**, con etiqueta propia | O6 |
| C6 | Hay que exponer la **TEA** además de la TNA (art. 36.d) | O6 |
| C7 | El proveedor de pagos debe ser un **PSP regulado** que separe los fondos y entregue saldos conciliables | O1 |
| C8 | PLA/FT mínimo: registro de operaciones inusuales, umbral de monitoreo, ROS en 24 h, conservación 10 años | O5 |

---

## 7. Qué falta y quién lo tiene que resolver

| Tema | Responsable | Estado |
|---|---|---|
| Validación legal de este documento y del procedimiento PLA/FT | Cliente + profesional | **[a validar]** |
| Definición del contrato con el proveedor (O1): saldos, liquidaciones, webhooks firmados | Cliente + proveedor | abierto → ADR 0008 |
| Cuenta segregada y condiciones de la cuenta del proveedor | Cliente + banco/PSP | abierto → ADR 0008/0009 |
| Rol de Presto ante la CNV si en el futuro se captan fondos de terceros para invertir | Profesional | **[a validar]** — no está en el alcance del MVP |
| Comisiones o seguros del producto: si se agregan, el CFT pasa a ser obligatorio | Cliente | sin comisiones por ahora (O6) |
| Umbral de operación inusual y responsable de compliance | Cliente + profesional | definido en el ADR 0011, **[a validar]** |

## 8. Referencias

- BCRA, Comunicación "A" 8407: <https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A8407.pdf>
- BCRA, TO del Sistema de Seguro de Garantía de los Depósitos:
  <https://www.bcra.gob.ar/archivos/Pdfs/Texord/t-seggar.pdf>
- BCRA, Comunicación "A" 6541/2018:
  <https://www.boletinoficial.gob.ar/detalleAviso/primera/190002/20180816>
- BCRA, Comunicación "A" 7645: <https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A7645.pdf>
- Ley 24.240 de Defensa del Consumidor, art. 36:
  <https://servicios.infoleg.gob.ar/infolegInternet/anexos/395000-399999/398486/norma.htm>
- Resolución 12/2024 de la Secretaría de Industria y Comercio (publicidad):
  <https://www.boletinoficial.gob.ar/detalleAviso/primera/303141/20240429>
- UIF, consultas sobre ROS: <https://www.argentina.gob.ar/uif/preguntas-frecuentes-generales-uif/consultas-acerca-de-reportes-de-operaciones-rsm-rsa-ros-la-ft-fp>
- UIF, Resolución 56/2024: <https://www.boletinoficial.gob.ar/detalleAviso/primera/305169/20240326>
- UIF, Resolución 43/2024: <https://servicios.infoleg.gob.ar/infolegInternet/anexos/395000-399999/398486/norma.htm>
- ARCA, regímenes informativos de plataformas electrónicas:
  <https://www.afip.gob.ar/economia-digital/activos-virtuales-y-no-virtuales/servicios-administracion-intermediacion/informacion.asp>
