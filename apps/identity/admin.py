"""Administración de Django para la app identity."""

from django.contrib import admin

from apps.identity.exceptions import InvalidKYCResolution, KYCAlreadyResolved
from apps.identity.models import (
    BackupAccount,
    BiometricCheck,
    KYCVerification,
    PrestoProfile,
    Profile,
    User,
)
from apps.identity.services import resolve_kyc


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Listado de usuarios de Presto."""

    list_display = ['id', 'email', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['email']
    readonly_fields = ['id', 'last_login', 'date_joined']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Listado de perfiles de usuario."""

    list_display = ['id', 'user', 'phone_number', 'country']
    search_fields = ['user__email']
    readonly_fields = ['id']


@admin.register(PrestoProfile)
class PrestoProfileAdmin(admin.ModelAdmin):
    """Perfiles de Presto de cada usuario (prestatario, prestamista e inversor)."""

    list_display = ['id', 'user', 'kind', 'is_active']
    list_filter = ['kind', 'is_active']
    search_fields = ['user__email']
    readonly_fields = ['id']


@admin.register(BackupAccount)
class BackupAccountAdmin(admin.ModelAdmin):
    """Cuentas de respaldo declaradas por los usuarios (solo lectura)."""

    list_display = [
        'id',
        'user',
        'provider',
        'display_name',
        'masked_ref',
        'currency',
        'declared_balance',
        'status',
        'verified_at',
    ]
    list_filter = ['provider', 'status', 'currency']
    search_fields = ['user__email', 'display_name']
    readonly_fields = [
        'id',
        'user',
        'provider',
        'display_name',
        'account_ref',
        'currency',
        'declared_balance',
        'status',
        'verified_at',
        'consent_at',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Las cuentas se crean solo por API/servicio."""
        return False

    @admin.display(description='Referencia')
    def masked_ref(self, obj):
        """Muestra el identificador enmascarado."""
        return obj.masked_ref


@admin.register(BiometricCheck)
class BiometricCheckAdmin(admin.ModelAdmin):
    """Validaciones biométricas simuladas: evidencia del KYC, de solo lectura."""

    list_display = [
        'id',
        'user',
        'kyc_verification',
        'status',
        'liveness_score',
        'match_score',
        'checked_at',
    ]
    list_filter = ['status', 'provider']
    search_fields = ['user__email']
    readonly_fields = [
        'id',
        'user',
        'kyc_verification',
        'status',
        'liveness_score',
        'match_score',
        'provider',
        'sample_hash',
        'result_details',
        'checked_at',
    ]

    def has_add_permission(self, request):
        """Las validaciones se crean solo por API/servicio, no a mano."""
        return False


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    """Gestión de verificaciones KYC: la decisión se toma acá, no por API."""

    list_display = ['id', 'user', 'status', 'requested_at', 'resolved_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['user__email']
    readonly_fields = [
        'id',
        'user',
        'status',
        'requested_at',
        'resolved_at',
        'resolved_by_user_id',
        'documents',
    ]
    actions = ['approve_kyc', 'reject_kyc']

    @admin.action(description='Aprobar las verificaciones KYC seleccionadas')
    def approve_kyc(self, request, queryset):
        """Aprueba las verificaciones seleccionadas que estén pendientes."""
        self._resolve_selected(request, queryset, KYCVerification.Status.APPROVED)

    @admin.action(description='Rechazar las verificaciones KYC seleccionadas')
    def reject_kyc(self, request, queryset):
        """Rechaza las verificaciones seleccionadas que estén pendientes."""
        self._resolve_selected(request, queryset, KYCVerification.Status.REJECTED)

    def _resolve_selected(self, request, queryset, status):
        """Resuelve las verificaciones pendientes del queryset, omitiendo las ya resueltas."""
        resolved = 0
        for verification in queryset:
            try:
                resolve_kyc(
                    verification_id=verification.id,
                    status=status,
                    resolved_by_user_id=request.user.id,
                )
            except (KYCAlreadyResolved, InvalidKYCResolution):
                continue
            resolved += 1
        self.message_user(request, f'{resolved} verificación(es) resuelta(s).')
