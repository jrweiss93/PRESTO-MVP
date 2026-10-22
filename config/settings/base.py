import logging
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/releases/5.0/#new-settings

# SECURITY WARNING: keep the secret key secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-do-not-use-in-prod')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = (
    os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if os.getenv('DJANGO_ALLOWED_HOSTS') else []
)
# Render inyecta el hostname público del servicio. Se agrega solo para que el
# deploy no dependa de que el blueprint sincronice DJANGO_ALLOWED_HOSTS.
if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.getenv('RENDER_EXTERNAL_HOSTNAME'))

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {}
db_url = os.getenv('DATABASE_URL')
if db_url:
    import dj_database_url

    DATABASES['default'] = dj_database_url.parse(db_url)
else:
    # Fallback to PostgreSQL using environment variables
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'presto'),
        'USER': os.getenv('POSTGRES_USER', 'presto'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'presto'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }

# Application definition
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Core apps
    'apps.core',
    'apps.identity',
    'apps.ledger',
    'apps.payments',
    'apps.offers',
    'apps.loans',
    'apps.investments',
    'apps.budgets',
    'apps.reports',
    'apps.notifications',
    'apps.demo',
    'apps.assistant',
    # Third party
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exception_handler.api_exception_handler',
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/min',
        'register': '5/hour',
        'webhook': '60/min',
        # Enlaces de reseteo y verificación: estrictos, para que no se puedan
        # usar para inundar de correos ni para probar emails.
        'password_reset': '5/hour',
        'email_verification': '5/hour',
        # Asistente: la pantalla pide mercado y noticias al abrir, y el chat es
        # por demanda. 120/hora alcanza para una demo sin abrir la puerta a
        # abusos contra las fuentes externas.
        'assistant': '120/hour',
    },
}

# JWT (simplejwt)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Refresh token en cookie httpOnly (ADR 0014): el cuerpo de la respuesta del
# login solo lleva el access token, que el frontend guarda en memoria.
JWT_REFRESH_COOKIE_NAME = os.getenv('JWT_REFRESH_COOKIE_NAME', 'presto_refresh')
JWT_REFRESH_COOKIE_PATH = os.getenv('JWT_REFRESH_COOKIE_PATH', '/api/v1/auth/')
JWT_REFRESH_COOKIE_SECURE = (
    os.getenv('JWT_REFRESH_COOKIE_SECURE', 'False').strip().lower() == 'true'
)
JWT_REFRESH_COOKIE_SAMESITE = os.getenv('JWT_REFRESH_COOKIE_SAMESITE', 'Lax')
JWT_REFRESH_COOKIE_HTTPONLY = True

# Notificaciones: base del backoff exponencial de los reintentos de email, en
# segundos (ADR 0013). El primer reintento espera la base y el siguiente el
# doble.
NOTIFICATIONS_RETRY_BASE_SECONDS = int(os.getenv('NOTIFICATIONS_RETRY_BASE_SECONDS', '60'))

# Proveedor de pagos (ADR 0008): `simulated` (modo demo y tests) o
# `mercadopago` (producción). El proveedor real necesita credenciales: sin
# ellas, `get_provider()` falla y no se puede mover dinero.
PAYMENTS_PROVIDER = os.getenv('PAYMENTS_PROVIDER', 'simulated')
MERCADO_PAGO_ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN', '')
MERCADO_PAGO_WEBHOOK_SECRET = os.getenv('MERCADO_PAGO_WEBHOOK_SECRET', '')
MERCADO_PAGO_BASE_URL = os.getenv('MERCADO_PAGO_BASE_URL', 'https://api.mercadopago.com')
# URL pública del webhook, que se manda al proveedor para que avise.
MERCADO_PAGO_WEBHOOK_URL = os.getenv('MERCADO_PAGO_WEBHOOK_URL', '')
# Antigüedad máxima que se acepta de la firma de un webhook, en segundos.
PAYMENTS_WEBHOOK_MAX_AGE_SECONDS = int(os.getenv('PAYMENTS_WEBHOOK_MAX_AGE_SECONDS', '300'))
# Timeout de las llamadas HTTP al proveedor, en segundos.
PAYMENTS_HTTP_TIMEOUT = int(os.getenv('PAYMENTS_HTTP_TIMEOUT', '15'))

# drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Presto API',
    'DESCRIPTION': 'API de finanzas e inversiones con marketplace de préstamos.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1',
    # Nombres explícitos para los choice sets de `status` que colisionaban entre
    # componentes (el de los préstamos y el de las posiciones de inversión).
    'ENUM_NAME_OVERRIDES': {
        'LoanStatusEnum': 'apps.loans.models.Loan.Status',
        'PositionStatusEnum': 'apps.investments.models.Position.Status',
    },
}

