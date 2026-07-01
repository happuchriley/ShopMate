# ShopMate — ensure .env exists from example
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example"
    } else {
        Write-Warning ".env.example not found"
    }
} else {
    Write-Host ".env already exists"
}

Write-Host "Edit .env and set OPENAI_API_KEY before starting the server."
