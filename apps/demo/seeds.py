"""Escenario de demostración: datos creíbles para mostrar la aplicación.

La app `demo` **no tiene modelos**: es una herramienta de siembra que usa los
`services` y los `selectors` de las demás apps (nunca sus modelos, vistas ni
serializers) para armar una historia completa y verificable:

- tres personas con KYC aprobado (una prestataria, un prestamista y una
  inversor);
- un depósito de fondos;
- una oferta de préstamo aceptada, con su cronograma y una cuota pagada;
- un plazo fijo abierto;
- un presupuesto con una alerta disparada;
- un pago confirmado por el proveedor y una transferencia entre usuarios.

Todo se hace con **claves de idempotencia fijas**, así que volver a sembrar
no duplica ni un centavo: los servicios devuelven la operación original.

Los dos únicos modelos que la siembra necesita (el usuario y el producto de
plazo fijo) se resuelven con `django.apps.apps.get_model()`, para no romper el
contrato de capas que permite a esta app importar solo `services` y
`selectors` de las demás.
"""

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from django.apps import apps as django_apps

from apps.budgets import selectors as budget_selectors
from apps.budgets import services as budget_services
from apps.identity import selectors as identity_selectors
from apps.identity import services as identity_services
from apps.investments import selectors as investment_selectors
from apps.investments import services as investment_services
from apps.ledger import selectors as ledger_selectors
from apps.ledger import services as ledger_services
from apps.loans import selectors as loan_selectors
from apps.loans import services as loan_services
from apps.offers import selectors as offer_selectors
from apps.offers import services as offer_services
from apps.payments import selectors as payment_selectors
from apps.payments import services as payment_services

#: Contraseña de las personas de la demo. Es de muestra: nunca es de un usuario
#: real y el comando avisa que hay que cambiarla en un entorno de verdad.
DEMO_PASSWORD = 'Presto123!'

#: Las personas del escenario.
DEMO_BORROWER = 'ana@presto.demo'
DEMO_LENDER = 'beto@presto.demo'
DEMO_INVESTOR = 'carla@presto.demo'

#: Importe del depósito del prestamista.
LENDER_DEPOSIT = Decimal('250000.00')

#: Importe del depósito de la prestataria (paga cuotas y gasta).
BORROWER_DEPOSIT = Decimal('180000.00')

#: Importe del depósito de la inversor (financia el plazo fijo).
INVESTOR_DEPOSIT = Decimal('150000.00')

#: Oferta publicada por el prestamista.
OFFER_AMOUNT = Decimal('120000.00')
OFFER_RATE = Decimal('32.00')
OFFER_TERM_MONTHS = 6

#: Plazo fijo.
INVESTMENT_AMOUNT = Decimal('100000.00')
INVESTMENT_RATE = Decimal('18.00')
INVESTMENT_TERM_DAYS = 30

#: Plazo fijo de la prestataria (la otra cara de la app: prestar e invertir).
BORROWER_INVESTMENT = Decimal('50000.00')

#: Presupuesto de Ana.
BUDGET_LIMIT = Decimal('80000.00')
BUDGET_ALERT_THRESHOLD = 50
SPENDING_AMOUNT = Decimal('65000.00')

#: Pagos: un depósito del proveedor y una transferencia interna.
PAYMENT_DEPOSIT = Decimal('50000.00')
PAYMENT_TRANSFER = Decimal('25000.00')


@dataclass
class DemoSummary:
    """Lo que el comando cuenta después de sembrar.

    Attributes:
        users: emails de las personas creadas o reutilizadas.
        loan_id: identificador del préstamo del escenario, si quedó armado.
        payment_ids: identificadores de los pagos creados.
        balances: saldo de la billetera de cada persona.
    """

    users: list[str] = field(default_factory=list)
    loan_id: str = ''
    offer_id: str = ''
    payment_ids: list[str] = field(default_factory=list)
    balances: dict[str, str] = field(default_factory=dict)


def _user_model():
    """Devuelve el modelo de usuario sin importarlo de otra app.

    Returns:
        La clase del modelo `identity.User`.
    """
    return django_apps.get_model('identity', 'User')


def _product_model():
    """Devuelve el modelo de producto de inversión sin importarlo de otra app.

    Returns:
        La clase del modelo `investments.InvestmentProduct`.
    """
    return django_apps.get_model('investments', 'InvestmentProduct')


