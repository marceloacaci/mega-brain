# Sprint 8 — M6 Polimento (orquestrador + integração + v1.0-MVP)
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: fechar a qualidade do repo com
orquestração de testes, teste de integração fim-a-fim e documentação de runbook,
entregando o **v1.0-MVP** do MEGA BRAIN.

## Meta do Sprint (Sprint Goal)
"Um contribuidor roda `make test` (ou `python tests/run_all.py`) e obtém o
veredito de toda a pirâmide de testes (unit/integration/e2e) em uma única
chamada; o fluxo fim-a-fim hook→MCP→validate está coberto por E2E."

## Tarefas (baixo nível, Story Points)
| ID | Tarefa | SP | Dependência | Artefato |
|----|--------|:--:|-------------|----------|
| T1 | Criar `tests/run_all.py` orquestrador da suíte | 2 | — | run_all.py |
| T2 | Criar `tests/e2e_integration.py` (hook→MCP→validate) | 3 | T1 | e2e_integration.py |
| T3 | Adicionar `Makefile` com alvos `test/lint/sast/validate` | 1 | T1 | Makefile |
| T4 | Ligar `run_all` ao CI (test-linux) | 1 | T1,T2 | ci-cd.yml |
| T5 | `docs/sprints/sprint-8.md` + chronogram M6 DONE | 2 | T1–T4 | docs |
| T6 | Tag `v1.0.0` (MVP) no GitHub | 1 | T1–T5 | release |

**Dependências**: T2–T4 dependem de T1; T5–T6 dependem de T1–T4.

## Critérios de Aceitação (Gherkin)
```gherkin
Dado que o dev executa `python tests/run_all.py` num checkout limpo
Quando todas as 6 suítes rodam
Então o veredito é "TODAS AS SUÍTES VERDES" e exit code 0

Dado um vault fixture com MOC válido
Quando o pre_task_hook grava o daily note, o MCP /write cria nota e o /validate roda
Então o daily note contém a entrada de início e o /validate retorna ok=true
E o post_task_hook adiciona o resultado no daily note
```

## Escopo entregue
- **Orquestrador** `tests/run_all.py`: roda smoke(8) + debounce(4) + e2e_validate(2)
  + e2e_backup(3) + e2e_hooks(4) + e2e_integration(3) = 24 casos.
- **Integração E2E** `tests/e2e_integration.py`: ciclo fim-a-fim (hook pre →
  MCP write → validate → hook post), resolvendo server/hooks via repo (CI-safe).
- **Makefile**: alvos `test`/`lint`/`sast`/`validate` para o dev local.
- **CI**: step `Suíte completa (run_all)` no job test-linux.

## Status
- Concluído em 2026-08-23. Todas as suítes verdes (run_all 6/6).
- v1.0-MVP atinge: M1 (Bootstrap), M2 (Stack Real), S3 (Hooks), S4 (QA),
  M3 (Observabilidade), M5 (Resiliência), M4 (Extensibilidade), M6 (Polimento).
- Próximo: v2.0 (ver `docs/brainstorm.md`) — LLMs locais, multi-agent swarms,
  compressão de contexto.
