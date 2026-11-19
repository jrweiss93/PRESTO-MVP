"""Tests de la simulación de identidad durante el registro."""

import pytest
from rest_framework.test import APIClient

from apps.identity.models import KYCVerification

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_register_with_simulated_identity_creates_kyc_without_full_dni(settings):
    """La simulación guarda solo los últimos 4 dígitos y aprueba KYC en demo."""
    from apps.identity.services import register_user

    settings.DEMO_MODE = True
    user = register_user(
        email='simulada@example.com',
        password='TestPass123!',
        dni='12345678',
        credential_type='dni',
        credential_verified=True,
        face_verified=True,
    )

    verification = KYCVerification.objects.get(user=user)
    assert verification.status == KYCVerification.Status.APPROVED
    assert verification.documents['dni_last4'] == '5678'
    assert '12345678' not in str(verification.documents)
    assert verification.documents['source'] == 'registration_simulation'


def test_register_without_identity_does_not_create_kyc():
    """Si no se simula identidad, el registro sigue igual que antes."""
    from apps.identity.services import register_user

    user = register_user(email='sin-simulacion@example.com', password='TestPass123!')

    assert not KYCVerification.objects.filter(user=user).exists()


def test_api_register_accepts_complete_identity_simulation(client):
    """La API acepta DNI, credencial y rostro simulados."""
    response = client.post(
        '/api/v1/auth/register/',
        {
            'email': 'api-simulada@example.com',
            'password': 'TestPass123!',
            'terms_accepted': True,
            'dni': '30123456',
            'credential_type': 'license',
            'credential_verified': True,
            'face_verified': True,
        },
        format='json',
    )

    assert response.status_code == 201
    verification = KYCVerification.objects.get(user__email='api-simulada@example.com')
    assert verification.status == KYCVerification.Status.PENDING


def test_api_register_rejects_partial_identity_simulation(client):
    """No se puede mandar solo una parte de la simulación."""
    response = client.post(
        '/api/v1/auth/register/',
        {
            'email': 'parcial@example.com',
            'password': 'TestPass123!',
            'terms_accepted': True,
            'dni': '30123456',
            'face_verified': True,
        },
        format='json',
    )

    assert response.status_code == 400
