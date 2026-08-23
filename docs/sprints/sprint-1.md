# Sprint 1 — MVP de Automação Estável
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: pipeline de reindex + hooks funcionando de ponta a ponta.

## Sprint Goal
Entregar um pipeline de automação **falha-seguro** (hooks + MCP 9 rotas + dashboard gerado) onde qualquer tarefa do Hermes atualiza o cérebro sem intervenção manual.

## Histórias associadas (do backlog)
- US-1 (registro em daily note) · US-2 (MCP HTTP) · US-3 (dashboard gerado por script)

## Tasks (engenharia de baixo nível)
| # | Task | Story Points | Dependência |
|---|------|:---:|-------------|
| S1-1 | Templates de hooks `pre_`/`post_task_hook` | 5 | — |
| S1-2 | Função `Invoke-LightReindexIfNeeded` com try/catch | 3 | S1-1 |
| S1-3 | Testar hooks com params PT (caso normal + corrompido) | 2 | S1-2 |
| S1-4 | MCP server: rotas GET/POST (health/search/read/write/append/link/tag/moc) | 8 | — |
| S1-5 | Testes de API (`/health`, `/search`, `/stats`, `/read`) | 3 | S1-4 |
| S1-6 | `reindex_hybrid.ps1` modo light + deep | 8 | — |
| S1-7 | Pipeline CI: PSScriptAnalyzer + py_compile + smoke test | 5 | S1-1, S1-4 |

**Total**: ~34 SP (1 dev full-time, ~2 semanas com buffer de 20%).

## Grafo de dependências
```
S1-1 ─► S1-2 ─► S1-3
S1-4 ─► S1-5
S1-6 (paralelo a S1-1/S1-4)
S1-1 ─┐
S1-4 ─┴─► S1-7
```

## Critérios de Aceitação (Gherkin)
- **CA-1**: Dado que `pre_task_hook.ps1 -Tarefa t -Projeto X` é executado, Quando o hook termina, Então ele completa com exit 0 e registra no daily note.
- **CA-2**: Dado que `.last_light.txt` está corrompido, Quando `Invoke-LightReindexIfNeeded` roda, Então ele força reindex (não aborta).
- **CA-3**: Dado que o MCP está rodando, Quando `curl /health`, Então retorna `{"ok": true}`.
- **CA-4**: Dado que `reindex_hybrid.ps1 -Mode deep` rodou, Quando leio `INDEX_GERAL.md`, Então ele foi regenerado por script (sem edição manual).
- **CA-5**: Dado que o CI roda, Quando o PR é aberto, Então PSScriptAnalyzer + py_compile + smoke_test passam.

[[sprint-4]]

[[sprint-3]]

[[sprint-6]]
