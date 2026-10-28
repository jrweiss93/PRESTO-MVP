# Levanta la demo local de Presto: PostgreSQL, Redis, API y front.
#
# Lo llama PRESTO-DEMO.cmd (doble clic). Tambien se puede correr a mano:
#   .\scripts\run-demo.ps1
#
# Con -NoPause no espera Enter al final (util para probar).

param([switch]$NoPause)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Write-Step($text) {
    Write-Host ''
    Write-Host "== $text ==" -ForegroundColor Cyan
}

function Stop-WithMessage($text) {
    Write-Host ''
    Write-Host "ERROR: $text" -ForegroundColor Red
    if (-not $NoPause) { Read-Host 'Presiona Enter para cerrar' }
    exit 1
}

function Test-PortInUse($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Url($url, $seconds) {
    for ($i = 1; $i -le $seconds; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return $true }
        }
        catch {
            # todavia no responde
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

Write-Host ''
Write-Host '  Presto - demo local' -ForegroundColor Magenta
Write-Host '  -------------------' -ForegroundColor Magenta
Write-Host ''

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Stop-WithMessage 'No encontre Python. Instalalo desde https://www.python.org/downloads/ y volve a intentar.'
}

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Step 'Preparando el entorno de Python'
    & "$root\scripts\setup-venv.ps1"
    if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'No se pudo crear el entorno de Python.' }
}

$pgCtl = Join-Path $env:LOCALAPPDATA 'presto\pg16\pgsql\bin\pg_ctl.exe'
if (-not (Test-Path $pgCtl)) {
    Write-Step 'Instalando PostgreSQL y Redis portables (la primera vez tarda)'
    & "$root\scripts\install-services.ps1"
    if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'No se pudieron instalar los servicios.' }
}

Write-Step 'Iniciando PostgreSQL y Redis'
& "$root\scripts\start-services.ps1"
if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'No se pudieron iniciar PostgreSQL o Redis.' }

# Variables de entorno del backend (base local, Redis, modo demo, CORS).
. "$root\scripts\env.ps1"
$env:LEGAL_REVIEW_ACKNOWLEDGED = '1'

if (-not (Test-PortInUse 8000)) {
    Write-Step 'Aplicando migraciones'
    & "$root\.venv\Scripts\python.exe" manage.py migrate --no-input
    if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'No se pudieron aplicar las migraciones.' }

    Write-Step 'Sembrando usuarios y datos de demo'
    & "$root\.venv\Scripts\python.exe" manage.py seed_demo
    if ($LASTEXITCODE -ne 0) { Stop-WithMessage 'No se pudo sembrar la demo.' }

    Write-Step 'Levantando la API en http://127.0.0.1:8000'
    Start-Process powershell -ArgumentList @(
        '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', "$root\scripts\run-api.ps1"
    )
}
else {
    Write-Host 'La API ya estaba corriendo en el puerto 8000.' -ForegroundColor Yellow
}

if (-not (Wait-Url 'http://127.0.0.1:8000/health/' 60)) {
    Stop-WithMessage 'La API no respondio. Mira la ventana "Presto API" para ver el error.'
}

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Stop-WithMessage 'No encontre pnpm. Instalalo con: npm install -g pnpm'
}

if (-not (Test-Path 'frontend\node_modules')) {
    Write-Step 'Instalando dependencias del front'
    Push-Location "$root\frontend"
    & pnpm install
    $installCode = $LASTEXITCODE
    Pop-Location
    if ($installCode -ne 0) { Stop-WithMessage 'No se pudieron instalar las dependencias del front.' }
}

if (-not (Test-PortInUse 5173)) {
    Write-Step 'Levantando el front en http://localhost:5173'
    Start-Process powershell -ArgumentList @(
        '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', "$root\scripts\run-front.ps1"
    )
}
else {
    Write-Host 'El front ya estaba corriendo en el puerto 5173.' -ForegroundColor Yellow
}

if (-not (Wait-Url 'http://localhost:5173/' 60)) {
    Stop-WithMessage 'El front no respondio. Mira la ventana "Presto Front" para ver el error.'
}

Start-Process 'http://localhost:5173'

Write-Host ''
Write-Host 'Demo lista.' -ForegroundColor Green
Write-Host '  Front:  http://localhost:5173'
Write-Host '  API:    http://127.0.0.1:8000'
Write-Host '  Admin:  http://127.0.0.1:8000/admin/'
Write-Host '  Docs:   http://127.0.0.1:8000/api/docs/'
Write-Host ''
Write-Host 'Usuarios: ana@presto.demo / beto@presto.demo / carla@presto.demo'
Write-Host 'Password: Presto123!'
Write-Host ''
Write-Host 'Para detener todo, usa PRESTO-DEMO-STOP.cmd.' -ForegroundColor Yellow

if (-not $NoPause) {
    Read-Host 'Presiona Enter para cerrar esta ventana (la demo sigue corriendo)'
}
