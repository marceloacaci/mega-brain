<#
.SYNOPSIS
    Restaura o cofre a partir de um backup (full ou incremental).
.DESCRIPTION
    Copia o conteúdo de $Source de volta para o vault.
.PARAMETER Source
    Pasta de origem do backup (ex.: D:\Backups\Obsidian\full\2026-08-21).
.PARAMETER Confirm
    Se ausente, roda em modo simulação (não escreve nada).
#>
[CmdletBinding()]
param(
    [string]$Source = "",
    [switch]$Confirm
)

$Vault = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"

if (-not $Source -or -not (Test-Path $Source)) {
    Write-Error "[MEGA BRAIN] informe -Source válido. Ex.: -Source 'D:\Backups\Obsidian\full\2026-08-21'"
    exit 1
}

if (-not $Confirm) {
    Write-Output "[MEGA BRAIN] MODO SIMULAÇÃO (use -Confirm para restaurar de verdade)."
    Write-Output "  Origem: $Source"
    Write-Output "  Destino: $Vault"
    $sim = ('"{0}" "{1}" /E /XD ".obsidian" ".trash" /R:1 /W:1 /NP /NFL /NDL /L' -f $Source, $Vault)
    Start-Process -FilePath robocopy -ArgumentList $sim -Wait -NoNewWindow
    exit 0
}

$log = Join-Path $Vault ("80_SYSTEM\LOGS\restore_" + (Get-Date -Format 'yyyy-MM-dd_HHmmss') + ".log")
$argStr = ('"{0}" "{1}" /E /XD ".obsidian" ".trash" /R:1 /W:1 /NP /NFL /NDL /LOG:"{2}"' -f $Source, $Vault, $log)
$proc = Start-Process -FilePath robocopy -ArgumentList $argStr -Wait -PassThru -NoNewWindow
if ($proc.ExitCode -lt 8) {
    Write-Output "[MEGA BRAIN] RESTORE ok <- $Source (exit $($proc.ExitCode))"
} else {
    Write-Error "[MEGA BRAIN] RESTORE FALHOU (exit $($proc.ExitCode)) — ver $log"
    exit 1
}
