# Levanta PostgreSQL y Redis portables (sin Docker y sin admin).
#
#   .\scripts\start-services.ps1
#
# Los binarios viven en %LOCALAPPDATA%\presto (los instala scripts\install-services.ps1).

$ErrorActionPreference = 'Stop'

$base = Join-Path $env:LOCALAPPDATA 'presto'
$pgBin = Join-Path $base 'pg16\pgsql\bin'
$pgData = Join-Path $base 'data'
$redisDir = Join-Path $base 'redis'

if (-not (Test-Path (Join-Path $pgBin 'pg_ctl.exe'))) {
    throw "No está PostgreSQL portable. Corré primero .\scripts\install-services.ps1"
}

# --- PostgreSQL ---
& "$pgBin\pg_isready.exe" -h 127.0.0.1 -p 5432 *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Iniciando PostgreSQL...'
    Start-Process -FilePath "$pgBin\pg_ctl.exe" `
        -ArgumentList @('-D', $pgData, '-l', (Join-Path $base 'pg.log'), '-o', '"-p 5432 -c listen_addresses=127.0.0.1"', 'start') `
        -WindowStyle Hidden
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        & "$pgBin\pg_isready.exe" -h 127.0.0.1 -p 5432 *> $null
        if ($LASTEXITCODE -eq 0) { break }
    }
}
& "$pgBin\pg_isready.exe" -h 127.0.0.1 -p 5432

# --- Redis ---
if (-not (Get-Process redis-server -ErrorAction SilentlyContinue)) {
    Write-Host 'Iniciando Redis...'
    Start-Process -FilePath (Join-Path $redisDir 'redis-server.exe') `
        -ArgumentList @('--port', '6379', '--bind', '127.0.0.1') `
        -WorkingDirectory $redisDir -WindowStyle Hidden
    Start-Sleep -Seconds 1
}
& (Join-Path $redisDir 'redis-cli.exe') -h 127.0.0.1 -p 6379 ping
