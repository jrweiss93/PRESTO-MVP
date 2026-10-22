"""Tests de la API de pagos."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.identity.services import register_user
from apps.payments.models import Payment
from apps.payments.tests.factories import PaymentFactory, create_approved_user

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


def balance_of(user_id, currency='ARS'):
    """Devuelve el saldo de la billetera del usuario."""
    from apps.ledger.selectors import get_user_wallet

    wallet = get_user_wallet(user_id=user_id, currency=currency)
    return wallet.balance if wallet is not None else Decimal('0.00')


def test_payments_list_requires_authentication(client):
    """El listado de pagos exige autenticación."""
    response = client.get('/api/v1/payments/')

    assert response.status_code == 401
    assert response.data['error']['code'] == 'not_authenticated'


def test_payments_list_returns_only_own_payments(client):
    """El listado devuelve solo los pagos del usuario autenticado."""
    user = create_approved_user()
    other = create_approved_user(email='otros@example.com')
    PaymentFactory(user_id=user.id)
    PaymentFactory(user_id=other.id)
    authenticate(client, user)

    response = client.get('/api/v1/payments/')

    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['provider_reference'].startswith('sim-ref-')


def test_payment_detail_of_another_user_is_not_found(client):
    """El detalle de un pago ajeno responde 404."""
    user = create_approved_user()
    other = create_approved_user(email='otros@example.com')
    payment = PaymentFactory(user_id=other.id)
    authenticate(client, user)

    response = client.get(f'/api/v1/payments/{payment.id}/')

    assert response.status_code == 404
    assert response.data['error']['code'] == 'not_found'


def test_create_payment_requires_idempotency_key(client):
    """Crear un pago sin Idempotency-Key responde 400."""
    user = create_approved_user()
    authenticate(client, user)

    response = client.post(
        '/api/v1/payments/',
        {'direction': 'deposit', 'amount': '100.00', 'currency': 'ARS'},
        format='json',
    )

    assert response.status_code == 400
    assert 'idempotency_key' in response.data['error']['details']


def test_create_deposit_confirms_the_payment_and_credits_the_wallet(client):
    """Un depósito con el proveedor simulado se confirma y acredita el saldo."""
    user = create_approved_user()
    authenticate(client, user)

    response = client.post(
        '/api/v1/payments/',
        {'direction': 'deposit', 'amount': '1000.00', 'currency': 'ARS'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-1',
    )

    assert response.status_code == 201
    assert response.data['status'] == Payment.Status.CONFIRMED
    assert response.data['amount'] == '1000.00'
    assert response.data['direction'] == Payment.Direction.DEPOSIT
    assert response.data['ledger_transaction_id'] is not None
    assert balance_of(user.id) == Decimal('1000.00')


def test_create_payment_requires_kyc(client):
    """Crear un pago sin KYC aprobada responde 403."""
    user = register_user(email='sin-kyc@example.com', password='TestPass123!')
    authenticate(client, user)

    response = client.post(
        '/api/v1/payments/',
        {'direction': 'deposit', 'amount': '100.00', 'currency': 'ARS'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-2',
    )

    assert response.status_code == 403
    assert response.data['error']['code'] == 'permission_denied'


def test_repeated_idempotency_key_does_not_move_the_money_twice(client):
    """Repetir la operación con la misma clave no mueve el saldo dos veces."""
    user = create_approved_user()
    authenticate(client, user)
    payload = {'direction': 'deposit', 'amount': '100.00', 'currency': 'ARS'}

    first = client.post(
        '/api/v1/payments/',
        payload,
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-3',
    )
    second = client.post(
        '/api/v1/payments/',
        payload,
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-3',
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.data['id'] == first.data['id']
    assert balance_of(user.id) == Decimal('100.00')


def test_idempotency_key_with_another_payload_conflicts(client):
    """La misma clave con otro payload responde 400."""
    user = create_approved_user()
    authenticate(client, user)
    client.post(
        '/api/v1/payments/',
        {'direction': 'deposit', 'amount': '100.00', 'currency': 'ARS'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-4',
    )

    response = client.post(
        '/api/v1/payments/',
        {'direction': 'deposit', 'amount': '500.00', 'currency': 'ARS'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-4',
    )

    assert response.status_code == 400
    assert 'idempotency_key' in response.data['error']['details']


def test_create_transfer_moves_the_money_to_the_destination(client):
    """Una transferencia mueve el saldo a la billetera del otro usuario."""
    user = create_approved_user()
    destination = create_approved_user(email='destino-api@example.com')
    authenticate(client, user)
    client.post(
        '/api/v1/payments/',
        {'direction': 'deposit', 'amount': '1000.00', 'currency': 'ARS'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-5',
    )

    response = client.post(
        '/api/v1/payments/',
        {
            'direction': 'transfer',
            'amount': '250.00',
            'currency': 'ARS',
            'destination_user_id': str(destination.id),
        },
        format='json',
        HTTP_IDEMPOTENCY_KEY='tr-api-1',
    )

    assert response.status_code == 201
    assert response.data['status'] == Payment.Status.CONFIRMED
    assert balance_of(user.id) == Decimal('750.00')
    assert balance_of(destination.id) == Decimal('250.00')


def test_create_transfer_without_destination_is_rejected(client):
    """Una transferencia sin destino responde 400."""
    user = create_approved_user()
    authenticate(client, user)

    response = client.post(
        '/api/v1/payments/',
        {'direction': 'transfer', 'amount': '250.00', 'currency': 'ARS'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='tr-api-2',
    )

    assert response.status_code == 400
    assert 'destination_user_id' in response.data['error']['details']


def test_create_payment_with_invalid_amount_is_rejected(client):
    """Un importe no positivo responde 400."""
    user = create_approved_user()
    authenticate(client, user)

    response = client.post(
        '/api/v1/payments/',
        {'direction': 'deposit', 'amount': '0.00', 'currency': 'ARS'},
        format='json',
        HTTP_IDEMPOTENCY_KEY='dep-api-6',
    )

    assert response.status_code == 400


def test_webhook_needs_no_authentication_and_ignores_unknown_payments(client):
    """El webhook no pide autenticación y descarta eventos sin pago."""
    response = client.post(
        '/api/v1/payments/webhooks/simulated/',
        {'id': 'evt-999', 'status': 'confirmed', 'action': 'payment.approved'},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['status'] == 'ignored'
    assert response.data['payment_id'] is None


def test_webhook_of_an_unknown_provider_is_not_found(client):
    """Un webhook de un proveedor no habilitado responde 404."""
    response = client.post(
        '/api/v1/payments/webhooks/otro/',
        {'id': 'evt-1000'},
        format='json',
    )

    assert response.status_code == 404
    assert response.data['error']['code'] == 'not_found'


def test_webhook_confirms_the_payment(client):
    """El webhook simulado confirma el pago pendiente y mueve el saldo."""
    user = create_approved_user()
    payment = PaymentFactory(
        user_id=user.id,
        status=Payment.Status.PENDING,
        provider_reference='sim-ref-webhook',
        payload={'external_reference': 'sim-ref-webhook'},
    )

    response = client.post(
        '/api/v1/payments/webhooks/simulated/',
        {
            'id': 'evt-1001',
            'external_reference': 'sim-ref-webhook',
            'status': 'confirmed',
            'action': 'payment.approved',
        },
        format='json',
    )

    assert response.status_code == 200
    assert response.data['status'] == 'processed'
    assert response.data['payment_id'] == str(payment.id)
    payment.refresh_from_db()
    assert payment.status == Payment.Status.CONFIRMED
    assert balance_of(user.id) == Decimal('100.00')
