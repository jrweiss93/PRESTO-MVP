# Ventana del front para la demo local.

$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\frontend"
$Host.UI.RawUI.WindowTitle = 'Presto Front'

$env:VITE_API_URL = 'http://localhost:8000/api/v1'
$env:VITE_ENABLE_ASSISTANT = 'true'

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Host 'No encontre pnpm. Instalalo con: npm install -g pnpm' -ForegroundColor Red
    Read-Host 'Presiona Enter para cerrar'
    exit 1
}

Write-Host 'Presto Front - http://localhost:5173' -ForegroundColor Cyan
Write-Host 'Cerra esta ventana o usa PRESTO-DEMO-STOP.cmd para detenerla.'
Write-Host ''

pnpm dev --host localhost --port 5173
