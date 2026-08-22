<#
.SYNOPSIS
    Reindex híbrido do Mega Brain (light = métricas/timestamp; deep = reconstrói INDEX_GERAL).
.DESCRIPTION
    Chamado pelas tarefas agendadas MEGA_BRAIN_Reindex_Light (6h) e _Deep (domingo 23h).
    Sem dependências externas — roda em PowerShell 5.1+.
.PARAMETER Mode
    light | deep  (padrão: light)
#>
[CmdletBinding()]
param([string]$Mode = "light")

$Vault    = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$LogDir   = Join-Path $Vault "80_SYSTEM\LOGS"
$IndexFile= Join-Path $Vault "10_MEGA_BRAIN\INDEX_GERAL.md"
$Metrics  = Join-Path $LogDir "metricas_horarias.json"
$ts       = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
$tsShort  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Stamp($rel) { $ts | Set-Content -Path (Join-Path $LogDir $rel) -Encoding UTF8 }
function StampISO($rel) { (Get-Date -Format "o") | Set-Content -Path (Join-Path $LogDir $rel) -Encoding UTF8 }

# --- carrega/aprimora métricas ---
$m = @{}
if (Test-Path $Metrics) {
    try { $m = Get-Content $Metrics -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable } catch { $m = @{} }
}
$m.ultima_execucao = $tsShort
$m.modo            = $Mode
$m.total_notas = (Get-ChildItem $Vault -Recurse -Filter *.md -File |
                  Where-Object { $_.FullName -notmatch '\\\.obsidian' -and
                                 $_.FullName -notmatch '\\venv\\' -and
                                 $_.FullName -notmatch '\\node_modules\\' }).Count
$m.projetos   = @((Get-ChildItem (Join-Path $Vault "30_PROJECTS") -Directory -ErrorAction SilentlyContinue).Name)
$m.mocs       = (Get-ChildItem (Join-Path $Vault "70_MOCS") -Filter *.md -File -ErrorAction SilentlyContinue).Count
$m | ConvertTo-Json -Depth 5 -Compress | Out-File -Encoding utf8 $Metrics

