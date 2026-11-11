"""Tests de las cuentas de respaldo y del cierre de cuenta."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.models import BackupAccount
from apps.identity.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def authenticate(client, user):
    """Autentica el cliente con un access token del usuario."""
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


def create_account(client, **overrides):
    """Crea una cuenta de respaldo por API y devuelve la respuesta."""
    payload = {
        'provider': 'bank',
        'display_name': 'Banco demo',
        'account_ref': '0000000000001234',
        'currency': 'ARS',
        'declared_balance': '50000.00',
        **overrides,
    }
    return client.post('/api/v1/backup-accounts/', payload, format='json')


@override_settings(DEMO_MODE=True)
def test_create_backup_account_returns_pending_with_masked_ref():
    """La cuenta se crea pendiente y no expone la referencia completa."""
    client = authenticate(APIClient(), UserFactory(email='respaldo@example.com'))

    response = create_account(client)

    assert response.status_code == 201
    assert response.data['status'] == 'pending'
    assert response.data['masked_ref'] == '****1234'
    assert '123456' in response.data['verification_hint']


def test_list_backup_accounts_returns_only_own():
    """Cada usuario ve solo sus cuentas de respaldo."""
    owner = UserFactory(email='respaldo-owner@example.com')
    other = UserFactory(email='respaldo-other@example.com')
    client = authenticate(APIClient(), owner)
    create_account(client)
    client.credentials()
    authenticate(client, other)

    response = client.get('/api/v1/backup-accounts/')

    assert response.status_code == 200
    assert response.data == []


def test_verify_backup_account_with_the_demo_code():
    """El código de la demo marca la cuenta como verificada."""
    client = authenticate(APIClient(), UserFactory(email='respaldo-verde@example.com'))
    created = create_account(client).data

    response = client.post(
        f'/api/v1/backup-accounts/{created["id"]}/verify/',
        {'code': '123456'},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['status'] == 'verified'
    assert response.data['verified_at'] is not None


def test_verify_backup_account_rejects_a_wrong_code():
    """Un código incorrecto no verifica la cuenta."""
    client = authenticate(APIClient(), UserFactory(email='respaldo-code@example.com'))
    created = create_account(client).data

    response = client.post(
        f'/api/v1/backup-accounts/{created["id"]}/verify/',
        {'code': '000000'},
        format='json',
    )

    assert response.status_code == 400
    assert response.data['error']['code'] == 'validation_error'


def test_duplicate_backup_account_returns_400():
    """No se puede vincular dos veces la misma cuenta."""
    client = authenticate(APIClient(), UserFactory(email='respaldo-dup@example.com'))
    create_account(client)

    response = create_account(client)

    assert response.status_code == 400


def test_delete_pending_backup_account():
    """Una cuenta sin préstamo activo se puede desvincular."""
    client = authenticate(APIClient(), UserFactory(email='respaldo-del@example.com'))
    created = create_account(client).data

    response = client.delete(f'/api/v1/backup-accounts/{created["id"]}/')

    assert response.status_code == 204
    assert not BackupAccount.objects.filter(id=created['id']).exists()


def test_delete_backup_account_is_blocked_with_an_active_loan():
    """Con un préstamo activo no se puede desvincular la cuenta."""
    client = authenticate(APIClient(), UserFactory(email='respaldo-loan@example.com'))
    created = create_account(client).data

    with patch(
        'apps.identity.services.has_active_loan_as_borrower',
        return_value=True,
    ):
        response = client.delete(f'/api/v1/backup-accounts/{created["id"]}/')

    assert response.status_code == 403
    assert 'préstamo activo' in response.data['error']['message']


def test_close_account_is_blocked_with_active_operations():
    """No se puede cerrar la cuenta con préstamos o inversiones activas."""
    user = UserFactory(email='cierre-bloqueado@example.com')
    client = authenticate(APIClient(), user)

    with patch(
        'apps.identity.services.get_active_financial_operations',
        return_value={'loans': 1, 'positions': 0},
    ):
        response = client.post(
            '/api/v1/auth/me/close/',
            {'confirm': True},
            format='json',
        )

    assert response.status_code == 403
    user.refresh_from_db()
    assert user.is_active is True


def test_close_account_deactivates_the_user():
    """Sin operaciones activas, la cuenta se cierra lógicamente."""
    user = UserFactory(email='cierre-ok@example.com')
    client = authenticate(APIClient(), user)

    response = client.post('/api/v1/auth/me/close/', {'confirm': True}, format='json')

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_active is False


def test_close_account_requires_confirmation():
    """El cierre exige confirmación explícita."""
    user = UserFactory(email='cierre-confirm@example.com')
    client = authenticate(APIClient(), user)

    response = client.post('/api/v1/auth/me/close/', {'confirm': False}, format='json')

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.is_active is True


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_repayment_source_requires_a_verified_account():
    """Sin cuenta verificada no se puede aceptar un préstamo."""
    from apps.identity.exceptions import BackupAccountRequired
    from apps.identity.services import require_repayment_source

    user = UserFactory(email='repago-sin-cuenta@example.com')

    with pytest.raises(BackupAccountRequired):
        require_repayment_source(
            user_id=user.id,
            currency='ARS',
            minimum_balance=Decimal('1000.00'),
        )


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_repayment_source_requires_enough_declared_balance():
    """La cuenta verificada tiene que cubrir la primera cuota."""
    from apps.identity.exceptions import InsufficientRepaymentCapacity
    from apps.identity.services import (
        create_backup_account,
        require_repayment_source,
        verify_backup_account,
    )

    user = UserFactory(email='repago-saldo-bajo@example.com')
    account = create_backup_account(
        user=user,
        provider='bank',
        display_name='Banco demo',
        account_ref='0000000000009999',
        currency='ARS',
        declared_balance=Decimal('500.00'),
    )
    verify_backup_account(user=user, account_id=account.id, code='123456')

    with pytest.raises(InsufficientRepaymentCapacity):
        require_repayment_source(
            user_id=user.id,
            currency='ARS',
            minimum_balance=Decimal('1000.00'),
        )


@override_settings(REPAYMENT_SOURCE_REQUIRED=True)
def test_repayment_source_accepts_a_verified_account_with_enough_balance():
    """Una cuenta verificada con saldo suficiente habilita el préstamo."""
    from apps.identity.services import (
        create_backup_account,
        require_repayment_source,
        verify_backup_account,
    )

    user = UserFactory(email='repago-ok@example.com')
    account = create_backup_account(
        user=user,
        provider='bank',
        display_name='Banco demo',
        account_ref='0000000000008888',
        currency='ARS',
        declared_balance=Decimal('5000.00'),
    )
    verify_backup_account(user=user, account_id=account.id, code='123456')

    require_repayment_source(
        user_id=user.id,
        currency='ARS',
        minimum_balance=Decimal('1000.00'),
    )
