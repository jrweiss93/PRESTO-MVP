"""Tests del comando `seed_demo`."""

from decimal import Decimal

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Sum

from apps.demo.seeds import DEMO_BORROWER, DEMO_INVESTOR, DEMO_LENDER, seed_demo

pytestmark = pytest.mark.django_db


def _total_balance(currency):
    """Suma los saldos de todas las cuentas de la moneda.

    Args:
        currency: la moneda.

    Returns:
        La suma de los saldos.
    """
    from apps.ledger.models import Account

    return Account.objects.filter(currency=currency).aggregate(total=Sum('balance'))['total']


def test_the_command_says_it_needs_simulated_money():
    """Sin dinero simulado el comando avisa y no siembra."""
    from django.test import override_settings

    with override_settings(LEDGER_SIMULATED_DEPOSITS_ENABLED=False):
        with pytest.raises(CommandError):
            call_command('seed_demo')


def test_seeding_creates_the_whole_scenario():
    """La siembra deja el escenario completo y el ledger cuadrado."""
    summary = seed_demo()

    assert summary.users == [DEMO_BORROWER, DEMO_LENDER, DEMO_INVESTOR]
    assert summary.loan_id
    assert summary.offer_id
    assert _total_balance('ARS') == Decimal('0.00')


def test_seeding_twice_does_not_move_money_twice():
    """La siembra es idempotente: repetirla no duplica movimientos."""
    seed_demo()
    balances = _balances()
    summary = seed_demo()

    assert _balances() == balances
    assert summary.payment_ids == []


def _balances():
    """Devuelve el saldo de la billetera de cada persona de la demo.

    Returns:
        Un diccionario con el saldo por email.
    """
    from apps.identity.models import User
    from apps.ledger import selectors as ledger_selectors

    result = {}
    for email in (DEMO_BORROWER, DEMO_LENDER, DEMO_INVESTOR):
        user = User.objects.get(email=email)
        wallet = ledger_selectors.get_user_wallet(user.id, 'ARS')
        result[email] = wallet.balance if wallet else Decimal('0.00')
    return result


def test_the_scenario_leaves_a_loan_with_a_paid_installment():
    """El préstamo del escenario tiene la primera cuota pagada."""
    from apps.loans import selectors as loan_selectors

    summary = seed_demo()
    installments = loan_selectors.list_installments(summary.loan_id).order_by('number')

    assert installments.count() == 6
    assert installments.first().status == 'paid'
