# ShopMate — production server (no reload)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = $Root

& "$Root\setup_env.ps1" | Out-Null

$python = & "$Root\scripts\get_python.ps1"
if (-not $python) { throw "Python not found. Run .\create_all.ps1 first." }

$port = if ($env:PORT) { $env:PORT } else { "8000" }
Write-Host "Starting ShopMate production server on port $port"
& $python -m uvicorn app.main:app --host 0.0.0.0 --port $port
