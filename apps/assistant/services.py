"""Respuestas del chat de Presti: intenciones por reglas, sin LLM.

El asistente entiende un conjunto acotado de preguntas y responde con datos
reales del usuario o con el contenido curado del marco legal. Si no entiende,
lo dice y propone opciones: nunca inventa una respuesta.
"""

import unicodedata
from datetime import date
from decimal import Decimal

from apps.assistant import market, regulations, selectors

GREETING = (
    '¡Hola! Soy Presti. Puedo contarte el mercado, tu saldo, tus préstamos, '
    'tus inversiones y el marco legal para operar. ¿Qué querés saber?'
)

SUGGESTIONS = (
    'Podés preguntarme: “¿cómo está el dólar?”, “¿cuál es mi saldo?”, '
    '“¿cuánto pago de cuota?”, “¿cómo van mis inversiones?” o '
    '“¿qué necesito para prestar?”.'
)


def _normalize(text: str) -> str:
    """Pasa a minúsculas y saca los acentos para comparar palabras clave."""
    decomposed = unicodedata.normalize('NFKD', text.lower())
    return ''.join(char for char in decomposed if not unicodedata.combining(char))


def _matches(text: str, *words: str) -> bool:
    """Devuelve True si alguna de las palabras aparece en el texto."""
    return any(word in text for word in words)


def _money(amount: Decimal | str, currency: str) -> str:
    """Formatea un importe como `ARS 1.234,56`."""
    value = Decimal(str(amount))
    formatted = f'{value:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    return f'{currency} {formatted}'


def _number(value: float | None) -> str:
    """Formatea un número de mercado, o devuelve un guion."""
    if value is None:
        return '—'
    return f'{value:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def _date(value: str | None) -> str:
    """Formatea una fecha ISO como dd/mm/aaaa."""
    if not value:
        return '—'
    try:
        return date.fromisoformat(value).strftime('%d/%m/%Y')
    except ValueError:
        return value


def _balance_reply(user_id) -> str:
    balances = selectors.get_wallet_balances(user_id=user_id)
    if not balances:
        return (
            'Todavía no tenés billeteras. Podés crearlas desde la sección '
            'Billetera o hacer un depósito desde Pagos.'
        )
    lines = [f'• {currency}: {_money(amount, currency)}' for currency, amount in balances.items()]
    return '*Tu saldo*\n' + '\n'.join(lines)


def _loans_reply(user_id) -> str:
    summary = selectors.get_loans_summary(user_id=user_id)
    parts = []
    if summary['borrower_active']:
        parts.append(f'Tenés {summary["borrower_active"]} préstamo(s) activo(s) como prestatario.')
    if summary['next_installment']:
        next_installment = summary['next_installment']
        parts.append(
            'Próxima cuota: '
            f'{_money(next_installment["amount"], next_installment["currency"])} '
            f'el {_date(next_installment["due_date"])}.'
        )
    if summary['pending_by_currency']:
        pendientes = ', '.join(
            _money(amount, currency) for currency, amount in summary['pending_by_currency'].items()
        )
        parts.append(f'Pendiente total: {pendientes}.')
    if summary['lender_active']:
        parts.append(f'Además prestaste en {summary["lender_active"]} préstamo(s) activo(s).')
    if not parts:
        return 'No tenés préstamos activos en este momento.'
    return '*Tus préstamos*\n' + '\n'.join(parts)


def _investments_reply(user_id) -> str:
    summary = selectors.get_investments_summary(user_id=user_id)
    if not summary['count']:
        return (
            'No tenés inversiones activas. Podés abrir un plazo fijo desde la sección Inversiones.'
        )
    lines = [
        '*Tus inversiones*',
        f'Posiciones activas: {summary["count"]}.',
    ]
    for currency, data in summary['by_currency'].items():
        lines.append(
            f'• {currency}: {_money(data["amount"], currency)} invertidos, '
            f'{_money(data["interest"], currency)} de interés estimado.'
        )
    if summary['next_maturity']:
        lines.append(f'Próximo vencimiento: {_date(summary["next_maturity"])}.')
    return '\n'.join(lines)


def _publish_offer_reply(user_id) -> str:
    kyc = selectors.get_kyc_status(user_id=user_id)
    offers = selectors.get_offers_summary(user_id=user_id)
    lines = ['*Para prestar en Presto*']
    if kyc == 'approved':
        lines.append('• Tu KYC está aprobado: ya podés publicar ofertas.')
    elif kyc == 'pending':
        lines.append('• Tu KYC está pendiente: esperá la aprobación para publicar.')
    elif kyc == 'rejected':
        lines.append('• Tu KYC fue rechazado: volvé a solicitar la verificación.')
    else:
        lines.append('• Necesitás completar el KYC antes de publicar ofertas.')
    lines.append(
        '• La oferta define monto, moneda, plazo y TNA. Publicarla no reserva '
        'fondos: el saldo se descuenta cuando alguien la acepta.'
    )
    if offers['active']:
        total = ', '.join(
            _money(amount, currency) for currency, amount in offers['by_currency'].items()
        )
        lines.append(f'• Tenés {offers["active"]} oferta(s) activa(s) por {total}.')
    return '\n'.join(lines)


