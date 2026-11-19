"""Serializers de la app loans: solo validan entrada y dan formato a la salida."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.money import effective_annual_rate
from apps.identity.selectors import get_user_email
from apps.loans.models import (
    Installment,
    Loan,
    LoanMessage,
    LoanReview,
    OfferTermsSnapshot,
)


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
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            'id',
            'borrower_user_id',
            'lender_user_id',
            'borrower_email',
            'lender_email',
            'can_cancel',
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

    @extend_schema_field(serializers.BooleanField())
    def get_can_cancel(self, loan: Loan) -> bool:
        """True si el préstamo está activo y no tiene cuotas pagadas/vencidas."""
        if loan.status != Loan.Status.ACTIVE:
            return False
        return all(
            installment.status == Installment.Status.PENDING
            for installment in loan.installments.all()
        )


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


class LoanMessageSerializer(serializers.ModelSerializer):
    """Mensaje del chat privado de un préstamo."""

    class Meta:
        model = LoanMessage
        fields = ['id', 'sender_user_id', 'body', 'created_at']
        read_only_fields = fields


class LoanMessageCreateSerializer(serializers.Serializer):
    """Datos para enviar un mensaje en el chat del préstamo."""

    body = serializers.CharField(
        max_length=1000,
        allow_blank=False,
        trim_whitespace=True,
    )


class LoanReviewSerializer(serializers.ModelSerializer):
    """Reseña de una parte sobre la otra en un préstamo."""

    loan_id = serializers.UUIDField(read_only=True)
    reviewer_email = serializers.SerializerMethodField()
    reviewee_email = serializers.SerializerMethodField()

    class Meta:
        model = LoanReview
        fields = [
            'id',
            'loan_id',
            'reviewer_user_id',
            'reviewee_user_id',
            'reviewer_email',
            'reviewee_email',
            'recommended',
            'comment',
            'created_at',
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.EmailField(allow_null=True))
    def get_reviewer_email(self, review: LoanReview) -> str | None:
        return get_user_email(user_id=review.reviewer_user_id)

    @extend_schema_field(serializers.EmailField(allow_null=True))
    def get_reviewee_email(self, review: LoanReview) -> str | None:
        return get_user_email(user_id=review.reviewee_user_id)


class LoanReviewCreateSerializer(serializers.Serializer):
    """Datos para dejar una reseña de un préstamo."""

    recommended = serializers.BooleanField()
    comment = serializers.CharField(
        max_length=500,
        allow_blank=True,
        required=False,
        trim_whitespace=True,
    )


class ReputationSummarySerializer(serializers.Serializer):
    """Resumen agregado de reputación de un usuario."""

    total = serializers.IntegerField()
    recommended = serializers.IntegerField()
    not_recommended = serializers.IntegerField()
    recommendation_rate = serializers.FloatField()


class UserReputationSerializer(ReputationSummarySerializer):
    """Reputación de un usuario y sus reseñas recibidas."""

    user_id = serializers.UUIDField()
    email = serializers.EmailField(allow_null=True)
    reviews = LoanReviewSerializer(many=True)

    class Meta:
        fields = [
            'user_id',
            'email',
            'total',
            'recommended',
            'not_recommended',
            'recommendation_rate',
            'reviews',
        ]


class LoanReviewStatusSerializer(serializers.Serializer):
    """Estado del intercambio de reseñas de un préstamo."""

    my_review = LoanReviewSerializer(allow_null=True)
    received_review = LoanReviewSerializer(allow_null=True)
    counterpart_user_id = serializers.UUIDField()
    counterpart_email = serializers.EmailField(allow_null=True)
    counterpart_reputation = ReputationSummarySerializer()


class AcceptOfferSerializer(serializers.Serializer):
    """Datos para aceptar una oferta."""

    offer_id = serializers.UUIDField()