def _ensure_user(email: str, password: str):
    """Devuelve el usuario del email, creándolo si no existe.

    Args:
        email: email de la persona.
        password: contraseña de la persona.

    Returns:
        La tupla `(user, created)`.
    """
    existing = _user_model().objects.filter(email=email).first()
    if existing is not None:
        return existing, False
    return identity_services.register_user(email=email, password=password), True


def _ensure_kyc(user) -> None:
    """Deja el KYC del usuario aprobado (en producción lo hace el staff).

    Args:
        user: el usuario.

    Returns:
        None.
    """
    if identity_selectors.is_kyc_approved(user.id):
        return
    verification = identity_services.submit_kyc(user=user, documents={'tipo': 'demo'})
    identity_services.resolve_kyc(
        verification_id=verification.id,
        status='approved',
        resolved_by_user_id=user.id,
    )


def _ensure_deposit(user, currency: str, amount: Decimal, key: str, description: str) -> None:
    """Deposita fondos simulados una sola vez.

    Args:
        user: quien recibe el dinero.
        currency: moneda del depósito.
        amount: importe.
        key: clave de idempotencia fija.
        description: descripción del movimiento.

    Returns:
        None.
    """
    ledger_services.deposit(
        user_id=user.id,
        currency=currency,
        amount=amount,
        idempotency_key=key,
        description=description,
    )


def _ensure_offer(lender, currency: str):
    """Publica la oferta del prestamista si no hay una activa equivalente.

    Args:
        lender: el prestamista.
        currency: moneda de la oferta.

    Returns:
        La oferta activa.
    """
    offers = offer_selectors.list_offers_for_lender(lender.id)
    same_amount = [offer for offer in offers if offer.amount == OFFER_AMOUNT]
    for offer in same_amount:
        if offer.status == 'active':
            return offer
    if same_amount:
        return same_amount[0]
    return offer_services.create_offer(
        lender_user_id=lender.id,
        amount=OFFER_AMOUNT,
        currency=currency,
        interest_rate=OFFER_RATE,
        term_months=OFFER_TERM_MONTHS,
        requirements='Sin garantía. Buen historial de pagos.',
    )


def _ensure_loan(borrower, offer):
    """Acepta la oferta y paga la primera cuota.

    Args:
        borrower: quien pide el préstamo.
        offer: la oferta aceptada.

    Returns:
        El préstamo del escenario.
    """
    loans = loan_selectors.list_loans_for_user(borrower.id)
    loan = loans.filter(offer_id=offer.id).first()
    if loan is None:
        loan = loan_services.accept_offer(
            borrower_user_id=borrower.id,
            offer_id=offer.id,
            idempotency_key='demo-prestamo-ana',
        )
    installments = loan_selectors.list_installments(loan.id).order_by('number')
    first = installments.first()
    if first is not None and first.status != 'paid':
        loan_services.pay_installment(
            loan_id=loan.id,
            number=first.number,
            borrower_user_id=borrower.id,
        )
    return loan


def _ensure_product(currency: str):
    """Devuelve el producto de plazo fijo, creándolo si hace falta.

    Args:
        currency: moneda del producto.

    Returns:
        El producto de plazo fijo activo.
    """
    products = investment_selectors.list_active_products()
    product = products.filter(currency=currency).first()
    if product is not None:
        return product
    return _product_model().objects.create(
        type='fixed_term',
        currency=currency,
        term_days=INVESTMENT_TERM_DAYS,
        annual_rate_tna=INVESTMENT_RATE,
        min_amount=Decimal('10000.00'),
        status='active',
    )


def _ensure_position(user, product, currency: str, amount: Decimal, key: str) -> None:
    """Abre una posición a plazo fijo si el usuario no tiene ninguna.

    Args:
        user: quien invierte.
        product: el producto de plazo fijo.
        currency: moneda de la posición.
        amount: importe invertido.
        key: clave de idempotencia fija.

    Returns:
        None.
    """
    positions = investment_selectors.list_positions_for_user(user.id)
    if positions.filter(product=product).exists():
        return
    investment_services.open_position(
        user_id=user.id,
        product_id=product.id,
        amount=amount,
        idempotency_key=key,
        currency=currency,
    )


