# Guía de código — apps/loans

Préstamos aceptados, snapshot de condiciones, cronograma de cuotas, pago, cancelación, archivado, chat y reseñas.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Consulta de préstamos, snapshot y cuotas; botón para marcar vencidas. |
| `exceptions.py` | Errores de préstamo, cuota, transición, mensaje, reseña, cancelación y archivado. |
| `models.py` | `Loan`, `OfferTermsSnapshot`, `Installment`, `LoanMessage` y `LoanReview`. |
| `selectors.py` | Préstamos por parte, mensajes, reseñas, reputación, cuotas, vencidas y desglose. |
| `serializers.py` | Snapshot, cuota, préstamo, detalle, mensajes, reseñas, reputación y aceptación. |
| `services.py` | Cronograma, aceptación atómica, pago, estados, vencimiento, chat, reseñas, cancelación y archivado. |
| `signals.py` | `loan_created` e `installment_paid` para notificaciones. |
| `tasks.py` | Marcar vencidos y avisar cuotas por vencer/vencidas; delegan en services. |
| `urls.py` | Préstamos, detalle, cancelar, archivar, mensajes, reseña, reputación y pago de cuota. |
| `views.py` | Listado, detalle, cancelación, archivado, chat, reseña, reputación y pago. |
| `management/commands/mark_overdue_loans.py` | Ejecuta `mark_overdue` desde consola. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Aceptación, cuotas, snapshot, concurrencia, respaldo, mensajes, reseñas, cancelación y tareas. |
| `migrations/` | Préstamos/cuotas, ledger de cuotas, chat, reseñas y cancelación/archivado. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
