# SAI Color Tracking Algorithm - All-in-One Setup & Run
# "Zero to Hero" Automated Distribution Script
# Handles: Admin Check -> Python Install -> Venv -> Deps -> Build -> Launch

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "Cyan"
Clear-Host

function Print-Header {
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "   SAI COLOR TRACKER - AUTO SETUP & LAUNCHER      " -ForegroundColor White
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Print-Step {
    param([string]$Message)
    Write-Host "`n>> $Message" -ForegroundColor Yellow
}

function Print-Success {
    param([string]$Message)
    Write-Host "   [OK] $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "   [ERROR] $Message" -ForegroundColor Red
}

Print-Header

# -----------------------------------------------------------------------------
# 1. Admin Privilege Check & Self-Elevation
# -----------------------------------------------------------------------------
Print-Step "Checking privileges..."
$isElevated = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isElevated) {
    Write-Host "   Requesting Administrator privileges for setup..." -ForegroundColor Magenta
    try {
        Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
        exit
    } catch {
        Print-Error "Failed to elevate privileges. Please run as Administrator."
        exit 1
    }
}
Print-Success "Running as Administrator"

# -----------------------------------------------------------------------------
# 2. Python Environment Check & Installation
# -----------------------------------------------------------------------------
Print-Step "Checking Python installation..."
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "Python 3\.") {
        Print-Success "Found $pyVersion"
    } else {
        throw "Python not found or version mismatch."
    }
} catch {
    Write-Host "   Python not found. Initiating automated installation..." -ForegroundColor Magenta
    
    $installerUrl = "https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe"
    $installerPath = "$env:TEMP\python_installer.exe"
    
    try {
        Print-Step "Downloading Python 3.12..."
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
        
        Print-Step "Installing Python 3.12 (Silent)..."
        Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
        
        # Refresh PATH for the current session
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        $pyVersion = python --version 2>&1
        Print-Success "Installed $pyVersion successfully"
        
        Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
    } catch {
        Print-Error "Failed to install Python automatically. Please install Python 3.12 manually."
        Write-Host "   Error: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# -----------------------------------------------------------------------------
# 3. Virtual Environment Setup
# -----------------------------------------------------------------------------
Set-Location -Path $PSScriptRoot
$venvName = ".venv"
$venvPath = Join-Path $PSScriptRoot $venvName
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

Print-Step "Checking Virtual Environment..."
if (-not (Test-Path $venvPath)) {
    Write-Host "   Creating virtual environment '$venvName'..." -ForegroundColor Magenta
    python -m venv $venvName
    Print-Success "Virtual environment created"
} else {
    Print-Success "Virtual environment exists"
}

# -----------------------------------------------------------------------------
# 4. Dependency Installation
# -----------------------------------------------------------------------------
Print-Step "Installing Dependencies..."
if (-not (Test-Path "requirements.txt")) {
    Print-Error "requirements.txt not found!"
    exit 1
}

# Always try to upgrade pip first
& $venvPython -m pip install --upgrade pip | Out-Null

# Install Deps
Write-Host "   Installing core requirements..." -ForegroundColor Gray
& $venvPip install -r requirements.txt | Out-Null

# Install PyInstaller
Write-Host "   Installing/Verifying PyInstaller..." -ForegroundColor Gray
& $venvPip install pyinstaller | Out-Null

Print-Success "Dependencies installed"

# -----------------------------------------------------------------------------
# 5. Build Executable
# -----------------------------------------------------------------------------
Print-Step "Building Application (PyInstaller)..."
if (-not (Test-Path "ColorTracker.spec")) {
    Print-Error "ColorTracker.spec not found! Cannot build."
    exit 1
}

$pyinstaller = Join-Path $venvPath "Scripts\pyinstaller.exe"
Write-Host "   Compiling EXE. This may take a minute..." -ForegroundColor Magenta

try {
    & $pyinstaller --clean --noconfirm --log-level=WARN ColorTracker.spec
    
    if ($LASTEXITCODE -eq 0) {
        Print-Success "Build Complete!"
    } else {
        throw "PyInstaller exited with code $LASTEXITCODE"
    }
} catch {
    Print-Error "Build Failed: $_"
    Read-Host "Press Enter to exit"
    exit 1
}

# -----------------------------------------------------------------------------
# 6. Launch Application
# -----------------------------------------------------------------------------
$exePath = Join-Path $PSScriptRoot "dist\ColorTracker.exe"

if (Test-Path $exePath) {
    Print-Step "Launching Application..."
    Start-Process -FilePath $exePath
    Print-Success "ColorTracker is running!"
} else {
    Print-Error "Executable not found at $exePath"
    exit 1
}

Write-Host "`nSetup & Launch Complete. You can close this window." -ForegroundColor Green
Start-Sleep -Seconds 3
