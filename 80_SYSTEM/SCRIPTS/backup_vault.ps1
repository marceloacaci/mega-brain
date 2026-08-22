<#
.SYNOPSIS
    Backup FULL do cofre Obsidian para D:\Backups\Obsidian\full\YYYY-MM-DD.
.DESCRIPTION
    Usa robocopy (já vem no Windows). Ignora .obsidian e .trash.
    Chamado pela tarefa MEGA_BRAIN_Backup_Full (diário 02:00).
#>
$Vault     = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$BackupRoot= "D:\Backups\Obsidian"
$Dest      = Join-Path $BackupRoot ("full\" + (Get-Date -Format 'yyyy-MM-dd'))
$LogDir    = Join-Path $Vault "80_SYSTEM\LOGS"
$log       = Join-Path $LogDir ("backup_full_" + (Get-Date -Format 'yyyy-MM-dd_HHmmss') + ".log")

if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Force -Path $Dest | Out-Null }

# String única com aspas em volta dos caminhos (caminhos com espaço quebram o robocopy se splitados)
$argStr = ('"{0}" "{1}" /E /XD ".obsidian" ".trash" /R:1 /W:1 /NP /NFL /NDL /LOG:"{2}"' -f $Vault, $Dest, $log)
$proc = Start-Process -FilePath robocopy -ArgumentList $argStr -Wait -PassThru -NoNewWindow
# robocopy: 0 = igual, 1 = copiado algo, >=8 = erro
if ($proc.ExitCode -lt 8) {
    Write-Output "[MEGA BRAIN] backup FULL ok -> $Dest (exit $($proc.ExitCode))"
    "$tsFull|full|$Dest" | Add-Content -Encoding UTF8 (Join-Path $LogDir "backup_history.log")
} else {
    Write-Error "[MEGA BRAIN] backup FULL FALHOU (exit $($proc.ExitCode)) — ver $log"
    exit 1
}
