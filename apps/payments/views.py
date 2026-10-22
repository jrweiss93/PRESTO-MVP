"""Vistas de la API de payments."""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import InsufficientFunds, InvalidAmount, KYCNotCompleted
from apps.core.pagination import StandardPagination
from apps.identity.permissions import KycApprovedForUnsafeMethods
from apps.payments.exceptions import (
    DestinationAccountRequired,
    IdempotencyConflict,
    InvalidWebhookSignature,
    ProviderError,
    ProviderNotConfigured,
)
from apps.payments.permissions import WebhookThrottle
from apps.payments.selectors import get_payment, list_payments_for_user
from apps.payments.serializers import (
    CreatePaymentSerializer,
    PaymentSerializer,
    WebhookEventSerializer,
)
from apps.payments.services import create_payment, handle_webhook

logger = logging.getLogger(__name__)


class PaymentListCreateView(KycApprovedForUnsafeMethods, APIView):
    """Pagos del usuario autenticado."""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    @extend_schema(
        responses={200: PaymentSerializer},
        summary='Listar los pagos del usuario',
        operation_id='payments_list',
    )
    def get(self, request):
        """Lista los pagos del usuario autenticado."""
        payments = list_payments_for_user(user_id=request.user.id)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(payments, request, view=self)
        return paginator.get_paginated_response(PaymentSerializer(page, many=True).data)

    @extend_schema(
        request=CreatePaymentSerializer,
        responses={201: PaymentSerializer},
        summary='Crear un pago (depósito, retiro o transferencia)',
        description=(
            'El header `Idempotency-Key` es obligatorio. El saldo se mueve '
            'cuando el proveedor confirma: de inmediato en el modo simulado, '
            'o con el webhook firmado cuando el proveedor es real.'
        ),
    )
    def post(self, request):
        """Crea un pago con idempotencia."""
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            raise ValidationError(
                {'idempotency_key': ['El header Idempotency-Key es obligatorio.']}
            )
        try:
            payment = create_payment(
                user_id=request.user.id,
                direction=serializer.validated_data['direction'],
                amount=serializer.validated_data['amount'],
                currency=serializer.validated_data['currency'],
                idempotency_key=idempotency_key,
                description=serializer.validated_data.get('description', ''),
                destination_user_id=serializer.validated_data.get('destination_user_id'),
                destination_account=serializer.validated_data.get('destination_account', ''),
            )
        except IdempotencyConflict as exc:
            raise ValidationError({'idempotency_key': [str(exc)]}) from exc
        except KYCNotCompleted as exc:
            raise PermissionDenied(str(exc)) from exc
        except InsufficientFunds as exc:
            raise ValidationError({'amount': [str(exc)]}) from exc
        except InvalidAmount as exc:
            raise ValidationError({'amount': [str(exc)]}) from exc
        except DestinationAccountRequired as exc:
            raise ValidationError({'destination_user_id': [str(exc)]}) from exc
        except ProviderNotConfigured as exc:
            raise ValidationError({'detail': [str(exc)]}) from exc
        except ProviderError as exc:
            raise ValidationError({'detail': [str(exc)]}) from exc
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    """Detalle de un pago propio."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: PaymentSerializer},
        summary='Ver un pago propio',
        operation_id='payments_retrieve',
    )
    def get(self, request, payment_id):
        """Devuelve el pago indicado si pertenece al usuario."""
        payment = get_payment(payment_id=payment_id, user_id=request.user.id)
        if payment is None:
            raise NotFound('El pago solicitado no existe.')
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)


class PaymentWebhookView(APIView):
    """Webhook del proveedor de pagos.

    **No pide autenticación**: la autenticación es la **firma** del evento.
    Con la firma inválida se responde `401` y no se toca el ledger.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [WebhookThrottle]
    throttle_scope = 'webhook'

    @extend_schema(
        request=None,
        responses={200: WebhookEventSerializer},
        summary='Recibir un webhook del proveedor de pagos',
    )
    def post(self, request, provider_name):
        """Verifica la firma y procesa el evento del proveedor."""
        body = request.body
        headers = {key: value for key, value in request.headers.items()}
        try:
            event = handle_webhook(
                provider_name=provider_name,
                body=body,
                headers=headers,
            )
        except InvalidWebhookSignature as exc:
            logger.warning('Webhook con firma inválida de %s', provider_name)
            raise AuthenticationFailed(str(exc)) from exc
        except ProviderNotConfigured as exc:
            raise NotFound(str(exc)) from exc
        except ProviderError as exc:
            raise ValidationError({'detail': [str(exc)]}) from exc
        return Response(
            WebhookEventSerializer(
                {
                    'status': event.status,
                    'event_id': str(event.id),
                    'payment_id': str(event.payment_id) if event.payment_id else None,
                }
            ).data,
            status=status.HTTP_200_OK,
        )
