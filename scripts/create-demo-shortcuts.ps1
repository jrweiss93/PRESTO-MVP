# Crea los accesos directos de la demo en el escritorio.

$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$icon = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe,0"

$start = $shell.CreateShortcut((Join-Path $desktop 'Presto Demo.lnk'))
$start.TargetPath = Join-Path $root 'PRESTO-DEMO.cmd'
$start.WorkingDirectory = $root
$start.Description = 'Levanta la demo local de Presto'
$start.IconLocation = $icon
$start.Save()

$stop = $shell.CreateShortcut((Join-Path $desktop 'Detener Presto Demo.lnk'))
$stop.TargetPath = Join-Path $root 'PRESTO-DEMO-STOP.cmd'
$stop.WorkingDirectory = $root
$stop.Description = 'Detiene la demo local de Presto'
$stop.IconLocation = $icon
$stop.Save()

Write-Host 'Accesos directos creados en el escritorio:' -ForegroundColor Green
Write-Host '  Presto Demo'
Write-Host '  Detener Presto Demo'
