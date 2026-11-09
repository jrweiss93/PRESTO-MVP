from django.apps import AppConfig


class DemoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.demo'
    verbose_name = 'Datos de demo'

    def ready(self):
        """Conecta los receptores de las señales de las apps emisoras."""
        from apps.demo import receivers  # noqa: F401
