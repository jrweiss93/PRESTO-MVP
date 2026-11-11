"""Serializers de la app notifications: solo validan entrada y dan formato a la salida."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Un aviso del usuario."""

    loan_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'user_id',
            'event_type',
            'reference_id',
            'loan_id',
            'status',
            'read_at',
            'created_at',
            'sent_at',
            'error',
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.UUIDField(allow_null=True))
    def get_loan_id(self, obj):
        """Devuelve el préstamo al que lleva el aviso, si corresponde."""
        if obj.event_type == Notification.EventType.LOAN_CREATED:
            return str(obj.reference_id)
        if obj.event_type in {
            Notification.EventType.INSTALLMENT_DUE_SOON,
            Notification.EventType.INSTALLMENT_OVERDUE,
            Notification.EventType.INSTALLMENT_PAID,
        }:
            from apps.loans.selectors import get_installment

            installment = get_installment(obj.reference_id)
            return str(installment.loan_id) if installment else None
        return None


class NotificationPreferenceSerializer(serializers.Serializer):
    """La preferencia de un tipo de evento."""

    event_type = serializers.ChoiceField(choices=Notification.EventType.choices)
    enabled = serializers.BooleanField()


class NotificationPreferenceListSerializer(serializers.Serializer):
    """Las preferencias del usuario con todos los eventos."""

    preferences = NotificationPreferenceSerializer(many=True)


class NotificationUnreadCountSerializer(serializers.Serializer):
    """Cantidad de avisos sin leer."""

    unread = serializers.IntegerField()


class NotificationReadAllSerializer(serializers.Serializer):
    """Resultado de marcar todos los avisos como leídos."""

    read = serializers.IntegerField()
