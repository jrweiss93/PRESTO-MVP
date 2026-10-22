"""Tests del chat de Presti (intenciones por reglas)."""

from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.tests.factories import UserFactory
from apps.investments.tests.factories import PositionFactory
from apps.ledger.tests.factories import AccountFactory
from apps.loans.tests.factories import InstallmentFactory, LoanFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return UserFactory(email='presti@example.com')


@pytest.fixture
def client(user):
    api = APIClient()
    token = RefreshToken.for_user(user)
    api.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return api


def ask(client, message: str):
    """Manda una consulta al chat."""
    return client.post('/api/v1/assistant/chat/', {'message': message}, format='json')


def test_chat_requires_authentication():
    """El chat no es público."""
    response = APIClient().post('/api/v1/assistant/chat/', {'message': 'hola'}, format='json')

    assert response.status_code == 401


def test_chat_answers_the_balance_with_real_data(client, user):
    """El saldo sale de las billeteras del usuario."""
    AccountFactory(user_id=user.id, currency='ARS', balance=Decimal('1500.00'))
    AccountFactory(user_id=user.id, currency='USD', balance=Decimal('20.00'))

    response = ask(client, '¿Cuál es mi saldo?')

    assert response.status_code == 200
    assert response.data['intent'] == 'rules'
    assert 'ARS 1.500,00' in response.data['reply']
    assert 'USD 20,00' in response.data['reply']


def test_chat_answers_the_next_installment(client, user):
    """La cuota próxima sale del préstamo activo del usuario."""
    loan = LoanFactory(
        borrower_user_id=user.id,
        currency='ARS',
        status='active',
    )
    InstallmentFactory(
        loan=loan,
        number=1,
        due_date=date(2026, 11, 1),
        amount=Decimal('945.60'),
        status='pending',
    )

    response = ask(client, '¿Cuánto pago de cuota?')

    assert response.status_code == 200
    assert 'ARS 945,60' in response.data['reply']
    assert '01/11/2026' in response.data['reply']


def test_chat_answers_the_investments_summary(client, user):
    """Las inversiones salen de las posiciones activas."""
    PositionFactory(
        user_id=user.id,
        amount=Decimal('5000.00'),
        interest_amount=Decimal('500.00'),
        status='active',
    )

    response = ask(client, '¿Cómo van mis inversiones?')

    assert response.status_code == 200
    assert 'ARS 5.000,00' in response.data['reply']
    assert 'ARS 500,00' in response.data['reply']


def test_chat_answers_the_legal_framework(client):
    """Las preguntas legales devuelven la ficha curada y el aviso."""
    response = ask(client, '¿Qué dice la CNV sobre invertir?')

    assert response.status_code == 200
    assert response.data['intent'] == 'rules'
    assert 'CNV' in response.data['reply'] or 'oferta pública' in response.data['reply']
    assert 'no es asesoramiento legal' in response.data['reply']


def test_chat_falls_back_with_suggestions(client):
    """Lo que no entiende no se inventa: propone opciones."""
    response = ask(client, 'Contame un chiste')

    assert response.status_code == 200
    assert response.data['intent'] == 'fallback'
    assert 'No entendí' in response.data['reply']


def test_chat_with_an_empty_message(client):
    """Un mensaje vacío no rompe: pide que escriba la consulta."""
    response = ask(client, '')

    assert response.status_code == 200
    assert response.data['intent'] == 'empty'
