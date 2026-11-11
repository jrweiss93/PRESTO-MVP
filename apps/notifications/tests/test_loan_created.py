"""Tests de la notificación que se genera al crear un préstamo."""

from decimal import Decimal

import pytest

from apps.ledger.services import deposit
from apps.loans.services import accept_offer
from apps.loans.tests.factories import create_approved_user
from apps.notifications.models import Notification
from apps.notifications.services import set_preference
from apps.offers.services import create_offer

pytestmark = pytest.mark.django_db


def _prepare_offer():
    """Crea un prestamista con fondos y una oferta activa."""
    lender = create_approved_user(email='notif-prestamista@example.com', profile_kind='lender')
    borrower = create_approved_user(email='notif-prestatario@example.com', profile_kind='borrower')
    deposit(
        user_id=lender.id,
        currency='ARS',
        amount=Decimal('10000.00'),
        idempotency_key='notif-prestamo-fondos',
    )
    offer = create_offer(
        lender_user_id=lender.id,
        amount=Decimal('5000.00'),
        currency='ARS',
        interest_rate=Decimal('24.00'),
        term_months=3,
    )
    return lender, borrower, offer


def test_accept_offer_notifies_both_parties():
    """Aceptar la oferta avisa al prestamista y al prestatario."""
    lender, borrower, offer = _prepare_offer()

    loan = accept_offer(
        borrower_user_id=borrower.id,
        offer_id=offer.id,
        idempotency_key='notif-prestamo-aceptar',
    )

    notifications = Notification.objects.filter(
        event_type=Notification.EventType.LOAN_CREATED,
        reference_id=loan.id,
    )
    assert set(notifications.values_list('user_id', flat=True)) == {lender.id, borrower.id}


def test_accept_offer_notifies_once_per_party_when_idempotent():
    """Repetir la misma aceptación no duplica los avisos."""
    _, borrower, offer = _prepare_offer()

    accept_offer(
        borrower_user_id=borrower.id,
        offer_id=offer.id,
        idempotency_key='notif-prestamo-idem',
    )
    accept_offer(
        borrower_user_id=borrower.id,
        offer_id=offer.id,
        idempotency_key='notif-prestamo-idem',
    )

    assert Notification.objects.filter(event_type=Notification.EventType.LOAN_CREATED).count() == 2


def test_loan_created_respects_the_preference_of_the_lender():
    """Si el prestamista desactivó el evento, no recibe el aviso."""
    lender, borrower, offer = _prepare_offer()
    set_preference(
        user_id=lender.id,
        event_type=Notification.EventType.LOAN_CREATED,
        enabled=False,
    )

    loan = accept_offer(
        borrower_user_id=borrower.id,
        offer_id=offer.id,
        idempotency_key='notif-prestamo-preferencia',
    )

    notifications = Notification.objects.filter(
        event_type=Notification.EventType.LOAN_CREATED,
        reference_id=loan.id,
    )
    assert set(notifications.values_list('user_id', flat=True)) == {borrower.id}


def test_resolving_kyc_does_not_create_a_loan_notification():
    """La aprobación de KYC no dispara el aviso de préstamo."""
    user = create_approved_user(email='notif-kyc@example.com')

    assert not Notification.objects.filter(
        user_id=user.id,
        event_type=Notification.EventType.LOAN_CREATED,
    ).exists()
