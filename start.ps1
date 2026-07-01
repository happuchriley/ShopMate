# ShopMate — development server with reload
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = $Root

& "$Root\setup_env.ps1" | Out-Null

$python = & "$Root\scripts\get_python.ps1"
if (-not $python) { throw "Python not found. Run .\create_all.ps1 first." }

Write-Host "Starting ShopMate dev server on http://127.0.0.1:8000"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
