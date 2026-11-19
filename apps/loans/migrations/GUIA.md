# Guía de código — apps/loans/migrations

Historial de esquema de la app. Las migraciones se generan con Django y no se editan a mano salvo una corrección puntual.

## Archivos

| Archivo | Qué hace |
|---|---|
| `0001_initial.py` | Préstamos, snapshot y cuotas. |
| `0002_installment_ledger_transaction_id_and_more.py` | Transacción del ledger en cuotas. |
| `0003_loanmessage.py` | Chat privado del préstamo. |
| `0004_loanreview.py` | Reseñas y reputación. |
| `0005_loan_borrower_archived_at_loan_cancelled_at_and_more.py` | Cancelación y archivado. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
