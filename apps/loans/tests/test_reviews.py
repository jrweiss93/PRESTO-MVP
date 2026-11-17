"""Tests de reseñas y reputación entre las partes de un préstamo."""

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

    lender = create_approved_user(email='review-prestamista@example.com')
    borrower = create_approved_user(email='review-prestatario@example.com')
    deposit(
        user_id=lender.id,
        currency='ARS',
        amount=Decimal('10000.00'),
        idempotency_key='review-fund',
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
        idempotency_key='review-accept',
    )
    return loan, borrower, lender


def test_borrower_can_recommend_lender_and_both_see_it(client):
    """Una parte reseña a la otra y el estado devuelve el intercambio."""
    loan, borrower, lender = make_loan()

    authenticate(client, borrower)
    response = client.post(
        f'/api/v1/loans/{loan.id}/review/',
        {'recommended': True, 'comment': 'Muy claro y cumplidor.'},
        format='json',
    )
    assert response.status_code == 201
    assert response.data['recommended'] is True

    response = client.get(f'/api/v1/loans/{loan.id}/review/')
    assert response.status_code == 200
    assert response.data['my_review']['comment'] == 'Muy claro y cumplidor.'
    assert response.data['counterpart_email'] == 'review-prestamista@example.com'
    assert response.data['counterpart_reputation']['total'] == 1
    assert response.data['counterpart_reputation']['recommendation_rate'] == 100.0

    authenticate(client, lender)
    response = client.get(f'/api/v1/loans/{loan.id}/review/')
    assert response.status_code == 200
    assert response.data['received_review']['recommended'] is True
    assert response.data['my_review'] is None
    assert response.data['counterpart_reputation']['total'] == 0

    response = client.get(f'/api/v1/reviews/users/{lender.id}/')
    assert response.status_code == 200
    assert response.data['total'] == 1
    assert response.data['recommended'] == 1
    assert response.data['recommendation_rate'] == 100.0


def test_duplicate_review_is_rejected(client):
    """Cada parte puede dejar una sola reseña por préstamo."""
    loan, borrower, _lender = make_loan()
    authenticate(client, borrower)

    payload = {'recommended': False, 'comment': 'No cumplió.'}
    assert (
        client.post(
            f'/api/v1/loans/{loan.id}/review/',
            payload,
            format='json',
        ).status_code
        == 201
    )
    response = client.post(
        f'/api/v1/loans/{loan.id}/review/',
        payload,
        format='json',
    )
    assert response.status_code == 400


def test_third_party_cannot_review_the_loan(client):
    """Un usuario ajeno al préstamo recibe 404."""
    loan, _borrower, _lender = make_loan()
    third = create_approved_user(email='review-tercero@example.com')
    authenticate(client, third)

    response = client.post(
        f'/api/v1/loans/{loan.id}/review/',
        {'recommended': True},
        format='json',
    )
    assert response.status_code == 404
