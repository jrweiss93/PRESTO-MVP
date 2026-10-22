"""Middleware transversal de la app core."""

from django.conf import settings


class HealthCheckMiddleware:
    """Responde `/health/` antes de validar el `Host` y antes del redirect TLS.

    Las plataformas (Render, Northflank, balanceadores) llaman al health check
    con la IP interna o con un `Host` que no está en `ALLOWED_HOSTS`. Si la
    petición llegara al resto de los middlewares, Django devolvería 400/301 y
    el servicio nunca quedaría sano.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health/':
            from apps.core.views import health_check

            return health_check(request)
        return self.get_response(request)


class DemoModeHeaderMiddleware:
    """Agrega la cabecera `X-Presto-Mode` cuando la aplicación está en modo demo.

    Sirve para que el frontend (y quien haga un diagnóstico) sepa de entrada
    que la aplicación corre como demostración y que el dinero es simulado.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.DEMO_MODE:
            response['X-Presto-Mode'] = 'demo'
        return response
