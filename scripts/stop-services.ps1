# Detiene PostgreSQL y Redis portables.
#
#   .\scripts\stop-services.ps1

$base = Join-Path $env:LOCALAPPDATA 'presto'
$pgBin = Join-Path $base 'pg16\pgsql\bin'
$pgData = Join-Path $base 'data'

if (Test-Path (Join-Path $pgBin 'pg_ctl.exe')) {
    & "$pgBin\pg_ctl.exe" -D $pgData stop -m fast 2>&1 | Out-Null
}

Get-Process redis-server -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host 'Servicios detenidos.'
