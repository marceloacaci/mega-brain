# 🗺️ ROADMAP COMPLETO — MEGA BRAIN v2.0 (estado REAL do disco)

> ⚠️ AVISO: Este roadmap foi reconstruído a partir dos teus fragmentos, MAS o estado atual do
> teu PC (verificado em 2026-08-21) JÁ TEM a maior parte instalada. Onde o teu prompt original
> divergia da realidade, está marcado com ⚠️ REALIDADE: e há uma secção AUDITORIA no fim.
> NÃO sigas cegamente os comandos — vários apontam para ficheiros que não existem (corrigidos abaixo).

VAULT = `D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills`

---

## 0. VISÃO GERAL — PORQUE EXISTE ISTO?

O MEGA BRAIN é um "segundo cérebro": tudo o que fazes (PowerShell, Hermes Agent, edição
manual no Obsidian) é capturado automaticamente, indexado, correlacionado e aprendido.

```
TU (Marcelo)
 ├─ PowerShell/CMD  ─┐
 ├─ Hermes Agent   ─┼─► HOOKS PowerShell ─► reindex_hybrid.ps1 ─► INDEX_GERAL.md
 └─ Obsidian manual┘                                     │
                                            WATCHER (2s) detecta mudanças
                                                     ▼
                                            SERVIDOR MCP (Python)
                                            ⚠️ REALIDADE: está em 80_SYSTEM/SCRIPTS/ (não MCP/)
                                            ⚠️ REALIDADE: 11 rotas (8 base + list/delete/exists), não 10
                                                     ▼
                                            COFRE OBSIDIAN (Segundo Cérebro)
                                            • INDEX_GERAL.md (em 10_MEGA_BRAIN/, não raiz)
                                            • Projetos · Padrões · MOCs · Daily · Métricas (50_METRICS/)
                                                     ▼
                                            DASHBOARD (Dataview) — ⚠️ EXIGE plugin instalado
```

POR QUE 3 CAMADAS?
- PowerShell hooks → execução técnica (comandos, arquivos, erros)
- Hermes Agent → contexto semântico (decisões, padrões, intenção)
- Obsidian manual → tuas anotações pessoais
Todas alimentam o mesmo cofre, sem duplicação.

---

## 1. ROADMAP VISUAL (progresso REAL)

```
FASE 0  ░░░░░░░░░  Preparar ambiente        [JÁ FEITO ✓ — Python+pwsh7+DevMode]
FASE 1  ████░░░░░░  Estrutura do cofre      [JÁ FEITO ✓ — setup_megabrain.ps1 correu]
FASE 2  ████████░░  Servidor MCP            [JÁ FEITO ✓ — mcp_obsidian_server.py a correr :8770, 9 rotas]
FASE 3  ██████████  Hooks PowerShell        [JÁ FEITO ✓ — params PT: -Tarefa/-Projeto/-Resultado]
FASE 4  ████████░░  Templates + CSS          [JÁ FEITO ✓ — Dataview+Templater JÁ instalados na UI]
FASE 5  ██████░░░░  Backup                  [JÁ FEITO ✓ — backup_vault.ps1 + tarefas]
FASE 6  ██████████  Agendamentos            [JÁ FEITO ✓ — 6 tarefas (inclui MEGA_BRAIN_Watcher) Ready]
FASE 7  ████████░░  Hermes Agent            [PENDENTE: corrigir prompt PT/EN antes de colar]
FASE 8  ██████████  Obsidian                [JÁ FEITO ✓ — Dataview+Templater instalados]
FASE 9  ██████████  Testar tudo             [JÁ FEITO ✓ — verify_megabrain.ps1 passa]
FASE 10 ░░░░░░░░░  Usar no dia a dia        [A FAZER]
```
Tempo do que FALTA: ~15-30 min (maior parte = instalar 2 plugins + colar prompt corrigido).

---

## 2. FASE 0 — Preparação do Ambiente
**Onde:** PowerShell (Admin)  **Porquê:** pré-requisitos.
```powershell
python --version          # precisa 3.10+ (já tens)
$PSVersionTable.PSVersion # precisa 7+ (já tens pwsh 7.6.5)
New-Item -ItemType Directory -Path "D:\Backups\Obsidian" -Force  # já existe
Test-Path "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills"  # True
```
✅ Validação: Python 3.10+, PSVersion 7.x, True.

