# Sprint 1 — MVP de Automação Estável
**Duração**: 2 semanas | **Objetivo**: pipeline de reindex + hooks funcionando de ponta a ponta.

## Objetivos
- Hooks pré/pós-tarefa confiáveis (falha-segura em arquivo corrompido).
- MCP server 9 rotas operacionais e testáveis.
- Dashboard `INDEX_GERAL.md` gerado por script (sem edição manual).

## Tasks
| # | Task | Estimativa (h) | Dependência |
|---|------|----------------|-------------|
| S1-1 | Templates de hooks `pre_`/`post_task_hook` | 8 | — |
| S1-2 | Função `Invoke-LightReindexIfNeeded` com try/catch | 6 | S1-1 |
| S1-3 | Testar hooks com params PT (caso normal + corrompido) | 4 | S1-2 |
| S1-4 | MCP server: rotas GET/POST | 10 | — |
| S1-5 | Testes de API (`/health`, `/search`, `/stats`) | 5 | S1-4 |
| S1-6 | `reindex_hybrid.ps1` modo light + deep | 12 | — |
| S1-7 | Pipeline CI: syntax check PowerShell + py_compile | 6 | S1-1, S1-4 |

**Total**: ~51h (~1 dev full-time por 1,5 semana com buffer).

## Critérios de Aceitação
- [ ] `pre_task_hook.ps1 -Tarefa t -Projeto X` completa com exit 0.
- [ ] Arquivo `.last_light.txt` corrompido → hook não aborta, força reindex.
- [ ] `curl /health` retorna `{"ok": true}`.
- [ ] `INDEX_GERAL.md` regenerado por `reindex_hybrid.ps1 -Mode deep`.
