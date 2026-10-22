"""Factories de la app payments."""

import uuid
from decimal import Decimal

import factory

from apps.payments.models import Payment, WebhookEvent


class PaymentFactory(factory.django.DjangoModelFactory):
    """Factory de Payment."""

    class Meta:
        model = Payment

    user_id = factory.LazyFunction(uuid.uuid4)
    direction = Payment.Direction.DEPOSIT
    amount = Decimal('100.00')
    currency = Payment.Currency.ARS
    provider = Payment.Provider.SIMULATED
    provider_reference = factory.Sequence(lambda n: f'sim-ref-{n}')
    status = Payment.Status.PENDING
    idempotency_key = factory.Sequence(lambda n: f'key-{n}')
    request_hash = factory.Sequence(lambda n: f'hash-{n}')
    payload = factory.Dict({})


class WebhookEventFactory(factory.django.DjangoModelFactory):
    """Factory de WebhookEvent."""

    class Meta:
        model = WebhookEvent

    provider = Payment.Provider.SIMULATED
    external_id = factory.Sequence(lambda n: f'event-{n}')
    event_type = 'payment.approved'
    status = WebhookEvent.Status.RECEIVED
    payload = factory.Dict({})


def create_approved_user(email: str = 'payments@example.com'):
    """Crea un usuario con KYC aprobada usando los servicios de identity."""
    from apps.identity.services import register_user, resolve_kyc, submit_kyc

    user = register_user(email=email, password='TestPass123!')
    verification = submit_kyc(user=user, documents={})
    resolve_kyc(
        verification_id=verification.id,
        status='approved',
        resolved_by_user_id=uuid.uuid4(),
    )
    return user
