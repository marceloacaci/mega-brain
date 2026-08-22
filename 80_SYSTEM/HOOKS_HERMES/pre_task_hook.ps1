# pre_task_hook.ps1 — MEGA BRAIN
# Executado ANTES de qualquer tarefa no Hermes Agent.
# Lê o cérebro, detecta contexto e registra o início no daily note.
# Uso: powershell -File pre_task_hook.ps1 -Tarefa "descricao" -Projeto "MeuBolso" -Stack "Electron,Vue"

param(
    [string]$Tarefa = "tarefa automatica",
    [string]$Projeto = "desconhecido",
    [string]$Stack = ""
)

$Vault = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$Index = Join-Path $Vault "10_MEGA_BRAIN\INDEX_GERAL.md"
$Daily = Join-Path $Vault ("20_DAILY_NOTES\{0:yyyy-MM-dd}.md" -f (Get-Date))
$Log   = Join-Path $Vault "80_SYSTEM\LOGS\setup.log"

function Write-LogEntry($msg, $Level = "INFO") {
    "$('[{0:HH:mm:ss}]' -f (Get-Date)) [$Level] $msg" | Out-File -Append -Encoding utf8 $Log
}

# Força reindexação LIGHT se a última light foi há mais de force_after_hours (config.json).
function Invoke-LightReindexIfNeeded {
    $ConfigFile = Join-Path $PSScriptRoot "..\SCRIPTS\config.json"
    if (-not (Test-Path $ConfigFile)) { Write-LogEntry "config.json não encontrado" "WARN"; return }
    try { $Config = Get-Content $ConfigFile -Raw | ConvertFrom-Json } catch { Write-LogEntry "Erro ao ler config.json" "ERROR"; return }

    $lastLightFile = Join-Path $Config.log_path ".last_light.txt"
    $threshold = (Get-Date).AddHours(-4)
    $shouldReindex = $false
    if (Test-Path $lastLightFile) {
        try {
            $raw = Get-Content $lastLightFile -Raw
            $lastLight = Get-Date -Date $raw
            if ($lastLight -lt $threshold) {
                $shouldReindex = $true
            }
        } catch {
            $shouldReindex = $true
        }
    } else {
        $shouldReindex = $true
    }

    if ($shouldReindex) {
        Write-LogEntry "⚡ Reindex light automática (última > 4h)" "INFO"
        $scriptReindex = Join-Path $PSScriptRoot "..\SCRIPTS\reindex_hybrid.ps1"
        if (Test-Path $scriptReindex) {
            try {
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptReindex -Mode light | Out-Null
                Set-Content -Path $lastLightFile -Value (Get-Date -Format "o") -Encoding UTF8
                Write-LogEntry "Reindex light executada e timestamp atualizado" "INFO"
            } catch {
                Write-LogEntry "⚠️ Falha na reindex light: $_" "WARN"
            }
        }
    } else {
        Write-LogEntry "Reindex light adiada (dentro da janela de 4 h)" "DEBUG"
    }
}

# ============================================
# VERIFICAR SE REINDEX ESTÁ RODANDO
# ============================================
$lockFile = Join-Path $Vault "80_SYSTEM\LOGS\.reindex.lock"
if (Test-Path $lockFile) {
    $lockAge = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    if ($lockAge.TotalMinutes -lt 30) {
        Write-LogEntry "⏭️ Reindex em andamento ($($lockAge.TotalMinutes.ToString('0'))min), prosseguindo sem lock" "DEBUG"
    }
}

# 1. Ler cérebro
$ctx = ""
if (Test-Path $Index) { $ctx = Get-Content $Index -Raw -ErrorAction SilentlyContinue }

# 2. Buscar similaridade simples (palavras do projeto/stack no índice)
$hits = 0; $padroes = 0; $prefs = 0
if ($ctx) {
    $termos = ($Projeto, $Stack -split ',') | Where-Object { $_ }
    foreach ($t in $termos) {
        if ($t -and ($ctx -match [regex]::Escape($t))) { $hits++ }
    }
}
if (Test-Path (Join-Path $Vault "10_MEGA_BRAIN\PADROES_RECorrentes.md")) { $padroes = (Get-Content (Join-Path $Vault "10_MEGA_BRAIN\PADROES_RECorrentes.md") | Where-Object { $_ -match '^## P' }).Count }
if (Test-Path (Join-Path $Vault "10_MEGA_BRAIN\PREFERENCIAS_PESSOAIS.md")) { $prefs = 1 }

# 3. Registrar início no daily note
$linha = "- **Início {0:HH:mm}** — {1} · Projeto: {2} · Stack: {3} · Similares no cérebro: {4}" -f (Get-Date), $Tarefa, $Projeto, $Stack, $hits
if (-not (Test-Path $Daily)) {
    $hdr = ("---\ndata: {0:yyyy-MM-dd}\ntags: [daily/{0:yyyy}/{0:MM}]\n---\n\n# 📓 {0:yyyy-MM-dd}\n\n## 🚀 Tarefas do Dia\n" -f (Get-Date))
    $hdr | Out-File -Encoding utf8 $Daily
}
"$linha" | Out-File -Append -Encoding utf8 $Daily

# 4. Comando silencioso (1 linha)
Write-Output ("[HERMES-AGENT] 🧠 Cérebro consultado → {0} resultados relevantes · {1} padrões detectados · {2} preferências aplicadas" -f $hits, $padroes, $prefs)
Write-LogEntry ("PRE  tarefa='$Tarefa' projeto='$Projeto' hits=$hits") "INFO"

# Força reindex light se última > limite (config.json)
Invoke-LightReindexIfNeeded
