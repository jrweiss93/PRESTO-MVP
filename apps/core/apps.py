from django.apps import AppConfig
from django.core.checks import register


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'

    def ready(self):
        """Registra los system checks de la app.

        Returns:
            None.
        """
        from apps.core.checks import check_legal_review_acknowledged

        register(check_legal_review_acknowledged)
