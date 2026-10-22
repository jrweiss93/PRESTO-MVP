"""Serializers del asistente: validan la entrada y dan formato a la salida."""

from rest_framework import serializers

from apps.assistant.regulations import CATEGORIES


class MarketCoinSerializer(serializers.Serializer):
    """Cotización de una criptomoneda."""

    symbol = serializers.CharField()
    name = serializers.CharField()
    price_usd = serializers.FloatField(allow_null=True)
    change_24h_pct = serializers.FloatField(allow_null=True)


class MarketIndexSerializer(serializers.Serializer):
    """Cotización de un índice o acción."""

    symbol = serializers.CharField()
    name = serializers.CharField()
    price_usd = serializers.FloatField(allow_null=True, required=False)
    price_local = serializers.FloatField(allow_null=True, required=False)
    currency = serializers.CharField()
    change_24h_pct = serializers.FloatField(allow_null=True, required=False)


class MarketDollarSerializer(serializers.Serializer):
    """Cotizaciones del dólar."""

    oficial = serializers.FloatField(allow_null=True)
    oficial_avg = serializers.FloatField(allow_null=True)
    blue = serializers.FloatField(allow_null=True)
    blue_avg = serializers.FloatField(allow_null=True)


class MarketSnapshotSerializer(serializers.Serializer):
    """Snapshot de mercado que muestra Presti."""

    updated_at = serializers.CharField()
    coins = MarketCoinSerializer(many=True)
    indices = MarketIndexSerializer(many=True)
    dollar = MarketDollarSerializer(allow_null=True)


class NewsItemSerializer(serializers.Serializer):
    """Una noticia del feed."""

    title = serializers.CharField()
    link = serializers.CharField(allow_null=True)
    published_at = serializers.CharField(allow_null=True)
    source = serializers.CharField()


class NewsFeedSerializer(serializers.Serializer):
    """Feed de noticias que muestra Presti."""

    updated_at = serializers.CharField()
    items = NewsItemSerializer(many=True)


class RegulationNormSerializer(serializers.Serializer):
    """Norma citada en una ficha regulatoria."""

    code = serializers.CharField()
    note = serializers.CharField()


class RegulationLinkSerializer(serializers.Serializer):
    """Enlace oficial de una ficha regulatoria."""

    label = serializers.CharField()
    url = serializers.CharField()


class RegulationCardSerializer(serializers.Serializer):
    """Ficha del marco regulatorio."""

    id = serializers.CharField()
    category = serializers.CharField()
    title = serializers.CharField()
    summary = serializers.CharField()
    key_points = serializers.ListField(child=serializers.CharField())
    norms = RegulationNormSerializer(many=True)
    links = RegulationLinkSerializer(many=True)
    applies_to = serializers.CharField()


class RegulationCategorySerializer(serializers.Serializer):
    """Categoría del marco regulatorio."""

    id = serializers.CharField()
    label = serializers.CharField()


class RegulationsResponseSerializer(serializers.Serializer):
    """Listado de fichas regulatorias."""

    disclaimer = serializers.CharField()
    categories = RegulationCategorySerializer(many=True)
    items = RegulationCardSerializer(many=True)


class RegulationDetailSerializer(serializers.Serializer):
    """Detalle de una ficha regulatoria."""

    disclaimer = serializers.CharField()
    item = RegulationCardSerializer()


class RegulationsQuerySerializer(serializers.Serializer):
    """Filtros del listado regulatorio."""

    category = serializers.ChoiceField(
        choices=[(category['id'], category['label']) for category in CATEGORIES],
        required=False,
    )
    q = serializers.CharField(required=False, max_length=100)


class ChatMessageSerializer(serializers.Serializer):
    """Consulta del usuario a Presti."""

    message = serializers.CharField(max_length=500, allow_blank=True)


class ChatReplySerializer(serializers.Serializer):
    """Respuesta de Presti."""

    reply = serializers.CharField()
    intent = serializers.ChoiceField(choices=['rules', 'fallback', 'empty'])
