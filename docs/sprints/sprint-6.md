# Sprint 6 — M5 Resiliência (failover de backup + integridade)
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: garantir que o backup nunca fique sem destino e que o cofre seja validável quanto a corrupção/perda.

## Sprint Goal
Implementar failover de backup para 2º destino (quando o primário falha) e uma
rotina de verificação de integridade do cofre (estrutura obrigatória, notas
corrompidas/0 bytes) e do backup (robocopy /L comparando vs vault). Stack preservado:
PowerShell 7 + robocopy (sem dependências externas).

## Histórias associadas (do backlog)
- US-7 (failover 2º destino de backup)
- US-8 (verificação de integridade do vault)

## Tasks (engenharia de baixo nível)
| # | Task | Story Points | Dependência |
|---|------|:---:|-------------|
| S6-1 | `backup_vault.ps1`: ler `backup.root` e `backup.secondary_root` do config | 2 | — |
| S6-2 | `backup_vault.ps1`: função `Invoke-BackupTo` + validação de drive acessível | 3 | S6-1 |
| S6-3 | `backup_vault.ps1`: failover primário→secundário + registro em `backup_history.log` | 3 | S6-2 |
| S6-4 | `verify_integrity.ps1`: estrutura obrigatória + notas 0 bytes/ilegíveis | 3 | — |
| S6-5 | `verify_integrity.ps1`: integridade de backup via robocopy /L | 2 | S6-4 |
| S6-6 | `config.json`: campo `secondary_root` | 1 | S6-1 |
| S6-7 | `tests/e2e_backup.py`: failover + integridade (fixtures tmp, pwsh) | 3 | S6-3, S6-5 |
| S6-8 | CI: rodar `e2e_backup.py` no job test-windows | 1 | S6-7 |

**Total**: ~18 SP.

## Grafo de dependências
```
S6-1 ─► S6-2 ─► S6-3 ─► S6-8
S6-4 ─► S6-5 ─┐
S6-1 ─┐        ├─► S6-7 ─► S6-8
S6-6 ─┘        ┘
```

## Critérios de Aceitação (Gherkin)
- **CA-1 (failover)**: Dado que `backup.root` aponta para drive inexistente e `secondary_root` é válido, Quando `backup_vault.ps1` roda, Então o backup é gravado no secundário e `backup_history.log` registra o destino usado.
- **CA-2 (sem 2º destino)**: Dado que ambos falham ou não há `secondary_root`, Quando roda, Então retorna exit 1 (falha explícita, não silenciosa).
- **CA-3 (integridade ok)**: Dado um cofre com estrutura completa e notas válidas, Quando `verify_integrity.ps1` roda, Então retorna exit 0.
- **CA-4 (integridade corrompida)**: Dado uma nota de 0 bytes, Quando `verify_integrity.ps1` roda, Então retorna exit 1 e lista o problema.
- **CA-5 (CI)**: Dado o pipeline, Quando `e2e_backup.py` roda no test-windows, Então PASS.

## Status de execução (2026-08-23)
- [x] S6-1/S6-2/S6-3 `backup_vault.ps1` com failover + validação de drive
- [x] S6-4/S6-5 `verify_integrity.ps1` (estrutura + corrupção + backup /L)
- [x] S6-6 `config.json` com `secondary_root`
- [x] S6-7 `tests/e2e_backup.py` → 3/3 PASS
- [x] S6-8 CI estendido (test-windows roda `e2e_backup.py`)
- **Suíte local**: smoke 8/8 + debounce 4/4 + e2e hooks 4/4 + e2e backup 3/3

[[sprint-7]]

[[sprint-4]]

[[sprint-1]]
