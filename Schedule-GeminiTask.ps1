# PowerShell script to register a scheduled task for Gemini CLI
# This task is configured to run for a maximum of 1 hour.

$TaskName = "Gemini_CLI_Task"
$BatchFilePath = "C:\Users\Admin\Documents\ColorTracker\run_gemini.bat"

Write-Host "--- Scheduled Task Registration: $TaskName ---" -ForegroundColor Cyan

# Define the action: Run the batch file via cmd.exe
Write-Host "[1/4] Defining task action..." -ForegroundColor Gray
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchFilePath`""

# Define triggers:
Write-Host "[2/4] Defining triggers (Daily @ 12 PM + 5m Delay after Logon)..." -ForegroundColor Gray
$Trigger1 = New-ScheduledTaskTrigger -AtLogon
$Trigger1.Delay = "PT5M" # ISO 8601 duration for 5 minutes
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "12:00PM"
$Triggers = @($Trigger1, $Trigger2)

# Define settings: Stop the task if it runs longer than 1 hour
Write-Host "[3/4] Defining settings (1-hour time limit)..." -ForegroundColor Gray
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Register the task
Write-Host "[4/4] Registering task in System..." -ForegroundColor Gray
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Triggers -Settings $Settings -Force

Write-Host "`nTask '$TaskName' has been registered successfully!" -ForegroundColor Green
Write-Host "It will run 5 minutes after you log in, and every day at 12:00 PM." -ForegroundColor Yellow
Write-Host "Maximum execution time: 1 hour."

Write-Host "`nPress any key to close this window..."
$null = [System.Console]::ReadKey($true)
