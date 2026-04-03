$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-PythonCommand {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "py"; Args = @("-3.10") },
        @{ Exe = "python"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) {
            continue
        }
        & $candidate.Exe @($candidate.Args + @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)")) | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return $candidate
        }
    }

    return $null
}

function Refresh-LocalPythonPath {
    $extraPaths = @(
        "$env:LocalAppData\Programs\Python\Launcher",
        "$env:LocalAppData\Programs\Python\Python311",
        "$env:LocalAppData\Programs\Python\Python310"
    )
    $current = @()
    if ($env:Path) {
        $current = $env:Path -split ";"
    }
    $env:Path = (($extraPaths + $current) | Where-Object { $_ } | Select-Object -Unique) -join ";"
}

function Install-PythonWithWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        return $false
    }

    Write-Step "Python 3.11 not found. Trying winget install"
    & winget install --exact --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements --silent --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        Write-Host "winget install did not finish successfully." -ForegroundColor Yellow
        return $false
    }

    Refresh-LocalPythonPath
    return $true
}

function Install-PythonFromOfficialInstaller {
    Write-Step "Trying official Python installer download"
    $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $installerPath = Join-Path $env:TEMP "python-3.11.9-amd64.exe"

    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
    $process = Start-Process -FilePath $installerPath -ArgumentList @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=1",
        "Include_test=0",
        "Include_doc=0",
        "Include_launcher=1",
        "SimpleInstall=1"
    ) -Wait -PassThru

    if ($process.ExitCode -ne 0) {
        throw "Python installer exited with code $($process.ExitCode)."
    }

    Refresh-LocalPythonPath
}

function Ensure-Python {
    $python = Get-PythonCommand
    if ($python) {
        return $python
    }

    $installed = Install-PythonWithWinget
    if ($installed) {
        $python = Get-PythonCommand
        if ($python) {
            return $python
        }
    }

    Install-PythonFromOfficialInstaller
    $python = Get-PythonCommand
    if ($python) {
        return $python
    }

    throw "Python 3.10+ could not be installed automatically."
}

$python = Ensure-Python
$pythonCmdText = ($python.Exe + " " + ($python.Args -join " ")).Trim()

Write-Step "Using Python command: $pythonCmdText"
& $python.Exe @($python.Args + @("--version"))

$venvPath = Join-Path $projectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Step "Creating virtual environment at .venv"
    & $python.Exe @($python.Args + @("-m", "venv", $venvPath))
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment."
    }
}
else {
    Write-Step "Virtual environment already exists at .venv"
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python not found at $venvPython"
}

Write-Step "Upgrading pip"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip."
}

Write-Step "Installing project dependencies"
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install requirements.txt."
}

Write-Step "Done"
Write-Host "Virtual environment: $venvPath"
Write-Host "GUI start command:"
Write-Host "  .venv\Scripts\python -m excel_data_analysis.gui.app"
Write-Host ""
Write-Host "Optional build dependencies:"
Write-Host "  .venv\Scripts\python -m pip install -r requirements-build.txt"
