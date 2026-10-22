# Instala Docker Desktop cuando la máquina ya está preparada.
#
# Requisitos (los tres): sesión de administrador, virtualización habilitada en
# la BIOS (SVM/AMD-V o VT-x) y WSL2. Si falta alguno, el script lo dice y no
# toca nada.
#
#   .\scripts\install-docker.ps1
#
# El instalador ya está descargado en %LOCALAPPDATA%\presto\installers.

$ErrorActionPreference = 'Stop'

function Fail($message) {
    Write-Host ''
    Write-Host "NO SE PUEDE INSTALAR: $message" -ForegroundColor Yellow
    Write-Host ''
    exit 1
}

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $admin) {
    Fail 'hace falta una consola de PowerShell como administrador.'
}

$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
if (-not $cpu.VirtualizationFirmwareEnabled) {
    Fail @'
la virtualización está deshabilitada en la BIOS.
  Reiniciá, entrá a la BIOS/UEFI y habilitá "SVM Mode" (AMD) o "Intel VT-x".
  Guardá y volvé a ejecutar este script.
'@
}

$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    Write-Host 'Instalando WSL2 (requiere reiniciar después)...'
    wsl.exe --install --no-distribution
    Write-Host 'Reiniciá la máquina y volvé a ejecutar este script.'
    exit 0
}
wsl.exe --status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'WSL existe pero no está inicializado: ejecutando wsl --install...'
    wsl.exe --install --no-distribution
    Write-Host 'Reiniciá la máquina y volvé a ejecutar este script.'
    exit 0
}

$installer = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'presto\installers') -Filter 'Docker Desktop*.exe' -ErrorAction SilentlyContinue |
    Select-Object -First 1
if (-not $installer) {
    Write-Host 'No está el instalador; descargándolo con winget...'
    $dest = Join-Path $env:LOCALAPPDATA 'presto\installers'
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    winget download --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements --download-directory $dest
    $installer = Get-ChildItem $dest -Filter 'Docker Desktop*.exe' | Select-Object -First 1
}

Write-Host "Instalando $($installer.Name)..."
$process = Start-Process -FilePath $installer.FullName `
    -ArgumentList @('install', '--quiet', '--accept-license') `
    -Wait -PassThru
if ($process.ExitCode -ne 0) {
    Fail "el instalador terminó con código $($process.ExitCode)."
}

Write-Host ''
Write-Host 'Docker Desktop instalado. Reiniciá la máquina y verificá con:' -ForegroundColor Green
Write-Host '  docker run --rm hello-world'
