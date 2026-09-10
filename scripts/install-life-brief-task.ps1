#!/usr/bin/env pwsh
#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Register a daily scheduled task for life-brief.

.DESCRIPTION
    Creates a Windows Task Scheduler task that runs life-brief.py every day at
    the specified time and writes the report to _brief/life-<date>.md.

.EXAMPLE
    pwsh -File tools/0-cli/scripts/install-life-brief-task.ps1 -Time 09:00
#>
[CmdletBinding()]
param(
    [string]$Time = "09:00",
    [string]$TaskName = "LifeBrief-Daily",
    [string]$WorkspaceRoot = "C:\Users\Administrator\Documents\0_docs"
)

$Script = Join-Path $WorkspaceRoot "tools\0-cli\scripts\life-brief.py"
$OutDir = Join-Path $WorkspaceRoot "_brief"

if (-not (Test-Path $Script)) {
    throw "脚本不存在: $Script"
}

$Command = @"
`$env:PATH = 'C:\Users\Administrator\AppData\Roaming\Python\Python314\Scripts;C:\Users\Administrator\AppData\Roaming\npm;' + `$env:PATH
cd '$WorkspaceRoot'
python '$Script' --out '$OutDir\life-' + (Get-Date -Format 'yyyy-MM-dd') + '.md'
"@

$Action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command $Command"
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
Write-Host "已注册计划任务: $TaskName，每天 $Time 运行" -ForegroundColor Green
Write-Host "查看: schtasks /query /tn $TaskName" -ForegroundColor Cyan