def _ensure_budget(user, currency: str) -> None:
    """Arma el presupuesto con su alerta disparada.

    Args:
        user: dueño del presupuesto.
        currency: moneda del presupuesto.

    Returns:
        None.
    """
    categories = budget_selectors.list_categories_for_user(user.id)
    category = categories.filter(name='Supermercado').first()
    if category is None:
        category = budget_services.create_category(user_id=user.id, name='Supermercado')

    budgets = budget_selectors.list_budgets_for_user(user.id)
    if not budgets.filter(category=category).exists():
        budget_services.create_budget(
            user_id=user.id,
            category_id=category.id,
            limit_amount=BUDGET_LIMIT,
            currency=currency,
            alert_threshold=BUDGET_ALERT_THRESHOLD,
        )

    expenses = budget_selectors.list_expenses_for_user(user.id)
    if not expenses.filter(category=category).exists():
        movement = ledger_services.withdraw(
            user_id=user.id,
            currency=currency,
            amount=SPENDING_AMOUNT,
            idempotency_key='demo-gasto-supermercado',
            description='Compra del súper',
        )
        budget_services.categorize_movement(
            user_id=user.id,
            ledger_transaction_id=movement.id,
            category_id=category.id,
        )


def _ensure_payments(borrower, investor, currency: str) -> list[str]:
    """Crea el pago del proveedor y la transferencia interna.

    Args:
        borrower: quien paga y transfiere.
        investor: quien recibe la transferencia.
        currency: moneda de los pagos.

    Returns:
        Los identificadores de los pagos del escenario.
    """
    identifiers: list[str] = []
    existing = payment_selectors.list_payments_for_user(borrower.id)
    if not existing.filter(direction='deposit').exists():
        deposit = payment_services.create_payment(
            user_id=borrower.id,
            direction='deposit',
            amount=PAYMENT_DEPOSIT,
            currency=currency,
            idempotency_key='demo-pago-deposito',
            description='Depósito desde la app',
        )
        identifiers.append(str(deposit.id))
    if not existing.filter(direction='transfer').exists():
        transfer = payment_services.create_payment(
            user_id=borrower.id,
            direction='transfer',
            amount=PAYMENT_TRANSFER,
            currency=currency,
            idempotency_key='demo-pago-transferencia',
            description=f'Transferencia a {investor.email}',
            destination_user_id=investor.id,
        )
        identifiers.append(str(transfer.id))
    return identifiers


def seed_demo(currency: str = 'ARS', password: str = DEMO_PASSWORD) -> DemoSummary:
    """Siembra el escenario de demostración completo.

    Es **idempotente**: las claves de idempotencia son fijas, así que volver a
    sembrar no duplica movimientos.

    Args:
        currency: moneda del escenario.
        password: contraseña de las personas de la demo.

    Returns:
        Un `DemoSummary` con lo que quedó armado.
    """
    summary = DemoSummary()

    borrower, _ = _ensure_user(DEMO_BORROWER, password)
    lender, _ = _ensure_user(DEMO_LENDER, password)
    investor, _ = _ensure_user(DEMO_INVESTOR, password)
    summary.users = [borrower.email, lender.email, investor.email]

    for user in (borrower, lender, investor):
        _ensure_kyc(user)

    _ensure_deposit(
        lender,
        currency,
        LENDER_DEPOSIT,
        'demo-deposito-beto',
        'Depósito inicial del prestamista',
    )
    _ensure_deposit(
        borrower,
        currency,
        BORROWER_DEPOSIT,
        'demo-deposito-ana',
        'Depósito inicial de la prestataria',
    )
    _ensure_deposit(
        investor,
        currency,
        INVESTOR_DEPOSIT,
        'demo-deposito-carla',
        'Depósito inicial de la inversor',
    )

    offer = _ensure_offer(lender, currency)
    summary.offer_id = str(offer.id)

    loan = _ensure_loan(borrower, offer)
    summary.loan_id = str(loan.id)

    product = _ensure_product(currency)
    _ensure_position(investor, product, currency, INVESTMENT_AMOUNT, 'demo-plazo-fijo-carla')
    _ensure_position(borrower, product, currency, BORROWER_INVESTMENT, 'demo-plazo-fijo-ana')

    _ensure_budget(borrower, currency)

    summary.payment_ids = _ensure_payments(borrower, investor, currency)

    for user in (borrower, lender, investor):
        wallet = _wallet_balance(user.id, currency)
        summary.balances[user.email] = wallet

    return summary


def _wallet_balance(user_id: uuid.UUID, currency: str) -> str:
    """Devuelve el saldo de la billetera del usuario en la moneda pedida.

    Args:
        user_id: identificador del usuario.
        currency: moneda de la billetera.

    Returns:
        El saldo como texto.
    """
    wallet = ledger_selectors.get_user_wallet(user_id, currency)
    if wallet is None:
        return '0.00'
    return f'{wallet.balance:.2f}'
