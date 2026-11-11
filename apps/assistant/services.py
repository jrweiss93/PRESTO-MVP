"""Respuestas del chat de Presti: intenciones por reglas, sin LLM.

El asistente entiende un conjunto acotado de preguntas y responde con datos
reales del usuario o con el contenido curado del marco legal. Si no entiende,
lo dice y propone opciones: nunca inventa una respuesta.
"""

import unicodedata
from datetime import date
from decimal import Decimal

from apps.assistant import market, regulations, selectors
from apps.core.money import effective_annual_rate, simple_interest

GREETING = (
    '¡Hola! Soy Presti. Puedo contarte el mercado, tu saldo, tus préstamos, '
    'tus inversiones y el marco legal para operar. ¿Qué querés saber?'
)

INVESTOR_GREETING = (
    '¡Hola! Soy Presti, tu asesor de inversiones. Te guío paso a paso para '
    'invertir sin errores: perfil, KYC, saldo, productos, riesgos y vencimientos.'
)

SUGGESTIONS = (
    'Podés preguntarme: “¿cómo está el dólar?”, “¿cuál es mi saldo?”, '
    '“¿cuánto pago de cuota?”, “¿cómo vinculo una cuenta de respaldo?”, '
    '“¿cómo van mis inversiones?” o “¿qué necesito para prestar?”.'
)

INVESTOR_MENU = (
    'Para no equivocarte, elegí una opción:\n'
    '• “¿Cómo invierto paso a paso?”\n'
    '• “¿Qué productos hay?”\n'
    '• “¿Qué riesgos tiene?”\n'
    '• “¿Puedo retirar antes?”\n'
    '• “¿Cuánto voy a ganar?”\n'
    '• “No me deja invertir”\n'
    '• “¿Qué es invertir en Presto?”\n'
    '• “¿Cómo van mis inversiones?”\n'
    '• “¿Cómo se integran bancos y Binance?”\n'
    '• “Marco legal”'
)

INVESTOR_DISCLAIMER = (
    'Esto es información general para la demo, no asesoramiento financiero personalizado.'
)

PROFILE_LABELS = {
    'borrower': 'Prestatario',
    'lender': 'Prestamista',
    'investor': 'Inversor',
}


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


def _rate(value: str | Decimal) -> str:
    """Formatea una tasa con coma decimal para español."""
    return str(value).replace('.', ',')


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
            'No tenés inversiones activas. Si querés empezar, preguntame '
            '“¿cómo invierto paso a paso?”.'
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
    lines.append(
        'El interés es estimado y se acredita al vencimiento. No incluye impuestos ni comisiones.'
    )
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
    if _matches(text, 'integr', 'binance', 'debin', 'open banking', 'mercado pago'):
        item = regulations.get_regulation('integraciones-pagos')
    elif _matches(text, 'cnv', 'oferta publica', 'inversion'):
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


def _profile_label(kind: str | None) -> str:
    """Devuelve el nombre legible del perfil activo."""
    return PROFILE_LABELS.get(kind or '', 'sin perfil')


def _kyc_line(status: str) -> str:
    """Devuelve el estado KYC con un texto accionable."""
    return {
        'approved': '✅ Aprobado',
        'pending': '⏳ Pendiente (esperá la aprobación)',
        'rejected': '❌ Rechazado (volvé a solicitarlo en Perfil)',
        'missing': '❌ Sin solicitar (completalo en Perfil y KYC)',
    }.get(status, f'❌ {status}')


def _product_lines(products: list[dict]) -> list[str]:
    """Formatea los productos activos para el chat."""
    return [
        (
            f'• {product["name"]}: {product["term_days"]} días · '
            f'TNA {_rate(product["annual_rate_tna"])}% · mínimo '
            f'{_money(product["min_amount"], product["currency"])}'
        )
        for product in products
    ]


