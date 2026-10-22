# ADR 0010 — Los plazos fijos no tienen garantía de capital: Presto asume el riesgo

- **Estado:** aceptado (decisión de producto tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** app `investments`
- **Resuelve:** O3 — si Presto asume el rendimiento de los plazos fijos

## Contexto

O3 tenía que definir si la tasa que se muestra está garantizada por Presto o
si depende del instrumento que respalda la posición, qué pasa si el rendimiento
real es menor que el prometido, si hay fondo de garantía o un spread de riesgo,
y quién asume la diferencia.

Estado actual del código (`apps/investments`):

- `InvestmentProduct` define la tasa y el plazo.
- `Position` guarda el **interés como `Decimal` fijo calculado al abrir** (no
  hay un motor que lo liquide periódicamente).

Base normativa: `docs/regulatorio-bcra.md` (C1, C3, C4). Un "plazo fijo" con
capital garantizado es un **CDBC** y solo lo puede emitir una **entidad
financiera** (o un banco con licencia). Presto no lo es.

Lo que pidió el cliente, por escrito:

- `PRESENTACIÓN DEL PROYECTO - PRESTO.docx`: *"aplicar el mismo tipo de
  dinámica que ciertas billeteras virtuales como Mercado Pago y la propia app
  del Banco, **sumando interés por monto de capital ingresado**"*.
- `PITCH\pitch.md`: *"Inversiones simuladas — plazos de 1 a 24 meses: ponés el
  monto y sabés exactamente cuánto recibís al finalizar"* y *"Fase 2 · con
  capital → pagos reales, integraciones bancarias, tarjetas, KYC"*.

## Decisión

1. **El capital de un plazo fijo en Presto NO está garantizado.** Presto es
    quien paga: la diferencia entre lo prometido y lo liquidado la asume Presto.
   Es la contrapartida de que el usuario no tiene cobertura del SGD (ADR 0009).
2. **El modelo de Presto es el "saldo remunerado"**, no el CDBC:
   - el interés se calcula **sobre el capitalIngressado** (la dinámica que pidió
     el cliente), con la misma función de interés simple que ya usa
     `investments` (`core.money.simple_interest`);
   - la **TNA es variable** y la publica Presto; se informa como **TNA anual en
     porcentaje**, igual que en los préstamos;
   - el rendimiento no depende de un instrumento de terceros: depende de que
     Presto cumpla.
3. **Se declara el riesgo en el producto.** El endpoint de productos y el
   detalle de la posición incluyen la leyenda de que **el capital no está
   garantizado** y que el rendimiento depende de Presto. El frontend la muestra
   junto a la tasa.
4. **No hay fondo de garantía ni spread de riesgo** en el MVP: el spread por
   riesgo de crédito del prestamista no está modelado (ver más abajo) y la
   diferencia la cubre el margen de la plataforma.
5. **El spread por riesgo del prestamista se resuelve en otra parte del
   modelo**: en el marketplace de préstamos, el **prestamista** es quien fija la
   TNA de su oferta y el riesgo es suyo; Presto no garantiza el pago del
   préstamo. `loans` ya tiene el estado `defaulted` y las cuotas vencidas.
6. **El interés se sigue calculando al abrir la posición** (como hoy), y la
   liquidación se hace al vencer. Cuando se sume un producto de **saldo
   remunerado diario** (interés acreditado sobre el saldo, como en una
   billetera), el cálculo pasa a ser diario y la posición tiene que tener
   fecha de origen y fecha de liquidación: es el bloque siguiente de
   `investments`.
7. **El marketing no puede decir "garantizado".** El pitch y la web tienen que
   decir **"rendimiento publicado por Presto, capital no garantizado"** o
   ninguna de las dos cosas.

## Consecuencias

**Positivas**

- El modelo es coherente con la realidad regulatoria: Presto no promete lo que
  no puede cumplir.
- Es el mismo motor de interés que ya está probado (`simple_interest`), con
  `Decimal` y redondeo en `core/money.py` (AGENTS §6).
- La diferencia con el CDBC es explícita: si más adelante el proveedor ofrece
  plazos fijos en un banco, se agrega como **producto aparte** con su propia
  leyenda, sin romper el modelo.

**Negativas / riesgos asumidos**

- **Presto tiene riesgo de balance**: si no puede pagar el rendimiento, hay
 responderle al usuario. Es un riesgo de negocio del modelo y hay que
  provisionarlo.
- El rendimiento es un **Decimal fijo al abrir**: si Presto cambia la TNA antes
  del vencimiento, la posición no cambia (queda el contrato de la apertura).
  Es lo correcto para el usuario y hay que dejarlo explícito.
- El "plazo fijo" del nombre puede confundir con un CDBC: el copy tiene que
  decir "inversión a plazo en Presto" y no "plazo fijo bancario".

**Pendiente**

- Reserva/provisión contable del rendimiento prometida.
- Producto de saldo remunerado diario (la "dinámica Mercado Pago" exacta).
- Validación legal de la leyenda y de los términos.
