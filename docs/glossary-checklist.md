# Glossário de Termos — MEGA BRAIN

| Termo | Definição |
|-------|-----------|
| **MEGA BRAIN** | O cofre Obsidian do Marcelo, tratado como "segundo cérebro" automatizado. |
| **Segundo Cérebro** | Sistema de PKM onde conhecimento é capturado e correlacionado externamente. |
| **Hook** | Script PowerShell disparado pelo Hermes Agent antes/após cada tarefa. |
| **MCP** | Model Context Protocol — servidor que expõe o vault via rotas HTTP. |
| **Reindex Light** | Regeneração rápida de timestamps/contagens (a cada 6h ou >4h desde última). |
| **Reindex Deep** | Reconstrução completa do dashboard (domingo 23h). |
| **Dataview** | Plugin do Obsidian que renderiza consultas sobre notas com frontmatter. |
| **MOC** | Map of Content — nota índice que liga outras notas por tema. |
| **Watcher** | Processo Python que monitora mudanças no vault (debounce 2s). |
| **Frontmatter** | Bloco YAML no topo de uma nota `.md` (tags, campos estruturados). |
| **Padrão de falha-segura** | try/catch que força reindex se `.last_light.txt` estiver corrompido. |

# Checklist de Qualidade (Revisão de Código)

- [ ] **Cobertura de erros**: todo acesso a `.last_light.txt`/`config.json` está em try/catch.
- [ ] **Parâmetros PT**: hooks usam `-Tarefa -Projeto -Resultado -Resumo`.
- [ ] **Dashboard intacto**: edições de `INDEX_GERAL.md` feitas no script, não à mão.
- [ ] **Dataview válido**: queries apontam para `.md` com frontmatter (nunca `.json`).
- [ ] **MCP testado**: `curl /health` retorna `{"ok": true}`.
- [ ] **Backup testado**: `restore_backup.ps1` consegue recuperar um zip.
- [ ] **Sem bloqueio**: MCP usa `ThreadingHTTPServer` (não single-thread).
- [ ] **Versionado**: mudanças passam por PR para `master`.

[[backlog]]

[[sprint-1]]

[[INTEGRACAO_HERMES_MEGABRAIN]]
