"""Vistas del asistente Presti (solo lectura + chat por reglas)."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assistant import market, regulations, services
from apps.assistant.permissions import AssistantThrottle
from apps.assistant.serializers import (
    ChatMessageSerializer,
    ChatReplySerializer,
    MarketSnapshotSerializer,
    NewsFeedSerializer,
    RegulationDetailSerializer,
    RegulationsQuerySerializer,
    RegulationsResponseSerializer,
)


class AssistantView(APIView):
    """Base de las vistas de Presti: autenticación y throttle comunes."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AssistantThrottle]
    throttle_scope = 'assistant'


class MarketView(AssistantView):
    """Snapshot de mercado (dólar y cripto)."""

    @extend_schema(
        responses={200: MarketSnapshotSerializer},
        summary='Ver el snapshot de mercado de Presti',
        operation_id='assistant_market',
    )
    def get(self, request):
        """Devuelve la cotización del dólar y de las criptomonedas."""
        snapshot = market.get_market_snapshot()
        return Response(MarketSnapshotSerializer(snapshot).data, status=status.HTTP_200_OK)


class NewsView(AssistantView):
    """Últimas noticias del feed configurado."""

    @extend_schema(
        responses={200: NewsFeedSerializer},
        summary='Ver las noticias de Presti',
        operation_id='assistant_news',
    )
    def get(self, request):
        """Devuelve las noticias cacheadas del feed configurado."""
        feed = market.get_news_feed()
        return Response(NewsFeedSerializer(feed).data, status=status.HTTP_200_OK)


class RegulationListView(AssistantView):
    """Listado del marco regulatorio curado."""

    @extend_schema(
        parameters=[RegulationsQuerySerializer],
        responses={200: RegulationsResponseSerializer},
        summary='Listar el marco regulatorio de Presti',
        operation_id='assistant_regulations',
    )
    def get(self, request):
        """Devuelve las fichas regulatorias, con filtros opcionales."""
        query = RegulationsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        items = regulations.list_regulations(
            category=query.validated_data.get('category'),
            q=query.validated_data.get('q'),
        )
        payload = {
            'disclaimer': regulations.DISCLAIMER,
            'categories': regulations.CATEGORIES,
            'items': items,
        }
        return Response(
            RegulationsResponseSerializer(payload).data,
            status=status.HTTP_200_OK,
        )


class RegulationDetailView(AssistantView):
    """Detalle de una ficha regulatoria."""

    @extend_schema(
        responses={200: RegulationDetailSerializer},
        summary='Ver una ficha del marco regulatorio',
        operation_id='assistant_regulation_detail',
    )
    def get(self, request, regulation_id):
        """Devuelve la ficha indicada, o 404 si no existe."""
        item = regulations.get_regulation(regulation_id)
        if item is None:
            raise NotFound('La ficha regulatoria no existe.')
        payload = {'disclaimer': regulations.DISCLAIMER, 'item': item}
        return Response(
            RegulationDetailSerializer(payload).data,
            status=status.HTTP_200_OK,
        )


class ChatView(AssistantView):
    """Chat de Presti por intenciones (sin LLM)."""

    @extend_schema(
        request=ChatMessageSerializer,
        responses={200: ChatReplySerializer},
        summary='Preguntarle algo a Presti',
        operation_id='assistant_chat',
    )
    def post(self, request):
        """Responde la consulta con datos del usuario o contenido curado."""
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply = services.answer_question(
            user_id=request.user.id,
            message=serializer.validated_data['message'],
        )
        return Response(ChatReplySerializer(reply).data, status=status.HTTP_200_OK)
