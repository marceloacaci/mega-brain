# Sprint 2 — Observabilidade e Backup
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: métricas, backups rotativos e watcher estáveis.

## Sprint Goal
Garantir **durabilidade e visibilidade** do vault: backups recuperáveis, detecção de mudanças em tempo real e métricas básicas de execução.

## Histórias associadas (do backlog)
- US-4 (backup rotativo) · US-5 (métricas, parcial M3)

## Tasks (engenharia de baixo nível)
| # | Task | Story Points | Dependência |
|---|------|:---:|-------------|
| S2-1 | `backup_vault.ps1` (robocopy) + retention | 5 | — |
| S2-2 | `backup_incremental.ps1` + `restore_backup.ps1` | 5 | S2-1 |
| S2-3 | `watcher.py` (debounce 2s) integrado ao vault | 8 | — |
| S2-4 | Gerar notas de métrica `50_METRICS/YYYY-MM-DDTHHmmss.md` | 3 | S1-6 |
| S2-5 | Registrar tarefas agendadas (install_tasks.ps1) | 3 | S2-1, S2-3 |
| S2-6 | Validação de integridade do vault pós-backup | 5 | S2-2 |

**Total**: ~29 SP.

## Grafo de dependências
```
S2-1 ─► S2-2 ─► S2-6
S2-3 (paralelo)
S1-6 ─► S2-4
S2-1 ─┐
S2-3 ─┴─► S2-5
```

## Critérios de Aceitação (Gherkin)
- **CA-1**: Dado que `backup_vault.ps1` executa, Quando termina, Então gera zip em `D:\Backups\Obsidian\full\AAAA-MM-DD`.
- **CA-2**: Dado que o Watcher está ativo, Quando uma nota muda, Então dispara sincronização em <5s (debounce 2s).
- **CA-3**: Dado que há execuções registradas, Quando leio `50_METRICS/`, Então há ≥1 nota com frontmatter válido.
- **CA-4**: Dado que as tarefas foram instaladas, Quando rodo `Get-ScheduledTask | Where TaskName -like 'MEGA_BRAIN_*'`, Então aparecem como `Ready`.
- **CA-5**: Dado que um backup foi criado, Quando `restore_backup.ps1` roda, Então o vault é restaurado do zip.

[[sprint-3]]

[[sprint-7]]

[[sprint-6]]
