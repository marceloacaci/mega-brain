# Arquitetura de Software — MEGA BRAIN

## Padrões de Projeto
- **Repository / Gateway**: o MCP server isola o acesso ao vault (leitura/escrita)
  por trás de rotas REST, permitindo que o Hermes Agent (ou outra ferramenta)
  opere sem conhecer a estrutura de arquivos.
- **Observer (Watcher)**: `watcher.py` monitora mudanças no vault (debounce 2s)
  e dispara ações de sincronização.
- **Strategy (Modos)**: `config.json` habilita modos (correlacionador, guardião,
  preditivo, métrico, indexador) que alteram o comportamento em runtime.
- **Template Method (Reindex)**: `reindex_hybrid.ps1` tem dois modos (`light`,
  `deep`) que compartilham a montagem do dashboard, variando só o escopo.
- **Facade (Hooks)**: `pre_`/`post_task_hook.ps1` expõem uma interface simples
  (`-Tarefa -Projeto -Resultado -Resumo`) sobre a complexidade do cérebro.

## Justificativa Técnica
- **PowerShell 7** para hooks: integra nativamente com o Agendador de Tarefas
  Windows e com o Hermes Agent; sintaxe moderna (`Join-Path`, `ConvertFrom-Json`).
- **Python `ThreadingHTTPServer`** para o MCP: evita dependências pesadas;
  `ThreadingHTTPServer` não bloqueia quando há ligações pendentes (crítico para
  o `/health` responder mesmo sob carga).
- **Obsidian + Dataview**: formato `.md` com frontmatter é indexável, versionável
  e legível; Dataview cria dashboards vivos sem banco de dados.
- **robocopy** para backup: nativo no Windows, suporta retries e exclusões
  (`.obsidian`, `.trash`) sem instalar ferramentas externas.
- **Git**: versiona o vault inteiro, permitindo auditoria e rollback de conhecimento.

## Fluxo de Dados (resumo)
1. Hermes Agent inicia tarefa → `pre_task_hook.ps1` consulta `INDEX_GERAL.md` + MOCs.
2. Tarefa executada; ao terminar, `post_task_hook.ps1` registra no daily note.
3. `Invoke-LightReindexIfNeeded` (nos hooks) força reindex light se última > 4h.
4. `reindex_hybrid.ps1` regenera `INDEX_GERAL.md` e grava `.last_light.txt`.
5. Watcher detecta mudanças e mantém o dashboard coerente entre execuções.

## Ambientes
| Ambiente | Descrição |
|----------|-----------|
| **Local** | Vault + MCP server manual (`python mcp_obsidian_server.py`) |
| **Agendado** | Tarefas Windows disparam reindex/backup/watcher sem interação |
| **Produção** | Vault em uso diário; MCP como serviço de fundo |

## Pipeline CI/CD Sugerido
```yaml
# .github/workflows/validate.yml (sugestão)
name: Validate Vault
on: [push, pull_request]
jobs:
  psscript-analyze:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Syntax check PowerShell
        shell: pwsh
        run: |
          Get-ChildItem 80_SYSTEM -Recurse -Filter *.ps1 |
            ForEach-Object { $null = [scriptblock]::Create((Get-Content $_ -Raw)) }
      - name: Python compile MCP
        run: python -m py_compile 80_SYSTEM/SCRIPTS/mcp_obsidian_server.py
```

## Testes
- **Unitários**: validação de sintaxe dos `.ps1` (parse em `[scriptblock]`).
- **Integração**: subir MCP server e `curl /health`, `/search`, `/stats`.
- **E2E**: rodar `pre_task_hook.ps1` com params PT e confirmar daily note + reindex.
- **Ferramentas**: PSScriptAnalyzer (PowerShell), `pytest` (Python), `curl` (API).
