# ADR 0012 — "Costo total" no es el CFT: se expone interés total, costo total y TEA

- **Estado:** aceptado (decisión de producto tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** apps `matching`, `loans`, `core`
- **Resuelve:** O6 — si el cliente quiere el costo financiero total en la comparación

## Contexto

O6 tenía que definir si el cliente quiere el **costo financiero total**
(capital + interés) en la comparación de ofertas, y si ese CFT debe
compararse contra el costo de otras alternativas del usuario (crédito, plazo
fijo, efectivo).

Estado actual del código:

- `matching.selectors.compare_offers` ya devuelve `installment`, `total_interest`
  y `total_cost` (calculados en `core/money.py`: `french_installment`,
  `french_total_interest`, `french_total_cost`).
- `total_cost` = **capital + interés** pagados. **No** es el CFT.
- El modelo guarda **TNA** (tasa nominal anual), no la TEA.

Decisión previa documentada en el contrato del frontend
(`PRESTOFRONT\PROYECTO_FRONT.md` §4.2, confirmada el 2026-10-21):

> *"**No existe CFT** (costo financiero total) por ahora. La comparación de
> ofertas devuelve **cuota, interés total y costo total**: mostrá esos tres. No
> presentes 'costo total' como si fuera el CFT. El CFT se agrega si el cliente
> lo pide."*

Base normativa: `docs/regulatorio-bcra.md` (F3, F4, F5 y conclusiones C5, C6).

- **Ley 24.240 art. 36**: en el crédito para consumo hay que consignar de modo
  claro, **bajo pena de nulidad**: precio al contado, importe a desembolsar y
  monto financiado, **tasa de interés efectiva anual**, **total de los intereses
  a pagar o el costo financiero total**, sistema de amortización, cantidad,
  periodicidad y monto de los pagos, y gastos extras, seguros o adicionales.
  O sea: el art. 36.e) admite **"el total de los intereses a pagar"** *o* el
  CFT.
- **BCRA Com. "A" 7645, punto 3.2.4**: el CFT se calcula con la tasa de
  interés, **las comisiones y los cargos** vigentes al momento de la
  contratación, indicando si pueden modificarse; y el tope de aplicar, como
  máximo, el CFT, la tasa promedio de depósitos a plazo fijo de 30 a 59 días
  que informa el BCRA si la documentación no incluye la tasa y/o el CFT.
- **Resolución 12/2024, art. 2.b)**: la publicidad de precios financiados
  incluye la **tasa de interés efectiva anual** y el **costo financiero total**.

## Decisión

1. **No se agrega un campo `cft` a la API.** Se mantiene lo decidido el
   2026-10-21: la comparación devuelve **cuota, interés total y costo total**,
   y `total_cost` se documenta como **capital + interés**, nunca como CFT.
2. **Motivo:** hoy Presto **no cobra comisiones, seguros ni gastos extra**: el
   CFT y el interés total **son el mismo número**, y el art. 36.e) se cumple
   mostrando el **total de los intereses a pagar**. El CFT pasa a ser
   **obligatorio en el momento en que el producto incorpore cualquier
   comisión**, y en ese momento se agrega el campo.
3. **Se agrega la TEA (tasa de interés efectiva anual)**, que hoy falta y que
   el art. 36.d) exige: la comparación de ofertas y el detalle del préstamo
   devuelven `effective_annual_rate`, en porcentaje, calculada en
   `core.money.effective_annual_rate` (la tasa mensual equivalente
   `(1 + i)^12 - 1`). La **TNA** sigue siendo el dato que se guarda y el que
   define la amortización.
4. **Los campos no se renombran.** El contrato con el frontend ya está
   generado desde el esquema; `total_interest` y `total_cost` no cambian de
   nombre ni de significado. Lo que cambia es que ahora el esquema **documenta
   explícitamente** qué es cada uno.
5. **No se compara el CFT contra otras alternativas** (efectivo, plazo fijo,
   otro crédito) en esta versión: no hay datos de mercado ni una fuente de
   tasas de referencia en el backend, y una comparación de esa naturaleza
   necesita un modelo que el cliente no pidió.
6. **El bloque que falta para cerrar el art. 36** es la documentación de la
   operación (el "documento" del contrato), que hoy es la pantalla de
   condiciones del frontend más el snapshot inmutable de la oferta aceptada
   (`OfferTermsSnapshot`). Los campos que ya están en el snapshot: monto,
   moneda, TNA, plazo, requisitos, installment, total_interest, total_cost.

## Consecuencias

**Positivas**

- La API sigue siendo la que el frontend ya conoce: no hay que regenerar
  tipos por un campo nuevo que rompa la pantalla.
- El dato que la ley exige (interés total y TEA) queda expuesto y documentado.
- Cuando haya comisión, agregar el CFT es un campo nuevo, no un cambio de
  significado de los existentes.

**Negativas / riesgos asumidos**

- **El nombre `total_cost` es ambiguo** para un usuario final: se mitiga
  documentando el esquema ("capital + interés") y con el copy del frontend
  ("total a pagar"), nunca con la palabra CFT.
- **La TEA expuesta es la equivalente de la tasa mensual**, no la TEA que
  resulta del flujo de caja real de la amortización francesa: se documenta así
  en el esquema.
- Si el cliente agrega una comisión, hay que tocar la API (campo `cft`) y el
  frontend: el cambio no es trivial pero es acotado.

**Pendiente**

- Confirmar con el cliente que no habrá comisión de apertura ni seguros en el
  MVP (mientras siga así, el CFT no hace falta).
- Definir el documento contractual del crédito (lo que el art. 36 exige que se
  consigne).
- Si aparece una comisión: agregar `cft` a `core.money`, a la comparación, a
  los reportes y al copy del frontend.
