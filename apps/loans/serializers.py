"""Serializers de la app loans: solo validan entrada y dan formato a la salida."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.money import effective_annual_rate
from apps.identity.selectors import get_user_email
from apps.loans.models import Installment, Loan, OfferTermsSnapshot


class OfferTermsSnapshotSerializer(serializers.ModelSerializer):
    """Snapshot inmutable de los términos de la oferta aceptada."""

    class Meta:
        model = OfferTermsSnapshot
        fields = [
            'id',
            'accepted_at',
            'accepted_by_user_id',
            'snapshot_data',
            'is_immutable',
        ]
        read_only_fields = fields


class InstallmentSerializer(serializers.ModelSerializer):
    """Cuota de un préstamo."""

    class Meta:
        model = Installment
        fields = [
            'id',
            'number',
            'due_date',
            'principal_amount',
            'interest_amount',
            'amount',
            'status',
            'paid_at',
        ]
        read_only_fields = fields


class LoanSerializer(serializers.ModelSerializer):
    """Datos de un préstamo."""

    effective_annual_rate = serializers.SerializerMethodField(
        help_text=('Tasa de interés efectiva anual (TEA) equivalente a la TNA, en porcentaje.'),
    )
    borrower_email = serializers.SerializerMethodField()
    lender_email = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            'id',
            'borrower_user_id',
            'lender_user_id',
            'borrower_email',
            'lender_email',
            'offer_id',
            'principal',
            'currency',
            'interest_rate',
            'effective_annual_rate',
            'term_months',
            'status',
            'accepted_at',
        ]
        read_only_fields = fields

    def get_effective_annual_rate(self, loan: Loan) -> str:
        """Devuelve la TEA equivalente a la TNA del préstamo."""
        return str(effective_annual_rate(loan.interest_rate))

    @extend_schema_field(serializers.EmailField(allow_null=True))
    def get_borrower_email(self, loan: Loan) -> str | None:
        """Email del prestatario para que el prestamista pueda coordinar."""
        return get_user_email(user_id=loan.borrower_user_id)

    @extend_schema_field(serializers.EmailField(allow_null=True))
    def get_lender_email(self, loan: Loan) -> str | None:
        """Email del prestamista para que el prestatario pueda coordinar."""
        return get_user_email(user_id=loan.lender_user_id)


class LoanDetailSerializer(LoanSerializer):
    """Préstamo con su snapshot de términos y sus cuotas."""

    terms_snapshot = OfferTermsSnapshotSerializer(read_only=True)
    installments = InstallmentSerializer(many=True, read_only=True)

    class Meta(LoanSerializer.Meta):
        fields = [
            *LoanSerializer.Meta.fields,
            'terms_snapshot',
            'installments',
        ]


class AcceptOfferSerializer(serializers.Serializer):
    """Datos para aceptar una oferta."""

    offer_id = serializers.UUIDField()
