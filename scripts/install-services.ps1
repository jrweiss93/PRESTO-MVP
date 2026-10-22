# Descarga e inicializa PostgreSQL 16 y Redis portables, sin Docker y sin admin.
#
#   .\scripts\install-services.ps1
#
# Quedan en %LOCALAPPDATA%\presto. Los datos de PostgreSQL en %LOCALAPPDATA%\presto\data.
# La contraseña del usuario `presto` y de la base es `presto` (solo para desarrollo).

param(
    [string]$PostgresVersion = '16.10',
    [string]$DbUser = 'presto',
    [string]$DbPassword = 'presto',
    [string]$DbName = 'presto'
)

$ErrorActionPreference = 'Stop'

$base = Join-Path $env:LOCALAPPDATA 'presto'
$pgRoot = Join-Path $base 'pg16'
$pgBin = Join-Path $pgRoot 'pgsql\bin'
$pgData = Join-Path $base 'data'
$redisDir = Join-Path $base 'redis'

New-Item -ItemType Directory -Force -Path $base | Out-Null

# --- PostgreSQL ---
if (-not (Test-Path (Join-Path $pgBin 'initdb.exe'))) {
    $zip = Join-Path $env:TEMP "postgresql-$PostgresVersion-binaries.zip"
    if (-not (Test-Path $zip)) {
        Write-Host "Descargando PostgreSQL $PostgresVersion (322 MB)..."
        curl.exe -L --fail --max-time 1800 -o $zip `
            "https://get.enterprisedb.com/postgresql/postgresql-$PostgresVersion-1-windows-x64-binaries.zip"
        if ($LASTEXITCODE -ne 0) { throw 'Falló la descarga de PostgreSQL.' }
    }
    New-Item -ItemType Directory -Force -Path $pgRoot | Out-Null
    tar -xf $zip -C $pgRoot
    if ($LASTEXITCODE -ne 0) { throw 'Falló la extracción de PostgreSQL.' }
}

if (-not (Test-Path (Join-Path $pgData 'PG_VERSION'))) {
    Write-Host 'Inicializando la base de datos...'
    $pwFile = Join-Path $base 'pw.txt'
    Set-Content -Path $pwFile -Value $DbPassword -NoNewline -Encoding ascii
    & "$pgBin\initdb.exe" -D $pgData -U $DbUser -A scram-sha-256 --pwfile=$pwFile -E UTF8 --locale=C
    Remove-Item $pwFile -Force
}

Write-Host 'Iniciando PostgreSQL...'
& "$pgBin\pg_isready.exe" -h 127.0.0.1 -p 5432 *> $null
if ($LASTEXITCODE -ne 0) {
    Start-Process -FilePath "$pgBin\pg_ctl.exe" `
        -ArgumentList @('-D', $pgData, '-l', (Join-Path $base 'pg.log'), '-o', '"-p 5432 -c listen_addresses=127.0.0.1"', 'start') `
        -WindowStyle Hidden
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        & "$pgBin\pg_isready.exe" -h 127.0.0.1 -p 5432 *> $null
        if ($LASTEXITCODE -eq 0) { break }
    }
}

$env:PGPASSWORD = $DbPassword
$exists = & "$pgBin\psql.exe" -w -h 127.0.0.1 -p 5432 -U $DbUser -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DbName'"
if ("$exists".Trim() -ne '1') {
    & "$pgBin\createdb.exe" -w -h 127.0.0.1 -p 5432 -U $DbUser $DbName
    Write-Host "Base '$DbName' creada."
}

# --- Redis ---
if (-not (Test-Path (Join-Path $redisDir 'redis-server.exe'))) {
    $zip = Join-Path $env:TEMP 'redis-win.zip'
    Write-Host 'Descargando Redis (12 MB)...'
    curl.exe -L --fail --max-time 300 -o $zip `
        'https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip'
    if ($LASTEXITCODE -ne 0) { throw 'Falló la descarga de Redis.' }
    New-Item -ItemType Directory -Force -Path $redisDir | Out-Null
    tar -xf $zip -C $redisDir
}

if (-not (Get-Process redis-server -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath (Join-Path $redisDir 'redis-server.exe') `
        -ArgumentList @('--port', '6379', '--bind', '127.0.0.1') `
        -WorkingDirectory $redisDir -WindowStyle Hidden
    Start-Sleep -Seconds 1
}

Write-Host ''
Write-Host 'Servicios listos:'
& "$pgBin\pg_isready.exe" -h 127.0.0.1 -p 5432
& (Join-Path $redisDir 'redis-cli.exe') -h 127.0.0.1 -p 6379 ping
Write-Host "DATABASE_URL=postgres://${DbUser}:${DbPassword}@127.0.0.1:5432/$DbName"
