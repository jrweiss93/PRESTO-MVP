"""Estado de cumplimiento y recordatorios de revisión legal.

Este módulo es la **única fuente de verdad** de lo que todavía necesita una
validación profesional. Vive en `core` (la app transversal) para que ninguna
app de dominio dependa de otra, y lo consumen:

- el endpoint público `GET /api/v1/meta/`, que lo expone como
  `compliance.legal_review_pending` para que el frontend pueda mostrar un
  recordatorio;
- el system check `legal.W001`, que avisa mientras el pendiente siga abierto.

El detalle largo de cada punto está en `docs/regulatorio-bcra.md` y en los ADR;
acá solo queda el resumen accionable.

**Acknowledgement**: el pendiente se da por revisado cuando el equipo pone
`LEGAL_REVIEW_ACKNOWLEDGED=1` en el entorno. La lista de puntos **no** depende
de ese flag: sigue siendo la foto de lo que hay que revisar, para que el
recordatorio no se pierda.
"""

from django.conf import settings

#: Puntos que necesitan validación legal o profesional antes de producción.
PENDING_REVIEW_ITEMS = (
    {
        'id': 'pla_ft',
        'label': 'PLA/FT: umbrales de reporte de operaciones sospechosas, screening y responsable.',
        'doc': 'docs/regulatorio-bcra.md',
    },
    {
        'id': 'custodia',
        'label': 'Encuadre de custodia: cuentas segregadas y cuentas de Presto en el proveedor.',
        'doc': 'docs/adr/0009-cuenta-segregada-y-no-custodia.md',
    },
    {
        'id': 'plazo_fijo',
        'label': 'Copy del plazo fijo: advertencia de que no hay garantía de capital.',
        'doc': 'docs/adr/0010-rendimiento-sin-garantia-de-capital.md',
    },
    {
        'id': 'cft',
        'label': 'Costo financiero total (CFT) cuando el proveedor de pagos cobre comisiones.',
        'doc': 'docs/adr/0012-costo-total-y-cft.md',
    },
    {
        'id': 'cnv',
        'label': 'Registro del agente ante la CNV y encuadre regulatorio final.',
        'doc': 'docs/regulatorio-bcra.md',
    },
)


def legal_review_acknowledged() -> bool:
    """Dice si el equipo ya tomó conocimiento del pendiente legal.

    Returns:
        True si `LEGAL_REVIEW_ACKNOWLEDGED` está activo en el entorno.
    """
    return bool(settings.LEGAL_REVIEW_ACKNOWLEDGED)


def legal_review_pending() -> bool:
    """Dice si la revisión legal sigue pendiente.

    Returns:
        True mientras nobody-la haya marcado como revisada.
    """
    return not legal_review_acknowledged()


def compliance_status() -> dict:
    """Devuelve el estado de cumplimiento que se expone en `/api/v1/meta/`.

    Returns:
        Un diccionario con `legal_review_pending`, `acknowledged` y la lista
        de puntos pendientes (`items`).
    """
    return {
        'legal_review_pending': legal_review_pending(),
        'acknowledged': legal_review_acknowledged(),
        'items': [dict(item) for item in PENDING_REVIEW_ITEMS],
    }
