# SAI Color Tracking Algorithm V3 - Enhanced Debug Launch Script
# Combines best features from BAT script with PowerShell robustness

# Set console colors for better visibility
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "Green"
Clear-Host

# Display header (BAT script simplicity)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SAI Color Tracking Algorithm V3 - Debug Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# NEW: Automatic dependency installation (from BAT script)
Write-Host "Checking and installing required packages..." -ForegroundColor Yellow
try {
    # Check if requirements.txt exists
    if (Test-Path "requirements.txt") {
        Write-Host "Found requirements.txt, installing dependencies..." -ForegroundColor Green
        pip install -r requirements.txt
        Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Installing core dependencies..." -ForegroundColor Yellow
        pip install dearpygui mss opencv-python numpy pyautogui pynput interception
        Write-Host "Core dependencies installed!" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Failed to install dependencies automatically" -ForegroundColor Red
    Write-Host "Please install manually: pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting algorithm with verbose debug logging..." -ForegroundColor Yellow
Write-Host "Log files will be saved in the 'logs' folder" -ForegroundColor Green

# NEW: User-friendly reminders (from BAT script)
Write-Host "Make sure your game is running before using this tool!" -ForegroundColor Magenta
Write-Host "Press F12 to toggle debug console" -ForegroundColor Cyan
Write-Host "Press PageUp to start algorithm, PageDown to stop" -ForegroundColor Magenta
Write-Host "Close the GUI window to exit" -ForegroundColor Magenta
Write-Host ""

# Change to script directory
Set-Location -Path $PSScriptRoot

# Enhanced Python checking (PowerShell robustness + BAT simplicity)
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found in PATH!" -ForegroundColor Red
    Write-Host "Installing Python automatically..." -ForegroundColor Yellow
    
    # NEW: Attempt to download and install Python (enhanced feature)
    try {
        Write-Host "Downloading Python installer..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe" -OutFile "python_installer.exe"
        Write-Host "Installing Python (this may take a few minutes)..." -ForegroundColor Yellow
        Start-Process -FilePath ".\python_installer.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        Remove-Item "python_installer.exe" -Force
        Write-Host "Python installed successfully!" -ForegroundColor Green
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # Verify installation
        $pythonVersion = python --version 2>&1
        Write-Host "Python verified: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "ERROR: Failed to install Python automatically" -ForegroundColor Red
        Write-Host "Please install Python manually from https://python.org" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check if main.py exists (PowerShell robustness)
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: main.py not found in current directory!" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create logs directory if it doesn't exist (PowerShell robustness)
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Name "logs" | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# NEW: Pre-launch system check (enhanced feature)
Write-Host "Performing pre-launch system check..." -ForegroundColor Yellow
try {
    # Check screen resolution
    Add-Type -AssemblyName System.Windows.Forms
    $screenWidth = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width
    $screenHeight = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height
    Write-Host "Screen resolution: ${screenWidth}x${screenHeight}" -ForegroundColor Green
    
    # Check available memory
    $memory = Get-CimInstance -ClassName Win32_OperatingSystem
    $freeMemory = [math]::Round($memory.FreePhysicalMemory / 1MB, 2)
    Write-Host "Available memory: ${freeMemory} GB" -ForegroundColor Green
    
    Write-Host "System check completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "WARNING: System check failed, continuing anyway..." -ForegroundColor Red
}

Write-Host ""
Write-Host "Launching SAI Color Tracking Algorithm V3..." -ForegroundColor Yellow
Write-Host ""

# Run the main Python script (BAT script simplicity + PowerShell error handling)
try {
    Write-Host "Starting main application..." -ForegroundColor Cyan
    python main.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Application exited with code $LASTEXITCODE" -ForegroundColor Yellow
    } else {
        Write-Host "Application completed successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR: Failed to run main.py" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Algorithm has been closed." -ForegroundColor Yellow
Write-Host "Check the logs folder for detailed debug information." -ForegroundColor Green

# Enhanced log file information (PowerShell robustness)
Write-Host ""
Write-Host "Log file information:" -ForegroundColor Cyan
if (Test-Path "logs") {
    $logFiles = Get-ChildItem -Path "logs" -Filter "*.log" | Sort-Object LastWriteTime -Descending
    if ($logFiles.Count -gt 0) {
        $latestLog = $logFiles[0]
        Write-Host "Latest log file: $($latestLog.Name)" -ForegroundColor Cyan
        Write-Host "Log file size: $([math]::Round($latestLog.Length / 1KB, 2)) KB" -ForegroundColor Cyan
        Write-Host "Log created: $($latestLog.CreationTime)" -ForegroundColor Cyan
        
        # Show log count
        Write-Host "Total log files: $($logFiles.Count)" -ForegroundColor Cyan
        
        # Offer to open log file
        $response = Read-Host "Would you like to open the latest log file? (Y/N)"
        if ($response -eq 'Y' -or $response -eq 'y') {
            Invoke-Item $latestLog.FullName
        }
    } else {
        Write-Host "No log files found in logs directory" -ForegroundColor Yellow
    }
} else {
    Write-Host "Logs directory not found" -ForegroundColor Yellow
}

# NEW: Post-launch options (enhanced feature)
Write-Host ""
Write-Host "What would you like to do next?" -ForegroundColor Cyan
Write-Host "1. Exit" -ForegroundColor White
Write-Host "2. Restart algorithm" -ForegroundColor White
Write-Host "3. Open logs directory" -ForegroundColor White
Write-Host "4. View system information" -ForegroundColor White

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    '1' { 
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0 
    }
    '2' { 
        Write-Host "Restarting algorithm..." -ForegroundColor Yellow
        & $PSCommandPath
        exit 0 
    }
    '3' { 
        if (Test-Path "logs") {
            Invoke-Item "logs"
        } else {
            Write-Host "Logs directory not found" -ForegroundColor Red
        }
        Read-Host "Press Enter to exit"
        exit 0 
    }
    '4' { 
        Write-Host "System Information:" -ForegroundColor Cyan
        Write-Host "OS Version: $((Get-CimInstance Win32_OperatingSystem).Caption)" -ForegroundColor White
        Write-Host "Architecture: $((Get-CimInstance Win32_OperatingSystem).OSArchitecture)" -ForegroundColor White
        Write-Host "Total Memory: $([math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)) GB" -ForegroundColor White
        Read-Host "Press Enter to exit"
        exit 0 
    }
    default { 
        Write-Host "Invalid choice, exiting..." -ForegroundColor Red
        exit 0 
    }
}