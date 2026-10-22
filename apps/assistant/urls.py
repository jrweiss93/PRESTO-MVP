"""URLs del asistente bajo el prefijo /api/v1/."""

from django.urls import path

from apps.assistant import views

urlpatterns = [
    path('assistant/market/', views.MarketView.as_view(), name='assistant-market'),
    path('assistant/news/', views.NewsView.as_view(), name='assistant-news'),
    path(
        'assistant/regulations/',
        views.RegulationListView.as_view(),
        name='assistant-regulations',
    ),
    path(
        'assistant/regulations/<str:regulation_id>/',
        views.RegulationDetailView.as_view(),
        name='assistant-regulation-detail',
    ),
    path('assistant/chat/', views.ChatView.as_view(), name='assistant-chat'),
]
