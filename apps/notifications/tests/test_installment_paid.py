"""Tests de la notificación al prestamista cuando se cobra una cuota."""

from decimal import Decimal

import pytest

from apps.ledger.services import deposit
from apps.loans.services import accept_offer, pay_installment
from apps.loans.tests.factories import create_approved_user
from apps.notifications.models import Notification
from apps.notifications.services import set_preference
from apps.offers.services import create_offer

pytestmark = pytest.mark.django_db


def _prepare_loan():
    """Crea un préstamo con fondos en ambas partes y devuelve sus datos."""
    lender = create_approved_user(email='cuota-prestamista@example.com', profile_kind='lender')
    borrower = create_approved_user(email='cuota-prestatario@example.com', profile_kind='borrower')
    deposit(
        user_id=lender.id,
        currency='ARS',
        amount=Decimal('10000.00'),
        idempotency_key='cuota-fondos-prestamista',
    )
    deposit(
        user_id=borrower.id,
        currency='ARS',
        amount=Decimal('10000.00'),
        idempotency_key='cuota-fondos-prestatario',
    )
    offer = create_offer(
        lender_user_id=lender.id,
        amount=Decimal('5000.00'),
        currency='ARS',
        interest_rate=Decimal('24.00'),
        term_months=3,
    )
    loan = accept_offer(
        borrower_user_id=borrower.id,
        offer_id=offer.id,
        idempotency_key='cuota-aceptar',
    )
    return lender, borrower, loan


def test_paying_an_installment_notifies_the_lender():
    """Pagar una cuota crea el aviso 'Cuota cobrada' del prestamista."""
    lender, borrower, loan = _prepare_loan()

    installment = pay_installment(
        loan_id=loan.id,
        number=1,
        borrower_user_id=borrower.id,
    )

    notification = Notification.objects.get(
        user_id=lender.id,
        event_type=Notification.EventType.INSTALLMENT_PAID,
        reference_id=installment.id,
    )
    assert notification.status == Notification.Status.PENDING


def test_installment_paid_only_notifies_the_lender():
    """El prestatario no recibe el aviso de cobro: él hizo el pago."""
    lender, borrower, loan = _prepare_loan()

    installment = pay_installment(
        loan_id=loan.id,
        number=1,
        borrower_user_id=borrower.id,
    )

    assert not Notification.objects.filter(
        user_id=borrower.id,
        event_type=Notification.EventType.INSTALLMENT_PAID,
        reference_id=installment.id,
    ).exists()


def test_installment_paid_respects_the_lender_preference():
    """Si el prestamista desactivó el evento, no se crea el aviso."""
    lender, borrower, loan = _prepare_loan()
    set_preference(
        user_id=lender.id,
        event_type=Notification.EventType.INSTALLMENT_PAID,
        enabled=False,
    )

    pay_installment(loan_id=loan.id, number=1, borrower_user_id=borrower.id)

    assert not Notification.objects.filter(
        user_id=lender.id,
        event_type=Notification.EventType.INSTALLMENT_PAID,
    ).exists()
