"""Tests del chat privado entre las partes de un préstamo."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.loans.tests.factories import create_approved_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def authenticate(client, user):
    """Autentica al cliente con un access token del usuario dado."""
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


def make_loan():
    """Crea un préstamo activo entre un prestamista y un prestatario."""
    from apps.ledger.services import deposit
    from apps.loans.services import accept_offer
    from apps.offers.services import create_offer

    lender = create_approved_user(email='chat-prestamista@example.com')
    borrower = create_approved_user(email='chat-prestatario@example.com')
    deposit(
        user_id=lender.id,
        currency='ARS',
        amount=Decimal('10000.00'),
        idempotency_key='chat-fund',
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
        idempotency_key='chat-accept',
    )
    return loan, borrower, lender


def test_borrower_and_lender_can_exchange_messages(client):
    """Ambas partes pueden enviar y leer los mensajes del préstamo."""
    loan, borrower, lender = make_loan()

    authenticate(client, borrower)
    response = client.post(
        f'/api/v1/loans/{loan.id}/messages/',
        {'body': 'Hola, ¿coordinamos la primera cuota?'},
        format='json',
    )
    assert response.status_code == 201
    assert response.data['sender_user_id'] == str(borrower.id)

    authenticate(client, lender)
    response = client.post(
        f'/api/v1/loans/{loan.id}/messages/',
        {'body': 'Sí, te escribo por acá.'},
        format='json',
    )
    assert response.status_code == 201

    response = client.get(f'/api/v1/loans/{loan.id}/messages/')
    assert response.status_code == 200
    assert [message['body'] for message in response.data] == [
        'Hola, ¿coordinamos la primera cuota?',
        'Sí, te escribo por acá.',
    ]


def test_third_party_cannot_read_or_write_the_chat(client):
    """Un usuario ajeno al préstamo recibe 404 en el chat."""
    loan, _borrower, _lender = make_loan()
    third = create_approved_user(email='chat-tercero@example.com')
    authenticate(client, third)

    assert client.get(f'/api/v1/loans/{loan.id}/messages/').status_code == 404
    response = client.post(
        f'/api/v1/loans/{loan.id}/messages/',
        {'body': 'No debería poder entrar.'},
        format='json',
    )
    assert response.status_code == 404


def test_empty_message_returns_400(client):
    """El mensaje no puede estar vacío."""
    loan, borrower, _lender = make_loan()
    authenticate(client, borrower)

    response = client.post(
        f'/api/v1/loans/{loan.id}/messages/',
        {'body': '   '},
        format='json',
    )

    assert response.status_code == 400
