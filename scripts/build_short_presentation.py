"""Genera la versión corta de la presentación (8 slides).

Uso:
    python scripts/build_short_presentation.py

Salidas:
    docs/presentacion-corta.pptx
    docs/presentacion-corta.html
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_presentation import DOCS, build_html, build_pptx  # noqa: E402

DEMO_URL = 'https://presto-mvp-alpha.vercel.app'
REPO_URL = 'https://github.com/jrweiss93/PRESTO-MVP'
DEMO_USERS = 'ana@presto.demo  ·  beto@presto.demo  ·  carla@presto.demo  ·  Presto123!'

SHORT_SLIDES = [
    {
        'kind': 'cover',
        'title': 'Presto',
        'subtitle': 'Finanzas e inversiones entre personas, en pesos y dólares.',
        'tag': 'DEMO PÚBLICA · DINERO SIMULADO',
        'url': DEMO_URL,
        'date': 'Octubre 2026',
        'notes': (
            'Presto reúne billetera, préstamos entre personas e inversiones en una sola app. '
            'La demo usa dinero simulado: no se mueve plata real.'
        ),
    },
    {
        'kind': 'bullets',
        'title': 'El problema',
        'kicker': '01 · CONTEXTO',
        'bullets': [
            'Pedir un préstamo es lento y los costos aparecen al final.',
            'Invertir parece difícil y las herramientas están dispersas.',
            'Quien presta no tiene un lugar simple con reglas claras.',
        ],
        'note': 'La claridad también es parte del producto.',
        'notes': (
            'El problema no es solo la plata: es la fricción y la falta de claridad. '
            'La gente no sabe cuánto va a pagar ni cómo empezar a invertir.'
        ),
    },
    {
        'kind': 'cards',
        'title': 'La solución',
        'kicker': '02 · PROPUESTA',
        'intro': 'Una sola app para mover, prestar, invertir y ordenar.',
        'cards': [
            ('Billetera en dos monedas', 'ARS y USD, depósitos, retiros y transferencias.'),
            ('Préstamos entre personas', 'Publicá, compará y aceptá con reglas claras.'),
            ('Inversiones simples', 'Plazo fijo con tasa, interés y vencimiento.'),
            ('Orden financiero', 'Presupuestos por categoría y control de gastos.'),
        ],
        'cols': 2,
        'note': 'Presti: el asistente que explica todo sin tecnicismos.',
        'notes': (
            'La propuesta es juntar lo que normalmente está disperso: '
            'billetera, préstamos, inversiones y control en una sola aplicación.'
        ),
    },
    {
        'kind': 'flow',
        'title': 'El circuito completo',
        'kicker': '03 · CÓMO FUNCIONA',
        'steps': [
            ('1', 'Verificás tu identidad', 'KYC una vez.'),
            ('2', 'Cargás saldo', 'ARS o USD.'),
            ('3', 'Elegís una oferta', 'Publicás o comparás.'),
            ('4', 'Pagás en cuotas', 'Cronograma claro.'),
            ('5', 'Invertís', 'Plazo fijo.'),
        ],
        'note': 'El circuito completo, en una sola app.',
        'notes': (
            'Este es el recorrido que se muestra en cinco minutos. '
            'La persona siempre sabe en qué paso está y qué sigue.'
        ),
    },
    {
        'kind': 'cards',
        'title': 'Qué nos diferencia',
        'kicker': '04 · BENEFICIOS',
        'cards': [
            ('Todo en un lugar', 'Billetera, préstamos, inversiones y gastos.'),
            ('Costos claros', 'Cuota, interés y total antes de aceptar.'),
            ('Dos monedas', 'ARS y USD separados, sin conversión.'),
            ('Presti sin humo', 'Datos reales y contenido curado.'),
        ],
        'cols': 2,
        'note': 'Comparación de enfoque y experiencia de uso. No compara precios.',
        'notes': (
            'Las ventajas no son solo funciones: son menos pasos, menos sorpresas y más claridad. '
            'No decimos que los demás sean malos; decimos qué problema resolvemos distinto.'
        ),
    },
    {
        'kind': 'cards',
        'title': 'Tecnología y confianza',
        'kicker': '05 · BASE',
        'cards': [
            ('Python + Django', 'Orden y seguridad para reglas de dinero.'),
            ('PostgreSQL', 'Consistencia y transacciones.'),
            ('Doble registro', 'Cada movimiento, dos veces.'),
            ('Identidad verificada', 'KYC antes de operar.'),
        ],
        'cols': 2,
        'note': 'Herramientas probadas y mantenibles, no las de moda.',
        'notes': (
            'La prioridad fue que el dinero esté bien cuidado y que el equipo pueda mantenerlo. '
            'Por eso Django, PostgreSQL y un libro contable de doble entrada.'
        ),
    },
    {
        'kind': 'stats',
        'title': 'Hoy y lo que sigue',
        'kicker': '06 · ESTADO',
        'stats': [
            ('13', 'módulos'),
            ('800', 'pruebas automáticas'),
            ('5', 'controles en cada cambio'),
            ('1', 'demo pública'),
        ],
        'bullets': [
            'Demo pública con dinero simulado.',
            'Circuito completo: billetera, préstamos, inversiones y Presti.',
            'Próximo: pagos reales, KYC con documentos y legales.',
        ],
        'note': 'Demo: https://presto-mvp-alpha.vercel.app',
        'notes': (
            'No es un prototipo visual: es una aplicación completa con pruebas. '
            'La demo ya muestra el circuito de punta a punta; falta conectar pagos y cerrar legales.'
        ),
    },
    {
        'kind': 'closing',
        'title': 'Presto',
        'subtitle': 'Menos fricción, más claridad.',
        'url': DEMO_URL,
        'meta': f'Usuarios demo: {DEMO_USERS}  ·  Repo: {REPO_URL}',
        'notes': (
            'Cierre: Presto ya muestra el circuito completo. '
            'El siguiente paso es llevar la demo a una operación real.'
        ),
    },
]


if __name__ == '__main__':
    print(f"PPTX: {build_pptx(SHORT_SLIDES, DOCS / 'presentacion-corta.pptx')}")
    print(f"HTML: {build_html(SHORT_SLIDES, DOCS / 'presentacion-corta.html')}")
