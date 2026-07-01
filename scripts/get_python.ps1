# ShopMate — resolve Python (bundled .python or system)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-ShopMatePython {
    $bundled = Join-Path $Root ".python\python.exe"
    if (Test-Path $bundled) { return $bundled }

    foreach ($cmd in @("py -3.12", "python3.12", "python3", "python")) {
        try {
            $out = Invoke-Expression "$cmd --version 2>&1"
            if ($LASTEXITCODE -eq 0) { return $cmd }
        } catch {}
    }
    return $null
}

function Install-BundledPython {
    $pyDir = Join-Path $Root ".python"
    $pyExe = Join-Path $pyDir "python.exe"
    if (Test-Path $pyExe) { return $pyExe }

    Write-Host "Downloading Python 3.12 embeddable..."
    New-Item -ItemType Directory -Force -Path $pyDir | Out-Null
    $zipUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
    $zipPath = Join-Path $env:TEMP "python-embed.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

    Expand-Archive -Path $zipPath -DestinationPath $pyDir -Force
    Remove-Item $zipPath -Force

    $pthFile = Get-ChildItem $pyDir -Filter "python*._pth" | Select-Object -First 1
    if ($pthFile) {
        $content = Get-Content $pthFile.FullName
        $content = $content -replace "#import site", "import site"
        if ($content -notcontains "Lib\site-packages") {
            $content += "Lib\site-packages"
        }
        Set-Content $pthFile.FullName $content
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $pyDir "Lib\site-packages") | Out-Null

    $getPip = Join-Path $env:TEMP "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
    & $pyExe $getPip --no-warn-script-location
    Remove-Item $getPip -Force

    return $pyExe
}

function Ensure-ShopMatePath {
    param([string]$PyDir)
    $sitePackages = Join-Path $PyDir "Lib\site-packages"
    New-Item -ItemType Directory -Force -Path $sitePackages | Out-Null
    $pth = Join-Path $sitePackages "shopmate.pth"
    Set-Content $pth $Root -Encoding ascii
}

$python = Get-ShopMatePython
if (-not $python) {
    $python = Install-BundledPython
}
if ($python -like "*python.exe") {
    $pyDir = Split-Path $python -Parent
    Ensure-ShopMatePath $pyDir
}
Write-Output $python
