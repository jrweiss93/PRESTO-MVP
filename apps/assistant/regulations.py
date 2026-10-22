"""Contenido curado del marco regulatorio del asistente.

Es información general con enlaces a las fuentes oficiales. **No es
asesoramiento legal**: la app lo muestra con ese aviso y el texto vive acá
(versionado con el código), no se genera con un modelo.
"""

DISCLAIMER = (
    'Información general con fines educativos: no es asesoramiento legal, '
    'contable ni de inversión. Antes de operar, consultá a un profesional y '
    'las normas vigentes en los organismos oficiales.'
)

CATEGORIES = [
    {'id': 'prestamos', 'label': 'Préstamos entre particulares'},
    {'id': 'entidades', 'label': 'Entidades y captación de fondos'},
    {'id': 'inversion', 'label': 'Inversión y oferta pública'},
    {'id': 'consumidor', 'label': 'Derechos del consumidor'},
    {'id': 'antilavado', 'label': 'Prevención de lavado (PLA/FT)'},
    {'id': 'general', 'label': 'General'},
]

REGULATIONS = [
    {
        'id': 'mutuo-entre-particulares',
        'category': 'prestamos',
        'title': 'Préstamo entre particulares (mutuo)',
        'summary': (
            'Prestar dinero de forma aislada entre personas está permitido por el '
            'Código Civil y Comercial. Lo que cambia el encuadre es la habitualidad '
            'y la captación de fondos del público.'
        ),
        'key_points': [
            'El mutuo es un contrato: conviene documentar monto, moneda, plazo y tasa.',
            'Si el préstamo se hace de forma profesional y reiterada, puede encuadrar '
            'como actividad financiera.',
            'No se puede captar dinero del público sin autorización del BCRA.',
        ],
        'norms': [
            {'code': 'CCyC arts. 1520 y ss.', 'note': 'Contrato de mutuo.'},
            {'code': 'CCyC art. 768', 'note': 'Intereses y tasa de interés.'},
        ],
        'links': [
            {
                'label': 'Código Civil y Comercial (InfoLeg)',
                'url': 'https://www.argentina.gob.ar/normativa/nacional/ley-26994-235975',
            }
        ],
        'applies_to': 'Personas que prestan o piden dinero a otra persona.',
    },
    {
        'id': 'entidades-financieras',
        'category': 'entidades',
        'title': 'Entidades financieras y captación de fondos',
        'summary': (
            'La Ley 21.526 regula a las entidades financieras. Recibir depósitos o '
            'captar fondos del público como negocio requiere autorización del BCRA.'
        ),
        'key_points': [
            'Captar fondos del público sin autorización está prohibido.',
            'Los proveedores no financieros de crédito (PNFC) tienen un régimen propio.',
            'Una plataforma que intermedia masivamente puede quedar alcanzada.',
        ],
        'norms': [
            {'code': 'Ley 21.526', 'note': 'Entidades financieras.'},
            {'code': 'Comunicaciones BCRA', 'note': 'Régimen de PNFC y demás sujetos.'},
        ],
        'links': [
            {'label': 'BCRA', 'url': 'https://www.bcra.gob.ar/'},
        ],
        'applies_to': 'Plataformas que reciben dinero de usuarios o intermedian crédito.',
    },
    {
        'id': 'oferta-publica-cnv',
        'category': 'inversion',
        'title': 'Oferta pública de inversión (CNV)',
        'summary': (
            'Ofrecer al público valores negociables o instrumentos de inversión '
            'para financiar créditos puede requerir autorización de la CNV o un '
            'vehículo autorizado, como un fideicomiso financiero.'
        ),
        'key_points': [
            'La Ley 26.831 regula el mercado de capitales y la oferta pública.',
            'No toda inversión es oferta pública, pero la captación masiva sí puede serlo.',
            'El plazo fijo de una plataforma no es un depósito bancario ni está garantizado.',
        ],
        'norms': [
            {'code': 'Ley 26.831', 'note': 'Mercado de capitales.'},
            {'code': 'Ley 24.441 / CCyC', 'note': 'Fideicomisos.'},
        ],
        'links': [
            {'label': 'CNV', 'url': 'https://www.argentina.gob.ar/cnv'},
        ],
        'applies_to': 'Productos de inversión ofrecidos al público.',
    },
    {
        'id': 'tasas-y-costo',
        'category': 'consumidor',
        'title': 'Tasas, intereses y costo total',
        'summary': (
            'El costo de un préstamo incluye capital e intereses (y comisiones, si '
            'las hay). La información tiene que ser clara y no puede esconder el '
            'costo real en la letra chica.'
        ),
        'key_points': [
            'La tasa nominal anual (TNA) no es lo mismo que el costo financiero total (CFT).',
            'En relaciones de consumo rigen deberes de información y trato digno.',
            'Las cláusulas abusivas pueden declararse nulas.',
        ],
        'norms': [
            {'code': 'Ley 24.240', 'note': 'Defensa del consumidor.'},
            {'code': 'CCyC art. 768', 'note': 'Intereses.'},
        ],
        'links': [
            {
                'label': 'Ley 24.240 (InfoLeg)',
                'url': 'https://www.argentina.gob.ar/normativa/nacional/ley-24240-6383',
            }
        ],
        'applies_to': 'Usuarios que toman un préstamo o contratan un producto.',
    },
    {
        'id': 'pla-ft',
        'category': 'antilavado',
        'title': 'Prevención de lavado y financiamiento del terrorismo',
        'summary': (
            'La Ley 25.246 y la UIF exigen identificar clientes, monitorear '
            'operaciones y reportar las sospechosas. El KYC es la base de ese '
            'esquema.'
        ),
        'key_points': [
            'Hay que identificar al cliente y, cuando corresponda, al beneficiario final.',
            'Las operaciones sospechosas se reportan a la UIF (ROS).',
            'La documentación y los registros se conservan por plazos legales.',
        ],
        'norms': [
            {'code': 'Ley 25.246', 'note': 'Encubrimiento y lavado de activos.'},
            {'code': 'Resoluciones UIF', 'note': 'Sujetos obligados y reportes.'},
        ],
        'links': [
            {'label': 'UIF', 'url': 'https://www.argentina.gob.ar/uif'},
        ],
        'applies_to': 'Plataformas que reciben y mueven dinero de terceros.',
    },
    {
        'id': 'consumidor',
        'category': 'consumidor',
        'title': 'Derechos del consumidor financiero',
        'summary': (
            'Además de la Ley 24.240, el usuario tiene derecho a recibir '
            'información veraz, clara y gratuita sobre las condiciones del '
            'producto que contrata.'
        ),
        'key_points': [
            'El proveedor debe informar precio, costo y condiciones antes de contratar.',
            'La publicidad forma parte del contrato y obliga.',
            'El usuario puede reclamar ante defensa del consumidor.',
        ],
        'norms': [
            {'code': 'Ley 24.240', 'note': 'Defensa del consumidor.'},
            {'code': 'CCyC arts. 1092 y ss.', 'note': 'Contratos de consumo.'},
        ],
        'links': [
            {
                'label': 'Defensa del consumidor',
                'url': 'https://www.argentina.gob.ar/produccion/defensadelconsumidor',
            }
        ],
        'applies_to': 'Todos los usuarios de la plataforma.',
    },
]


def list_regulations(category: str | None = None, q: str | None = None) -> list[dict]:
    """Lista las fichas regulatorias, filtrando por categoría y texto.

    Args:
        category: id de categoría, o None para todas.
        q: texto a buscar en título, resumen, puntos y normas.

    Returns:
        La lista de fichas que cumplen los filtros.
    """
    items = REGULATIONS
    if category:
        items = [item for item in items if item['category'] == category]
    if q:
        needle = q.strip().lower()
        items = [
            item
            for item in items
            if needle in item['title'].lower()
            or needle in item['summary'].lower()
            or any(needle in point.lower() for point in item['key_points'])
        ]
    return items


def get_regulation(regulation_id: str) -> dict | None:
    """Devuelve una ficha por su id, o None si no existe."""
    return next((item for item in REGULATIONS if item['id'] == regulation_id), None)
