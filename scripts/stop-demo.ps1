# Detiene la demo local: API, front, PostgreSQL y Redis.
#
# Mata el arbol de procesos (para que no quede un Vite o un runserver vivo) y
# despues baja los servicios portables.

param([switch]$NoPause)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Stop-Tree($processId) {
    try {
        Start-Process -FilePath 'taskkill.exe' `
            -ArgumentList @('/PID', "$processId", '/T', '/F') `
            -WindowStyle Hidden -Wait -ErrorAction SilentlyContinue
    }
    catch {
        # el proceso ya no existe
    }
}

$targets = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and (
        $_.CommandLine -match 'PRESTO-MVP\\frontend' -or
        $_.CommandLine -match 'manage\.py runserver' -or
        $_.CommandLine -match 'run-api\.ps1' -or
        $_.CommandLine -match 'run-front\.ps1'
    )
}

foreach ($target in ($targets | Select-Object -ExpandProperty ProcessId -Unique)) {
    Stop-Tree $target
}

foreach ($port in @(8000, 5173)) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        if ($null -ne $process -and @('python', 'node') -contains $process.ProcessName) {
            Stop-Tree $process.Id
            Write-Host "Detenido $($process.ProcessName) en el puerto $port." -ForegroundColor Yellow
        }
    }
}

& "$root\scripts\stop-services.ps1"

Write-Host ''
Write-Host 'Demo detenida.' -ForegroundColor Green
if (-not $NoPause) {
    Read-Host 'Presiona Enter para cerrar'
}
