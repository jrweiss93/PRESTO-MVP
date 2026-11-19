# Guía de código — apps/ledger/migrations

Historial de esquema de la app. Las migraciones se generan con Django y no se editan a mano salvo una corrección puntual.

## Archivos

| Archivo | Qué hace |
|---|---|
| `0001_initial.py` | Tablas de cuentas, transacciones y asientos. |
| `0002_ledger_triggers.py` | Triggers de doble entrada e inmutabilidad. |
| `0003_account_ledger_account_currency_ars_or_usd_and_more.py` | Constraints de moneda y saldo. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
