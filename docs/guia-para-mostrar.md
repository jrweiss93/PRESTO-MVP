# Presto — guía para mostrar la demo

**Para explicar sin tecnicismos.**

## En una frase

Presto es una aplicación donde una persona puede **guardar y mover su dinero**,
**pedir un préstamo**, **prestar**, **invertir** y **organizar sus gastos**, todo
en un mismo lugar y en pesos o dólares.

## Las cuatro ideas para transmitir

1. **Una billetera con dos compartimentos.** El usuario tiene saldo en pesos y
   en dólares, separados. No se mezclan ni se convierten solos.
2. **Préstamos entre personas.** Quien tiene dinero puede ofrecer prestarlo.
   Quien lo necesita, lo pide y lo devuelve en cuotas.
3. **Inversiones simples.** Quien tiene saldo puede dejarlo un tiempo a cambio
   de un interés, con una fecha de vencimiento clara.
4. **Todo queda registrado.** Cada movimiento se anota dos veces, como en un
   libro contable: si sale de un lado, entra en el otro. Si alguien toca dos
   veces el botón por error, el sistema no lo cobra dos veces.

## Antes de empezar

- **Link:** <https://presto-mvp-alpha.vercel.app>
- **Usuarios:** `ana@presto.demo` (prestataria), `beto@presto.demo`
  (prestamista), `carla@presto.demo` (inversora).
- **Contraseña para los tres:** `Presto123!`
- La demo usa **dinero simulado**. No se mueve plata real.
- Si la página tarda en abrir, esperá **30–60 segundos**: la demo se suspende
  cuando nadie la usa y la primera visita la despierta.

## Guion de 5 minutos

### 1. La puerta de entrada (30 segundos)

**Hacé:** abrí el link.

**Decí:** “Esta es la página de inicio. Abajo están las cuentas de prueba y el
aviso de que el dinero es simulado, para que nadie se confunda.”

### 2. Entrar como Ana (40 segundos)

**Hacé:** iniciá sesión con `ana@presto.demo`.

**Decí:** “Ana ya tiene su identidad verificada. Acá ve su saldo, su préstamo
activo y la próxima cuota que tiene que pagar.”

### 3. La billetera y los pagos (60 segundos)

**Hacé:** entrá a **Billetera** y después a **Pagos**.

**Decí:** “La billetera muestra los pesos y los dólares por separado, con todos
los movimientos. Desde Pagos se puede depositar, retirar o transferir a otra
persona. En la demo, el depósito es simulado.”

### 4. El marketplace de préstamos (60 segundos)

**Hacé:** entrá a **Marketplace**.

**Decí:** “Acá están las ofertas de personas que quieren prestar. Se puede
filtrar por monto, plazo y tasa, y comparar cuánto termina costando cada opción
antes de aceptar.”

### 5. Un préstamo y su cuota (60 segundos)

**Hacé:** entrá a **Préstamos** y abrí el préstamo de Ana. Pagá una cuota.

**Decí:** “Cuando Ana aceptó la oferta, el sistema guardó las condiciones y armó
el plan de cuotas. Al pagar, se descuenta el saldo y la cuota queda marcada. No
se puede pagar dos veces por error.”

### 6. Una inversión (45 segundos)

**Hacé:** cerrá sesión, entrá como `carla@presto.demo` y abrí **Inversiones**.

**Decí:** “Carla puso parte de su saldo en un plazo fijo. Acá ve el monto, la
tasa, el interés estimado y la fecha en que recupera el dinero.”

### 7. Los presupuestos (30 segundos)

**Hacé:** entrá a **Presupuestos**.

**Decí:** “El usuario puede poner un límite mensual por categoría, por ejemplo
comida o transporte. La app le avisa cuando se acerca al límite.”

### 8. Presti, el asistente (45 segundos)

**Hacé:** entrá a **Presti** y preguntá “¿cuál es mi saldo?” o “¿cómo está el
dólar?”.

**Decí:** “Presti responde con datos reales de la cuenta y del mercado. No
inventa: si no entiende una pregunta, ofrece opciones. También explica el marco
legal en palabras simples.”

### 9. Cierre (20 segundos)

**Decí:** “Todo esto es una demostración con dinero simulado. El siguiente paso
es conectar los pagos reales y completar la verificación de identidad con
documentos.”

## Preguntas que te pueden hacer

| Pregunta | Respuesta simple |
|---|---|
| ¿Es un banco? | No. Es una aplicación de finanzas entre personas. En esta etapa es una demo y no mueve dinero real. |
| ¿Se puede usar con plata de verdad? | Todavía no. Falta conectar el proveedor de pagos y cerrar el marco legal. |
| ¿De dónde sale el interés? | Del préstamo que paga la persona que pidió el dinero. La aplicación muestra el costo antes de aceptar. |
| ¿Qué pasa si alguien no paga? | En la demo la cuota queda vencida y el préstamo en mora. En producción habría que definir cobranza y garantías. |
| ¿Es seguro? | La demo usa datos de prueba. En producción hay inicio de sesión seguro, verificación de identidad y un registro de cada movimiento. |
| ¿El asistente es inteligencia artificial? | No es un chat que inventa. Responde con reglas, datos de la cuenta y textos legales revisados. |
| ¿Quién puede pedir prestado? | Una persona con identidad verificada y con ofertas disponibles en el marketplace. |
| ¿Cuánto falta para lanzarlo? | Depende de pagos, verificación de identidad y legales. La demo ya muestra el circuito completo. |

## Qué no prometer

- **No** decir que ya se puede depositar dinero real.
- **No** prometer rendimientos garantizados: el interés es un ejemplo.
- **No** decir que está aprobado por un banco o por el Estado.
- **No** cargar datos personales reales en la demo.
- Si algo falla, no improvisar: decir “es una demo” y seguir con otra pantalla.

## Si algo no anda

- **No entra el login:** verificá el email y que la contraseña sea `Presto123!`.
- **Tarda:** esperá un minuto; la demo se despierta.
- **Una pantalla está vacía:** volvé al panel y entrá de nuevo.
- **El asistente no responde:** puede ser el mercado externo; probá con “¿cuál es
  mi saldo?”.

## Para cerrar la presentación

“Presto ya tiene el circuito completo funcionando: billetera, préstamos,
inversiones, presupuestos, reportes y un asistente que explica. Lo que sigue es
conectar los pagos reales y completar la parte legal y de identidad.”

**Demo:** <https://presto-mvp-alpha.vercel.app>
**Repositorio y documentación:** <https://github.com/jrweiss93/PRESTO-MVP>
