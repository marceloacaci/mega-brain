# Cronograma Detalhado — MEGA BRAIN

## Gantt Simplificado (Markdown)

| Marco / Fase | M1 | M2 | M3 | M4 | M5 | M6 | Buffer |
|--------------|----|----|----|----|----|----|--------|
| Consolidação (hooks/MCP/dashboard) | ████ | | | | | | |
| Inteligência (preditivo/correlação) | | ████ | | | | | |
| Observabilidade (métricas/alertas) | | | ████ | | | | |
| Extensibilidade (rotas/templates) | | | | ████ | | | |
| Resiliência (failover/integridade) | | | | | ████ | | |
| Polimento (docs/testes) | | | | | | ████ | |
| **Buffer 20%** | | | | | | | █████ |

## Marcos (Milestones)
- **MS1** (fim M1): pipeline de reindex + hooks estável em produção.
- **MS2** (fim M2): modo preditivo sugerindo arquivos.
- **MS3** (fim M3): métricas + alertas operacionais.
- **MS4** (fim M4): novas rotas MCP sob demanda.
- **MS5** (fim M5): failover de backup validado.
- **MS6** (fim M6): documentação + testes E2E.

## Dependências entre marcos
- MS2 só após MS1 (base heurística pronta).
- MS3 após MS1 (dashboard gerado).
- MS5 após MS3 (métricas de integridade).
- MVP testável apenas após **Sprint 2** (hooks + reindex + watcher).

## Buffer de 20%
Reservado para: correção de bugs em hooks, ajustes de Dataview, falhas de
agendamento Windows, e refino de documentação.

## Recursos Alocados
- **1 desenvolvedor full-time** (PowerShell + Python) por 6 meses.
- **1 revisor** (Hermes Agent) contínuo para validação de vault.
- Ambiente: Windows 10/11, Obsidian + Dataview, Python 3.10+, Git.

> Versão renderizável em PlantUML: [`docs/uml/gantt.puml`](../uml/gantt.puml).

[[chronogram]]
