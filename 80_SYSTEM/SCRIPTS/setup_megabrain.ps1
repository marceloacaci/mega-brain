<#
.SYNOPSIS
Configura a estrutura completa do MEGA BRAIN no Obsidian.
.DESCRIPTION
Cria todas as pastas, arquivos base, e estrutura inicial do Segundo Cérebro. Idempotente: pode ser executado múltiplas vezes sem duplicar.
.NOTES
Autor: Hermes Agent + Marcelo
Versão: 2.0.0 (Modelo Híbrido)
Compatível com: PowerShell 7+
#>
[CmdletBinding()]
param()
# ============================================
# CONFIGURAÇÃO
# ============================================
$ErrorActionPreference = "Stop"
# Detectar caminho do vault automaticamente
# (assume que o script está em 80_SYSTEM\SCRIPTS\)
$Vault = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$LogFile = Join-Path $Vault "80_SYSTEM\LOGS\setup_$(Get-Date -Format 'yyyy-MM-dd_HHmmss').log"
# Se não conseguir detectar, pedir ao usuário
if (-not (Test-Path $Vault)) {
Write-Host "❌ Não foi possível detectar o vault automaticamente." -ForegroundColor Red
Write-Host "Por favor, edite a variável `$Vault no início deste script." -ForegroundColor Yellow
Write-Host "Caminho esperado: D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills" -ForegroundColor Yellow
exit 1
}
# Criar pasta de logs se não existir
$logDir = Join-Path $Vault "80_SYSTEM\LOGS"
if (-not (Test-Path $logDir)) {
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
# ============================================
# FUNÇÕES AUXILIARES
# ============================================
function Write-SetupLog {
param(
[string]$Message,
[string]$Level = "INFO"
)
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$entry = "[$timestamp] [$Level] $Message"
# Gravar no arquivo de log
Add-Content -Path $LogFile -Value $entry -Encoding UTF8 -ErrorAction SilentlyContinue
# Exibir no console com cores
$color = switch ($Level) {
"ERROR" { "Red" }
"WARN"  { "Yellow" }
"OK"    { "Green" }
"STEP"  { "Cyan" }
default { "White" }
}
Write-Host $entry -ForegroundColor $color
}
function New-Directory {
param([string]$Path)
if (-not (Test-Path $Path)) {
New-Item -ItemType Directory -Path $Path -Force | Out-Null
Write-SetupLog "📁 Pasta criada: $Path" "OK"
} else {
Write-SetupLog "⏭️  Pasta já existe: $Path"
}
}
function New-FileFromTemplate {
param(
[string]$Path,
[string]$Content,
[string]$Description = ""
)
$parent = Split-Path $Path -Parent
# Garantir que pasta existe
if (-not (Test-Path $parent)) {
New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
if (-not (Test-Path $Path)) {
Set-Content -Path $Path -Value $Content -Encoding UTF8
$desc = if ($Description) { " — $Description" } else { "" }
Write-SetupLog "📄 Arquivo criado: $Path$desc" "OK"
} else {
Write-SetupLog "⏭️  Arquivo já existe: $Path"
}
}
# ============================================
# INÍCIO
# ============================================
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🧠 MEGA BRAIN v2.0 — Setup Inicial" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-SetupLog "=== INÍCIO DA CONFIGURAÇÃO ===" "STEP"
Write-SetupLog "Vault detectado: $Vault" "STEP"
Write-Host ""
# ============================================
# 1. CRIAR ESTRUTURA DE PASTAS
# ============================================
Write-SetupLog "[1/5] Criando estrutura de pastas..." "STEP"
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
foreach ($folder in $folders) {
$fullPath = Join-Path $Vault $folder
New-Directory $fullPath
}
Write-Host ""
# ============================================
# 2. CRIAR ARQUIVOS DO MEGA BRAIN
# ============================================
Write-SetupLog "[2/5] Criando arquivos do MegaBrain..." "STEP"
$today = Get-Date -Format "yyyy-MM-dd"
$now = Get-Date -Format "yyyy-MM-dd HH:mm"
$year = Get-Date -Format "yyyy"
$month = Get-Date -Format "MM"
# ------------------------------------------
# INDEX_GERAL.md (raiz do cofre)
# ------------------------------------------
$indexContent = @"
---
tipo: meta-indice
criado: $today
atualizado: $today
tags: [meta/index]
---
# 🧠 MEGA BRAIN — Índice Geral
> Dashboard vivo do meu Segundo Cérebro. Atualizado automaticamente.
## ⏰ Status de Sincronização
- **Última light:** $now
- **Última deep:** $now
- **Próxima light:** $((Get-Date).AddHours(6).ToString('yyyy-MM-dd HH:mm'))
- **Próxima deep:** $((Get-Date).AddDays(7).ToString('yyyy-MM-dd HH:mm'))
- **Última reindexação:** $now (deep)
> Modelo híbrido: light a cada 6h + deep semanal (domingo 23h).
---
## 📊 Visão Geral
```dataview
TABLE WITHOUT ID
length(rows) AS "Total"
FROM ""
WHERE type = "meta-indice"
```
## 📁 Projetos Ativos
```dataview
TABLE
status AS "Status",
stack AS "Stack",
criado AS "Criado"
FROM "30_PROJETS"
WHERE status = "ativo"
SORT criado DESC
```
## 🧩 Stack Mapeada (Top 10)
```dataview
TABLE WITHOUT ID
stack AS "Stack",
length(rows) AS "Uso"
FROM "30_PROJETS"
WHERE stack
FLATTEN stack
GROUP BY stack
SORT length(rows) DESC
LIMIT 10
```
## 🕒 Últimas 7 Execuções
```dataview
TABLE
file.link AS "Dia",
humor AS "Humor"
FROM "20_DAILY_NOTES"
SORT file.name DESC
LIMIT 7
```
## 🔍 Padrões Detectados (Top 10)
```dataview
TABLE
categoria AS "Categoria",
ocorrencias AS "Ocorrências",
ultima_vez AS "Última"
FROM "10_MEGA_BRAIN"
WHERE contains(tags, "padrao")
SORT ocorrencias DESC
LIMIT 10
```
## 🗂️ Maps of Content (MOCs)
```dataview
LIST
FROM "70_MOCS"
WHERE contains(tags, "moc")
SORT file.name ASC
```
## 🔔 Alertas Ativos
```dataview
TABLE
prioridade AS "Prioridade",
categoria AS "Categoria",
file.link AS "Arquivo"
FROM "90_ALERTS"
WHERE !resolved
SORT prioridade DESC
```
---
*Total de notas: — | Próxima light: $((Get-Date).AddHours(6).ToString('yyyy-MM-dd HH:mm')) | Próxima deep: $((Get-Date).AddDays(7).ToString('yyyy-MM-dd HH:mm'))*
"@
New-FileFromTemplate (Join-Path $Vault "INDEX_GERAL.md") $indexContent "Dashboard principal"
# ------------------------------------------
# 10_MEGA_BRAIN/PADROES_RECorrentes.md
# ------------------------------------------
New-FileFromTemplate (Join-Path $Vault "10_MEGA_BRAIN\PADROES_RECorrentes.md") @"
---
tipo: meta
criado: $today
tags: [meta, padrao, megabrain]
---
# 🔁 Padrões Recorrentes
> Detectado automaticamente quando um padrão aparece ≥ 2 vezes em projetos distintos.
## 📋 Índice de Padrões
```dataview
TABLE
categoria AS "Categoria",
ocorrencias AS "Ocorrências",
ultima_vez AS "Última Vez"
FROM "10_MEGA_BRAIN"
WHERE contains(tags, "padrao")
SORT ocorrencias DESC
```
---
<!-- TEMPLATE PARA NOVO PADRÃO -->
## 🧩 {{nome-do-padrao}}
- **Categoria:** {{categoria}}
- **Ocorrências:** {{n}}
- **Detectado em:** {{projetos}}
- **Última vez:** {{data}}
- **Descrição:** {{descricao}}
- **Quando aplicar:** {{trigger}}
- **Como aplicar:**
```{{linguagem}}
{{codigo}}
```
- **Projetos relacionados:**
```dataview
LIST
FROM ""
WHERE contains(tags, "padrao/{{slug}}")
```
"@ "Registro de padrões"
# ------------------------------------------
# 10_MEGA_BRAIN/STACKS_MAPeadas.md
# ------------------------------------------
New-FileFromTemplate (Join-Path $Vault "10_MEGA_BRAIN\STACKS_MAPeadas.md") @"
---
tipo: meta
criado: $today
tags: [meta, stack, megabrain]
---
# 🧩 Stacks Mapeadas
> Inventário vivo de todas as tecnologias utilizadas.
```dataview
TABLE
categoria AS "Categoria",
versao AS "Versão",
projetos AS "Projetos",
ultima_vez AS "Última Vez"
FROM "10_MEGA_BRAIN"
WHERE contains(tags, "stack")
SORT categoria ASC
```
---
## 🐍 Python
## 🟢 Node.js
## 🦀 Rust
## ☕ Java
## 🌐 Web (HTML/CSS/JS)
## 🗄️ Banco de Dados
## 🐳 DevOps / Containers
## 🔌 APIs
"@ "Mapa de stacks"
# ------------------------------------------
# 10_MEGA_BRAIN/PREFERENCIAS_PESSOAIS.md
# ------------------------------------------
New-FileFromTemplate (Join-Path $Vault "10_MEGA_BRAIN\PREFERENCIAS_PESSOAIS.md") @"
---
tipo: meta
criado: $today
tags: [meta, preferencias, megabrain]
---
# ⚙️ Preferências Pessoais
> Como eu gosto que as coisas sejam feitas.
## 🗣️ Linguagem
- **Comunicação:** Português (PT-BR)
- **Código:** Inglês em variáveis, comentários em PT-BR
- **Logs:** Português
## 📐 Formatação
- Markdown padrão GitHub
- Máximo 1 emoji por cabeçalho
- Listas ordenadas para procedimentos
- Tabelas para comparações
## 🛠️ Stack Preferida
- **Linguagem principal:** Python
- **Editor:** VS Code / Obsidian
- **Terminal:** PowerShell 7
- **Versionamento:** Git + GitHub
## 🤖 Comportamentos
- ❌ Não pedir confirmações desnecessárias
- ✅ Fazer log de tudo automaticamente
- ✅ Atualizar índices em background
- ✅ Silencioso em sucesso, barulhento em erro
## 💻 Estilo de Código
- Funções pequenas (< 30 linhas)
- Type hints em Python
- Documentação em docstrings
- Testes para funções críticas
"@ "Preferências pessoais"
# ------------------------------------------
# 10_MEGA_BRAIN/DECISOES_REUTILIZAVEIS.md
# ------------------------------------------
New-FileFromTemplate (Join-Path $Vault "10_MEGA_BRAIN\DECISOES_REUTILIZAVEIS.md") @"
---
tipo: meta
criado: $today
tags: [meta, decisao, megabrain]
---
# 🎯 Decisões Reutilizáveis
> Decisões já tomadas que devem ser respeitadas em projetos futuros.
```dataview
TABLE
contexto AS "Contexto",
decisao AS "Decisão",
data AS "Data"
FROM "10_MEGA_BRAIN"
WHERE contains(tags, "decisao")
SORT data DESC
```
---
<!-- TEMPLATE PARA NOVA DECISÃO -->
## 🎯 Decisão #{{numero}} — {{titulo}}
- **Data:** {{data}}
- **Contexto:** {{contexto}}
- **Decisão:** {{decisao}}
- **Razão:** {{razao}}
- **Consequências:** {{consequencias}}
- **Aplicar em:** {{aplicacao}}
"@ "Decisões técnicas"
Write-Host ""
# ============================================
# 3. CRIAR MOC INICIAL
# ============================================
Write-SetupLog "[3/5] Criando MOC inicial..." "STEP"
New-FileFromTemplate (Join-Path $Vault "70_MOCS\MOC_GERAL.md") @"
---
tipo: moc
criado: $today
tags: [moc, moc/raiz]
---
# 🗺️ MOC Geral
> Map of Content central. Conecta todas as áreas do conhecimento.
## 📁 Por Projeto
```dataview
LIST
FROM "30_PROJETS"
SORT file.name ASC
```
## 🔁 Por Padrão
```dataview
LIST
FROM "10_MEGA_BRAIN"
WHERE contains(tags, "padrao")
```
## 🧩 Por Stack
```dataview
LIST
FROM "50_RESOURCES"
SORT file.name ASC
```
## 🗂️ Por Área
```dataview
LIST
FROM "40_AREAS"
```
## 🔗 Conexões Externas
```dataview
LIST
FROM ""
WHERE contains(tags, "moc") AND !contains(tags, "moc/raiz")
```
"@ "MOC raiz"
Write-Host ""
# ============================================
# 4. CRIAR DAILY NOTE DO DIA
# ============================================
Write-SetupLog "[4/5] Criando daily note de hoje..." "STEP"
New-FileFromTemplate (Join-Path $Vault "20_DAILY_NOTES\$today.md") @"
---
data: $today
humor: neutro
tags: [daily/$year/$month]
---
# 📅 $today
> **Humor:** neutro
## 🎯 Foco do Dia
- [ ]
## ⏳ Em Andamento
```dataview
TASK
FROM "30_PROJETS"
WHERE !completed AND contains(file.tags, "prioridade/alta")
```
## 📆 Tarefas Agendadas
```dataview
TASK
FROM ""
WHERE due = "$today"
```
## ✅ Execuções do Dia
*(preenchido automaticamente pelos hooks)*
## 💡 Aprendizados
-
## 🔗 Links Gerados
```dataview
LIST
FROM ""
WHERE file.cday = date("$today")
```
"@ "Daily note de hoje"
Write-Host ""
# ============================================
# 5. CRIAR READMES E PLACEHOLDERS
# ============================================
Write-SetupLog "[5/5] Criando READMEs nas pastas..." "STEP"
$readmeFolders = @{
"00_INBOX"      = "Capturas brutas automáticas. Arquivos temporários."
"10_MEGA_BRAIN" = "Cérebro central consolidado. Apenas o Hermes Agent escreve aqui."
"20_DAILY_NOTES"= "Uma nota por dia. Formato: YYYY-MM-DD.md"
"30_PROJECTS"   = "Projetos ativos. Um sub-pasta por projeto."
"40_AREAS"      = "Áreas contínuas da vida. Não temporal."
"50_RESOURCES"  = "Conhecimento reutilizável. Linguagens, frameworks, ferramentas."
"60_ARCHIVE"    = "Projetos concluídos ou descartados. Nunca deletar."
"70_MOCS"       = "Maps of Content. Índices temáticos."
"80_SYSTEM"     = "Configurações, scripts, templates, MCP. Não mexer manualmente."
"90_ALERTS"     = "Alertas, exceções, pendências críticas."
}
foreach ($folder in $readmeFolders.Keys) {
$path = Join-Path $Vault "$folder\README.md"
$desc = $readmeFolders[$folder]
New-FileFromTemplate $path @"
# 📂 $folder
> $desc
"@ "README"
}
Write-Host ""
# ============================================
# 6. CONFIG.JSON INICIAL
# ============================================
Write-SetupLog "[6/5] Criando config.json inicial..." "STEP"
$configContent = @{
vault_path = $Vault
log_path = Join-Path $Vault "80_SYSTEM\LOGS"
log_retention_days = 30
silent_mode = $true
mcp_server_url = "http://localhost:8770"
auto_reindex = @{
enabled = $true
mode = "hybrid"
light = @{
interval_hours = 6
force_after_hours = 4
}
deep = @{
day_of_week = "Sunday"
time = "23:00"
}
}
watcher = @{
enabled = $true
debounce_ms = 2000
}
modes = @{
indexador = $true
correlacionador = $true
guardiao = $true
metrico = $true
preditivo = $true
}
backup = @{
enabled = $true
root = "D:\Backups\Obsidian"
full_schedule = "02:00"
incremental_interval_hours = 6
retention = @{
daily = 7
weekly = 4
monthly = 6
incremental_days = 30
}
}
}
$configPath = Join-Path $Vault "80_SYSTEM\SCRIPTS\config.json"
$configContent | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
Write-SetupLog "📄 Arquivo criado: $configPath" "OK"
Write-Host ""
# ============================================
# 7. CRIAR PLACEHOLDER PARA TEMPLATES
# ============================================
Write-SetupLog "[7/5] Criando diretório de templates..." "STEP"
$templatesReadme = Join-Path $Vault "80_SYSTEM\TEMPLATES\README.md"
New-FileFromTemplate $templatesReadme @"
# 📝 Templates — Templater
> Cole aqui os templates `.md` do Templater.
## Templates disponíveis
- \`novo_projeto.md\` — Cria projeto com 1 clique
- \`novo_recurso.md\` — Adiciona resource
- \`novo_padrao.md\` — Registra padrão
- \`nova_daily.md\` — Auto-cria daily
- \`novo_moc.md\` — Gera MOC
## Como usar no Obsidian
1. Settings → Templater → Template folder location
2. Apontar para esta pasta
3. Usar comando \`Templater: Insert template from file\`
"@ "README de templates"
Write-Host ""
# ============================================
# STATUS FINAL
# ============================================
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ MEGA BRAIN v2.0 — Instalação Concluída!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
# Estatísticas
$folderCount = (Get-ChildItem -Path $Vault -Recurse -Directory |
Where-Object { $_.FullName -notmatch "\.obsidian|\.trash" }).Count
$fileCount = (Get-ChildItem -Path $Vault -Recurse -File -Filter "*.md" -ErrorAction SilentlyContinue).Count
Write-Host "📊 Estatísticas:" -ForegroundColor Cyan
Write-Host "   📁 Pastas criadas: $folderCount"
Write-Host "   📄 Arquivos .md: $fileCount"
Write-Host "   📂 Vault: $Vault"
Write-Host "   📄 Log: $LogFile"
Write-Host ""
# Banner de ativação
Write-Host "┌─────────────────────────────────────────────────────────┐" -ForegroundColor Magenta
Write-Host "│  [MEGA BRAIN v2.0] ✅ Segundo Cérebro online              │" -ForegroundColor Magenta
Write-Host "│                                                          │" -ForegroundColor Magenta
Write-Host "│  📂 Vault: D:\Programas (Disco D)\Obsidian\cofres\...     │" -ForegroundColor Magenta
Write-Host "│  🧠 Modos: Indexador · Correlacionador · Guardião        │" -ForegroundColor Magenta
Write-Host "│           Métrico · Preditivo                             │" -ForegroundColor Magenta
Write-Host "│  ⏰ Reindex: light 6h · deep semanal · watcher 2s         │" -ForegroundColor Magenta
Write-Host "│  💾 Backup: full 02:00 · incremental 6h                   │" -ForegroundColor Magenta
Write-Host "│                                                          │" -ForegroundColor Magenta
Write-Host "│  📋 Próximos passos:                                     │" -ForegroundColor Magenta
Write-Host "│     1. Abrir Obsidian → ativar CSS 'megabrain'           │" -ForegroundColor Magenta
Write-Host "│     2. Instalar plugins: Dataview, Templater, QuickAdd   │" -ForegroundColor Magenta
Write-Host "│     3. Executar install_hooks.ps1                        │" -ForegroundColor Magenta
Write-Host "│     4. Configurar MCP no Hermes Agent                    │" -ForegroundColor Magenta
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor Magenta
Write-Host ""
Write-SetupLog "=== SETUP CONCLUÍDO COM SUCESSO ===" "STEP"
exit 0
