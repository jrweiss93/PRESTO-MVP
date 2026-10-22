"""Selectores de lectura del asistente: los datos del usuario que usa Presti.

La app no tiene modelos: arma los resúmenes con los selectores de las apps
dueñas (AGENTS §5.2) y devuelve solo primitivos.
"""

import uuid
from decimal import Decimal

from apps.identity import selectors as identity_selectors
from apps.investments import selectors as investments_selectors
from apps.ledger import selectors as ledger_selectors
from apps.loans import selectors as loans_selectors
from apps.offers import selectors as offers_selectors

# Estados y constantes de otras apps (no se importan sus modelos).
ACTIVE = 'active'
PENDING = 'pending'
APPROVED = 'approved'


def get_wallet_balances(user_id: uuid.UUID) -> dict[str, str]:
    """Devuelve el saldo de cada billetera del usuario, por moneda.

    Args:
        user_id: identificador del usuario.

    Returns:
        Dict moneda → saldo como string decimal.
    """
    accounts = ledger_selectors.list_accounts_for_user(user_id=user_id)
    return {account.currency: str(account.balance) for account in accounts}


def get_loans_summary(user_id: uuid.UUID) -> dict:
    """Resume los préstamos activos del usuario y su próxima cuota.

    Args:
        user_id: identificador del usuario.

    Returns:
        Dict con los préstamos como prestatario y prestamista, la próxima cuota
        pendiente y el total pendiente por moneda.
    """
    loans = list(loans_selectors.list_loans_for_user(user_id=user_id))
    as_borrower = [loan for loan in loans if loan.borrower_user_id == user_id]
    as_lender = [loan for loan in loans if loan.lender_user_id == user_id]

    pending = []
    for loan in as_borrower:
        if loan.status != ACTIVE:
            continue
        for installment in loan.installments.all():
            if installment.status == PENDING:
                pending.append(installment)

    next_installment = min(
        pending,
        key=lambda installment: (installment.due_date, installment.number),
        default=None,
    )
    pending_by_currency: dict[str, Decimal] = {}
    for installment in pending:
        currency = installment.loan.currency
        pending_by_currency[currency] = (
            pending_by_currency.get(currency, Decimal('0.00')) + installment.amount
        )

    return {
        'borrower_active': sum(1 for loan in as_borrower if loan.status == ACTIVE),
        'lender_active': sum(1 for loan in as_lender if loan.status == ACTIVE),
        'next_installment': (
            {
                'loan_id': str(next_installment.loan_id),
                'number': next_installment.number,
                'due_date': next_installment.due_date.isoformat(),
                'amount': str(next_installment.amount),
                'currency': next_installment.loan.currency,
            }
            if next_installment is not None
            else None
        ),
        'pending_by_currency': {
            currency: str(amount) for currency, amount in pending_by_currency.items()
        },
    }


def get_investments_summary(user_id: uuid.UUID) -> dict:
    """Resume las posiciones de inversión activas del usuario.

    Args:
        user_id: identificador del usuario.

    Returns:
        Dict con la cantidad de posiciones, los totales por moneda y el próximo
        vencimiento.
    """
    positions = [
        position
        for position in investments_selectors.list_positions_for_user(user_id=user_id)
        if position.status == ACTIVE
    ]
    by_currency: dict[str, dict] = {}
    for position in positions:
        currency = position.product.currency
        entry = by_currency.setdefault(
            currency,
            {'count': 0, 'amount': Decimal('0.00'), 'interest': Decimal('0.00')},
        )
        entry['count'] += 1
        entry['amount'] += position.amount
        entry['interest'] += position.interest_amount

    next_maturity = min(
        (position.maturity_date for position in positions),
        default=None,
    )
    return {
        'count': len(positions),
        'by_currency': {
            currency: {
                'count': entry['count'],
                'amount': str(entry['amount']),
                'interest': str(entry['interest']),
            }
            for currency, entry in by_currency.items()
        },
        'next_maturity': next_maturity.isoformat() if next_maturity else None,
    }


def get_offers_summary(user_id: uuid.UUID) -> dict:
    """Resume las ofertas de préstamo publicadas por el usuario.

    Args:
        user_id: identificador del usuario.

    Returns:
        Dict con la cantidad de ofertas activas y el total por moneda.
    """
    offers = [
        offer
        for offer in offers_selectors.list_offers_for_lender(lender_user_id=user_id)
        if offer.status == ACTIVE
    ]
    by_currency: dict[str, Decimal] = {}
    for offer in offers:
        by_currency[offer.currency] = (
            by_currency.get(offer.currency, Decimal('0.00')) + offer.amount
        )
    return {
        'active': len(offers),
        'by_currency': {currency: str(amount) for currency, amount in by_currency.items()},
    }


def get_kyc_status(user_id: uuid.UUID) -> str:
    """Devuelve el estado KYC vigente: approved, pending, rejected o missing."""
    verification = identity_selectors.get_kyc_for_user(user_id=user_id)
    if verification is None:
        return 'missing'
    return verification.status
