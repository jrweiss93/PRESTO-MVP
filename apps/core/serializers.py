"""Serializers de la app core."""

from rest_framework import serializers


class ComplianceItemSerializer(serializers.Serializer):
    """Un punto que necesita validación legal o profesional."""

    id = serializers.CharField()
    label = serializers.CharField()
    doc = serializers.CharField()


class ComplianceSerializer(serializers.Serializer):
    """Estado de cumplimiento de la aplicación."""

    legal_review_pending = serializers.BooleanField()
    acknowledged = serializers.BooleanField()
    items = ComplianceItemSerializer(many=True)


class MetaSerializer(serializers.Serializer):
    """Información pública del modo en que corre la aplicación."""

    mode = serializers.CharField()
    simulated_money = serializers.BooleanField()
    compliance = ComplianceSerializer()
