# Guía de código — apps (backend)

Cada carpeta es una app de Django con una responsabilidad de dominio. La regla es entrar por `services.py`/`selectors.py`, nunca por modelos de otra app.

## Apps

| App | Qué hace |
|---|---|
| `core` | Utilidades transversales que no dependen de ninguna app de dominio. Acá viven el modelo base, el dinero, los errores HTTP y los endpoints operativos. |
| `identity` | Usuarios, login JWT, perfiles de Presto, KYC, biometría simulada, cuentas de respaldo y cierre de cuenta. |
| `ledger` | Libro mayor de doble entrada: cuentas, transacciones, asientos, saldos, idempotencia, bloqueos y reversos. |
| `payments` | Intención de pago, webhooks y adaptadores de proveedor. El saldo real se mueve siempre en el ledger. |
| `offers` | Ofertas de préstamo publicadas por prestamistas: monto, moneda, TNA, plazo, requisitos y estado. |
| `matching` | App de solo lectura para buscar y comparar ofertas sin crear préstamos ni modificar estado. |
| `loans` | Préstamos aceptados, snapshot de condiciones, cronograma de cuotas, pago, cancelación, archivado, chat y reseñas. |
| `investments` | Productos de plazo fijo y posiciones de inversión, con apertura, interés simple y liquidación idempotente. |
| `budgets` | Categorías, presupuestos y clasificación de gastos. El importe se deriva del ledger; no se duplica. |
| `reports` | Reportes de solo lectura y exportación CSV; no tiene modelos ni escribe estado. |
| `notifications` | Avisos in-app y por email, preferencias y reintentos. No guarda datos financieros. |
| `assistant` | Presti: mercado, noticias, marco legal curado y chat por reglas, sin LLM. |
| `demo` | Datos de demostración y comandos de siembra. No tiene modelos propios. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