MIDDLEWARE = [
    # El CORS va lo más arriba posible: tiene que responder los preflight
    # OPTIONS antes de que otro middleware genere la respuesta.
    'corsheaders.middleware.CorsMiddleware',
    'apps.core.middleware.DemoModeHeaderMiddleware',
    # El health check se contesta antes de validar el Host y antes del redirect
    # a HTTPS: las plataformas lo llaman con la IP interna del servicio.
    'apps.core.middleware.HealthCheckMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

ASGI_APPLICATION = 'config.asgi.application'

ROOT_URLCONF = 'config.urls'

# Password validators (AGENTS §9.5: los validadores de Django, activos)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Password hashers: Argon2 first, then Django built-in hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Environment marker used by the system checks (never rely on DEBUG)
DJANGO_ENV = os.getenv('DJANGO_ENV', 'local')

# Redis: broker de Celery (el servicio redis ya existe en docker-compose.yml)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Email: las notificaciones se envían por email. En desarrollo el backend es
# de consola; en producción, SMTP configurado por variables de entorno.
# Email: en modo demo (sin EMAIL_HOST) los avisos de las notificaciones salen
# por consola, o sea en los logs del worker. Si EMAIL_HOST está definido, el
# backend por defecto pasa a ser SMTP. Un EMAIL_BACKEND explícito manda siempre.
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    (
        'django.core.mail.backends.smtp.EmailBackend'
        if EMAIL_HOST
        else 'django.core.mail.backends.console.EmailBackend'
    ),
)
EMAIL_PORT = int(os.getenv('EMAIL_PORT') or 587)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').strip().lower() == 'true'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@presto.local')

# URL del front: con ella se arman los enlaces de los correos (reseteo de
# contraseña y verificación de email). En producción es el dominio real.
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')

# Los enlaces de reseteo y de verificación vencen en una hora. Se puede subir
# por entorno; los tokens se invalidan igual al cambiar la contraseña.
PASSWORD_RESET_TIMEOUT = int(os.getenv('PASSWORD_RESET_TIMEOUT') or 3600)

# Asistente Presti (sin LLM). Las fuentes externas son de solo lectura y se
# cachean; si no responden, el asistente devuelve la parte que pudo armar.
ASSISTANT_MARKET_ENABLED = os.getenv('ASSISTANT_MARKET_ENABLED', 'True').strip().lower() == 'true'
ASSISTANT_HTTP_TIMEOUT = float(os.getenv('ASSISTANT_HTTP_TIMEOUT') or 5)
ASSISTANT_MARKET_CACHE_SECONDS = int(os.getenv('ASSISTANT_MARKET_CACHE_SECONDS') or 60)
ASSISTANT_NEWS_CACHE_SECONDS = int(os.getenv('ASSISTANT_NEWS_CACHE_SECONDS') or 300)
# Un feed RSS público; vacío lo desactiva (la pantalla muestra solo mercado).
ASSISTANT_NEWS_FEED_URL = os.getenv(
    'ASSISTANT_NEWS_FEED_URL',
    'https://www.ambito.com/rss/pages/economia.xml',
)

# Celery (AGENTS §3 y §4): tareas asíncronas y periódicas con Redis como broker.
# No hay result backend persistente: las tareas del proyecto no devuelven
# resultados, solo efectos sobre el ledger.
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 15 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 10 * 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Demo mode: with DEMO_MODE=true the stack behaves like a demo (the simulated
# deposits are enabled and the ledger system check allows them). Without it,
# the simulated deposits are only for local/test environments.
DEMO_MODE = os.getenv('DEMO_MODE', 'False').strip().lower() == 'true'

# Ledger: simulated deposits are only for local/test environments
LEDGER_SIMULATED_DEPOSITS_ENABLED = DEMO_MODE or (
    os.getenv('LEDGER_SIMULATED_DEPOSITS_ENABLED', 'False').strip().lower() == 'true'
)

# Revisión legal y de PLA/FT: recordatorio (ver `apps/core/compliance.py`).
# Mientras esté en False, el endpoint `/api/v1/meta/` informa que la revisión
# sigue pendiente y el system check `legal.W001` avisa. Se pone en True cuando
# el equipo terminó la revisión (docs/regulatorio-bcra.md).
LEGAL_REVIEW_ACKNOWLEDGED = os.getenv('LEGAL_REVIEW_ACKNOWLEDGED', 'False').strip().lower() in {
    '1',
    'true',
    'yes',
    'on',
}

# CORS (AGENTS §9.3): el front vive en otro origen (Vercel), así que la API
# responde con los headers de CORS.
# - Los orígenes vienen de `CORS_ALLOWED_ORIGINS`, separados por comas.
# - Nunca se usa `*`: una lista vacía significa "ningún origen permitido".
# - Sí se permiten credenciales: el refresh token viaja en una cookie httpOnly
#   (ADR 0014) y el front lo renueva con `credentials: "include"`.
# - `Idempotency-Key` va en la lista de headers permitidos porque las
#   operaciones de dinero lo exigen (PROYECTO_FRONT.md §6.1).
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if origin.strip()
]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'idempotency-key',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = ['Content-Type']

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = str(BASE_DIR / 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'identity.User'

# Logging
logger = logging.getLogger(__name__)
