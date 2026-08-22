# Agendamento das tarefas do MEGA BRAIN (executar como Admin).
$Scripts = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills\80_SYSTEM\SCRIPTS"

# 1) Backup diário 02:00
$act = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Scripts\backup_vault.ps1`""
Register-ScheduledTask -TaskName "MEGA_BRAIN_Backup" -Action $act -Trigger (New-ScheduledTaskTrigger -Daily -At "02:00") -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun) -Force | Out-Null
Write-Host "✅ MEGA_BRAIN_Backup (diário 02:00)"

# 2) Reindex light a cada 6h
$actL = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Scripts\reindex_hybrid.ps1`" -Mode light"
Register-ScheduledTask -TaskName "MEGA_BRAIN_Reindex_Light" -Action $actL -Trigger (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration (New-TimeSpan -Days 365)) -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) -Force | Out-Null
Write-Host "✅ MEGA_BRAIN_Reindex_Light (6h)"

# 3) Reindex deep domingo 23:00
$actD = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Scripts\reindex_hybrid.ps1`" -Mode deep"
Register-ScheduledTask -TaskName "MEGA_BRAIN_Reindex_Deep" -Action $actD -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "23:00") -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) -Force | Out-Null
Write-Host "✅ MEGA_BRAIN_Reindex_Deep (domingo 23:00)"

Write-Host "`nTarefas registradas:"
Get-ScheduledTask | Where-Object { $_.TaskName -like "MEGA_BRAIN*" } | Format-Table TaskName, State -AutoSize
