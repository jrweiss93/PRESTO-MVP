"""Tests del regalo de bienvenida del prestatario."""

from decimal import Decimal

import pytest
from django.test import override_settings

from apps.demo.welcome import WELCOME_BONUS_AMOUNT, grant_welcome_bonus
from apps.identity.services import register_user, resolve_kyc, submit_kyc

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _demo_mode(settings):
    """El bono de bienvenida es una funcionalidad de demo."""
    settings.DEMO_MODE = True
    settings.LEDGER_SIMULATED_DEPOSITS_ENABLED = True


def _wallet_balance(user_id):
    """Devuelve el saldo ARS de la billetera del usuario, o 0."""
    from apps.ledger import selectors as ledger_selectors

    wallet = ledger_selectors.get_user_wallet(user_id, 'ARS')
    return wallet.balance if wallet else Decimal('0.00')


def _approved_kyc_user(email: str, profile_kind: str):
    """Crea un usuario con perfil fijo y KYC aprobada."""
    user = register_user(email=email, password='TestPass123!', profile_kind=profile_kind)
    verification = submit_kyc(user=user, documents={})
    resolve_kyc(verification_id=verification.id, status='approved', resolved_by_user_id=user.id)
    return user


def test_welcome_bonus_credits_the_borrower():
    """El regalo acredita 100.000 ARS a un prestatario."""
    user = _approved_kyc_user('regalo-prestatario@example.com', 'borrower')

    granted = grant_welcome_bonus(user.id)

    assert granted is True
    assert _wallet_balance(user.id) == WELCOME_BONUS_AMOUNT


def test_welcome_bonus_is_idempotent():
    """Repetir el regalo no acredita dos veces."""
    user = _approved_kyc_user('regalo-idem@example.com', 'borrower')

    grant_welcome_bonus(user.id)
    grant_welcome_bonus(user.id)

    assert _wallet_balance(user.id) == WELCOME_BONUS_AMOUNT


def test_welcome_bonus_skips_non_borrowers():
    """Prestamistas e inversores no reciben el regalo."""
    lender = _approved_kyc_user('regalo-prestamista@example.com', 'lender')
    investor = _approved_kyc_user('regalo-inversor@example.com', 'investor')

    assert grant_welcome_bonus(lender.id) is False
    assert grant_welcome_bonus(investor.id) is False
    assert _wallet_balance(lender.id) == Decimal('0.00')
    assert _wallet_balance(investor.id) == Decimal('0.00')


@override_settings(DEMO_MODE=True)
def test_welcome_bonus_requires_simulated_deposits():
    """Sin depósitos simulados habilitados el regalo no se acredita."""
    user = _approved_kyc_user('regalo-sin-demo@example.com', 'borrower')

    with override_settings(DEMO_MODE=True, LEDGER_SIMULATED_DEPOSITS_ENABLED=False):
        assert grant_welcome_bonus(user.id) is False

    assert _wallet_balance(user.id) == Decimal('0.00')


def test_kyc_approval_triggers_the_welcome_bonus():
    """Aprobar el KYC de un prestatario acredita el regalo por la señal."""
    user = register_user(
        email='regalo-senal@example.com', password='TestPass123!', profile_kind='borrower'
    )
    verification = submit_kyc(user=user, documents={})

    resolve_kyc(verification_id=verification.id, status='approved', resolved_by_user_id=user.id)

    assert _wallet_balance(user.id) == WELCOME_BONUS_AMOUNT
