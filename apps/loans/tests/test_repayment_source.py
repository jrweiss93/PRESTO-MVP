"""Tests del requisito de cuenta de respaldo para aceptar préstamos."""

from decimal import Decimal

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.identity.services import (
    create_backup_account,
    verify_backup_account,
)
from apps.ledger.services import deposit
from apps.loans.services import accept_offer
from apps.loans.tests.factories import create_approved_user
from apps.offers.services import create_offer

pytestmark = pytest.mark.django_db


def _prepare_offer():
    """Crea un prestamista con fondos, un prestatario y una oferta."""
    lender = create_approved_user(email='repago-prestamista@example.com', profile_kind='lender')
    borrower = create_approved_user(email='repago-prestatario@example.com', profile_kind='borrower')
    deposit(
        user_id=lender.id,
        currency='ARS',
        amount=Decimal('20000.00'),
        idempotency_key='repago-fondos',
    )
    offer = create_offer(
        lender_user_id=lender.id,
        amount=Decimal('10000.00'),
        currency='ARS',
        interest_rate=Decimal('24.00'),
        term_months=12,
    )
    return lender, borrower, offer


def _add_verified_account(user, balance='5000.00'):
    """Vincula y verifica una cuenta de respaldo para el usuario."""
    account = create_backup_account(
        user=user,
        provider='bank',
        display_name='Banco demo',
        account_ref='0000000000007777',
        currency='ARS',
        declared_balance=Decimal(balance),
    )
    verify_backup_account(user=user, account_id=account.id, code='123456')
    return account


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_accept_offer_requires_a_backup_account():
    """Sin cuenta de respaldo verificada no se crea el préstamo."""
    from apps.identity.exceptions import BackupAccountRequired

    _, borrower, offer = _prepare_offer()

    with pytest.raises(BackupAccountRequired):
        accept_offer(
            borrower_user_id=borrower.id,
            offer_id=offer.id,
            idempotency_key='repago-sin-cuenta',
        )


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_accept_offer_requires_enough_declared_balance():
    """La cuenta verificada no alcanza si no cubre la primera cuota."""
    from apps.identity.exceptions import InsufficientRepaymentCapacity

    _, borrower, offer = _prepare_offer()
    _add_verified_account(borrower, balance='100.00')

    with pytest.raises(InsufficientRepaymentCapacity):
        accept_offer(
            borrower_user_id=borrower.id,
            offer_id=offer.id,
            idempotency_key='repago-saldo-bajo',
        )


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_accept_offer_with_verified_backup_account():
    """Con una cuenta verificada y saldo suficiente el préstamo se crea."""
    _, borrower, offer = _prepare_offer()
    _add_verified_account(borrower)

    loan = accept_offer(
        borrower_user_id=borrower.id,
        offer_id=offer.id,
        idempotency_key='repago-ok',
    )

    assert loan.borrower_user_id == borrower.id
    assert loan.installments.count() == 12


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_api_accept_offer_returns_403_without_backup_account():
    """La API corta la aceptación con un mensaje accionable."""
    from rest_framework_simplejwt.tokens import RefreshToken

    _, borrower, offer = _prepare_offer()
    client = APIClient()
    token = RefreshToken.for_user(borrower)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    response = client.post(
        '/api/v1/loans/',
        {'offer_id': str(offer.id)},
        format='json',
        HTTP_IDEMPOTENCY_KEY='repago-api-sin-cuenta',
    )

    assert response.status_code == 403
    assert 'cuenta de respaldo' in response.data['error']['message']


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_api_accept_offer_succeeds_after_verifying_the_account():
    """La API acepta el préstamo después de verificar la cuenta."""
    from rest_framework_simplejwt.tokens import RefreshToken

    _, borrower, offer = _prepare_offer()
    _add_verified_account(borrower)
    client = APIClient()
    token = RefreshToken.for_user(borrower)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    response = client.post(
        '/api/v1/loans/',
        {'offer_id': str(offer.id)},
        format='json',
        HTTP_IDEMPOTENCY_KEY='repago-api-ok',
    )

    assert response.status_code == 201
    assert response.data['status'] == 'active'


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_accept_offer_does_not_consume_the_offer_when_blocked():
    """Si falta la cuenta, la oferta sigue activa para reintentar."""
    from apps.identity.exceptions import BackupAccountRequired

    _, borrower, offer = _prepare_offer()

    with pytest.raises(BackupAccountRequired):
        accept_offer(
            borrower_user_id=borrower.id,
            offer_id=offer.id,
            idempotency_key='repago-oferta-activa',
        )

    offer.refresh_from_db()
    assert offer.status == 'active'
