<#
  popular_scripts.ps1
  MegaBrain — prepara o vault para automacao completa:
    1. Ativa/configure Dataview + Templater (prepara ficheiros; instalacao UI fica a cargo do utilizador)
    2. Garante hooks Hermes ligados (pre/post) e cria o watcher agendado
    3. Cria tarefa agendada MEGA_BRAIN_Watcher (heartbeat diario -> daily note via MCP)
  Idempotente: correr varias vezes nao duplica.
  PT-BR. Sem confirmacoes interativas.
#>

$ErrorActionPreference = "Stop"
$VAULT = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$OBS   = Join-Path $VAULT ".obsidian"
$MCP   = "http://127.0.0.1:8770"
$HOOKS = Join-Path $VAULT "80_SYSTEM\HOOKS_HERMES"
$SCRIPTS = Join-Path $VAULT "80_SYSTEM\SCRIPTS"

function Log($m){ $ts = Get-Date -Format "HH:mm:ss"; Write-Host "[$ts] $m" }

# ---------------------------------------------------------------------------
# 1) DATAVIEW + TEMPLATER
# ---------------------------------------------------------------------------
Log "== Dataview / Templater =="
$pluginsDir = Join-Path $OBS "plugins"
$commJson   = Join-Path $OBS "community-plugins.json"
$dataviewInstalled = Test-Path (Join-Path $pluginsDir "dataview")
$templaterInstalled = Test-Path (Join-Path $pluginsDir "templater-obsidian")

# Prepara o community-plugins.json com a lista desejada SEMPRE (o Obsidian ativa
# automaticamente quando os ficheiros dos plugins aparecerem na pasta plugins/).
$desired = @("dataview", "templater-obsidian")
if (-not (Test-Path $commJson)) {
    Set-Content -Path $commJson -Value ($desired | ConvertTo-Json -Compress) -Encoding utf8
    Log "community-plugins.json criado: $($desired -join ', ')"
} else {
    # garante que os dois estao na lista (idempotente)
    try {
        $atuais = Get-Content $commJson -Raw | ConvertFrom-Json
        if ($atuais -isnot [array]) { $atuais = @($atuais) }
    } catch { $atuais = @() }
    $novos = @("dataview", "templater-obsidian") | Where-Object { $_ -notin $atuais }
    if ($novos) { $atuais = $atuais + $novos; Set-Content -Path $commJson -Value ($atuais | ConvertTo-Json -Compress) -Encoding utf8; Log "community-plugins.json atualizado: $($atuais -join ', ')" }
    else { Log "community-plugins.json ja tem dataview+templater." }
}

if (-not $dataviewInstalled -or -not $templaterInstalled) {
    Log "AVISO: Dataview/Templater NAO estao instalados em .obsidian/plugins."
    Log "       Acao manual (UI do Obsidian): Settings -> Community plugins -> Browse"
    Log "       -> instalar 'Dataview' e 'Templater'. Depois re-correr este script."
} else {
    Log "Dataview + Templater detetados; ativacao preparada."
}

# Config Templater (template folder = 80_SYSTEM/TEMPLATES)
$templaterCfg = Join-Path $pluginsDir "templater-obsidian\data.json"
if ($templaterInstalled -and -not (Test-Path $templaterCfg)) {
    $cfg = @{ "templates_folder" = "80_SYSTEM/TEMPLATES"; "trigger_on_new_file" = $true } | ConvertTo-Json
    Set-Content -Path $templaterCfg -Value $cfg -Encoding utf8
    Log "Templater configurado (template folder = 80_SYSTEM/TEMPLATES)."
}

# ---------------------------------------------------------------------------
# 2) HOOKS HERMES
# ---------------------------------------------------------------------------
Log "== Hooks Hermes =="
$hookPre  = Join-Path $HOOKS "pre_task_hook.ps1"
$hookPost = Join-Path $HOOKS "post_task_hook.ps1"
if (Test-Path $hookPre)  { Log "pre_task_hook.ps1  OK" } else { Log "FALTA pre_task_hook.ps1" }
if (Test-Path $hookPost) { Log "post_task_hook.ps1 OK" } else { Log "FALTA post_task_hook.ps1" }
Log "Hooks sao adotados pelo agente (ver skill hermes-megabrain). Nada a registar no OS."

# ---------------------------------------------------------------------------
# 3) WATCHER AGENDADO (heartbeat diario -> daily note via MCP)
# ---------------------------------------------------------------------------
Log "== Watcher agendado =="
$watcher = Join-Path $SCRIPTS "watcher_daily.ps1"
@"
# watcher_daily.ps1 — heartbeat do MegaBrain
`$MCP = "http://127.0.0.1:8770"
`$hoje = Get-Date -Format "yyyy-MM-dd"
`$body = @{ path = "20_DAILY_NOTES/`$hoje.md"; content = "- 🔄 heartbeat MegaBrain $(Get-Date -Format 'HH:mm')" } | ConvertTo-Json
try { Invoke-RestMethod -Uri "`$MCP/append" -Method Post -ContentType "application/json" -Body `$body | Out-Null; Write-Host "heartbeat OK" }
catch { Write-Warning "MCP indisponivel: `$_" }
"@ | Set-Content -Path $watcher -Encoding utf8
Log "watcher_daily.ps1 criado."

$taskName = "MEGA_BRAIN_Watcher"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$watcher`""
$trigger = New-ScheduledTaskTrigger -Daily -At "23:30"
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
    Log "Tarefa agendada '$taskName' criada (diario 23:30)."
} catch {
    Log "AVISO: nao foi possivel registar tarefa (precisa de Admin). Corra como Administrador."
}

# ---------------------------------------------------------------------------
Log "== Fim =="
Log "Pendente (UI Obsidian): instalar Dataview + Templater (Browse). Resto automatizado."
