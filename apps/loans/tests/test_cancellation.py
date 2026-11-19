"""Tests de cancelación y de quitar préstamos de la lista."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.loans.tests.factories import create_approved_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def authenticate(client, user):
    """Autentica el cliente con un access token del usuario."""
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


def make_loan():
    """Crea un préstamo activo entre un prestamista y un prestatario."""
    from apps.ledger.services import deposit
    from apps.loans.services import accept_offer
    from apps.offers.services import create_offer

    lender = create_approved_user(
        email='cancel-prestamista@example.com',
        profile_kind='lender',
    )
    borrower = create_approved_user(
        email='cancel-prestatario@example.com',
        profile_kind='borrower',
    )
    deposit(
        user_id=lender.id,
        currency='ARS',
        amount=Decimal('10000.00'),
        idempotency_key='cancel-fund',
    )
    offer = create_offer(
        lender_user_id=lender.id,
        amount=Decimal('10000.00'),
        currency='ARS',
        interest_rate=Decimal('24.00'),
        term_months=12,
    )
    loan = accept_offer(
        borrower_user_id=borrower.id,
        offer_id=offer.id,
        idempotency_key='cancel-accept',
    )
    return loan, borrower, lender


def wallet_balance(user_id):
    from apps.ledger.selectors import get_user_wallet

    wallet = get_user_wallet(user_id=user_id, currency='ARS')
    return wallet.balance if wallet else Decimal('0.00')


def test_cancel_reverses_money_and_cancels_installments(client):
    """Cancelar revierte el desembolso y anula todas las cuotas."""
    from apps.loans.models import Installment, Loan

    loan, borrower, lender = make_loan()
    assert wallet_balance(borrower.id) == Decimal('10000.00')
    assert wallet_balance(lender.id) == Decimal('0.00')

    authenticate(client, borrower)
    response = client.post(f'/api/v1/loans/{loan.id}/cancel/')

    assert response.status_code == 200
    assert response.data['status'] == Loan.Status.CANCELLED
    assert wallet_balance(borrower.id) == Decimal('0.00')
    assert wallet_balance(lender.id) == Decimal('10000.00')
    assert not loan.installments.exclude(status=Installment.Status.CANCELLED).exists()


def test_cancel_after_a_payment_is_rejected(client):
    """No se puede cancelar si ya hay una cuota pagada."""
    loan, borrower, _lender = make_loan()
    authenticate(client, borrower)
    assert client.post(f'/api/v1/loans/{loan.id}/installments/1/pay/').status_code == 200

    response = client.post(f'/api/v1/loans/{loan.id}/cancel/')

    assert response.status_code == 400


def test_lender_can_cancel_and_third_party_cannot(client):
    """Cualquiera de las partes puede cancelar; un tercero recibe 404."""
    loan, _borrower, lender = make_loan()
    third = create_approved_user(email='cancel-tercero@example.com')
    authenticate(client, third)
    assert client.post(f'/api/v1/loans/{loan.id}/cancel/').status_code == 404

    authenticate(client, lender)
    response = client.post(f'/api/v1/loans/{loan.id}/cancel/')
    assert response.status_code == 200


def test_archive_hides_only_for_the_user_who_removes_it(client):
    """Quitar de la lista es una acción por usuario, no un borrado."""
    loan, borrower, lender = make_loan()
    authenticate(client, borrower)
    client.post(f'/api/v1/loans/{loan.id}/cancel/')
    assert client.post(f'/api/v1/loans/{loan.id}/archive/').status_code == 204
    assert client.get('/api/v1/loans/').data['results'] == []

    authenticate(client, lender)
    assert [item['id'] for item in client.get('/api/v1/loans/').data['results']] == [str(loan.id)]
    assert client.post(f'/api/v1/loans/{loan.id}/archive/').status_code == 204
    assert client.get('/api/v1/loans/').data['results'] == []


def test_active_loan_cannot_be_archived(client):
    """No se oculta un préstamo activo: primero hay que cancelarlo o pagarlo."""
    loan, borrower, _lender = make_loan()
    authenticate(client, borrower)

    response = client.post(f'/api/v1/loans/{loan.id}/archive/')

    assert response.status_code == 400
