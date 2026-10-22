"""Administración de Django para la app loans.

Los préstamos y sus cuotas los crea el motor de matching y los servicios de
loans: el admin solo permite consultarlos.
"""

from django.contrib import admin

from apps.loans.models import Installment, Loan, OfferTermsSnapshot


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Consulta de los préstamos."""

    list_display = [
        'id',
        'borrower_user_id',
        'lender_user_id',
        'principal',
        'currency',
        'interest_rate',
        'term_months',
        'status',
        'accepted_at',
    ]
    list_filter = ['status', 'currency', 'term_months']
    search_fields = ['borrower_user_id', 'lender_user_id', 'offer_id']
    readonly_fields = [
        'id',
        'borrower_user_id',
        'lender_user_id',
        'offer_id',
        'principal',
        'currency',
        'interest_rate',
        'term_months',
        'status',
        'accepted_at',
        'ledger_transaction_id',
        'idempotency_key',
        'request_hash',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Los préstamos se crean únicamente desde los servicios de loans."""
        return False

    def has_change_permission(self, request, obj=None):
        """Los préstamos no se editan a mano."""
        return False


@admin.register(OfferTermsSnapshot)
class OfferTermsSnapshotAdmin(admin.ModelAdmin):
    """Consulta de la foto de las condiciones de la oferta aceptada.

    La foto es inmutable: es la evidencia de las condiciones con las que se
    firmó el préstamo.
    """

    list_display = ['id', 'loan', 'accepted_at', 'accepted_by_user_id', 'is_immutable']
    search_fields = ['loan__id', 'accepted_by_user_id']
    readonly_fields = [
        'id',
        'loan',
        'accepted_at',
        'accepted_by_user_id',
        'snapshot_data',
        'is_immutable',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """La foto se crea únicamente al aceptar la oferta."""
        return False

    def has_change_permission(self, request, obj=None):
        """La foto de condiciones es inmutable."""
        return False


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    """Consulta de las cuotas de los préstamos."""

    list_display = [
        'id',
        'loan',
        'number',
        'due_date',
        'amount',
        'principal_amount',
        'interest_amount',
        'status',
        'paid_at',
    ]
    list_filter = ['status', 'due_date']
    search_fields = ['loan__id']
    readonly_fields = [
        'id',
        'loan',
        'number',
        'due_date',
        'principal_amount',
        'interest_amount',
        'amount',
        'status',
        'paid_at',
        'ledger_transaction_id',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Las cuotas se crean únicamente desde los servicios de loans."""
        return False

    def has_change_permission(self, request, obj=None):
        """Las cuotas no se editan a mano."""
        return False
