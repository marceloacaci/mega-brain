# Sprint 3 — Inteligência e Extensibilidade
**Duração**: 2 semanas | **Objetivo**: modos preditivo/correlacionador + novas rotas MCP.

## Objetivos
- Modo preditivo sugere arquivos com base em histórico.
- Expansão de rotas MCP (ex: `rename`, `move`) sob demanda.
- Templates de captura reutilizáveis.

## Tasks
| # | Task | Estimativa (h) | Dependência |
|---|------|----------------|-------------|
| S3-1 | Modo preditivo (heurística de histórico) | 12 | S1-2 |
| S3-2 | Correlação leve entre notas (links sugeridos) | 10 | S3-1 |
| S3-3 | Nova rota MCP `rename` + `move` | 8 | S1-4 |
| S3-4 | Templates de captura em `80_SYSTEM/TEMPLATES/` | 6 | — |
| S3-5 | Documentação de runbook (90_ALERTS) | 4 | S2-2 |

**Total**: ~40h.

## Critérios de Aceitação
- [ ] Hook sugere arquivo relevante antes da tarefa (modo preditivo).
- [ ] `megabrain.ps1 rename <n1> <n2>` funciona contra o vault real.
- [ ] Templates aplicáveis via `post_task_hook` sem erro.
