#!/bin/sh
# Punto de entrada de la imagen para plataformas que la corren tal cual
# (Render, Northflank, Railway, un VPS con Docker, etc.).
#
# - Si RUN_MIGRATIONS=1, aplica las migraciones antes de arrancar y reintenta
#   mientras la base administrada termina de estar disponible.
# - Después ejecuta el comando recibido (gunicorn, celery, etc.).
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    attempts="${DB_WAIT_ATTEMPTS:-30}"
    i=1
    while [ "$i" -le "$attempts" ]; do
        if python manage.py migrate --no-input; then
            break
        fi
        echo "migrate falló (intento $i/$attempts); reintentando en 2s..." >&2
        i=$((i + 1))
        sleep 2
    done
    if [ "$i" -gt "$attempts" ]; then
        echo "No se pudieron aplicar las migraciones." >&2
        exit 1
    fi
fi

exec "$@"
