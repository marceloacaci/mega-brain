# Sprint 2 — Observabilidade e Backup
**Duração**: 2 semanas | **Objetivo**: métricas, backups rotativos e watcher estáveis.

## Objetivos
- Backup full + incremental com retenção configurável.
- Watcher de mudanças com debounce.
- Métricas enriquecidas em `50_METRICS/`.

## Tasks
| # | Task | Estimativa (h) | Dependência |
|---|------|----------------|-------------|
| S2-1 | `backup_vault.ps1` (robocopy) + retention | 8 | — |
| S2-2 | `backup_incremental.ps1` + `restore_backup.ps1` | 8 | S2-1 |
| S2-3 | `watcher.py` (debounce 2s) integrado ao vault | 10 | — |
| S2-4 | Gerar notas de métrica `50_METRICS/YYYY-MM-DDTHHmmss.md` | 6 | S1-6 |
| S2-5 | Registrar tarefas agendadas (install_tasks.ps1) | 5 | S2-1, S2-3 |
| S2-6 | Validação de integridade do vault pós-backup | 6 | S2-2 |

**Total**: ~43h.

## Critérios de Aceitação
- [ ] `backup_vault.ps1` gera zip em `D:\Backups\Obsidian\full\YYYY-MM-DD`.
- [ ] Watcher detecta mudança e dispara sincronização em <5s.
- [ ] `50_METRICS/` tem pelo menos 1 nota com frontmatter válido.
- [ ] Tarefas `MEGA_BRAIN_*` listadas como `Ready` no Agendador.
