"""Crea o actualiza el superusuario de una demo desplegada.

Se usa desde `scripts/create-superuser-remote.ps1`, que conecta la base externa
de Render y pasa el email y la contraseña por variables de entorno.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

MIN_PASSWORD_LENGTH = 12


class Command(BaseCommand):
    """Crea o actualiza un superusuario desde el entorno."""

    help = 'Crea o actualiza un superusuario con DEMO_SUPERUSER_EMAIL y DEMO_SUPERUSER_PASSWORD.'

    def handle(self, *args, **options):
        email = (os.environ.get('DEMO_SUPERUSER_EMAIL') or '').strip().lower()
        password = os.environ.get('DEMO_SUPERUSER_PASSWORD') or ''
        if not email or not password:
            raise CommandError('Faltan DEMO_SUPERUSER_EMAIL o DEMO_SUPERUSER_PASSWORD.')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise CommandError(
                f'La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.'
            )

        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()
        if user is None:
            user = user_model.objects.create_superuser(email=email, password=password)
            action = 'creado'
        else:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            action = 'actualizado'

        if user.email_verified_at is None:
            user.email_verified_at = timezone.now()
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Superusuario {action}: {user.email}'))
