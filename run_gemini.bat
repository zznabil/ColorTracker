@echo off
setlocal
:: Navigate to the directory where the script is located
cd /d "%~dp0"

echo [STORY TRACKER] Starting Gemini CLI task...
echo [STORY TRACKER] Reading prompt from: prompt.txt
echo [STORY TRACKER] Output will be logged to: gemini_output.log
echo ---------------------------------------------------------

:: Check if prompt.txt exists
if not exist "prompt.txt" (
    echo [ERROR] prompt.txt not found!
    echo [ERROR] prompt.txt not found! > error.log
    pause
    exit /b 1
)

:: Execute gemini CLI using prompt.txt as input with --yolo flag
:: We use PowerShell to pipe the content and Tee-Object to show output while logging
powershell -Command "Get-Content prompt.txt | gemini --yolo | Tee-Object -FilePath gemini_output.log"

echo ---------------------------------------------------------
echo [STORY TRACKER] Task completed.
echo [STORY TRACKER] Check gemini_output.log for historical records.

:: Only pause if we're not running as a scheduled task (SessionName is usually 'Console' or 'RDP-Tcp#X')
:: Task Scheduler runs in a non-interactive session or has 'Unknown' session name in some contexts.
:: A better way is checking for an environment variable or simply letting it close if it's scheduled.
:: For now, let's just pause so the user can see it when they run it manually.
if "%SESSIONNAME%"=="Console" pause