def _investor_tutorial_reply(user_id) -> str:
    """Guía paso a paso para invertir sin errores."""
    kind = selectors.get_profile_kind(user_id)
    kyc = selectors.get_kyc_status(user_id)
    balances = selectors.get_wallet_balances(user_id)
    products = selectors.get_active_investment_products()

    if kind == 'investor':
        profile_line = '✅ Inversor'
    else:
        profile_line = f'❌ {_profile_label(kind)} (invertir requiere perfil Inversor)'

    lines = [
        '*Guía para invertir en Presto*',
        f'1. Perfil: {profile_line}.',
        f'2. KYC: {_kyc_line(kyc)}.',
    ]
    if balances:
        balance_text = ', '.join(_money(amount, currency) for currency, amount in balances.items())
        lines.append(f'3. Saldo en billetera: {balance_text}.')
    else:
        lines.append('3. Saldo: no tenés billetera todavía. Creala o depositá en Billetera.')

    if products:
        lines.append(f'4. Productos activos: {len(products)}.')
        lines.extend(f'   {line}' for line in _product_lines(products))
    else:
        lines.append('4. Productos activos: no hay ninguno disponible ahora.')

    lines.extend(
        [
            '5. Elegí un producto y un monto igual o mayor al mínimo. La moneda '
            'del producto debe coincidir con tu billetera.',
            '6. Confirmá en Inversiones → Abrir inversión. El dinero se descuenta '
            'de tu billetera al abrir la posición.',
            '7. El capital y el interés se acreditan al vencimiento. No hay retiro '
            'anticipado ni pagos parciales.',
            '8. Si el botón no responde o da error, preguntame “no me deja invertir”.',
            INVESTOR_DISCLAIMER,
        ]
    )
    return '\n'.join(lines)


def _investor_checklist_reply(user_id) -> str:
    """Revisa los requisitos reales y explica por qué podría fallar."""
    kind = selectors.get_profile_kind(user_id)
    kyc = selectors.get_kyc_status(user_id)
    balances = selectors.get_wallet_balances(user_id)
    products = selectors.get_active_investment_products()

    lines = ['*Checklist antes de invertir*']
    if kind == 'investor':
        lines.append('• Perfil Inversor: ✅')
    else:
        lines.append(
            f'• Perfil Inversor: ❌ tu perfil es {_profile_label(kind)}. '
            'Este perfil no puede invertir por diseño.'
        )
    lines.append(f'• KYC: {_kyc_line(kyc)}.')

    ars = balances.get('ARS')
    if ars is None:
        lines.append('• Saldo ARS: ❌ no tenés billetera ARS. Depositá en Billetera.')
    else:
        lines.append(f'• Saldo ARS: ✅ {_money(ars, "ARS")}.')

    if products:
        cheapest = min(products, key=lambda product: Decimal(product['min_amount']))
        lines.append(
            f'• Productos activos: ✅ {len(products)}. Mínimo más bajo: '
            f'{_money(cheapest["min_amount"], cheapest["currency"])}.'
        )
    else:
        lines.append('• Productos activos: ❌ no hay productos disponibles.')

    lines.extend(
        [
            '• Monto: debe ser ≥ mínimo y ≤ saldo disponible.',
            '• Moneda: el producto y tu billetera deben coincidir.',
            '• Plazo: el dinero queda inmovilizado hasta el vencimiento.',
            'Si todo está ✅ y el botón falla, reintentá o avisá a soporte.',
            INVESTOR_DISCLAIMER,
        ]
    )
    return '\n'.join(lines)


def _investment_products_reply() -> str:
    """Lista los productos activos y explica cómo compararlos."""
    products = selectors.get_active_investment_products()
    if not products:
        return 'No hay productos de inversión activos en este momento.'

    lines = ['*Productos de inversión activos*', *_product_lines(products)]
    lines.extend(
        [
            '',
            '*Cómo comparar*',
            '• Más plazo significa más tiempo con el dinero inmovilizado.',
            '• La TNA es nominal y se prorratea por días; la TEA equivalente puede ser distinta.',
            '• No hago recomendaciones personalizadas: elegí según tu horizonte '
            'y tu necesidad de liquidez.',
        ]
    )
    if any(
        'invert' in _normalize(product['name']) and 'presto' in _normalize(product['name'])
        for product in products
    ):
        lines.append(
            '• “Invertí en Presto” es renta fija simulada: no es una acción ni '
            'una participación societaria.'
        )
    lines.append(INVESTOR_DISCLAIMER)
    return '\n'.join(lines)


def _investment_interest_reply() -> str:
    """Explica el cálculo de interés y la diferencia TNA/TEA."""
    amount = Decimal('10000.00')
    rate = Decimal('22.00')
    days = 90
    interest = simple_interest(amount, rate, days)
    total = amount + interest
    tea = effective_annual_rate(rate)
    return (
        '*Cómo se calcula tu interés*\n'
        'La TNA se prorratea por días: interés = monto × TNA/100 × días/365.\n'
        f'Ejemplo: {_money(amount, "ARS")} al 22,00% TNA a 90 días → interés '
        f'{_money(interest, "ARS")}, total {_money(total, "ARS")}.\n'
        f'La TEA equivalente de una TNA del 22,00% es {_rate(tea)}% '
        '(capitalización mensual).\n'
        'El interés se acredita al vencimiento, no mes a mes. En la demo no se '
        'cobran comisiones ni impuestos.\n'
        f'{INVESTOR_DISCLAIMER}'
    )


