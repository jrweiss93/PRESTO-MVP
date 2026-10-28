# Ventana de la API para la demo local.

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$Host.UI.RawUI.WindowTitle = 'Presto API'

. "$root\scripts\env.ps1"
$env:LEGAL_REVIEW_ACKNOWLEDGED = '1'

Write-Host 'Presto API - http://127.0.0.1:8000' -ForegroundColor Cyan
Write-Host 'Cerra esta ventana o usa PRESTO-DEMO-STOP.cmd para detenerla.'
Write-Host ''

& "$root\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
