import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class UserManager(BaseUserManager):
    """Manager de User que usa el email como campo de login."""

    def create_user(self, email, password=None, **extra_fields):
        """Crea un usuario con el email como identificador.

        Args:
            email: email único del usuario.
            password: contraseña en texto plano; se hashea antes de guardar.
            **extra_fields: campos adicionales del modelo.

        Raises:
            ValueError: si el email viene vacío.
        """
        if not email:
            raise ValueError('El email es obligatorio para crear un usuario.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea un superusuario con is_staff e is_superuser activados.

        Raises:
            ValueError: si se fuerza is_staff o is_superuser en False.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuario de Presto: el email es el único campo de login."""

    username = None

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Cuándo se confirmó el email (null si todavía no se verificó).',
    )
    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Cuándo aceptó los términos y condiciones (null si no los aceptó).',
    )

    @property
    def email_verified(self) -> bool:
        """Indica si el email del usuario ya fue confirmado."""
        return self.email_verified_at is not None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Profile(BaseModel):
    """Datos adicionales del usuario."""

    country_validator = RegexValidator(
        regex=r'^[A-Z]{2}$',
        message='El país debe ser un código ISO 3166-1 alpha-2 (ej. AR, US).',
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=32, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=2, blank=True, validators=[country_validator])

    def __str__(self):
        return f'Profile<{self.user_id}>'


class PrestoProfile(BaseModel):
    """Perfil de Presto que un usuario puede activar.

    Un usuario puede tener los tres perfiles (prestatario, prestamista e
    inversor) y alternar cuál está activo. El perfil activo define qué ve en el
    menú y qué operaciones puede hacer: es la identidad con la que opera en
    cada momento, no un dato estático de la cuenta.
    """

    class Kind(models.TextChoices):
        BORROWER = 'borrower', 'Prestatario'
        LENDER = 'lender', 'Prestamista'
        INVESTOR = 'investor', 'Inversor'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presto_profiles')
    kind = models.CharField(max_length=16, choices=Kind.choices)
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'kind'],
                name='identity_prestoprofile_unique_kind_per_user',
            ),
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_active=True),
                name='identity_prestoprofile_one_active_per_user',
            ),
        ]
        ordering = ['kind']

    def __str__(self):
        return f'PrestoProfile<{self.user_id}:{self.kind}:{self.is_active}>'


class KYCVerification(BaseModel):
    """Solicitud de verificación KYC de un usuario. Se conserva el historial."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobada'
        REJECTED = 'rejected', 'Rechazada'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_verifications')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by_user_id = models.UUIDField(null=True, blank=True)
    documents = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status='pending'),
                name='identity_kycverification_one_pending_per_user',
            ),
        ]
        ordering = ['-requested_at']

    def __str__(self):
        return f'KYCVerification<{self.user_id}:{self.status}>'


class BiometricCheck(BaseModel):
    """Resultado de una validación biométrica simulada.

    Modela el flujo real de una verificación de identidad biométrica (selfie en
    vivo + comparación contra el documento) pero **sin procesar datos
    biométricos reales**: los puntajes de vida y de coincidencia son simulados y
    deterministas, y solo se guarda una referencia (`sample_hash`), nunca la
    muestra ni imágenes.

    El resultado queda como evidencia del KYC; la aprobación final de la
    identidad sigue siendo una decisión del staff (igual que el resto del KYC).
    """

    class Status(models.TextChoices):
        PASSED = 'passed', 'Aprobado'
        FAILED = 'failed', 'Rechazado'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='biometric_checks')
    kyc_verification = models.ForeignKey(
        KYCVerification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='biometric_checks',
    )
    status = models.CharField(max_length=16, choices=Status.choices)
    liveness_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Puntaje de prueba de vida (0 a 1).',
    )
    match_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Puntaje de coincidencia del rostro contra el documento (0 a 1).',
    )
    provider = models.CharField(max_length=32, default='simulated')
    sample_hash = models.CharField(max_length=64, blank=True)
    result_details = models.JSONField(default=dict, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(liveness_score__gte=0, liveness_score__lte=1),
                name='identity_biometriccheck_liveness_range',
            ),
            models.CheckConstraint(
                condition=models.Q(match_score__gte=0, match_score__lte=1),
                name='identity_biometriccheck_match_range',
            ),
        ]

    def __str__(self):
        return f'BiometricCheck<{self.user_id}:{self.status}>'