def _investment_risks_reply() -> str:
    """Explica los riesgos y límites para evitar expectativas erróneas."""
    return (
        '*Riesgos y límites*\n'
        '• No hay garantía de capital: podés perder parte o todo.\n'
        '• El dinero queda inmovilizado hasta el vencimiento: no hay retiro '
        'anticipado.\n'
        '• Existe riesgo de contraparte y de plataforma.\n'
        '• Producto de demo, sujeto a autorización regulatoria (CNV/BCRA).\n'
        '• La TNA no es la TEA; el rendimiento efectivo puede diferir.\n'
        '• Invertí solo dinero que no necesites antes del vencimiento.\n'
        f'{INVESTOR_DISCLAIMER}'
    )


def _investment_liquidity_reply() -> str:
    """Aclara que el plazo fijo no se puede rescatar antes."""
    return (
        '*Liquidez*\n'
        'Los plazos fijos no se pueden retirar, cancelar ni rescatar antes del '
        'vencimiento. Si necesitás el dinero antes, no lo inviertas o elegí el '
        'plazo más corto disponible (30 días).\n'
        f'{INVESTOR_DISCLAIMER}'
    )


def _backup_account_reply(user_id) -> str:
    """Explica cómo vincular y verificar una cuenta de respaldo."""
    accounts = selectors.get_backup_accounts_summary(user_id=user_id)
    lines = [
        '*Cuenta de respaldo para préstamos*',
        'Para aceptar un préstamo necesitás al menos una cuenta de respaldo '
        'verificada. Es un requisito de la demo para reducir el riesgo de impago.',
    ]
    if accounts:
        lines.append('*Tus cuentas*')
        for account in accounts:
            lines.append(
                f'• {account["provider"]} · {account["display_name"]} · '
                f'{account["masked_ref"]} · {account["status"]} · saldo informado '
                f'{_money(account["declared_balance"], account["currency"])}'
            )
    else:
        lines.append('Todavía no tenés cuentas de respaldo vinculadas.')
    lines.extend(
        [
            'Pasos: Perfil y KYC → Cuentas de respaldo → elegí banco/billetera → '
            'cargá una referencia y el saldo informado → verificá con el código '
            'de la demo.',
            'Solo guardamos proveedor, referencia enmascarada y saldo informado. '
            'No pedimos claves, tokens ni datos bancarios completos.',
            'El saldo informado no se consulta al banco: es una declaración del '
            'usuario y no garantiza el pago.',
            'Mientras tengas un préstamo activo o en mora no podés desvincular la cuenta.',
        ]
    )
    return '\n'.join(lines)


def _integrations_reply() -> str:
    """Explica el alcance real de integrar bancos, billeteras y Binance."""
    return (
        '*Integraciones y regulación*\n'
        '• En la demo, la vinculación es simulada: no se consulta ni debita una '
        'cuenta real.\n'
        '• Banco: se puede leer saldo con un proveedor de open banking y '
        'consentimiento del usuario; debitar requiere DEBIN, un PSP o un convenio '
        'bancario.\n'
        '• Mercado Pago: OAuth del usuario y preapproval para débitos recurrentes.\n'
        '• Binance: la API permite leer saldos con permisos de solo lectura; no '
        'permite que un tercero debite automáticamente. Binance Pay requiere que '
        'el usuario confirme el pago.\n'
        '• Datos personales: Ley 25.326; consentimiento, finalidad y seguridad de '
        'la información.\n'
        '• Para operar con dinero real hacen falta contratos con los proveedores, '
        'homologaciones y encuadre BCRA/CNV.\n'
        'Abrí “Marco legal” en Presti → Integraciones y pagos para ver las normas '
        'y los enlaces oficiales.\n'
        f'{regulations.DISCLAIMER}'
    )


