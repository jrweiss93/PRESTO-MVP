# Levanta el backend de Presto en local (127.0.0.1:8000) con el entorno de
# `env.ps1`. Es lo que usan la demo y la suite E2E del front.
#
#   powershell -ExecutionPolicy Bypass -File scripts/run_server.ps1

. (Join-Path $PSScriptRoot 'env.ps1')
Set-Location (Join-Path $PSScriptRoot '..')

if (-not $env:VENV_PY) {
    $env:VENV_PY = (Get-Command python -ErrorAction SilentlyContinue).Source
}

Write-Host "Presto API en http://127.0.0.1:8000/api/v1 (CORS: $env:CORS_ALLOWED_ORIGINS)"
& $env:VENV_PY manage.py runserver 127.0.0.1:8000 --noreload
