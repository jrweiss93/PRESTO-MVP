# Crea o actualiza el superusuario del admin en la base remota de Render.
#
# El plan free de Render no incluye Shell. Este script usa la "External
# Database URL" del Postgres y corre un comando de Django desde tu maquina.
#
#   .\scripts\create-superuser-remote.ps1
#
# La URL y la contrasena se piden de forma interactiva y no se imprimen.

param(
    [string]$DatabaseUrl,
    [string]$Email = 'admin@presto.demo',
    [string]$AdminUrl = 'https://presto-api-r8vc.onrender.com/admin/'
)

$ErrorActionPreference = 'Stop'

if (-not $DatabaseUrl) {
    $DatabaseUrl = Read-Host 'Pega la External Database URL de Render (presto-db -> Connect)'
}
if (-not $DatabaseUrl) {
    throw 'Falta la URL de la base.'
}

$inputEmail = Read-Host "Email del superusuario [$Email]"
if ($inputEmail) {
    $Email = $inputEmail
}

$securePassword = Read-Host "Contrasena para $Email (minimo 12 caracteres)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

if ($password.Length -lt 12) {
    throw 'La contrasena debe tener al menos 12 caracteres.'
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'No existe .venv. Corre primero .\scripts\setup-venv.ps1'
}

$env:DJANGO_SETTINGS_MODULE = 'config.settings.local'
$env:DJANGO_SECRET_KEY = 'create-superuser-remote-only'
$env:DEMO_MODE = 'true'
$env:LEDGER_SIMULATED_DEPOSITS_ENABLED = 'true'
$env:LEGAL_REVIEW_ACKNOWLEDGED = '1'
$env:DATABASE_URL = $DatabaseUrl
$env:CELERY_BROKER_URL = 'memory://'
$env:REDIS_URL = 'redis://localhost:6379/0'
$env:DEMO_SUPERUSER_EMAIL = $Email
$env:DEMO_SUPERUSER_PASSWORD = $password

try {
    Write-Host "Creando superusuario $Email..."
    $ErrorActionPreference = 'Continue'
    & .\.venv\Scripts\python.exe manage.py create_demo_superuser
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -ne 0) {
        throw "El comando fallo con codigo $code"
    }
    Write-Host ''
    Write-Host "Admin listo: $AdminUrl" -ForegroundColor Green
    Write-Host "Usuario: $Email"
}
finally {
    Remove-Item Env:DEMO_SUPERUSER_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:DEMO_SUPERUSER_EMAIL -ErrorAction SilentlyContinue
    $password = $null
}
