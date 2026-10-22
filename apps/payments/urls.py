"""URLs de la app payments bajo el prefijo /api/v1/."""

from django.urls import path

from apps.payments import views

urlpatterns = [
    path('payments/', views.PaymentListCreateView.as_view(), name='payments'),
    path('payments/<uuid:payment_id>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path(
        'payments/webhooks/<str:provider_name>/',
        views.PaymentWebhookView.as_view(),
        name='payment-webhook',
    ),
]
