from .base import *

# Development overrides
DEBUG = True


# Use console backend for emails in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# En local el límite de intentos de login (5/min en producción) choca con la
# suite E2E y con las demos: se sube solo para desarrollo.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        **REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'],
        'login': '60/min',
        'register': '60/hour',
    },
}
