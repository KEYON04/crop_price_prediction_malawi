# PowerShell Script to register a weekly Windows Scheduled Task
# Runs every Monday at 06:00 AM

$TaskName = "MalawiCropPricePipeline"
$RepoPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PythonExe = Join-Path $RepoPath ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $RepoPath "automation\run_all.py"

Write-Host "Registering Scheduled Task: $TaskName"
Write-Host "Repository Path: $RepoPath"
Write-Host "Python Executable: $PythonExe"

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory $RepoPath
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 6am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Runs the Malawi Crop Price Forecasting Pipeline weekly on Monday morning" -Force

Write-Host "Task '$TaskName' registered successfully!"
