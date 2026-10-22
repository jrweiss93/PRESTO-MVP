# ADR 0009 — Los fondos viven en una cuenta segregada del proveedor; Presto no es custodio

- **Estado:** aceptado (decisión de producto tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** `ledger`, `investments`, `payments`, copy del producto
- **Resuelve:** O2 — marco regulatorio de la custodia de fondos

## Contexto

O2 tenía que definir si Presto es una **plataforma de inversión** o un
**agente de custodia**, qué entidad regulada respalda los saldos, si los
fondos van a una cuenta segregada en un banco o a una cuenta del proveedor, y
si Presto puede **llamarse "custodia"** a lo que hace hoy.

El modelo de datos ya tiene el equivalente: `Account.kind` con tres valores
(`user_wallet`, `custody`, `system`), donde `custody` es la **cuenta de
contrapartida** de los depósitos y retiros.

Base normativa: `docs/regulatorio-bcra.md` (F1, F2 y conclusiones C1, C2, C4).

- Presto **no es una entidad financiera**: no tiene licencia del BCRA, no
  integra el Sistema de Seguro de Garantía de los Depósitos (SGD) y **no puede
  emitir un CDBC** (certificado de depósito a plazo fijo).
- El SGD (Com. "A" 8407, vigente desde 01/04/2026) cubre hasta **$50.000.000
  por persona, cuenta y depósito** en cada entidad financiera, y **excluye**
  los depósitos en otros intermediarios, los plazos fijos de títulos valores y
  los captados a tasa por encima de 1,3× la tasa de referencia (o tasa + 5
  puntos porcentuales, la mayor).

## Decisión

1. **Presto no es custodio ni entidad financiera.** El backend **no** ofrece
   un producto con la palabra "custodia": el nombre visible del producto es
   **"saldo en Presto"** / **"fondos en la cuenta de Presto"**.
2. **Los fondos de todos los usuarios están en una cuenta segregada de Presto
   en el proveedor** (ADR 0008), separada por moneda. El saldo del usuario en
   el ledger es un **derecho contractual** sobre esa cuenta, no un depósito en
   entidad financiera.
3. **La palabra "custodia" se conserva solo como nombre técnico interno** del
   `Account.kind = custody`, por no romper el ledger, las migraciones ni los
   tests. En cualquier texto de cara al usuario (API, emails, web, al pitch)
   se usa **"cuenta de Presto"** o **"cuenta segregada"**. Queda anotado en el
   código con un comentario que apunta a este ADR.
4. **No se promete garantía de capital** en ningún producto ni en la web, y no
   se usa la leyenda del SGD ("cuenta con garantía de hasta $50.000.000"): no
   aplica. Si alguna vez el proveedor ofreciera una **cuenta a nombre del
   usuario en un banco**, se puede agregar la leyenda correspondiente; hoy no
   aplica.
5. **El "saldo remunerado"** (la "dinámica de Mercado Pago" que pidió el
   cliente: interés sobre el capital ingressado) es un producto **del
   proveedor**, no de Presto: Presto lo muestra y lo liquida, no lo capta ni
   lo garantiza. Se modela en `investments` como producto **sin garantía de
   capital** (ADR 0010).
6. **No se capta dinero de terceros para invertir.** El marketplace de préstamos
   mueve dinero entre usuarios (préstamo) y|Presto no invierte ese money por su
   cuenta. Si en el futuro Presto quisiera captar fondos para invertirlos,
   eso cae en el ámbito de la **CNV** (agente de servicios de inversión) y
   requiere registro, capital mínimo y proceso propio: **queda fuera del
   alcance** y se documenta como **[a validar]**.
7. **El saldo del ledger es la fuente de verdad** (AGENTS §6): el saldo del
   proveedor es un dato de conciliación, no la fuente para el usuario.

## Consecuencias

**Positivas**

- Se evita una promesa que no se puede cumplir (garantía de capital).
- El copy del producto es honesto y no necesita cambios legales para funcionar.
- La separación de fondos del proveedor (ADR 0008) es un requisito verificable.

**Negativas / riesgos asumidos**

- El usuario no tiene la protección del SGD sobre su saldo en Presto: hay que
  decirlo de forma clara en la web y en los términos.
- El nombre técnico `custody` convive con el nombre de producto "cuenta de
  Presto": hay que cuidar el copy en serializers, emails y textos.
- Presto asume el riesgo de insolvencia del proveedor y de la propia
  plataforma: es el riesgo de negocio del modelo P2P.

**Pendiente**

- Validación legal del modelo (cuenta segregada, contrato con el proveedor,
  Consumer law).
- Términos y condiciones y política de privacidad: no existen todavía.
- Definir el plazo de atención de un retiro en el contrato con el proveedor.
