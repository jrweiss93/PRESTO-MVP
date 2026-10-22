"""Administración de Django para la app payments.

Los pagos los crea el usuario desde la API y los confirma el proveedor: el
admin solo permite consultarlos.
"""

from django.contrib import admin

from apps.payments.models import Payment, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Consulta de los pagos."""

    list_display = [
        'id',
        'user_id',
        'direction',
        'amount',
        'currency',
        'provider',
        'status',
        'provider_reference',
        'created_at',
    ]
    list_filter = ['direction', 'status', 'provider', 'currency']
    search_fields = ['user_id', 'provider_reference', 'idempotency_key']
    readonly_fields = [
        'id',
        'user_id',
        'direction',
        'amount',
        'currency',
        'provider',
        'provider_reference',
        'status',
        'idempotency_key',
        'request_hash',
        'ledger_transaction_id',
        'destination_user_id',
        'payload',
        'error',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Los pagos se crean únicamente desde los servicios de payments."""
        return False

    def has_change_permission(self, request, obj=None):
        """Los pagos no se editan a mano."""
        return False


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Consulta de los eventos de webhook recibidos."""

    list_display = [
        'id',
        'provider',
        'external_id',
        'event_type',
        'status',
        'payment_id',
        'created_at',
    ]
    list_filter = ['provider', 'status', 'event_type']
    search_fields = ['external_id', 'payment_id']
    readonly_fields = [
        'id',
        'provider',
        'external_id',
        'event_type',
        'status',
        'payment_id',
        'payload',
        'error',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Los eventos se crean únicamente desde los servicios de payments."""
        return False

    def has_change_permission(self, request, obj=None):
        """Los eventos no se editan a mano."""
        return False
