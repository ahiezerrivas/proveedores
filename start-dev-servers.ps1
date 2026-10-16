$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$backendDirectory = Join-Path $projectRoot 'backend'
$frontendDirectory = Join-Path $projectRoot 'frontend'
$pythonExecutable = Join-Path $projectRoot 'venv\Scripts\python.exe'
$npmCommand = 'C:\Program Files\nodejs\npm.cmd'
$commandProcessor = Join-Path $env:SystemRoot 'System32\cmd.exe'

function Test-PortInUse {
    param([int]$Port)

    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (Test-PortInUse -Port 8004)) {
    Start-Process -FilePath $pythonExecutable `
        -ArgumentList @('manage.py', 'runserver', '0.0.0.0:8004') `
        -WorkingDirectory $backendDirectory `
        -WindowStyle Hidden
}

if (-not (Test-PortInUse -Port 5177)) {
    Start-Process -FilePath $commandProcessor `
        -ArgumentList @('/c', "`"$npmCommand`" run dev:network") `
        -WorkingDirectory $frontendDirectory `
        -WindowStyle Hidden
}