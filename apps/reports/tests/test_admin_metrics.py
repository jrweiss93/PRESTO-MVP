"""Tests del panel de métricas del admin."""

import pytest
from django.utils import timezone

from apps.identity.tests.factories import BiometricCheckFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_admin_metrics_renders_and_counts_verified_users(admin_client):
    """El dashboard responde y cuenta usuarios verificados y biometrías aprobadas."""
    UserFactory(email_verified_at=timezone.now())
    BiometricCheckFactory()

    response = admin_client.get('/admin/metrics/')

    assert response.status_code == 200
    metrics = response.context['metrics']
    assert metrics['users']['total'] >= 2
    assert metrics['users']['verified'] == 1
    assert metrics['kyc']['biometric_passed'] == 1
