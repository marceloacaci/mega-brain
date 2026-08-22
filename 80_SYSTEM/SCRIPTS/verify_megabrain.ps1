# verify_megabrain.ps1 — Verificação real da integração Hermes Agent ↔ Obsidian (MEGA BRAIN)
$VAULT = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$SEP = "═══════════════════════════════════════"

function Linha($txt, $ok) {
    $cor = if ($ok) { "Green" } else { "Red" }
    $simb = if ($ok) { "✅" } else { "❌" }
    Write-Host "  $simb $txt" -ForegroundColor $cor
}

Write-Host $SEP -ForegroundColor Cyan
Write-Host "  MEGA BRAIN — VERIFICAÇÃO DE INTEGRAÇÃO" -ForegroundColor Cyan
Write-Host $SEP -ForegroundColor Cyan

# 1. Estrutura de pastas
Write-Host "`n[1] Estrutura do cofre" -ForegroundColor Yellow
$dirs = @("00_INBOX","10_MEGA_BRAIN","20_DAILY_NOTES","30_PROJECTS","40_AREAS","50_RESOURCES","60_ARCHIVE","70_MOCS","80_SYSTEM","90_ALERTS")
$okDirs = ($dirs | Where-Object { Test-Path (Join-Path $VAULT $_) }).Count -eq $dirs.Count
Linha "Pastas 00→90 presentes ($((($dirs | Where-Object { Test-Path (Join-Path $VAULT $_) }).Count)/$($dirs.Count))" $okDirs

# 2. MCP server
Write-Host "`n[2] Servidor MCP (porta 8770)" -ForegroundColor Yellow
try {
    $r = Invoke-RestMethod -Uri "http://localhost:8770/health" -TimeoutSec 4 -ErrorAction Stop
    Linha "MCP a responder: $($r.ok) · vault=$(Split-Path $r.vault -Leaf)" $true
} catch {
    Linha "MCP NÃO responde na 8770 (arrancar: python mcp_obsidian_server.py --port 8770)" $false
}

# 3. Hooks
Write-Host "`n[3] Hooks" -ForegroundColor Yellow
Linha "pre_task_hook.ps1"  (Test-Path "$VAULT\80_SYSTEM\HOOKS_HERMES\pre_task_hook.ps1")
Linha "post_task_hook.ps1" (Test-Path "$VAULT\80_SYSTEM\HOOKS_HERMES\post_task_hook.ps1")

# 4. Scripts
Write-Host "`n[4] Scripts de apoio" -ForegroundColor Yellow
foreach ($s in @("backup_vault.ps1","reindex_hybrid.ps1","install_tasks.ps1")) {
    Linha $s (Test-Path "$VAULT\80_SYSTEM\SCRIPTS\$s")
}

# 5. Templates Templater
Write-Host "`n[5] Templates Templater" -ForegroundColor Yellow
foreach ($t in @("novo_projeto.md","novo_recurso.md","novo_padrao.md","nova_daily.md","novo_moc.md")) {
    Linha $t (Test-Path "$VAULT\80_SYSTEM\TEMPLATES\$t")
}

# 6. CSS snippet
Write-Host "`n[6] Snippet de cores" -ForegroundColor Yellow
$ap = Join-Path $VAULT ".obsidian\appearance.json"
$snipOk = (Test-Path $ap) -and ((Get-Content $ap -Raw) -match "megabrain")
Linha "megabrain.css ativo" $snipOk

# 7. Tarefas agendadas
Write-Host "`n[7] Tarefas agendadas (Task Scheduler)" -ForegroundColor Yellow
$tasks = @("MEGA_BRAIN_Backup","MEGA_BRAIN_Reindex_Light","MEGA_BRAIN_Reindex_Deep")
$real = 0
foreach ($t in $tasks) {
    $st = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    if ($st) { Linha "$t ($($st.State))" $true; $real++ } else { Linha "$t (em falta)" $false }
}
# obsoletas
$obs = @("MEGA_BRAIN_Backup_Full","MEGA_BRAIN_Backup_Incremental") | Where-Object { Get-ScheduledTask -TaskName $_ -ErrorAction SilentlyContinue }
if ($obs) { Write-Host "  ⚠️  Obsoletas (inofensivas, sem trigger): $($obs -join ', ')" -ForegroundColor DarkYellow }

# 8. Dataview
Write-Host "`n[8] Plugins Obsidian" -ForegroundColor Yellow
Linha "Dataview instalado" (Test-Path (Join-Path $VAULT ".obsidian\plugins"))

Write-Host $SEP -ForegroundColor Cyan
Write-Host "  Verificação concluída. Pendência do utilizador: instalar Dataview/Templater na UI do Obsidian." -ForegroundColor Cyan
Write-Host $SEP -ForegroundColor Cyan
