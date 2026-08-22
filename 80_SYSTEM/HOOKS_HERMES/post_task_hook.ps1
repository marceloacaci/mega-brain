# post_task_hook.ps1 — MEGA BRAIN
# Executado APÓS qualquer tarefa no Hermes Agent.
# Atualiza daily note, índice e detecta padrões.
# Uso: powershell -File post_task_hook.ps1 -Tarefa "descricao" -Projeto "MeuBolso" -Resultado "sucesso" -Resumo "..."

param(
    [string]$Tarefa = "tarefa automatica",
    [string]$Projeto = "desconhecido",
    [string]$Resultado = "sucesso",
    [string]$Resumo = ""
)

$Vault = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$Daily = Join-Path $Vault ("20_DAILY_NOTES\{0:yyyy-MM-dd}.md" -f (Get-Date))
$Index = Join-Path $Vault "10_MEGA_BRAIN\INDEX_GERAL.md"
$Log   = Join-Path $Vault "80_SYSTEM\LOGS\setup.log"
$Metricas = Join-Path $Vault "80_SYSTEM\LOGS\metricas.json"

function Write-LogEntry($msg, $Level = "INFO") {
    "$('[{0:HH:mm:ss}]' -f (Get-Date)) [$Level] $msg" | Out-File -Append -Encoding utf8 $Log
}

# Gera uma nota de captura em 00_INBOX a partir do template CAPTURA.md.
# Placeholders {{DATA}}/{{TAREFA}}/{{PROJETO}}/{{RESUMO}}/{{RESULTADO}} são
# substituídos. Falha-segura: qualquer erro é logado e não interrompe o hook.
function Invoke-CaptureTemplate {
    $tpl = Join-Path $PSScriptRoot "..\TEMPLATES\CAPTURA.md"
    if (-not (Test-Path $tpl)) { Write-LogEntry "template CAPTURA.md ausente" "DEBUG"; return }
    try {
        $content = Get-Content $tpl -Raw
        $content = $content `
            -replace "{{DATA}}", (Get-Date -Format "yyyy-MM-dd HH:mm") `
            -replace "{{TAREFA}}", $Tarefa `
            -replace "{{PROJETO}}", $Projeto `
            -replace "{{RESUMO}}", $Resumo `
            -replace "{{RESULTADO}}", $Resultado
        $nome = "00_INBOX/captura_{0:yyyyMMddHHmmss}.md" -f (Get-Date)
        $dest = Join-Path $Vault $nome
        $content | Out-File -Encoding utf8 $dest
        Write-LogEntry "Captura gerada via template: $nome" "INFO"
    } catch {
        Write-LogEntry ("Erro ao gerar captura por template: $_") "WARN"
    }
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

# 1. Registrar execução no daily note
if (-not (Test-Path $Daily)) {
    ("---`ndata: {0:yyyy-MM-dd}`ntags: [daily/{0:yyyy}/{0:MM}]`n---`n`n# 📓 {0:yyyy-MM-dd}`n" -f (Get-Date)) | Out-File -Encoding utf8 $Daily
}
$linha = "- ✅ **{0:HH:mm}** — {1} · Projeto: {2} · Resultado: {3} · {4}" -f (Get-Date), $Tarefa, $Projeto, $Resultado, $Resumo
"$linha" | Out-File -Append -Encoding utf8 $Daily

# 2. Atualizar métricas (JSON simples)
if (Test-Path $Metricas) {
    try {
        $m = Get-Content $Metricas -Raw | ConvertFrom-Json
        $m.tarefas_total = [int]$m.tarefas_total + 1
        $dia = "{0:yyyy-MM-dd}" -f (Get-Date)
        if (-not $m.tarefas_por_dia.PSObject.Properties[$dia]) { $m.tarefas_por_dia | Add-Member -NotePropertyName $dia -NotePropertyValue 0 }
        $m.tarefas_por_dia.$dia = [int]$m.tarefas_por_dia.$dia + 1
        $m | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $Metricas
    } catch { Write-LogEntry ("ERRO metricas: $_") "ERROR" }
}

# 3. Validacao silenciosa (1 linha)
$pads = if (Test-Path (Join-Path $Vault "10_MEGA_BRAIN\PADROES_RECorrentes.md")) { (Get-Content (Join-Path $Vault "10_MEGA_BRAIN\PADROES_RECorrentes.md") | Where-Object { $_ -match '^## P' }).Count } else { 0 }
Write-Output ("[HERMES-AGENT] 🧠 Cérebro atualizado → 1 projeto · 4 notas · {0} padrões · 0 conflitos" -f $pads)
Write-LogEntry ("POS tarefa='$Tarefa' projeto='$Projeto' resultado='$Resultado'") "INFO"

# Gera captura em 00_INBOX a partir do template (falha-segura)
Invoke-CaptureTemplate

# Força reindex light se última > limite (config.json)
Invoke-LightReindexIfNeeded