def _kyc_reply(user_id) -> str:
    status = selectors.get_kyc_status(user_id=user_id)
    messages = {
        'approved': 'Tu identidad ya está verificada. Podés operar con dinero.',
        'pending': 'Tu verificación está pendiente de revisión.',
        'rejected': 'Tu verificación fue rechazada. Podés volver a solicitarla con documentación actualizada.',
        'missing': 'Todavía no pediste la verificación. Se hace desde Perfil y KYC.',
    }
    return messages[status]


def _dollar_reply() -> str:
    snapshot = market.get_market_snapshot()
    dollar = snapshot['dollar']
    if not dollar:
        return (
            'No pude obtener la cotización del dólar en este momento. '
            'Probá de nuevo en unos minutos.'
        )
    return (
        '*Dólar*\n'
        f'• Oficial: ${_number(dollar["oficial"])}\n'
        f'• Blue: ${_number(dollar["blue"])}\n'
        f'Actualizado: {snapshot["updated_at"]}'
    )


def _coins_reply() -> str:
    snapshot = market.get_market_snapshot()
    if not snapshot['coins']:
        return 'No pude obtener las cotizaciones de cripto en este momento.'
    lines = ['*Cripto*']
    for coin in snapshot['coins']:
        change = coin['change_24h_pct']
        trend = '' if change is None else f' ({change:+.2f}% 24 h)'
        lines.append(f'• {coin["name"]}: US$ {_number(coin["price_usd"])}{trend}')
    return '\n'.join(lines)


def _market_reply() -> str:
    snapshot = market.get_market_snapshot()
    dollar = snapshot['dollar'] or {}
    lines = ['*Mercado*']
    lines.append(
        f'• Dólar oficial: ${_number(dollar.get("oficial"))} · blue: ${_number(dollar.get("blue"))}'
    )
    for coin in snapshot['coins']:
        lines.append(f'• {coin["symbol"]}: US$ {_number(coin["price_usd"])}')
    if not snapshot['coins'] and not snapshot['dollar']:
        return 'No pude obtener datos de mercado en este momento.'
    return '\n'.join(lines)


def _legal_reply(text: str) -> str:
    if _matches(text, 'cnv', 'oferta publica', 'inversion'):
        item = regulations.get_regulation('oferta-publica-cnv')
    elif _matches(text, 'bcra', 'captar', 'entidad'):
        item = regulations.get_regulation('entidades-financieras')
    elif _matches(text, 'uif', 'lavado', 'pla', 'ft'):
        item = regulations.get_regulation('pla-ft')
    elif _matches(text, 'tasa', 'interes', 'cft', 'costo'):
        item = regulations.get_regulation('tasas-y-costo')
    else:
        item = regulations.get_regulation('mutuo-entre-particulares')

    if item is None:
        return 'No encontré esa ficha regulatoria.'
    points = '\n'.join(f'• {point}' for point in item['key_points'][:3])
    return (
        f'*{item["title"]}*\n{item["summary"]}\n{points}\n\n'
        'Abrí “Marco legal” en Presti para ver las normas y los enlaces oficiales.\n'
        f'{regulations.DISCLAIMER}'
    )


def answer_question(user_id, message: str) -> dict:
    """Responde una pregunta del usuario con una regla.

    Args:
        user_id: identificador del usuario autenticado.
        message: texto de la consulta.

    Returns:
        Dict con `reply` e `intent` (`rules`, `fallback` o `empty`).
    """
    text = _normalize(message).strip()
    if not text:
        return {
            'reply': 'Escribí tu consulta y te ayudo.',
            'intent': 'empty',
        }

    if _matches(text, 'hola', 'buenas', 'que podes', 'ayuda', 'que sabes'):
        return {'reply': f'{GREETING}\n\n{SUGGESTIONS}', 'intent': 'rules'}
    if _matches(text, 'saldo', 'cuenta', 'billetera', 'cuanto tengo'):
        return {'reply': _balance_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'cuota', 'prestamo', 'deuda', 'debo'):
        return {'reply': _loans_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'inversion', 'plazo fijo', 'rendimiento', 'interes ganado'):
        return {'reply': _investments_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'prestar', 'prestamista', 'publicar', 'oferta', 'captar'):
        return {'reply': _publish_offer_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'kyc', 'verificacion', 'identidad'):
        return {'reply': _kyc_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'legal', 'ley', 'norma', 'regulacion', 'cnv', 'bcra', 'uif', 'impuesto'):
        return {'reply': _legal_reply(text), 'intent': 'rules'}
    if _matches(text, 'dolar', 'blue', 'cotizacion'):
        return {'reply': _dollar_reply(), 'intent': 'rules'}
    if _matches(text, 'bitcoin', 'btc', 'cripto', 'ethereum', 'eth'):
        return {'reply': _coins_reply(), 'intent': 'rules'}
    if _matches(text, 'mercado', 'acciones', 'bolsa'):
        return {'reply': _market_reply(), 'intent': 'rules'}

    return {
        'reply': f'No entendí esa consulta. {SUGGESTIONS}',
        'intent': 'fallback',
    }
