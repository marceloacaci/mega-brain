# Sprint 4 — QA & Consolidação (M6 parcial / fundacao de confianca)
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: fechar os gaps de qualidade antes de evoluir para M3 (Observabilidade).

## Sprint Goal
Ter uma **suíte de testes automatizada verde** que exercita o pipeline real (hooks + watcher + MCP), com cobertura de falha-segura, para que qualquer evolução futura seja segura.

## Histórias associadas (do backlog)
- US-10 (smoke test contribuidor) · US-1/US-2 (registro + MCP) · qualidade (`docs/quality.md`)

## Tasks (engenharia de baixo nível)
| # | Task | Story Points | Dependência |
|---|------|:---:|-------------|
| S4-1 | Corrigir debounce de 2s na via watchdog do `watcher.py` | 2 | — |
| S4-2 | `tests/test_watcher_debounce.py` (unitário, stdlib) | 3 | S4-1 |
| S4-3 | `tests/e2e_hooks.py` (pre/post com params PT num fixture) | 5 | S1-1, S1-2 |
| S4-4 | Validar fallback falha-segura (config corrompido) no E2E | 3 | S4-3 |
| S4-5 | Estender `ci-cd.yml` para rodar smoke + debounce (Linux) + E2E (Windows) | 3 | S4-2, S4-3 |
| S4-6 | Documentar cobertura e portão de qualidade em `docs/quality.md` | 2 | S4-5 |

**Total**: ~18 SP.

## Grafo de dependências
```
S4-1 ─► S4-2
S1-1 ─┐
S1-2 ─┴─► S4-3 ─► S4-4
S4-2 ─┐
S4-3 ─┴─► S4-5 ─► S4-6
```

## Critérios de Aceitação (Gherkin)
- **CA-1**: Dado que o watcher está ativo, Quando a mesma nota muda 2x em <2s, Então apenas 1 evento é registrado (debounce).
- **CA-2**: Dado que `pre_task_hook.ps1 -Tarefa t -Projeto X` roda, Quando termina, Então daily note recebe linha "Início" e exit 0.
- **CA-3**: Dado que `post_task_hook.ps1` roda, Quando termina, Então daily note recebe linha de execução (✅) e exit 0.
- **CA-4**: Dado que `.last_light.txt` está ausente, Quando `pre_task_hook` roda, Então o timestamp é criado (reindex light disparado).
- **CA-5**: Dado que `config.json` está corrompido, Quando o hook roda, Então ele NÃO quebra (exit 0, falha-segura).
- **CA-6**: Dado que o CI roda, Quando o PR é aberto, Então smoke + debounce (Linux) + E2E (Windows) passam.

## Status de execução (2026-08-23)
- [x] S4-1 debounce corrigido em `watcher.py`
- [x] S4-2 `test_watcher_debounce.py` → 4/4 PASS
- [x] S4-3 `e2e_hooks.py` → 4/4 PASS
- [x] S4-4 fallback corrompido validado (PASS)
- [x] S4-5 `ci-cd.yml` estendido (test-linux + test-windows)
- [x] S4-6 qualidade documentada
- **Suíte total verde**: smoke MCP 6/6 + debounce 4/4 + E2E hooks 4/4
