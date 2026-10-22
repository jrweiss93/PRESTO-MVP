# Crea .venv e instala las dependencias del backend (Windows, sin Docker).
#
#   .\scripts\setup-venv.ps1
#
# Después: .\scripts\start-services.ps1
#          . .\scripts\env.ps1
#          .venv\Scripts\python.exe manage.py migrate
#          .venv\Scripts\python.exe manage.py seed_demo
#          .venv\Scripts\python.exe manage.py runserver

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Creando .venv...'
    python -m venv .venv
}

$py = Join-Path $root '.venv\Scripts\python.exe'

Write-Host 'Instalando dependencias...'
& $py -m pip install --quiet --upgrade pip
& $py -m pip install --quiet `
    "Django>=5.2,<6" `
    "djangorestframework>=3.14" `
    "drf-spectacular>=0.30" `
    "djangorestframework-simplejwt>=5.3" `
    "psycopg[binary]>=3.2" `
    "pytest>=7.0" `
    "pytest-django>=4.0" `
    "pytest-cov>=5.0" `
    "factory-boy>=3.0" `
    "ruff>=0.1.0" `
    "import-linter>=2.0" `
    "python-dotenv>=1.0" `
    "argon2-cffi>=21.0.0" `
    "celery>=5.3.0" `
    "redis>=5.0.0" `
    "dj-database-url>=2.2" `
    "django-cors-headers>=4.4" `
    "whitenoise>=6.6" `
    "pip-audit>=2.7"

& $py -c "import django; print('Python y Django listos:', django.get_version())"
