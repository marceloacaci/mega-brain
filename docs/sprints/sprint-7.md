# Sprint 7 — M4 Extensibilidade (validação contínua + rota /validate)
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: fechar a extensibilidade do MCP com
validação contínua do vault (frontmatter obrigatório, links quebrados, estrutura) exposta
via nova rota `/validate`, encerrando o Épico E3.

## Sprint Goal
Adicionar validação contínua do cofre como recurso de primeira classe do MCP: um módulo
`validate_vault.py` (stdlib) e a rota `GET /validate` que reporta problemas estruturais.
Isso habilita o watcher/hooks e o CI a detectarem degradação de qualidade sem abrir o Obsidian.

## Histórias associadas (do backlog)
- E3 (Inteligência & Extensibilidade): fechar "validação contínua" (gap de M4 ~40%).
- US-7 (rotas rename/move) já DONE em S3; este sprint cobre a validação.

## Tasks (engenharia de baixo nível)
| # | Task | Story Points | Dependência |
|---|------|:---:|-------------|
| S7-1 | `validate_vault.py`: varredura de notas .md (stdlib) | 2 | — |
| S7-2 | Detecção: estrutura obrigatória + notas vazias | 2 | S7-1 |
| S7-3 | Detecção: frontmatter MOC (`tipo: moc`, `tags`) | 2 | S7-1 |
| S7-4 | Detecção: links `[[...]]` quebrados (alvo inexistente) | 3 | S7-1 |
| S7-5 | Rota `GET /validate` no MCP (importa validate_vault) | 2 | S7-2, S7-3, S7-4 |
| S7-6 | `tests/e2e_validate.py` (vault íntegro + link quebrado) | 3 | S7-5 |
| S7-7 | CI: rodar `e2e_validate.py` no job test-linux | 1 | S7-6 |

**Total**: ~15 SP.

## Grafo de dependências
```
S7-1 ─► S7-2 ─┐
S7-1 ─► S7-3 ─┤
S7-1 ─► S7-4 ─┴─► S7-5 ─► S7-6 ─► S7-7
```

## Critérios de Aceitação (Gherkin)
- **CA-1**: Dado um vault íntegro, Quando `GET /validate`, Então retorna `ok: true` e `total_notas >= 1`.
- **CA-2**: Dado uma nota com `[[NotaInexistente]]`, Quando `GET /validate`, Então retorna `ok: false` e um problema `tipo: link_quebrado`.
- **CA-3**: Dado uma pasta obrigatória ausente, Quando `GET /validate`, Então lista `tipo: estrutura`.
- **CA-4**: Dado o CI, Quando `e2e_validate.py` roda, Então PASS (2/2).

## Status de execução (2026-08-23)
- [x] S7-1..S7-5 `validate_vault.py` + rota `/validate` no MCP
- [x] S7-6 `tests/e2e_validate.py` → 2/2 PASS
- [x] S7-7 CI estendido (test-linux roda `e2e_validate.py`)
- **Suíte local**: smoke 8/8 + e2e_validate 2/2 + debounce 4/4 + e2e backup 3/3 + e2e hooks 4/4

[[sprint-6]]

[[sprint-3]]

[[sprint-4]]