# --- gera nota de métrica em 50_METRICS/ (para o Dataview ler) ---
try {
    $MetricsDir = Join-Path $Vault "50_METRICS"
    if (-not (Test-Path $MetricsDir)) { New-Item -ItemType Directory -Path $MetricsDir -Force | Out-Null }
    $tamanhoMB = [math]::Round((Get-ChildItem $Vault -Recurse -File | Where-Object { $_.FullName -notmatch '\\\.obsidian' -and $_.FullName -notmatch '\\venv\\' -and $_.FullName -notmatch '\\node_modules\\' } | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    $tsFile = Get-Date -Format "yyyy-MM-ddTHHmmss"
    $notaMetricas = Join-Path $MetricsDir "$tsFile.md"
    $conteudo = @(
        "---",
        "tags: [metrica]",
        "mode: $Mode",
        "total_notas: $($m.total_notas)",
        "total_projetos: $($m.projetos.Count)",
        "total_mocs: $($m.mocs)",
        "tamanho_mb: $tamanhoMB",
        "timestamp: $ts",
        "---",
        "",
        "Snapshot de métricas ($Mode) gerado por reindex_hybrid.ps1 em $tsShort."
    )
    $conteudo | Set-Content -Path $notaMetricas -Encoding UTF8
} catch {
    Write-Warning "Falha ao gerar nota de métricas: $_"
}

if ($Mode -eq "deep") {
    # reconstrói o corpo do INDEX_GERAL.md, preservando o frontmatter (tipo/criado/tags/atualizado)
    $projetos = @(Get-ChildItem (Join-Path $Vault "30_PROJECTS") -Directory -ErrorAction SilentlyContinue)
    $mocs     = @(Get-ChildItem (Join-Path $Vault "70_MOCS") -Filter *.md -File -ErrorAction SilentlyContinue)
    $L = @()
    $L += "# 🧠 MEGA BRAIN — Índice Geral"
    $L += ""
    $L += "> Dashboard vivo do meu Segundo Cérebro."
    $L += "> Atualizado automaticamente pelo `reindex_hybrid.ps1` (light 6h + deep semanal)."
    $L += ""
    $L += "## ⏱️ Timestamps"
    $L += "- **Última reindexação:** {{LAST_REINDEX}}"
    $L += "- **Última light:** {{LAST_LIGHT}}"
    $L += "- **Última deep:** {{LAST_DEEP}}"
    $L += "- **Próxima light:** {{NEXT_LIGHT}}"
    $L += "- **Próxima deep:** {{NEXT_DEEP}}"
    $L += ""
    $L += "## ⏰ Status de Sincronização"
    $L += "- MCP server: {{MCP_STATUS}}"
    $L += "- **Última sincronização:** {{LAST_SYNC}}"
    $L += ""
    $L += "## 📊 Visão Geral"
    $L += "- Projetos: {{N_PROJETOS}}"
    $L += "- MOCs: {{N_MOCS}}"
    $L += "- Notas (.md): {{N_NOTAS}}"
    $L += ""
    $L += "## 📂 Projetos Ativos"
    $L += '```dataview'
    $L += 'TABLE status AS "Status",'
    $L += '      stack AS "Stack",'
    $L += '      criado AS "Criado"'
    $L += 'FROM "30_PROJECTS"'
    $L += 'WHERE status = "ativo"'
    $L += 'SORT criado DESC'
    $L += '```'
    $L += ""
    $L += "## 🧩 Stack Mapeada (Top 10)"
    $L += '```dataview'
    $L += 'TABLE WITHOUT ID'
    $L += '  stack AS "Stack",'
    $L += '  length(rows) AS "Uso"'
    $L += 'FROM "30_PROJECTS"'
    $L += 'WHERE stack != ""'
    $L += 'FLATTEN stack'
    $L += 'GROUP BY stack'
    $L += 'SORT length(rows) DESC'
    $L += 'LIMIT 10'
    $L += '```'
    $L += ""
    $L += "## 🕒 Últimas 7 Execuções"
    $L += '```dataview'
    $L += 'TABLE file.link AS "Dia",'
    $L += '      humor AS "Humor"'
    $L += 'FROM "20_DAILY_NOTES"'
    $L += 'SORT file.name DESC'
    $L += 'LIMIT 7'
    $L += '```'
    $L += "## 🔍 Padrões Detectados (Top 10)"
    $L += '```dataview'
    $L += 'TABLE categoria AS "Categoria",'
    $L += '      ocorrencias AS "Ocorrências",'
    $L += '      ultima_vez AS "Última"'
    $L += 'FROM "10_MEGA_BRAIN"'
    $L += 'WHERE contains(tags, "padrao")'
    $L += 'SORT ocorrencias DESC'
    $L += 'LIMIT 10'
    $L += '```'
    $L += ""
    $L += "## Projetos indexados"
    $L += ""
    if ($projetos.Count -eq 0) { $L += "_Nenhum projeto em 30_PROJECTS/_" }
    else {
        foreach ($p in $projetos) {
            $readme = Join-Path $p.FullName "README.md"
            $stack = ""
            if (Test-Path $readme) {
                $c = Get-Content $readme -Raw -Encoding UTF8
                if ($c -match '(?s)##\s*🧩\s*Stack\s*\n+(.+?)\n##') { $stack = ($Matches[1]).Trim() }
            }
            $L += "- [[$($p.Name)]]" + $(if ($stack) { " — $stack" } else { "" })
        }
    }
    $L += ""
    $L += "## 🗂️ MOCs"
    $L += '```dataview'
    $L += 'LIST'
    $L += 'FROM "70_MOCS"'
    $L += 'WHERE contains(tags, "moc")'
    $L += 'SORT file.name ASC'
    $L += '```'
    $L += ""
    $L += "## 🔔 Alertas Ativos"
    $L += '```dataview'
    $L += 'TABLE prioridade AS "Prioridade",'
    $L += '      categoria AS "Categoria",'
    $L += '      file.link AS "Arquivo"'
    $L += 'FROM "90_ALERTS"'
    $L += 'WHERE !resolved'
    $L += 'SORT prioridade DESC'
    $L += '```'
    $L += ""
    $L += "## 📈 Histórico de Métricas (últimas 24h)"
    $L += '```dataview'
    $L += 'TABLE mode AS "Modo",'
    $L += '      total_notas AS "Notas",'
    $L += '      total_projetos AS "Proj",'
    $L += '      total_mocs AS "MOCs",'
    $L += '      tamanho_mb AS "MB"'
    $L += 'FROM "50_METRICS"'
    $L += 'WHERE timestamp >= date(now) - dur(24 hours)'
    $L += 'SORT timestamp DESC'
    $L += 'LIMIT 4'
    $L += '```'
    $L += ""
    $L += "## Arquivos de peso máximo"
    $L += "- [[PREFERENCIAS_PESSOAIS]] · [[PADROES_RECorrentes]] · [[DECISOES_REUTILIZAVEIS]] · [[STACKS_MAPeadas]]"
    $L += ""
    $L += "## Métricas"
    $L += "- Notas .md: $($m.total_notas) · Projetos: $($m.projetos.Count) · MOCs: $($m.mocs)"
    $L += "- Última execução (deep): $tsShort"

    # Preenche os placeholders dinâmicos
    $lastLightISO = ""
    $llFile = Join-Path $LogDir ".last_light.txt"
    if (Test-Path $llFile) { $lastLightISO = (Get-Content $llFile -Raw -Encoding UTF8).Trim() }
    if ($lastLightISO) { $L = $L -replace "\{\{LAST_LIGHT\}\}", $lastLightISO }
    else { $L = $L -replace "\{\{LAST_LIGHT\}\}", "nunca executada" }

    $L = $L -replace "\{\{LAST_DEEP\}\}", $tsShort

    # Status do MCP (porta 8770)
    $mcpStatus = "OFFLINE"
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:8770/health" -TimeoutSec 3 -ErrorAction Stop
        if ($r.ok) { $mcpStatus = "ONLINE (8770)" }
    } catch { $mcpStatus = "OFFLINE" }
    $L = $L -replace "\{\{MCP_STATUS\}\}", $mcpStatus

    # Próxima light = última light + interval_hours (config.auto_reindex.light.interval_hours, default 6)
    $nextLight = "agora"
    if ($lastLightISO) {
        try {
            $llDt = [datetime]::Parse((Get-Content $llFile -Raw -Encoding UTF8).Trim())
            $iv = 6
            if ($Config.auto_reindex -and $Config.auto_reindex.light -and $Config.auto_reindex.light.interval_hours) {
                $iv = [int]$Config.auto_reindex.light.interval_hours
            }
            $nextLight = ($llDt.AddHours($iv)).ToString("yyyy-MM-dd HH:mm:ss")
        } catch { $nextLight = "desconhecida" }
    }
    $L = $L -replace "\{\{NEXT_LIGHT\}\}", $nextLight

    # Última sincronização = timestamp da light (ou agora se nunca)
    $lastSync = if ($lastLightISO) { $lastLightISO } else { (Get-Date -Format "o") }
    $L = $L -replace "\{\{LAST_SYNC\}\}", $lastSync

    # Próxima deep = próximo dia da semana configurado (default Sunday) às 23:00
    $nextDeep = "desconhecida"
    try {
        $dow = if ($Config.auto_reindex -and $Config.auto_reindex.deep -and $Config.auto_reindex.deep.day_of_week) { [string]$Config.auto_reindex.deep.day_of_week } else { "Sunday" }
        $t = if ($Config.auto_reindex -and $Config.auto_reindex.deep -and $Config.auto_reindex.deep.time) { [string]$Config.auto_reindex.deep.time } else { "23:00" }
        $target = [System.DayOfWeek]::$($dow)
        $now = Get-Date
        $days = (7 - [int]$now.DayOfWeek + [int]$target) % 7
        if ($days -eq 0) { $days = 7 }
        $nd = $now.Date.AddDays($days).Add([TimeSpan]::Parse($t))
        if ($nd -lt $now) { $nd = $nd.AddDays(7) }
        $nextDeep = $nd.ToString("yyyy-MM-dd HH:mm:ss")
    } catch { $nextDeep = "desconhecida" }
    $L = $L -replace "\{\{NEXT_DEEP\}\}", $nextDeep

    # Visão geral (contagens)
    $L = $L -replace "\{\{N_PROJETOS\}\}", $m.projetos.Count
    $L = $L -replace "\{\{N_MOCS\}\}", $m.mocs
    $L = $L -replace "\{\{N_NOTAS\}\}", $m.total_notas

    # Última reindexação = a mais recente entre light e deep
    $lastReindex = $tsShort
    $cands = @()
    if ($lastLightISO) { $cands += $lastLightISO }
    $deepFile = Join-Path $LogDir ".last_deep.txt"
    if (Test-Path $deepFile) { $cands += (Get-Content $deepFile -Raw -Encoding UTF8).Trim() }
    foreach ($c in $cands) {
        try { $d = [datetime]::Parse($c); if ($d -gt [datetime]::Parse($lastReindex)) { $lastReindex = $c } } catch {}
    }
    $L = $L -replace "{{LAST_REINDEX}}", $lastReindex

    # Relatório de saúde executivo (esperado pelo PROMPT_MESTRE_v2.md em health/health_YYYY-MM-DD.md)
    $tamanhoMB = [math]::Round((Get-ChildItem $Vault -Recurse -File | Where-Object { $_.FullName -notmatch '\\\.obsidian' -and $_.FullName -notmatch '\\venv\\' -and $_.FullName -notmatch '\\node_modules\\' } | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    $healthDir = Join-Path $LogDir "health"
    if (-not (Test-Path $healthDir)) { New-Item -ItemType Directory -Path $healthDir -Force | Out-Null }
    $tsFile = (Get-Date).ToString("yyyy-MM-ddTHHmmss")
    $healthFile = Join-Path $healthDir "health_$tsFile.md"
    $health = @()
    $health += "# 🩺 Relatório de Saúde — MEGA BRAIN"
    $health += ""
    $health += "> Gerado automaticamente por `reindex_hybrid.ps1 -Mode deep` em $tsShort."
    $health += ""
    $health += "## 1. Métricas principais"
    $health += "- Total de notas: $($m.total_notas)"
    $health += "- Projetos ativos: $($m.projetos.Count)"
    $health += "- MOCs: $($m.mocs)"
    $health += "- Tamanho do vault: $tamanhoMB MB"
    $health += ""
    $health += "## 2. Saúde do sistema"
    $health += "- Status do MCP: $mcpStatus"
    $health += "- Última reindexação: $lastReindex"
    $health += "- Próxima light: $nextLight"
    $health += "- Próxima deep: $nextDeep"
    $health += ""
    $health += "## 3. Recomendações"
    $health += "- Manter reindex light 6h e deep semanal agendados."
    $health += "- Manter backup diário (02:00) + incremental (6h) ativos."
    $health += "- Consultar o cérebro antes de cada tarefa (hooks pré/pós)."
    $health | Set-Content -Path $healthFile -Encoding UTF8
    Write-Output "[MEGA BRAIN] relatório de saúde: $healthFile"

    $hoje = Get-Date -Format "yyyy-MM-dd"
    $fm = @()
    $fm += "---"
    $fm += "tipo: meta-indice"
    $fm += "criado: $(if (Test-Path $IndexFile) { $ex = Get-Content $IndexFile -Raw -Encoding UTF8; if ($ex -match '(?s)criado:\s*(\S+)') { $Matches[1] } else { $hoje } } else { $hoje })"
    $fm += "atualizado: $hoje"
    $fm += "tags: [meta/index]"
    $fm += "---"
    $conteudo = $fm + $L
    $conteudo | Set-Content -Path $IndexFile -Encoding UTF8
    Stamp ".last_deep.txt"
    Write-Output "[MEGA BRAIN] reindex DEEP concluído · notas=$($m.total_notas) · INDEX_GERAL reconstruído"
} else {
    StampISO ".last_light.txt"
    Write-Output "[MEGA BRAIN] reindex LIGHT concluído · notas=$($m.total_notas) · timestamp=$tsShort"
}
