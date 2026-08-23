<#
.SYNOPSIS
    Backup FULL do cofre Obsidian com failover para 2o destino.
.DESCRIPTION
    Usa robocopy (nativo do Windows). Ignora .obsidian e .trash.
    Tenta $BackupRoot (primario); se falhar (exit >= 8 ou destino inacessivel),
    tenta $BackupRoot2 (secundario, se configurado). Registra em backup_history.log
    qual destino foi usado.
    Stack preservado: PowerShell 7 + robocopy (sem dependencias externas).
.PARAMETER Vault
    Caminho do cofre (padrao: o vault real). Usado pelos testes E2E.
.PARAMETER ConfigPath
    Caminho do config.json (padrao: 80_SYSTEM/SCRIPTS/config.json).
#>
[CmdletBinding()]
param(
    [string]$Vault      = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills",
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"
$ts = Get-Date -Format 'yyyy-MM-dd_HHmmss'

# --- Leitura de config (failover de 2o destino) -----------------------------
function Get-Cfg {
    param([string]$Path)
    if (-not $Path) { $Path = Join-Path $Vault "80_SYSTEM\SCRIPTS\config.json" }
    if (Test-Path $Path) {
        try { return (Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json) }
        catch { return $null }
    }
    return $null
}
$cfg = Get-Cfg -Path $ConfigPath
$BackupRoot  = if ($cfg -and $cfg.backup.root) { $cfg.backup.root } else { "D:\Backups\Obsidian" }
$BackupRoot2 = if ($cfg -and $cfg.backup.secondary_root) { $cfg.backup.secondary_root } else { "" }

$LogDir = Join-Path $Vault "80_SYSTEM\LOGS"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }
$history = Join-Path $LogDir "backup_history.log"

function Invoke-BackupTo {
    param([string]$Dest)
    if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Force -Path $Dest | Out-Null }
    $log = Join-Path $LogDir ("backup_full_" + $ts + ".log")
    $argStr = ('"{0}" "{1}" /E /XD ".obsidian" ".trash" /R:1 /W:1 /NP /NFL /NDL /LOG:"{2}"' -f $Vault, $Dest, $log)
    try {
        $proc = Start-Process -FilePath robocopy -ArgumentList $argStr -Wait -PassThru -NoNewWindow
        # robocopy: 0=igual, 1=copiou, >=8=erro
        return ($proc.ExitCode -lt 8)
    } catch {
        Write-Warning ("[MEGA BRAIN] falha ao invocar robocopy para " + $Dest + " : " + $_)
        return $false
    }
}

function Test-DestinoAcessivel {
    param([string]$Root)
    if (-not $Root) { return $false }
    # Se o root aponta para um drive (ex.: X:), o drive deve existir.
    if ($Root -match '^[A-Za-z]:') {
        $drive = $Root[0] + ":"
        if (-not (Test-Path -LiteralPath $drive)) { return $false }
    }
    return $true
}

$Dest1 = $null
if (Test-DestinoAcessivel -Root $BackupRoot) {
    try { $Dest1 = Join-Path $BackupRoot ("full\" + (Get-Date -Format 'yyyy-MM-dd')) }
    catch { $Dest1 = $null }
}
Write-Output ("[MEGA BRAIN] tentando backup FULL primario -> " + $Dest1)
$ok1 = $false
if ($Dest1) { $ok1 = Invoke-BackupTo -Dest $Dest1 }

$used = ""
if ($ok1) {
    $used = $Dest1
    Write-Output ("[MEGA BRAIN] backup FULL ok (primario) -> " + $Dest1)
} elseif ($BackupRoot2) {
    $Dest2 = Join-Path $BackupRoot2 ("full\" + (Get-Date -Format 'yyyy-MM-dd'))
    Write-Warning "[MEGA BRAIN] primario FALHOU -- failover para 2o destino -> $Dest2"
    $ok2 = Invoke-BackupTo -Dest $Dest2
    if ($ok2) { $used = $Dest2; Write-Output ("[MEGA BRAIN] backup FULL ok (failover 2o) -> " + $Dest2) }
    else      { Write-Error "[MEGA BRAIN] backup FULL FALHOU nos dois destinos."; exit 1 }
} else {
    Write-Error "[MEGA BRAIN] backup FULL FALHOU (sem 2o destino configurado)."
    exit 1
}

("$ts|full|$used") | Add-Content -Encoding UTF8 $history
exit 0
