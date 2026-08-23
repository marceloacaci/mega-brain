<#
.SYNOPSIS
    Verifica a INTEGRIDADE do cofre (M5 Resiliencia).
.DESCRIPTION
    Checagens:
      1. Estrutura obrigatoria: pastas 10_MEGA_BRAIN, 70_MOCS, 80_SYSTEM existem.
      2. Notas corrompidas: .md com 0 bytes ou que falham ao ler como UTF-8.
      3. (Opcional, -Backup) integridade de backup: robocopy /L conta arquivos
         em falta no destino vs origem.
    Retorna exit 0 se integro, 1 se há problemas (e lista no stdout).
.PARAMETER Vault
    Caminho do cofre.
.PARAMETER Backup
    Pasta de backup a validar contra o vault (opcional).
#>
[CmdletBinding()]
param(
    [string]$Vault  = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills",
    [string]$Backup = ""
)

$problems = @()
$required = @("10_MEGA_BRAIN", "70_MOCS", "80_SYSTEM")

# 1. Estrutura obrigatoria
foreach ($d in $required) {
    $p = Join-Path $Vault $d
    if (-not (Test-Path $p)) { $problems += "PASTA AUSENTE: $d" }
}

# 2. Notas corrompidas (0 bytes / ilegivel)
if (Test-Path $Vault) {
    Get-ChildItem -Path $Vault -Recurse -Filter *.md | Where-Object {
        $_.FullName -notmatch '\\\.obsidian\\'
    } | ForEach-Object {
        try {
            if ($_.Length -eq 0) { $problems += "NOTA VAZIA (0 bytes): $($_.FullName)" }
            else { $null = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::UTF8) }
        } catch {
            $problems += "NOTA ILEGIVEL (encoding): $($_.FullName)"
        }
    }
}

# 3. Integridade de backup (robocopy /L)
if ($Backup -and (Test-Path $Backup)) {
    $logDir = Join-Path $Vault "80_SYSTEM\LOGS"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
    $log = Join-Path $logDir ("integrity_" + (Get-Date -Format 'yyyy-MM-dd_HHmmss') + ".log")
    $argStr = ('"{0}" "{1}" /E /XD ".obsidian" ".trash" /R:1 /W:1 /NP /NFL /NDL /L /LOG:"{2}"' -f $Vault, $Backup, $log)
    Start-Process -FilePath robocopy -ArgumentList $argStr -Wait -NoNewWindow | Out-Null
    # robocopy /L nao copia; se houver arquivos em falta no destino, o log cita "0" copiados
    # mas listaria diferencas. Checagem simples: conta linhas de "Extra" ou "Newer"/"Older".
    $diff = (Select-String -Path $log -Pattern "Extra File|Newer|Older|Mismatched" -SimpleMatch).Count
    if ($diff -gt 0) { $problems += "BACKUP DESATUALIZADO: $diff diferenca(s) vs vault (ver $log)" }
    Write-Output "[MEGA BRAIN] integridade de backup: $(if($diff -eq 0){'OK'}else{'PROBLEMAS'})"
}

if ($problems.Count -eq 0) {
    Write-Output "[MEGA BRAIN] INTEGRIDADE DO COFRE: OK (sem problemas detectados)"
    exit 0
} else {
    Write-Error "[MEGA BRAIN] INTEGRIDADE: $($problems.Count) problema(s):"
    $problems | ForEach-Object { Write-Error "  - $_" }
    exit 1
}
