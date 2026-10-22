"""Administración de Django para la app notifications.

Los avisos los crea el sistema cuando ocurre un evento y las preferencias las
edita el usuario desde la API: el admin solo permite consultarlos.
"""

from django.contrib import admin

from apps.notifications.models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Consulta de los avisos enviados."""

    list_display = [
        'id',
        'user_id',
        'event_type',
        'status',
        'attempts',
        'sent_at',
        'created_at',
    ]
    list_filter = ['status', 'event_type']
    search_fields = ['user_id', 'reference_id']
    readonly_fields = [
        'id',
        'user_id',
        'event_type',
        'reference_id',
        'status',
        'sent_at',
        'error',
        'attempts',
        'created_at',
        'updated_at',
    ]

    def has_add_permission(self, request):
        """Los avisos se crean únicamente desde los servicios de notifications."""
        return False

    def has_change_permission(self, request, obj=None):
        """Los avisos no se editan a mano."""
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Consulta de las preferencias de aviso por usuario y evento."""

    list_display = ['id', 'user_id', 'event_type', 'enabled', 'updated_at']
    list_filter = ['event_type', 'enabled']
    search_fields = ['user_id']
    readonly_fields = ['id', 'user_id', 'event_type', 'enabled', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        """Las preferencias se crean únicamente desde los servicios de notifications."""
        return False

    def has_change_permission(self, request, obj=None):
        """Las preferencias no se editan a mano."""
        return False
