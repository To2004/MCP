# install_cleanup_task.ps1
# Run once (as the current user) to register the weekly Saturday cleanup job.
# No admin rights required — the task runs as the current user.
#
# Usage:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
#   .\scripts\install_cleanup_task.ps1
#
# To run immediately:  Start-ScheduledTask -TaskName 'MCP_WeeklyCleanup'
# To remove:           Unregister-ScheduledTask -TaskName 'MCP_WeeklyCleanup' -Confirm:$false

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python   = Join-Path $repoRoot ".venv\Scripts\python.exe"
$script   = Join-Path $repoRoot "scripts\weekly_cleanup.py"
$taskName = "MCP_WeeklyCleanup"

# Validate python exists
if (-not (Test-Path $python)) {
    Write-Error "Python not found at $python. Run 'uv sync' first."
    exit 1
}

# Build the action: run python with the cleanup script
$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "`"$script`"" `
    -WorkingDirectory $repoRoot

# Trigger: every Saturday at 09:00
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At "09:00"

# Settings: run even on battery, don't stop if on battery, start if missed
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries

# Register (or update if already exists) — runs as current logged-in user
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force | Out-Null

Write-Host ""
Write-Host "Task '$taskName' registered successfully." -ForegroundColor Green
Write-Host "  Schedule : Every Saturday at 09:00"
Write-Host "  Python   : $python"
Write-Host "  Script   : $script"
Write-Host "  Repo     : $repoRoot"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  Run now   : Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  View task : Get-ScheduledTask -TaskName '$taskName'"
Write-Host "  Remove    : Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
