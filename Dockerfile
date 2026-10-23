FROM python:3.14-slim AS base

# The application never runs as root: the web, worker and beat containers
# use this unprivileged user (audit M-3).
RUN groupadd --gid 1000 presto \
    && useradd --uid 1000 --gid 1000 --create-home --home-dir /home/presto \
        --shell /usr/sbin/nologin --no-log-init presto

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTEST_ADDOPTS="-o cache_dir=/tmp/pytest_cache" \
    COVERAGE_FILE=/tmp/.coverage \
    RUFF_CACHE_DIR=/tmp/ruff-cache

EXPOSE 8000

# Runtime only: the production image does not carry pytest, ruff, etc.
FROM base AS runtime

RUN pip install --no-cache-dir --no-compile \
    "Django>=6.1,<7" \
    "djangorestframework>=3.14" \
    "drf-spectacular>=0.30" \
    "djangorestframework-simplejwt>=5.3" \
    "psycopg[binary]>=3.2" \
    "python-dotenv>=1.0" \
    "argon2-cffi>=21.0.0" \
    "gunicorn>=22.2.0" \
    "celery>=5.3.0" \
    "redis>=5.0.0" \
    "dj-database-url>=2.2.0" \
    "django-cors-headers>=4.4" \
    "whitenoise>=6.6"

# El código va después de las dependencias: un cambio de código no invalida
# la capa de pip y los deploys siguientes son mucho más rápidos.
COPY --chown=presto:presto . .

# Recolecta los estáticos del admin: WhiteNoise los sirve desde STATIC_ROOT.
RUN DJANGO_SETTINGS_MODULE=config.settings.local \
    LEGAL_REVIEW_ACKNOWLEDGED=1 \
    python manage.py collectstatic --noinput

RUN chmod +x /app/deploy/entrypoint.sh \
    && mkdir -p /var/celerybeat \
    && chown presto:presto /var/celerybeat

USER presto

ENTRYPOINT ["sh", "/app/deploy/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]


# Development: the services of docker-compose.yml use this target.
FROM runtime AS development

USER root

RUN pip install --no-cache-dir \
    "pytest>=7.0" \
    "pytest-django>=4.0" \
    "pytest-cov>=5.0" \
    "factory-boy>=3.0" \
    "ruff>=0.1.0" \
    "import-linter>=2.0" \
    "pip-audit>=2.7"

USER presto


# Production is the last stage, so `docker build .` (and Render) use it by default.
FROM runtime AS production
