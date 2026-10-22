"""Tests del system check `legal.W001` (recordatorio de revisión legal)."""

import pytest
from django.core.checks import Warning
from django.test import override_settings

from apps.core.checks import check_legal_review_acknowledged


@pytest.mark.parametrize('app_configs', [None])
def test_the_check_warns_while_the_review_is_pending(app_configs):
    """Mientras nadie la haya marcado como revisada, el check avisa."""
    with override_settings(LEGAL_REVIEW_ACKNOWLEDGED=False):
        messages = check_legal_review_acknowledged(app_configs)

    assert len(messages) == 1
    assert messages[0].id == 'legal.W001'
    assert isinstance(messages[0], Warning)


@pytest.mark.parametrize('app_configs', [None])
def test_the_check_is_silent_once_the_review_is_acknowledged(app_configs):
    """Con el pendiente reconocido, el check no dice nada."""
    with override_settings(LEGAL_REVIEW_ACKNOWLEDGED=True):
        messages = check_legal_review_acknowledged(app_configs)

    assert messages == []


def test_the_check_is_registered():
    """El check está registrado en Django, así que `manage.py check` lo muestra."""
    from django.core.checks import registry

    registered = registry.registry.get_checks()
    assert check_legal_review_acknowledged in registered
