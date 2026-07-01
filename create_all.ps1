# ShopMate — full setup: Python, deps, DB
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = $Root

& "$Root\setup_env.ps1"

$python = & "$Root\scripts\get_python.ps1"
if (-not $python) { throw "Python not available" }
Write-Host "Using Python: $python"
& $python --version

Write-Host "Installing requirements..."
& $python -m pip install -r requirements.txt

Write-Host "Initializing database..."
& $python -c "from app.db.models import init_db; init_db(); print('DB initialized')"

Write-Host "Verifying imports..."
& $python -c "import app.main; import app.services.handler; print('Imports OK')"

Write-Host ""
Write-Host "Setup complete! Run .\start.ps1 to launch (set OPENAI_API_KEY in .env first)."