def _presto_investment_reply() -> str:
    """Explica el producto para invertir en el propio Presto."""
    products = selectors.get_active_investment_products()
    presto = next(
        (
            product
            for product in products
            if 'invert' in _normalize(product['name']) and 'presto' in _normalize(product['name'])
        ),
        None,
    )
    lines = ['*Invertí en Presto*']
    if presto is not None:
        lines.append(
            f'Producto: {presto["name"]} · {presto["term_days"]} días · '
            f'TNA {_rate(presto["annual_rate_tna"])}% · mínimo '
            f'{_money(presto["min_amount"], presto["currency"])}.'
        )
    lines.extend(
        [
            'Es un plazo fijo simulado para financiar el crecimiento de Presto. '
            'No es una acción ni una participación societaria.',
            'No hay garantía de capital y el dinero no se puede retirar antes del vencimiento.',
            'Podés verlo y abrirlo en la sección Inversiones.',
            f'{regulations.DISCLAIMER}',
        ]
    )
    return '\n'.join(lines)


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

    is_investor = selectors.get_profile_kind(user_id) == 'investor'

    if _matches(text, 'hola', 'buenas', 'que podes', 'ayuda', 'que sabes'):
        if is_investor:
            return {
                'reply': f'{INVESTOR_GREETING}\n\n{INVESTOR_MENU}',
                'intent': 'rules',
            }
        return {'reply': f'{GREETING}\n\n{SUGGESTIONS}', 'intent': 'rules'}
    if _matches(
        text,
        'integrar',
        'integracion',
        'binance',
        'open banking',
        'debin',
        'mercado pago',
        'debito automatico',
        'api bancaria',
        'proveedor de pagos',
    ):
        return {'reply': _integrations_reply(), 'intent': 'rules'}
    if _matches(
        text,
        'cuenta de respaldo',
        'vincular',
        'cbu',
        'cvu',
        'cuenta bancaria',
        'alias bancario',
    ):
        return {'reply': _backup_account_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'saldo', 'cuenta', 'billetera', 'cuanto tengo'):
        return {'reply': _balance_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'cuota', 'prestamo', 'deuda', 'debo'):
        return {'reply': _loans_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'dolar', 'blue', 'cotizacion'):
        return {'reply': _dollar_reply(), 'intent': 'rules'}
    if _matches(text, 'bitcoin', 'btc', 'cripto', 'ethereum', 'eth'):
        return {'reply': _coins_reply(), 'intent': 'rules'}
    if _matches(text, 'mercado', 'acciones', 'bolsa', 'merval'):
        return {'reply': _market_reply(), 'intent': 'rules'}
    if _matches(text, 'legal', 'ley', 'norma', 'regulacion', 'cnv', 'bcra', 'uif', 'impuesto'):
        return {'reply': _legal_reply(text), 'intent': 'rules'}
    if _matches(text, 'presto') and _matches(text, 'invertir', 'inversion', 'inverti', 'invierto'):
        return {'reply': _presto_investment_reply(), 'intent': 'rules'}
    if _matches(
        text,
        'como invierto',
        'paso a paso',
        'tutorial',
        'guia',
        'empezar a invertir',
        'primera inversion',
        'como hago para invertir',
        'como puedo invertir',
        'quiero invertir',
        'que es invertir',
        'como funciona',
    ):
        return {'reply': _investor_tutorial_reply(user_id), 'intent': 'rules'}
    if _matches(
        text,
        'no me deja',
        'no puedo invertir',
        'no me permite',
        'error al invertir',
        'problema para invertir',
        'requisito',
        'que necesito para invertir',
        'cuanto necesito',
        'monto minimo',
        'minimo',
    ):
        return {'reply': _investor_checklist_reply(user_id), 'intent': 'rules'}
    if _matches(
        text,
        'retirar antes',
        'rescatar',
        'cancelar',
        'liquidez',
        'antes del vencimiento',
        'sacar antes',
        'retiro anticipado',
    ):
        return {'reply': _investment_liquidity_reply(), 'intent': 'rules'}
    if _matches(
        text,
        'riesgo',
        'garantia',
        'seguro',
        'puedo perder',
        'que pasa si',
        'contraparte',
        'perder dinero',
    ):
        return {'reply': _investment_risks_reply(), 'intent': 'rules'}
    if _matches(
        text,
        'cuanto gano',
        'cuanto voy a ganar',
        'interes',
        'rendimiento',
        'tna',
        'tea',
        'calcula',
        'cuanto me rinde',
    ):
        return {'reply': _investment_interest_reply(), 'intent': 'rules'}
    if _matches(
        text,
        'producto',
        'productos',
        'opciones',
        'comparar',
        'que me conviene',
        'conviene',
        'donde invierto',
        'que puedo invertir',
        'plazo fijo',
    ):
        return {'reply': _investment_products_reply(), 'intent': 'rules'}
    if _matches(
        text,
        'mis inversiones',
        'como van',
        'posiciones',
        'vencimiento',
        'cuando cobro',
        'cuando vence',
        'cuando termina',
    ):
        return {'reply': _investments_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'prestar', 'prestamista', 'publicar', 'oferta', 'captar'):
        return {'reply': _publish_offer_reply(user_id), 'intent': 'rules'}
    if _matches(text, 'kyc', 'verificacion', 'identidad'):
        return {'reply': _kyc_reply(user_id), 'intent': 'rules'}

    if is_investor:
        return {
            'reply': f'No entendí esa consulta.\n\n{INVESTOR_MENU}',
            'intent': 'fallback',
        }
    return {
        'reply': f'No entendí esa consulta. {SUGGESTIONS}',
        'intent': 'fallback',
    }
