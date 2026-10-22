"""Administración de Django para la app offers.

Las ofertas las publica el prestamista desde la API: el admin solo permite
consultarlas.
"""

from django.contrib import admin

from apps.offers.models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Consulta de las ofertas de préstamo publicadas."""

    list_display = [
        'id',
        'lender_user_id',
        'amount',
        'currency',
        'interest_rate',
        'term_months',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'currency', 'term_months']
    search_fields = ['lender_user_id']
    readonly_fields = [
        'id',
        'lender_user_id',
        'amount',
        'currency',
        'interest_rate',
        'term_months',
        'requirements',
        'status',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Las ofertas se crean únicamente desde los servicios de offers."""
        return False

    def has_change_permission(self, request, obj=None):
        """Las ofertas no se editan a mano."""
        return False
