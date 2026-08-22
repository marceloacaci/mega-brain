<#
.SYNOPSIS
Migra o setup do MEGA BRAIN para o modelo híbrido de reindexação.
.DESCRIPTION
- Remove tarefas agendadas antigas
- Instala novas tarefas (light 6h + deep semanal)
- Atualiza INDEX_GERAL.md com novos placeholders
- Cria estrutura de diretórios necessária
- Valida instalação
#>
[CmdletBinding()]
param()
$ConfigPath = Join-Path $PSScriptRoot "config.json"
$Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$Vault = $Config.vault_path
$ScriptsPath = Join-Path $Vault "80_SYSTEM\SCRIPTS"
$LogPath = $Config.log_path
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✦ MIGRAÇÃO PARA MODELO HÍBRIDO" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
# ============================================
# 1. BACKUP DOS SCRIPTS ANTIGOS
# ============================================
Write-Host "[1/6] Backup dos scripts antigos..." -ForegroundColor Yellow
$backupDir = Join-Path $ScriptsPath "legacy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}
$legacyScripts = @("reindex_weekly.ps1")
foreach ($script in $legacyScripts) {
    $src = Join-Path $ScriptsPath $script
    if (Test-Path $src) {
        $dst = Join-Path $backupDir $script
        Move-Item $src $dst -Force
        Write-Host "  → Movido: $script" -ForegroundColor DarkCyan
    }
}
Write-Host "  ✦ Scripts antigos salvos em: $backupDir" -ForegroundColor DarkCyan
# ============================================
# 2. REMOVER TAREFAS AGENDADAS ANTIGAS
# ============================================
Write-Host ""
Write-Host "[2/6] Removendo tarefas antigas..." -ForegroundColor Yellow
$oldTasks = @(
"MEGA_BRAIN_WeeklyReindex"
)
foreach ($task in $oldTasks) {
    $exists = Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
    if ($exists) {
        Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "  → Removida: $task" -ForegroundColor DarkCyan
    }
}
# ============================================
# 3. CRIAR ESTRUTURA DE LOGS
# ============================================
Write-Host ""
Write-Host "[3/6] Criando estrutura de logs..." -ForegroundColor Yellow
$healthDir = Join-Path $LogPath "health"
if (-not (Test-Path $healthDir)) {
    New-Item -ItemType Directory -Path $healthDir -Force | Out-Null
    Write-Host "  → Criado: $healthDir" -ForegroundColor DarkCyan
}
# ============================================
# 4. INICIALIZAR ARQUIVOS DE CONTROLE
# ============================================
Write-Host ""
Write-Host "[4/6] Inicializando controle de timestamps..." -ForegroundColor Yellow
$lastDeepFile = Join-Path $LogPath ".last_deep.txt"
$lastLightFile = Join-Path $LogPath ".last_light.txt"
if (-not (Test-Path $lastDeepFile)) {
    Set-Content -Path $lastDeepFile -Value (Get-Date -Format "o") -Encoding UTF8
    Write-Host "  → .last_deep.txt criado" -ForegroundColor DarkCyan
}
if (-not (Test-Path $lastLightFile)) {
    Set-Content -Path $lastLightFile -Value (Get-Date -Format "o") -Encoding UTF8
    Write-Host "  → .last_light.txt criado" -ForegroundColor DarkCyan
}
# Inicializar métricas horárias
$metricsFile = Join-Path $LogPath "metricas_horarias.json"
if (-not (Test-Path $metricsFile)) {
    "[]" | Set-Content $metricsFile -Encoding UTF8
    Write-Host "  → metricas_horarias.json criado" -ForegroundColor DarkCyan
}
# ============================================
# 5. ATUALIZAR INDEX_GERAL.MD
# ============================================
Write-Host ""
Write-Host "[5/6] Atualizando INDEX_GERAL.md..." -ForegroundColor Yellow
$indexPath = Join-Path $Vault "INDEX_GERAL.md"
if (Test-Path $indexPath) {
    $content = Get-Content $indexPath -Raw
    $now = Get-Date -Format "yyyy-MM-dd HH:mm"
    # Adicionar/atualizar seção de status se não existir
    if ($content -notmatch "Última light:") {
        $statusSection = @"
## ⏰ Status de Sincronização
- **Última light:** $now
- **Última deep:** $now
- **Próxima light:** $((Get-Date).AddHours(6).ToString('yyyy-MM-dd HH:mm'))
- **Próxima deep:** $((Get-Date).AddDays((7 - [int](Get-Date).DayOfWeek)).ToString('yyyy-MM-dd HH:mm'))
- **Última reindexação:** $now (deep)
> Modelo híbrido: light a cada 6h + deep semanal (domingo 23h).
"@
        # Inserir depois do título principal (usa aspas simples p/ $& ser backreference do -replace)
        $content = $content -replace "(?m)^# MEGA BRAIN.*$", ('$&' + $statusSection)
        Set-Content -Path $indexPath -Value $content -Encoding UTF8
        Write-Host "  → Status de sincronização adicionado" -ForegroundColor DarkCyan
    } else {
        Write-Host "  → Já possui seção de status (skip)" -ForegroundColor DarkGray
    }
}
# ============================================
# 6. AGENDAR NOVAS TAREFAS
# ============================================
Write-Host ""
Write-Host "[6/6] Agendando tarefas híbridas..." -ForegroundColor Yellow
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ScriptsPath "install_tasks.ps1")
# ============================================
# TESTE DE SANIDADE
# ============================================
Write-Host ""
Write-Host "✦ Executando teste de sanidade (light)..." -ForegroundColor Cyan
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ScriptsPath "reindex_hybrid.ps1") -Mode light
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ MIGRAÇÃO CONCLUÍDA" -ForegroundColor Green
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. Verifique as tarefas: Get-ScheduledTask | Where { `$_.TaskName -like 'MEGA_BRAIN_*' }"
Write-Host "  2. Abra o Obsidian e veja o INDEX_GERAL.md atualizado"
Write-Host "  3. Próxima light: ~1 minuto | Próxima deep: próximo domingo 23h"
Write-Host ""
