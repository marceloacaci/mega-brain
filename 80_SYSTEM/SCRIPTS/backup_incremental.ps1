<#
.SYNOPSIS
    Backup INCREMENTAL do cofre (apenas arquivos alterados nas últimas 24h).
.DESCRIPTION
    robocopy /MAXAGE:1 copia só o que mudou no último dia.
    Chamado pela tarefa MEGA_BRAIN_Backup_Incremental (6h).
#>
$Vault     = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$BackupRoot= "D:\Backups\Obsidian"
$Dest      = Join-Path $BackupRoot ("inc\" + (Get-Date -Format 'yyyy-MM-dd_HHmm'))
$LogDir    = Join-Path $Vault "80_SYSTEM\LOGS"
$log       = Join-Path $LogDir ("backup_inc_" + (Get-Date -Format 'yyyy-MM-dd_HHmmss') + ".log")

if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Force -Path $Dest | Out-Null }

$argStr = ('"{0}" "{1}" /E /XD ".obsidian" ".trash" /MAXAGE:1 /R:1 /W:1 /NP /NFL /NDL /LOG:"{2}"' -f $Vault, $Dest, $log)
$proc = Start-Process -FilePath robocopy -ArgumentList $argStr -Wait -PassThru -NoNewWindow
if ($proc.ExitCode -lt 8) {
    Write-Output "[MEGA BRAIN] backup INCREMENTAL ok -> $Dest (exit $($proc.ExitCode))"
} else {
    Write-Error "[MEGA BRAIN] backup INCREMENTAL FALHOU (exit $($proc.ExitCode)) — ver $log"
    exit 1
}
