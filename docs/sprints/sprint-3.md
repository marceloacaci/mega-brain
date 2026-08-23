# Sprint 3 — Inteligência e Extensibilidade
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: modos preditivo/correlacionador + novas rotas MCP.

## Sprint Goal
Tornar o cérebro **proativo**: sugerir contexto antes da tarefa e expor operações de reorganização do vault via MCP.

## Histórias associadas (do backlog)
- US-6 (modo preditivo) · US-7 (rotas rename/move)

## Tasks (engenharia de baixo nível)
| # | Task | Story Points | Dependência |
|---|------|:---:|-------------|
| S3-1 | Modo preditivo (heurística de histórico) | 8 | S1-2 |
| S3-2 | Correlação leve entre notas (links sugeridos) | 5 | S3-1 |
| S3-3 | Nova rota MCP `rename` + `move` | 5 | S1-4 |
| S3-4 | Templates de captura em `80_SYSTEM/TEMPLATES/` | 3 | — |
| S3-5 | Documentação de runbook (90_ALERTS) | 2 | S2-2 |

**Total**: ~23 SP.

## Grafo de dependências
```
S1-2 ─► S3-1 ─► S3-2
S1-4 ─► S3-3
S2-2 ─► S3-5
S3-4 (paralelo)
```

## Critérios de Aceitação (Gherkin)
- **CA-1**: Dado que há histórico no Projeto X, Quando `pre_task_hook.ps1` roda no modo preditivo, Então ele sugere um arquivo relevante antes da tarefa.
- **CA-2**: Dado que `40_AREAS/old.md` existe, Quando `megabrain.ps1 rename old.md new.md`, Então o vault reflete `40_AREAS/new.md` com o mesmo conteúdo.
- **CA-3**: Dado que um template existe, Quando aplicado via `post_task_hook`, Então a nota é criada sem erro e segue o schema.
- **CA-4**: Dado que `90_ALERTS/runbook.md` existe, Quando um alerta de integridade dispara, Então o runbook descreve o passo de recuperação.
