# Entorno local de Presto (desarrollo).
#
#   . scripts/env.ps1
#   python manage.py runserver 8000
#
# Las variables apuntan a los servicios locales (Postgres y Redis). Para un
# despliegue real usá `docs/deploy-demo.md`, que exige `DJANGO_DEBUG=False` y
# secretos propios.

$env:DJANGO_SETTINGS_MODULE = 'config.settings.local'
$env:DJANGO_SECRET_KEY = 'django-insecure-local-preview-key-not-for-production'
$env:DJANGO_DEBUG = 'True'
$env:DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1'
$env:DATABASE_URL = 'postgres://presto:presto@127.0.0.1:5432/presto'
$env:REDIS_URL = 'redis://127.0.0.1:6379/0'
$env:DEMO_MODE = 'true'
$env:LEDGER_SIMULATED_DEPOSITS_ENABLED = 'true'

# Orígenes del front: Vite en dev (5173), el front de Next en 3000 y los
# puertos que usa la suite E2E de Playwright (4181 contra el mock y 4182
# contra la API real).
$env:CORS_ALLOWED_ORIGINS = 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:4181,http://127.0.0.1:4181,http://localhost:4182,http://127.0.0.1:4182'

$env:PYTHONPATH = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:REPO = $env:PYTHONPATH
