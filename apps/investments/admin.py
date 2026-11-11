"""Administración de Django para la app investments.

Los productos de inversión se dan de alta únicamente desde acá, que solo es
accesible para usuarios staff. Desde acá también se puede forzar la liquidación
de posiciones vencidas (la tarea que normalmente dispara el beat de Celery).
"""

from django.contrib import admin
from django.utils import timezone

from apps.investments.models import InvestmentProduct, Position


@admin.register(InvestmentProduct)
class InvestmentProductAdmin(admin.ModelAdmin):
    """Alta y edición de productos de inversión a plazo fijo."""

    list_display = [
        'id',
        'name',
        'type',
        'currency',
        'term_days',
        'annual_rate_tna',
        'min_amount',
        'status',
    ]
    list_filter = ['type', 'status', 'currency']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Consulta de las posiciones de inversión abiertas."""

    list_display = ['id', 'user_id', 'product', 'amount', 'status', 'opened_at', 'maturity_date']
    list_filter = ['status', 'product']
    readonly_fields = [
        'id',
        'user_id',
        'product',
        'amount',
        'status',
        'opened_at',
        'maturity_date',
        'interest_amount',
        'idempotency_key',
        'request_hash',
        'created_at',
        'updated_at',
    ]
    actions = ['settle_now']

    def has_add_permission(self, request):
        """Las posiciones se crean únicamente desde los servicios de investments."""
        return False

    def has_change_permission(self, request, obj=None):
        """Las posiciones no se editan a mano."""
        return False

    def has_view_permission(self, request, obj=None):
        """El detalle se puede abrir en modo solo lectura."""
        return True

    @admin.action(description='Liquidar inversiones vencidas (ahora)')
    def settle_now(self, request, queryset):
        """Liquida las posiciones vencidas sin esperar al beat de Celery."""
        from apps.investments.services import settle_matured_positions

        settled = settle_matured_positions(today=timezone.localdate())
        self.message_user(request, f'{settled} posición(es) liquidada(s).')
