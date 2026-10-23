"""Tests del comando que crea el superusuario de la demo."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

pytestmark = pytest.mark.django_db

User = get_user_model()

EMAIL = 'admin@presto.demo'
PASSWORD = 'AdminPass123!'


def test_creates_a_superuser_from_the_environment(monkeypatch):
    """Crea el usuario con flags de admin y el email verificado."""
    monkeypatch.setenv('DEMO_SUPERUSER_EMAIL', EMAIL)
    monkeypatch.setenv('DEMO_SUPERUSER_PASSWORD', PASSWORD)

    call_command('create_demo_superuser')

    user = User.objects.get(email=EMAIL)
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True
    assert user.email_verified_at is not None
    assert user.check_password(PASSWORD)


def test_updates_an_existing_user(monkeypatch):
    """Si el email ya existe, lo promueve y le cambia la contraseña."""
    user = User.objects.create_user(email=EMAIL, password='OldPass123!')
    assert user.is_superuser is False
    monkeypatch.setenv('DEMO_SUPERUSER_EMAIL', EMAIL)
    monkeypatch.setenv('DEMO_SUPERUSER_PASSWORD', PASSWORD)

    call_command('create_demo_superuser')

    user.refresh_from_db()
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.check_password(PASSWORD)


def test_requires_the_environment(monkeypatch):
    """Sin email o contraseña el comando falla con un error claro."""
    monkeypatch.delenv('DEMO_SUPERUSER_EMAIL', raising=False)
    monkeypatch.delenv('DEMO_SUPERUSER_PASSWORD', raising=False)

    with pytest.raises(CommandError):
        call_command('create_demo_superuser')


def test_rejects_a_short_password(monkeypatch):
    """Una contraseña corta se rechaza antes de crear el usuario."""
    monkeypatch.setenv('DEMO_SUPERUSER_EMAIL', EMAIL)
    monkeypatch.setenv('DEMO_SUPERUSER_PASSWORD', 'corta')

    with pytest.raises(CommandError):
        call_command('create_demo_superuser')

    assert not User.objects.filter(email=EMAIL).exists()
