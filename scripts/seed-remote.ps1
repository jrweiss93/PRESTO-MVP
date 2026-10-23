# Siembra la demo en la base remota de Render, desde tu maquina.
#
# El plan free de Render no incluye Shell. Este script usa la "External
# Database URL" del Postgres de Render y corre `seed_demo` sin tocar el
# servicio web.
#
#   .\scripts\seed-remote.ps1
#
# La URL se pega cuando la pide el script y no se imprime ni se guarda.

param([string]$DatabaseUrl)

$ErrorActionPreference = 'Stop'

if (-not $DatabaseUrl) {
    $DatabaseUrl = Read-Host 'Pega la External Database URL de Render (presto-db -> Connect)'
}
if (-not $DatabaseUrl) {
    throw 'Falta la URL de la base.'
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'No existe .venv. Corre primero .\scripts\setup-venv.ps1'
}

$env:DJANGO_SETTINGS_MODULE = 'config.settings.local'
$env:DJANGO_SECRET_KEY = 'seed-remote-only'
$env:DEMO_MODE = 'true'
$env:LEDGER_SIMULATED_DEPOSITS_ENABLED = 'true'
$env:LEGAL_REVIEW_ACKNOWLEDGED = '1'
$env:DATABASE_URL = $DatabaseUrl
# Sin Redis remoto: los avisos de la siembra no se encolan.
$env:CELERY_BROKER_URL = 'memory://'
$env:REDIS_URL = 'redis://localhost:6379/0'

Write-Host 'Sembrando la demo en la base remota...'
$ErrorActionPreference = 'Continue'
& .\.venv\Scripts\python.exe manage.py seed_demo
$code = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($code -ne 0) {
    throw "seed_demo fallo con codigo $code"
}
Write-Host 'Listo: usuarios, oferta, prestamo, inversion y pagos creados.'
