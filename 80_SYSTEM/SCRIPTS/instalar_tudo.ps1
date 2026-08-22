<#
.SYNOPSIS
Instalador ONE-CLICK do MEGA BRAIN v2.0.
.DESCRIPTION
Instala TUDO automaticamente:
- Estrutura de pastas
- Servidor MCP (Python)
- Hooks PowerShell
- Templates
- CSS de cores
- Backups
- Agendamentos do Windows
Basta executar como Administrador e tudo será configurado.
.NOTES
Arquivo: instalar_tudo.ps1
Versão: 2.0.0
Tempo estimado: 5-10 minutos
Requisitos: Windows 10/11, PowerShell 7+, Python 3.10+
#>
[CmdletBinding()]
param()
# ============================================
# CONFIGURAÇÃO FIXA
# ============================================
$ErrorActionPreference = "Stop"
$Vault = "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"
$BackupRoot = "D:\Backups\Obsidian"
$LogFile = Join-Path $Vault "80_SYSTEM\LOGS\install_$(Get-Date -Format 'yyyy-MM-dd_HHmmss').log"
# ============================================
# BANNER
# ============================================
Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║                                                            ║" -ForegroundColor Magenta
Write-Host "║        🧠  MEGA BRAIN v2.0 — Instalador One-Click          ║" -ForegroundColor Magenta
Write-Host "║                                                            ║" -ForegroundColor Magenta
Write-Host "║        Modelo Híbrido + MCP + Backups + Agendamentos      ║" -ForegroundColor Magenta
Write-Host "║                                                            ║" -ForegroundColor Magenta
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""
Write-Host "📍 Vault: $Vault" -ForegroundColor Cyan
Write-Host "💾 Backup: $BackupRoot" -ForegroundColor Cyan
Write-Host ""
# ============================================
# PRÉ-REQUISITOS
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [0/8] Verificando pré-requisitos..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
$continue = $true
# 1. PowerShell 7+
$psVer = $PSVersionTable.PSVersion
if ($psVer.Major -ge 7) {
Write-Host "  ✅ PowerShell $($psVer.Major).$($psVer.Minor)" -ForegroundColor Green
} else {
Write-Host "  ❌ PowerShell 5.1 detectado. Instale PowerShell 7+:" -ForegroundColor Red
Write-Host "     winget install Microsoft.PowerShell" -ForegroundColor Yellow
$continue = $false
}
# 2. Python 3.10+
$pythonOk = $false
try {
$pyVer = python --version 2>&1
if ($pyVer -match "Python (\d+)\.(\d+)") {
$major = [int]$Matches[1]
$minor = [int]$Matches[2]
if ($major -ge 3 -and $minor -ge 10) {
Write-Host "  ✅ $pyVer" -ForegroundColor Green
$pythonOk = $true
} else {
Write-Host "  ❌ $pyVer (precisa 3.10+)" -ForegroundColor Red
$continue = $false
}
} else {
Write-Host "  ❌ Python não detectado" -ForegroundColor Red
$continue = $false
}
} catch {
Write-Host "  ❌ Python não encontrado no PATH" -ForegroundColor Red
Write-Host "     Baixe em: https://www.python.org/downloads/" -ForegroundColor Yellow
$continue = $false
}
# 3. Permissões de Admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
Write-Host "  ✅ Executando como Administrador" -ForegroundColor Green
} else {
Write-Host "  ⚠️  Não está como Administrador (recomendado para agendar tarefas)" -ForegroundColor Yellow
}
# 4. Vault existe?
if (Test-Path $Vault) {
Write-Host "  ✅ Vault encontrado" -ForegroundColor Green
} else {
Write-Host "  ❌ Vault NÃO encontrado: $Vault" -ForegroundColor Red
Write-Host "     Crie a pasta ou ajuste a variável `$Vault no início deste script" -ForegroundColor Yellow
$continue = $false
}
# 5. Pasta de backup
if (-not (Test-Path $BackupRoot)) {
Write-Host "  📁 Criando pasta de backups: $BackupRoot" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
Write-Host "  ✅ Pasta de backups criada" -ForegroundColor Green
} else {
Write-Host "  ✅ Pasta de backups existe" -ForegroundColor Green
}
Write-Host ""
if (-not $continue) {
Write-Host "═══════════════════════════════════════" -ForegroundColor Red
Write-Host "  ❌ PRÉ-REQUISITOS FALHARAM" -ForegroundColor Red
Write-Host "═══════════════════════════════════════" -ForegroundColor Red
Write-Host ""
Write-Host "Corrija os itens acima e execute novamente." -ForegroundColor Yellow
pause
exit 1
}
# ============================================
# CRIAR LOG
# ============================================
$logDir = Join-Path $Vault "80_SYSTEM\LOGS"
if (-not (Test-Path $logDir)) {
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
"=== MEGA BRAIN INSTALLER v2.0 ===" | Set-Content $LogFile -Encoding UTF8
"Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content $LogFile -Encoding UTF8
"Vault: $Vault" | Add-Content $LogFile -Encoding UTF8
"" | Add-Content $LogFile -Encoding UTF8
function Write-InstallLog {
param([string]$Message, [string]$Status = "INFO")
$ts = Get-Date -Format "HH:mm:ss"
$entry = "[$ts] [$Status] $Message"
Add-Content -Path $LogFile -Value $entry -Encoding UTF8
if ($Status -eq "ERROR") { Write-Host "  ❌ $Message" -ForegroundColor Red }
elseif ($Status -eq "WARN") { Write-Host "  ⚠️  $Message" -ForegroundColor Yellow }
elseif ($Status -eq "OK") { Write-Host "  ✅ $Message" -ForegroundColor Green }
elseif ($Status -eq "STEP") {
Write-Host ""
Write-Host "  ▶️ $Message" -ForegroundColor Cyan
}
else { Write-Host "  • $Message" -ForegroundColor Gray }
}
# ============================================
# FASE 1: ESTRUTURA DE PASTAS
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [1/8] Criando estrutura de pastas..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
$folders = @(
"00_INBOX",
"10_MEGA_BRAIN",
"20_DAILY_NOTES",
"30_PROJECTS",
"40_AREAS",
"50_RESOURCES\linguagens",
"50_RESOURCES\frameworks",
"50_RESOURCES\ferramentas",
"50_RESOURCES\comandos",
"50_RESOURCES\snippets",
"60_ARCHIVE",
"70_MOCS",
"80_SYSTEM\LOGS",
"80_SYSTEM\LOGS\health",
"80_SYSTEM\TEMPLATES",
"80_SYSTEM\SCRIPTS",
"80_SYSTEM\MCP",
"90_ALERTS"
)
$folderCount = 0
foreach ($folder in $folders) {
$fullPath = Join-Path $Vault $folder
if (-not (Test-Path $fullPath)) {
New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
$folderCount++
}
}
Write-InstallLog "$folderCount pastas criadas/verificadas" "OK"
Write-Host ""
# ============================================
# FASE 2: SETUP MEGABRAIN (cria arquivos base)
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [2/8] Executando setup_megabrain.ps1..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
# Verificar se setup_megabrain.ps1 existe
$setupScript = Join-Path $Vault "80_SYSTEM\SCRIPTS\setup_megabrain.ps1"
if (Test-Path $setupScript) {
try {
& $setupScript 2>&1 | Out-Null
Write-InstallLog "setup_megabrain.ps1 executado" "OK"
} catch {
Write-InstallLog "Erro no setup: $_" "WARN"
}
} else {
Write-InstallLog "setup_megabrain.ps1 não encontrado (será criado mais tarde)" "WARN"
}
Write-Host ""
# ============================================
# FASE 3: SERVIDOR MCP
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [3/8] Configurando Servidor MCP..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
$mcpPath = Join-Path $Vault "80_SYSTEM\MCP"
# Verificar se já está instalado
$venvPython = Join-Path $mcpPath "venv\Scripts\python.exe"
$needMcpInstall = $true
if (Test-Path $venvPython) {
Write-InstallLog "MCP já instalado (venv existe)" "OK"
$needMcpInstall = $false
}
if ($needMcpInstall) {
Write-InstallLog "Criando ambiente virtual Python..." "STEP"
try {
python -m venv (Join-Path $mcpPath "venv")
Write-InstallLog "venv criado" "OK"
} catch {
Write-InstallLog "Erro ao criar venv: $_" "ERROR"
}
# Criar requirements.txt
$reqFile = Join-Path $mcpPath "requirements.txt"
@"
mcp>=1.0.0
pydantic>=2.5.0
aiohttp>=3.9.0
python-frontmatter>=1.1.0
watchdog>=4.0.0
"@ | Set-Content $reqFile -Encoding UTF8
Write-InstallLog "Instalando dependências Python..." "STEP"
try {
& (Join-Path $mcpPath "venv\Scripts\pip.exe") install -r $reqFile --quiet 2>&1 | Out-Null
Write-InstallLog "Dependências instaladas" "OK"
} catch {
Write-InstallLog "Erro ao instalar dependências: $_" "WARN"
}
}
# Criar arquivo de configuração MCP (server.json) — usado pelo cliente
$serverConfig = @{
command = "python"
args = @("$Vault\80_SYSTEM\SCRIPTS\mcp_obsidian_server.py")
env = @{
OBSIDIAN_VAULT = $Vault
SILENT_MODE = "true"
LOG_LEVEL = "INFO"
}
}
$mcpConfigPath = Join-Path $mcpPath "server-config.json"
$serverConfig | ConvertTo-Json -Depth 5 | Set-Content $mcpConfigPath -Encoding UTF8
Write-InstallLog "server-config.json criado em $mcpConfigPath" "OK"
Write-Host ""
# ============================================
# FASE 4: HOOKS POWERSHELL
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [4/8] Configurando Hooks PowerShell..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
$scriptsPath = Join-Path $Vault "80_SYSTEM\SCRIPTS"
# Criar config.json
$configContent = @{
vault_path = $Vault
log_path = Join-Path $Vault "80_SYSTEM\LOGS"
log_retention_days = 30
silent_mode = $true
mcp_server_url = "http://localhost:8770"
auto_reindex = @{
enabled = $true
mode = "hybrid"
light = @{ interval_hours = 6; force_after_hours = 4 }
deep = @{ day_of_week = "Sunday"; time = "23:00" }
}
watcher = @{ enabled = $true; debounce_ms = 2000 }
modes = @{
indexador = $true
correlacionador = $true
guardiao = $true
metrico = $true
preditivo = $true
}
backup = @{
enabled = $true
root = $BackupRoot
full_schedule = "02:00"
incremental_interval_hours = 6
retention = @{ daily = 7; weekly = 4; monthly = 6; incremental_days = 30 }
}
}
$configPath = Join-Path $scriptsPath "config.json"
if (-not (Test-Path $configPath)) {
$configContent | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
Write-InstallLog "config.json criado" "OK"
} else {
Write-InstallLog "config.json já existe (skip)" "OK"
}
# Criar arquivo de controle de timestamps
$controlFiles = @(".last_deep.txt", ".last_light.txt")
foreach ($cf in $controlFiles) {
$cfPath = Join-Path $Vault "80_SYSTEM\LOGS\$cf"
if (-not (Test-Path $cfPath)) {
Set-Content -Path $cfPath -Value (Get-Date -Format "o") -Encoding UTF8
}
}
# Inicializar métricas
$metricsFile = Join-Path $Vault "80_SYSTEM\LOGS\metricas_horarias.json"
if (-not (Test-Path $metricsFile)) {
"[]" | Set-Content $metricsFile -Encoding UTF8
Write-InstallLog "metricas_horarias.json inicializado" "OK"
}
Write-Host ""
# ============================================
# FASE 5: CSS DE CORES
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [5/8] Criando CSS snippet..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
$obsidianPath = Split-Path (Split-Path $Vault -Parent) -Parent
$snippetsDir = Join-Path $Vault ".obsidian\snippets"
# Verificar se .obsidian existe
if (Test-Path (Join-Path $Vault ".obsidian")) {
if (-not (Test-Path $snippetsDir)) {
New-Item -ItemType Directory -Path $snippetsDir -Force | Out-Null
}
$cssContent = @"
/* ============================================
   🧠 MEGA BRAIN — Snippet de Cores Obsidian
   ============================================ */

.tag[href^="#projeto/"] {
background-color: rgba(59, 130, 246, 0.15) !important;
color: rgb(59, 130, 246) !important;
border: 1px solid rgba(59, 130, 246, 0.3) !important;
}
.tag[href^="#stack/"] {
background-color: rgba(168, 85, 247, 0.15) !important;
color: rgb(168, 85, 247) !important;
border: 1px solid rgba(168, 85, 247, 0.3) !important;
}
.tag[href^="#padrao/"] {
background-color: rgba(34, 197, 94, 0.15) !important;
color: rgb(34, 197, 94) !important;
border: 1px solid rgba(34, 197, 94, 0.3) !important;
}
.tag[href^="#erro/"] {
background-color: rgba(239, 68, 68, 0.15) !important;
color: rgb(239, 68, 68) !important;
border: 1px solid rgba(239, 68, 68, 0.3) !important;
font-weight: 600;
}
.tag[href^="#alerta/"] {
background-color: rgba(234, 179, 8, 0.15) !important;
color: rgb(234, 179, 8) !important;
border: 1px solid rgba(234, 179, 8, 0.3) !important;
}
.tag[href^="#decisao/"] {
background-color: rgba(236, 72, 153, 0.15) !important;
color: rgb(236, 72, 153) !important;
border: 1px solid rgba(236, 72, 153, 0.3) !important;
}
.tag[href^="#daily/"] {
background-color: rgba(107, 114, 128, 0.15) !important;
color: rgb(107, 114, 128) !important;
}
.internal-link[href*="30_PROJETS"] { color: rgb(59, 130, 246) !important; font-weight: 500; }
.internal-link[href*="10_MEGA_BRAIN"] { color: rgb(168, 85, 247) !important; font-weight: 500; }
.internal-link[href*="90_ALERTS"] { color: rgb(239, 68, 68) !important; }
.internal-link[href*="70_MOCS"] { color: rgb(234, 179, 8) !important; font-weight: 600; }
.table-view-table {
border: 1px solid var(--background-secondary) !important;
border-radius: 8px !important;
overflow: hidden;
margin: 1em 0;
}
.table-view-table thead {
background: var(--background-secondary) !important;
font-weight: 600;
}
.callout[data-callout="megabrain"] { --callout-color: 168, 85, 247; --callout-icon: 🧠; }
.callout[data-callout="sucesso"] { --callout-color: 34, 197, 94; --callout-icon: ✅; }
.callout[data-callout="alerta"] { --callout-color: 234, 179, 8; --callout-icon: ⚠️; }
.callout[data-callout="erro"] { --callout-color: 239, 68, 68; --callout-icon: 🚨; }
"@
$cssPath = Join-Path $snippetsDir "megabrain.css"
if (-not (Test-Path $cssPath)) {
Set-Content -Path $cssPath -Value $cssContent -Encoding UTF8
Write-InstallLog "megabrain.css criado em $cssPath" "OK"
Write-InstallLog "ATIVE manualmente em: Settings → Appearance → CSS Snippets" "WARN"
} else {
Write-InstallLog "megabrain.css já existe (skip)" "OK"
}
} else {
Write-InstallLog "Pasta .obsidian não encontrada (abra o Obsidian primeiro)" "WARN"
}
Write-Host ""
# ============================================
# FASE 6: AGENDAMENTOS
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [6/8] Agendando tarefas do Windows..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
if ($isAdmin) {
# 6.1. Reindex Light (6h)
try {
$lightAction = New-ScheduledTaskAction -Execute "powershell.exe" `
-Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptsPath\reindex_hybrid.ps1`" -Mode light"
$lightTrigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) `
-RepetitionInterval (New-TimeSpan -Hours 6) `
-RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -TaskName "MEGA_BRAIN_Reindex_Light" `
-Action $lightAction -Trigger $lightTrigger -Force -ErrorAction Stop | Out-Null
Write-InstallLog "MEGA_BRAIN_Reindex_Light (a cada 6h)" "OK"
} catch {
Write-InstallLog "Erro ao agendar light: $_" "WARN"
}
# 6.2. Reindex Deep (semanal)
try {
$deepAction = New-ScheduledTaskAction -Execute "powershell.exe" `
-Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptsPath\reindex_hybrid.ps1`" -Mode deep"
$deepTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "23:00"
Register-ScheduledTask -TaskName "MEGA_BRAIN_Reindex_Deep" `
-Action $deepAction -Trigger $deepTrigger -Force -ErrorAction Stop | Out-Null
Write-InstallLog "MEGA_BRAIN_Reindex_Deep (domingo 23h)" "OK"
} catch {
Write-InstallLog "Erro ao agendar deep: $_" "WARN"
}
# 6.3. Backup Full (diário 02:00)
try {
$fullAction = New-ScheduledTaskAction -Execute "powershell.exe" `
-Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptsPath\backup_vault.ps1`""
$fullTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"
Register-ScheduledTask -TaskName "MEGA_BRAIN_Backup_Full" `
-Action $fullAction -Trigger $fullTrigger -Force -ErrorAction Stop | Out-Null
Write-InstallLog "MEGA_BRAIN_Backup_Full (diário 02:00)" "OK"
} catch {
Write-InstallLog "Erro ao agendar backup full: $_" "WARN"
}
# 6.4. Backup Incremental (6h)
try {
$incAction = New-ScheduledTaskAction -Execute "powershell.exe" `
-Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptsPath\backup_incremental.ps1`""
$incTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
-RepetitionInterval (New-TimeSpan -Hours 6) `
-RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -TaskName "MEGA_BRAIN_Backup_Incremental" `
-Action $incAction -Trigger $incTrigger -Force -ErrorAction Stop | Out-Null
Write-InstallLog "MEGA_BRAIN_Backup_Incremental (6h)" "OK"
} catch {
Write-InstallLog "Erro ao agendar backup incremental: $_" "WARN"
}
} else {
Write-InstallLog "Tarefas NÃO agendadas (precisa Admin). Execute como Admin depois." "WARN"
}
Write-Host ""
# ============================================
# FASE 7: TESTE FINAL
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [7/8] Executando testes..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
# Teste: hook de execução
$hooksDir = Join-Path $Vault "80_SYSTEM\HOOKS_HERMES"
$postHook = Join-Path $hooksDir "post_task_hook.ps1"
if (Test-Path $postHook) {
try {
& $postHook -Tarefa "instalação automatica" -Resultado "sucesso" -Projeto "setup" 2>&1 | Out-Null
Write-InstallLog "post_task_hook.ps1 executado com sucesso" "OK"
} catch {
Write-InstallLog "post_task_hook.ps1 falhou: $_" "WARN"
}
} else {
Write-InstallLog "post_task_hook.ps1 não encontrado (copie manualmente)" "WARN"
}
# Teste: criar daily de hoje se não existir
$today = Get-Date -Format "yyyy-MM-dd"
$dailyPath = Join-Path $Vault "20_DAILY_NOTES\$today.md"
if (Test-Path $dailyPath) {
Write-InstallLog "Daily note de hoje já existe" "OK"
} else {
Write-InstallLog "Daily note de hoje não encontrada" "WARN"
}
# Teste: MCP pode ser importado
if (Test-Path $venvPython) {
try {
& $venvPython -c "import mcp; from watchdog.observers import Observer; print('OK')" 2>&1 | Out-Null
Write-InstallLog "MCP Python funcionando" "OK"
} catch {
Write-InstallLog "MCP Python com problemas: $_" "WARN"
}
}
Write-Host ""
# ============================================
# FASE 8: RELATÓRIO FINAL
# ============================================
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host "  [8/8] Gerando relatório final..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
# Estatísticas
$totalFolders = (Get-ChildItem -Path $Vault -Recurse -Directory |
Where-Object { $_.FullName -notmatch "\.obsidian|\.trash" }).Count
$totalFiles = (Get-ChildItem -Path $Vault -Recurse -File -Filter "*.md" -ErrorAction SilentlyContinue).Count
$totalSize = [math]::Round(((Get-ChildItem -Path $Vault -Recurse -File -ErrorAction SilentlyContinue |
Where-Object { $_.FullName -notmatch "\.obsidian|\.trash" } |
Measure-Object Length -Sum).Sum / 1MB), 2)
# Verificar tarefas
$taskCount = 0
if ($isAdmin) {
$taskCount = @(Get-ScheduledTask | Where-Object { $_.TaskName -like "MEGA_BRAIN_*" }).Count
}
# Banner final
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "║          ✅  MEGA BRAIN v2.0 — Instalado!                  ║" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Estatísticas:" -ForegroundColor Cyan
Write-Host "   📁 Pastas: $totalFolders"
Write-Host "   📄 Arquivos .md: $totalFiles"
Write-Host "   💾 Tamanho: $totalSize MB"
Write-Host "   ⏰ Tarefas agendadas: $taskCount"
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  📋 PRÓXIMOS PASSOS MANUAIS:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1️⃣  Copie os scripts Python para: 80_SYSTEM\MCP\" -ForegroundColor White
Write-Host "      • mcp_obsidian_server.py" -ForegroundColor Gray
Write-Host "      • obsidian_client.py" -ForegroundColor Gray
Write-Host "      • config.py" -ForegroundColor Gray
Write-Host "      • watcher.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2️⃣  Copie os scripts PowerShell para: 80_SYSTEM\SCRIPTS\" -ForegroundColor White
Write-Host "      • pre_task_hook.ps1" -ForegroundColor Gray
Write-Host "      • post_task_hook.ps1" -ForegroundColor Gray
Write-Host "      • reindex_hybrid.ps1" -ForegroundColor Gray
Write-Host "      • backup_vault.ps1" -ForegroundColor Gray
Write-Host "      • backup_incremental.ps1" -ForegroundColor Gray
Write-Host "      • restore_backup.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  3️⃣  Copie os templates para: 80_SYSTEM\TEMPLATES\" -ForegroundColor White
Write-Host "      • novo_projeto.md" -ForegroundColor Gray
Write-Host "      • novo_recurso.md" -ForegroundColor Gray
Write-Host "      • novo_padrao.md" -ForegroundColor Gray
Write-Host "      • nova_daily.md" -ForegroundColor Gray
Write-Host "      • novo_moc.md" -ForegroundColor Gray
Write-Host ""
Write-Host "  4️⃣  Abra o Obsidian e:" -ForegroundColor White
Write-Host "      • Settings → Community plugins → Instale: Dataview, Templater" -ForegroundColor Gray
Write-Host "      • Settings → Appearance → CSS Snippets → Ative 'megabrain'" -ForegroundColor Gray
Write-Host "      • Settings → Daily notes → Ative com formato YYYY-MM-DD" -ForegroundColor Gray
Write-Host ""
Write-Host "  5️⃣  Configure o Hermes Agent:" -ForegroundColor White
Write-Host "      • Adicione o bloco MCP no config.json (use o server-config.json gerado)" -ForegroundColor Gray
Write-Host "      • Reinicie o Hermes Agent" -ForegroundColor Gray
Write-Host ""
Write-Host "  6️⃣  Após copiar todos os scripts, reexecute este instalador" -ForegroundColor White
Write-Host "      para ativar as tarefas pendentes." -ForegroundColor Gray
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📄 Log completo salvo em:" -ForegroundColor Cyan
Write-Host "   $LogFile" -ForegroundColor Gray
Write-Host ""
Write-Host "📂 Estrutura criada em:" -ForegroundColor Cyan
Write-Host "   $Vault" -ForegroundColor Gray
Write-Host ""
# Salvar log final
"=== INSTALAÇÃO CONCLUÍDA ===" | Add-Content $LogFile -Encoding UTF8
"Pastas: $totalFolders | Arquivos: $totalFiles | Tarefas: $taskCount" | Add-Content $LogFile -Encoding UTF8
"Log encerrado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Add-Content $LogFile -Encoding UTF8
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
exit 0
