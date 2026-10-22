"""Tests de los modelos de payments."""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.payments.models import Payment, WebhookEvent
from apps.payments.tests.factories import PaymentFactory, WebhookEventFactory

pytestmark = pytest.mark.django_db


def test_payment_rejects_a_non_positive_amount():
    """El importe del pago tiene que ser mayor que cero."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PaymentFactory(amount=Decimal('0.00'))


def test_payment_idempotency_key_is_unique_per_user():
    """La clave de idempotencia es única por usuario."""
    user_id = PaymentFactory().user_id
    PaymentFactory(user_id=user_id, idempotency_key='misma-clave')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PaymentFactory(user_id=user_id, idempotency_key='misma-clave')


def test_payment_idempotency_key_can_repeat_across_users():
    """Dos usuarios distintos pueden usar la misma clave."""
    PaymentFactory(idempotency_key='misma-clave')
    PaymentFactory(idempotency_key='misma-clave')

    assert Payment.objects.filter(idempotency_key='misma-clave').count() == 2


def test_payment_provider_reference_is_unique():
    """La referencia del proveedor es única."""
    PaymentFactory(provider_reference='ref-unica')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PaymentFactory(provider_reference='ref-unica')


def test_webhook_event_is_unique_per_provider():
    """El mismo evento del proveedor no se guarda dos veces."""
    WebhookEventFactory(provider='simulated', external_id='evento-1')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            WebhookEventFactory(provider='simulated', external_id='evento-1')


def test_webhook_event_of_another_provider_is_a_different_event():
    """El mismo identificador en otro proveedor es otro evento."""
    WebhookEventFactory(provider='simulated', external_id='evento-1')
    WebhookEventFactory(provider='mercadopago', external_id='evento-1')

    assert WebhookEvent.objects.filter(external_id='evento-1').count() == 2


def test_payment_str_is_readable():
    """El `str` del pago describe la operación."""
    payment = PaymentFactory(direction=Payment.Direction.DEPOSIT, amount=Decimal('50.00'))

    assert 'deposit' in str(payment)
    assert '50.00' in str(payment)