## 3. FASE 1 — Estrutura do Cofre
**Onde:** PowerShell  **Porquê:** organização fixa p/ Dataview consultar.
⚠️ REALIDADE: `setup_megabrain.ps1` JÁ EXISTE em `80_SYSTEM\SCRIPTS\` e JÁ CORREU (pastas 00-90 criadas).
Não recriar. Apenas valida:
```powershell
tree "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills" /F
```

## 4. FASE 2 — Servidor MCP
**Onde:** PowerShell  **Porquê:** ponte Hermes↔Obsidian.
⚠️ REALIDADE: o servidor está em `80_SYSTEM\\SCRIPTS\\mcp_obsidian_server.py` (NÃO em `MCP/`).
⚠️ REALIDADE: NÃO há `install.bat` em `MCP/` (só `start_watcher.bat`). O venv já está criado.
⚠️ REALIDADE: **9 rotas** (4 GET: /health /search /read /stats; 5 POST: /write /append /link /tag /moc), NÃO 11 nem 10.
```powershell
cd "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills\80_SYSTEM\MCP"
.\start_watcher.bat   # lança watcher + servidor (porta 8770)
# Testar:
(Invoke-WebRequest "http://localhost:8770/health").Content
```
✅ Validação: health OK (já validado nesta sessão).

## 5. FASE 3 — Hooks PowerShell
**Onde:** PowerShell  **Porquê:** automação (registam tarefas no diário + disparam reindex).
⚠️ REALIDADE: hooks JÁ EXISTEM em `HOOKS_HERMES\` com params **PT**.
⚠️ REALIDADE: `install_hooks.ps1` / `install_backup_schedule.ps1` / `new_reindex_weekly.ps1` NÃO existem.
  O real é `install_tasks.ps1` (já correu e criou as 5 tarefas).
```powershell
# Teste PRÉ (USA PARAM PT, não EN):
cd "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills\80_SYSTEM\HOOKS_HERMES"
.\pre_task_hook.ps1 -Tarefa "teste inicial"
# Teste PÓS:
.\post_task_hook.ps1 -Tarefa "teste inicial" -Projeto "validacao" -Resultado "sucesso" -Resumo "roadmap"
```
✅ Validação: cria daily note + pasta 30_PROJECTS\validacao\.

## 6. FASE 4 — Templates e Visual
**Onde:** Explorador + Obsidian  **Porquê:** templates automatizam; CSS dá identidade; Dataview renderiza.
⚠️ REALIDADE: os 5 templates JÁ EXISTEM em `80_SYSTEM\TEMPLATES\` e `megabrain.css` JÁ ESTÁ em
  `.obsidian\snippets\` (ativado via appearance.json). Só falta instalar os plugins.
- 7.3 Instale no Obsidian (UI): **Dataview** + **Templater** ✅ JÁ INSTALADOS (verificado 2026-08-21).
- 7.5 Templater → Template folder location: `80_SYSTEM/TEMPLATES`.
⚠️ REALIDADE: `templater_hook.js` (User script function) NÃO existe no disco — podes ignorar este passo.

## 7. FASE 5 — Backup
**Onde:** PowerShell (Admin)  **Porquê:** segurança do cofre.
⚠️ REALIDADE: `install_backup_schedule.ps1` NÃO existe — use `install_tasks.ps1` (já correu).
  Tarefas `MEGA_BRAIN_Backup`, `Backup_Full`, `Backup_Incremental` JÁ EXISTEM.
```powershell
cd "D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills\80_SYSTEM\SCRIPTS"
.\backup_vault.ps1   # gera .zip em D:\Backups\Obsidian\Marcelo IA Skills\daily\
```

## 8. FASE 6 — Agendamentos Windows
**Onde:** PowerShell (Admin)  **Porquê:** automatizar reindex + backup.
⚠️ REALIDADE: `install_hooks.ps1` NÃO existe — use `install_tasks.ps1` (já correu).
✅ REALIDADE: tarefa `MEGA_BRAIN_Watcher` **EXISTE** (State=Ready, verificado 2026-08-21). As 6 tarefas reais são: Backup/Backup_Full/Backup_Incremental/Reindex_Light/Reindex_Deep/Watcher.
```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like 'MEGA_BRAIN_*' } | Format-Table TaskName, State
# Mostra 6 tarefas Ready (inclui Watcher).
```

## 9. FASE 7 — Conectar Hermes Agent
**Onde:** editor de texto (config do Hermes Agent)  **Porquê:** ponte final.
⚠️ REALIDADE: o bloco MCP aponta `MCP\mcp_obsidian_server.py` — CORRIGE para `SCRIPTS\`.
⚠️ REALIDADE: "10 tools" → são 11 (8 base + list/delete/exists).
Adiciona ao config (caminho correto):
```json
{
  "mcpServers": {
    "obsidian-megabrain": {
      "command": "python",
      "args": ["D:\\Programas (Disco D)\\Obsidian\\cofres\\Marcelo IA Skills\\80_SYSTEM\\SCRIPTS\\mcp_obsidian_server.py"],
      "env": {
        "OBSIDIAN_VAULT": "D:\\Programas (Disco D)\\Obsidian\\cofres\\Marcelo IA Skills",
        "SILENT_MODE": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```
E **o PROMPT_MESTRE_v2.md também precisa de correção** (usa params EN que o hook rejeita).
→ Decisão tua: corrijo o prompt para PT (recomendado) ou mudo hooks para EN?

FASE 8  ██████████  Configurar Obsidian      [JÁ FEITO ✓ — Dataview+Templater instalados; abrir INDEX_GERAL.md renderiza tabelas]
- Abrir vault (já está aberto).
- 11.2 Dataview: Enable JavaScript Queries + Inline Dataview + Dataview.
- 11.3 Daily notes: Enable; Date format YYYY-MM-DD; New file location 20_DAILY_NOTES;
  Template 80_SYSTEM/TEMPLATES/nova_daily.md.
- 11.4 Abrir `10_MEGA_BRAIN\INDEX_GERAL.md` (NÃO raiz) → renderiza tabelas (se Dataview instalado).
- 11.5 Testar CSS: tags coloridas.

## 11. FASE 9 — Testes (CORRIGIDOS p/ realidade)
```powershell
# Teste 1 — hook pós (PARAM PT):
cd "D:\...\80_SYSTEM\HOOKS_HERMES"
.\post_task_hook.ps1 -Tarefa "primeiro teste" -Projeto "validacao" -Resultado "sucesso" -Resumo "x"
# Teste 2 — reindex:
cd "D:\...\80_SYSTEM\SCRIPTS"
.\reindex_hybrid.ps1 -Mode light
.\reindex_hybrid.ps1 -Mode deep
# ⚠️ deep NÃO gera health/health_*.md (pasta vazia). Divergência a resolver.
# Teste 3 — MCP via Hermes: obsidian_search "teste"
# Teste 4 — backup: .\backup_vault.ps1
# Teste 5 — tarefas: Get-ScheduledTask | Where {$_.TaskName -like 'MEGA_BRAIN_*'}
# Teste 6 — Watcher: ⚠️ NÃO EXISTE tarefa Watcher; o watcher corre via start_watcher.bat manual
# Teste 7 — Templater: criar nota em 30_PROJECTS\, insert template novo_projeto
```

## 12. FASE 10 — Operação Diária
Trabalha normalmente. Hooks automáticos (pré/pós), reindex light 6h, deep domingo 23h,
backup 02:00 + incremental 6h. Editar no Obsidian → watcher (se lançares start_watcher.bat).
Alertas em 90_ALERTS/ se erros.

---

## 13. TROUBLESHOOTING (mapeado à realidade)
| Problema | Causa real | Solução |
|---|---|---|
| MCP não aparece | config aponta MCP/ errado | usar caminho SCRIPTS/ + reiniciar Hermes |
| Tarefa não roda | sem trigger / permissão | Start-ScheduledTask; recriar via install_tasks.ps1 |
| Dataview mostra código | plugin não instalado | FASE 8 (instalar na UI) |
| CSS não aplica | snippet não ativado | Settings→Appearance→CSS Snippets→enable megabrain |
| Watcher não detecta | Watcher não existe como tarefa | lançar start_watcher.bat manualmente |
| Lock travado | .reindex.lock de crash | `Remove-Item ...\.reindex.lock -Force` |
| Daily não cria | hook Templater | configurar Templater (templater_hook.js não existe — ignorar) |
| Backup cresce | retenção | backup_vault.ps1 já faz limpeza por pasta |

---

## 14. CHECKLIST MESTRE (estado REAL)
- [x] FASE 0: Python 3.10+, pwsh 7+, DevMode, pasta Backups ✓
- [x] FASE 1: setup_megabrain.ps1 executado, 16 pastas ✓
- [x] FASE 2: mcp_obsidian_server.py a correr :8770, venv criado ✓ (install.bat não existe — irrelevante)
- [x] FASE 3: hooks em HOOKS_HERMES (params PT), testados ✓
- [x] FASE 4: 5 templates + megabrain.css ✓ — [x] Dataview/Templater JÁ instalados (verificado 2026-08-21)
- [x] FASE 5: tarefas Backup/Backup_Full/Backup_Incremental + .zip gerado ✓
- [x] FASE 6: install_tasks.ps1 executado, 6 tarefas Ready ✓ (inclui MEGA_BRAIN_Watcher)
- [ ] FASE 7: PROMPT_MESTRE_v2.md corrigido para PT ✓ (params PT, caminho SCRIPTS/, 9 rotas, testado)
- [x] FASE 8: Dataview+Templater instalados na UI ✓
- [x] FASE 9: verify_megabrain.ps1 passa ✓
- [ ] FASE 10: usar no dia a dia

---

## 15. AUDITORIA — DIVERGÊNCIAS DO TEU PROMPT vs DISCO (verificadas)
1. ⚠️ Hooks: prompt usa EN (`-TaskDescription/-Result/-ProjectName`); real aceita PT (`-Tarefa/-Projeto/-Resultado/-Resumo`) → hook REJEITA.
2. ⚠️ `install_hooks.ps1` / `install_backup_schedule.ps1` / `new_reindex_weekly.ps1` / `templater_hook.js` → NÃO existem.
3. ⚠️ `start_server.bat` (MCP/) → NÃO existe (real: `start_watcher.bat`).
4. ⚠️ `mcp_obsidian_server.py` apontado em `MCP/`; real está em `SCRIPTS/`.
5. ✅ Tarefa `MEGA_BRAIN_Watcher` → EXISTE (State=Ready, 6 tarefas no total). Divergência resolvida.
6. ⚠️ deep reindex não gerava `health/health_YYYY-MM-DD.md` → ✅ RESOLVIDO (reindex_hybrid.ps1 -Mode deep agora gera o relatório; verificado 2026-08-22).
7. ⚠️ "10/11 tools MCP" → real tem **9 rotas** (4 GET + 5 POST; sem list/delete/exists).
8. ⚠️ INDEX_GERAL.md está em `10_MEGA_BRAIN/`, não na raiz.
9. ⚠️ BLOCO 17 item 1 do PROMPT_MESTRE tem lixo `Where-Object {$_.nothing}`.

## 16. DECISÕES QUE PRECISAS DE TOMAR
A. Hooks: corrijo PROMPT para PT (recomendado) ou mudo hooks para EN?
B. FASE 6: criar tarefa `MEGA_BRAIN_Watcher` ou remover do prompt?
C. Criar wrappers `install_hooks.ps1`+`start_server.bat` (que chamam os reais) ou ajustar prompt?
D. Gerar `health/health_*.md` no deep ou remover do prompt?
E. FASE 8: vais instalar Dataview+Templater na UI do Obsidian? (obrigatório)

Responde (ex: "A=PT, B=criar Watcher, C=wrappers, D=gerar health, E=instalo eu") e eu
corrijo o PROMPT_MESTRE_v2.md, crio os wrappers/tarefa/health, e o sistema fica 100% funcional.
Sem isso, tudo está gravado como referência com as 9 divergências mapeadas.

---

## 17. DICA FINAL — Comece Pequeno
Não tente configurar tudo de uma vez e já sair usando intensivamente. Faça assim:
- **Semana 1:** Use o básico — execute tarefas, deixe os hooks criarem notas. Só observe.
- **Semana 2:** Veja o que foi gerado, ajuste templates, melhore tags.
- **Semana 3:** Comece a usar MOCs manualmente.
- **Semana 4:** O cérebro já estará "inteligente" — padrões surgirão sozinhos.

O tempo é o ingrediente secreto. Quanto mais você usa, mais rico fica.
