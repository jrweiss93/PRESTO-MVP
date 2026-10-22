"""Serializers de la app payments."""

from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Representación de un pago en la API.

    Los importes van como string decimal (AGENTS §8) y el `checkout_url` del
    proveedor, si lo hay, se expone aparte.
    """

    checkout_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'direction',
            'amount',
            'currency',
            'provider',
            'provider_reference',
            'status',
            'ledger_transaction_id',
            'checkout_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_checkout_url(self, payment: Payment) -> str:
        """Devuelve el link de pago del proveedor, si lo hay."""
        return str(payment.payload.get('checkout_url', ''))


class CreatePaymentSerializer(serializers.Serializer):
    """Datos de un pago nuevo."""

    direction = serializers.ChoiceField(choices=Payment.Direction.choices)
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    currency = serializers.ChoiceField(choices=Payment.Currency.choices)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)
    destination_user_id = serializers.UUIDField(required=False)
    destination_account = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_amount(self, value):
        """Rechaza los importes que no son positivos.

        Args:
            value: importe validado por el serializer.

        Returns:
            El importe.

        Raises:
            serializers.ValidationError: si el importe no es mayor que cero.
        """
        if value <= 0:
            raise serializers.ValidationError('El importe debe ser mayor que cero.')
        return value


class WebhookEventSerializer(serializers.Serializer):
    """Respuesta del endpoint de webhook."""

    status = serializers.CharField()
    event_id = serializers.CharField(allow_null=True)
    payment_id = serializers.CharField(allow_null=True)
