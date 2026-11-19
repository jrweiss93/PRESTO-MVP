"""Regla de retiro: un prestatario con deuda vigente no puede retirar."""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.loans.tests.factories import LoanFactory, create_approved_user

pytestmark = pytest.mark.django_db


def fund_user(user, amount: str = '100.00', key: str | None = None) -> None:
    """Deposita saldo simulado en la billetera del usuario."""
    from apps.ledger.services import deposit

    deposit(
        user_id=user.id,
        currency='ARS',
        amount=Decimal(amount),
        idempotency_key=key or f'fund-{uuid.uuid4()}',
    )


def make_withdrawal(user, amount: str = '10.00', key: str | None = None):
    """Pide un retiro de la billetera del usuario."""
    from apps.ledger.services import withdraw

    return withdraw(
        user_id=user.id,
        currency='ARS',
        amount=Decimal(amount),
        idempotency_key=key or f'withdraw-{uuid.uuid4()}',
    )


def authenticate(client: APIClient, user) -> APIClient:
    """Autentica el cliente con un access token del usuario."""
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


def test_borrower_with_an_active_loan_cannot_withdraw():
    """Un préstamo activo bloquea el retiro del prestatario."""
    from apps.ledger.exceptions import WithdrawalBlockedByActiveLoan

    borrower = create_approved_user(email='retiro-activo@example.com')
    fund_user(borrower)
    LoanFactory(
        borrower_user_id=borrower.id,
        lender_user_id=uuid.uuid4(),
    )

    with pytest.raises(WithdrawalBlockedByActiveLoan):
        make_withdrawal(borrower)


def test_borrower_in_default_cannot_withdraw():
    """Un préstamo en mora también bloquea el retiro."""
    from apps.ledger.exceptions import WithdrawalBlockedByActiveLoan
    from apps.loans.models import Loan

    borrower = create_approved_user(email='retiro-mora@example.com')
    fund_user(borrower)
    LoanFactory(
        borrower_user_id=borrower.id,
        lender_user_id=uuid.uuid4(),
        status=Loan.Status.DEFAULTED,
    )

    with pytest.raises(WithdrawalBlockedByActiveLoan):
        make_withdrawal(borrower)


def test_borrower_can_withdraw_after_the_loan_is_paid():
    """Al terminar la deuda, el retiro vuelve a estar disponible."""
    from apps.loans.models import Loan

    borrower = create_approved_user(email='retiro-pagado@example.com')
    fund_user(borrower)
    LoanFactory(
        borrower_user_id=borrower.id,
        lender_user_id=uuid.uuid4(),
        status=Loan.Status.PAID,
    )

    movement = make_withdrawal(borrower)

    assert movement.type == 'withdrawal'


def test_borrower_can_withdraw_after_the_loan_is_cancelled():
    """Un préstamo cancelado libera el retiro."""
    from apps.loans.models import Loan

    borrower = create_approved_user(email='retiro-cancelado@example.com')
    fund_user(borrower)
    LoanFactory(
        borrower_user_id=borrower.id,
        lender_user_id=uuid.uuid4(),
        status=Loan.Status.CANCELLED,
    )

    movement = make_withdrawal(borrower)

    assert movement.type == 'withdrawal'


def test_lender_can_withdraw_while_their_loan_is_active():
    """El prestamista no contrajo la deuda: puede retirar su saldo."""
    lender = create_approved_user(email='retiro-prestamista@example.com')
    fund_user(lender)
    LoanFactory(
        borrower_user_id=uuid.uuid4(),
        lender_user_id=lender.id,
    )

    movement = make_withdrawal(lender)

    assert movement.type == 'withdrawal'


def test_borrower_can_still_deposit_with_an_active_loan():
    """El bloqueo aplica solo al retiro: depositar sigue permitido."""
    borrower = create_approved_user(email='deposito-activo@example.com')
    LoanFactory(
        borrower_user_id=borrower.id,
        lender_user_id=uuid.uuid4(),
    )

    fund_user(borrower, amount='25.00', key='deposito-con-prestamo')

    from apps.ledger.selectors import get_user_wallet

    wallet = get_user_wallet(borrower.id, 'ARS')
    assert wallet.balance == Decimal('25.00')


def test_api_returns_409_with_a_clear_message():
    """La API responde 409 y explica por qué no se puede retirar."""
    borrower = create_approved_user(email='retiro-api@example.com')
    fund_user(borrower)
    LoanFactory(
        borrower_user_id=borrower.id,
        lender_user_id=uuid.uuid4(),
    )
    client = authenticate(APIClient(), borrower)

    response = client.post(
        '/api/v1/ledger/transactions/',
        {'type': 'withdrawal', 'currency': 'ARS', 'amount': '5.00'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='retiro-api-bloqueado',
    )

    assert response.status_code == 409
    assert response.data['error']['code'] == 'withdrawal_blocked'
    assert 'préstamo' in response.data['error']['message']
