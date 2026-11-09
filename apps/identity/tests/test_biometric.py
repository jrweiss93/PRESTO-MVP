"""Tests de la validación biométrica simulada."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.identity.exceptions import InvalidBiometricSample
from apps.identity.models import BiometricCheck
from apps.identity.services import register_user, run_biometric_check, submit_kyc
from apps.identity.tests.factories import BiometricCheckFactory, UserFactory

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


def make_user_with_kyc(email: str = 'biometrico@example.com'):
    """Crea un usuario con una verificación KYC pendiente."""
    user = register_user(email=email, password='TestPass123!')
    verification = submit_kyc(user=user, documents={'tipo': 'dni'})
    return user, verification


# ---- servicio ----


def test_biometric_check_passes_with_gesture_and_no_mismatch():
    """Con gesto de vida y sin mismatch, la validación aprueba."""
    user, verification = make_user_with_kyc()

    check = run_biometric_check(
        user=user, kyc_verification=verification, sample={'gesture': 'blink'}
    )

    assert check.status == BiometricCheck.Status.PASSED
    assert check.liveness_score == Decimal('0.98')
    assert check.match_score == Decimal('0.96')
    assert check.provider == 'simulated'
    assert check.result_details['liveness_check'] == 'passed'
    assert check.result_details['face_match'] == 'matched'


def test_biometric_check_fails_on_face_mismatch():
    """Un rostro que no coincide con el documento rechaza la validación."""
    user, verification = make_user_with_kyc()

    check = run_biometric_check(
        user=user,
        kyc_verification=verification,
        sample={'gesture': 'blink', 'mismatch': True},
    )

    assert check.status == BiometricCheck.Status.FAILED
    assert check.match_score == Decimal('0.12')
    assert check.result_details['face_match'] == 'not_matched'


def test_biometric_check_fails_without_liveness():
    """Sin gesto de vida (posible foto/replay) la validación rechaza."""
    user, verification = make_user_with_kyc()

    check = run_biometric_check(user=user, kyc_verification=verification, sample={})

    assert check.status == BiometricCheck.Status.FAILED
    assert check.liveness_score == Decimal('0.15')
    assert check.result_details['liveness_check'] == 'failed'


def test_biometric_check_rejects_non_object_sample():
    """Una muestra que no es un objeto JSON levanta un error de dominio."""
    user, verification = make_user_with_kyc()

    with pytest.raises(InvalidBiometricSample):
        run_biometric_check(user=user, kyc_verification=verification, sample=[1, 2, 3])


def test_biometric_check_stores_a_hash_and_not_the_sample():
    """Se guarda un hash de referencia, nunca la muestra cruda."""
    user, verification = make_user_with_kyc()

    check = run_biometric_check(
        user=user,
        kyc_verification=verification,
        sample={'gesture': 'blink'},
    )

    assert check.sample_hash
    assert len(check.sample_hash) == 64
    assert 'gesture' not in str(check.result_details)


# ---- selector ----


def test_latest_biometric_check_returns_the_most_recent():
    """El selector devuelve la validación más reciente de la verificación."""
    from apps.identity.selectors import get_latest_biometric_check

    user, verification = make_user_with_kyc()
    first = BiometricCheckFactory(user=user, kyc_verification=verification)
    second = BiometricCheckFactory(user=user, kyc_verification=verification)

    assert get_latest_biometric_check(user.id, verification.id).id == second.id
    assert get_latest_biometric_check(user.id).id == second.id
    assert first.id != second.id


# ---- modelo ----


def test_biometric_check_str_identifies_user_and_status():
    """El __str__ identifica al usuario y el estado."""
    check = BiometricCheckFactory()

    assert str(check.user_id) in str(check)
    assert 'passed' in str(check)


# ---- API ----


def test_post_biometric_returns_201_and_passes(client):
    """Ejecutar la validación biométrica por API devuelve 201 con el resultado."""
    user, verification = make_user_with_kyc()
    authenticate(client, user)

    response = client.post(
        f'/api/v1/kyc/{verification.id}/biometric/',
        {'sample': {'gesture': 'blink'}},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['status'] == 'passed'
    assert response.data['liveness_score'] == '0.9800'
    assert response.data['match_score'] == '0.9600'


def test_post_biometric_simulates_a_failure(client):
    """Con mismatch la validación devuelve rejected."""
    user, verification = make_user_with_kyc()
    authenticate(client, user)

    response = client.post(
        f'/api/v1/kyc/{verification.id}/biometric/',
        {'sample': {'gesture': 'blink', 'mismatch': True}},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['status'] == 'failed'


def test_post_biometric_requires_authentication(client):
    """Ejecutar la validación biométrica exige autenticación."""
    user, verification = make_user_with_kyc()

    response = client.post(
        f'/api/v1/kyc/{verification.id}/biometric/',
        {'sample': {'gesture': 'blink'}},
        format='json',
    )

    assert response.status_code == 401
    assert response.data['error']['code'] == 'not_authenticated'


def test_post_biometric_of_other_user_returns_404(client):
    """No se puede validar la verificación KYC de otro usuario."""
    user, verification = make_user_with_kyc(email='dueno@example.com')
    other = UserFactory(email='intruso@example.com')
    authenticate(client, other)

    response = client.post(
        f'/api/v1/kyc/{verification.id}/biometric/',
        {'sample': {'gesture': 'blink'}},
        format='json',
    )

    assert response.status_code == 404
    assert response.data['error']['code'] == 'not_found'


def test_post_biometric_rejects_non_object_sample(client):
    """Una muestra no válida devuelve 400."""
    user, verification = make_user_with_kyc()
    authenticate(client, user)

    response = client.post(
        f'/api/v1/kyc/{verification.id}/biometric/',
        {'sample': [1, 2, 3]},
        format='json',
    )

    assert response.status_code == 400
    assert response.data['error']['code'] == 'validation_error'


def test_get_biometric_lists_checks(client):
    """El GET lista las validaciones biométricas de la verificación."""
    user, verification = make_user_with_kyc()
    run_biometric_check(user=user, kyc_verification=verification, sample={'gesture': 'blink'})
    authenticate(client, user)

    response = client.get(f'/api/v1/kyc/{verification.id}/biometric/')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['status'] == 'passed'


def test_kyc_detail_includes_the_latest_biometric_check(client):
    """El detalle de la verificación expone la validación biométrica."""
    user, verification = make_user_with_kyc()
    run_biometric_check(user=user, kyc_verification=verification, sample={'gesture': 'blink'})
    authenticate(client, user)

    response = client.get(f'/api/v1/kyc/{verification.id}/')

    assert response.status_code == 200
    assert response.data['biometric']['status'] == 'passed'


def test_kyc_list_includes_biometric(client):
    """El estado KYC propio incluye el campo biometric (null sin validación)."""
    user, verification = make_user_with_kyc()
    authenticate(client, user)

    response = client.get('/api/v1/kyc/')

    assert response.status_code == 200
    assert response.data['id'] == str(verification.id)
    assert response.data['biometric'] is None


# ---- auto-aprobación en demo ----


def test_passing_biometric_auto_approves_kyc_in_demo(settings):
    """En modo demo, una biometría aprobada resuelve el KYC automáticamente."""
    from apps.identity.selectors import get_kyc_for_user

    settings.DEMO_AUTO_APPROVE_KYC = True
    settings.LEDGER_SIMULATED_DEPOSITS_ENABLED = True
    user, verification = make_user_with_kyc(email='auto-demo@example.com')

    check = run_biometric_check(
        user=user, kyc_verification=verification, sample={'gesture': 'blink'}
    )

    assert check.status == BiometricCheck.Status.PASSED
    kyc = get_kyc_for_user(user_id=user.id)
    assert kyc.status == 'approved'
    assert kyc.resolved_by_user_id is None


def test_failed_biometric_does_not_auto_approve_kyc(settings):
    """Una biometría rechazada no aprueba el KYC, ni en demo."""
    from apps.identity.selectors import get_kyc_for_user

    settings.DEMO_AUTO_APPROVE_KYC = True
    user, verification = make_user_with_kyc(email='auto-falla@example.com')

    run_biometric_check(
        user=user,
        kyc_verification=verification,
        sample={'gesture': 'blink', 'mismatch': True},
    )

    kyc = get_kyc_for_user(user_id=user.id)
    assert kyc.status == 'pending'


def test_passing_biometric_does_not_auto_approve_without_flag(settings):
    """Sin el flag de auto-aprobación, el KYC sigue pendiente (flujo manual)."""
    from apps.identity.selectors import get_kyc_for_user

    settings.DEMO_AUTO_APPROVE_KYC = False
    user, verification = make_user_with_kyc(email='manual@example.com')

    run_biometric_check(user=user, kyc_verification=verification, sample={'gesture': 'blink'})

    kyc = get_kyc_for_user(user_id=user.id)
    assert kyc.status == 'pending'
