# Sprint 25 — Watcher exclui pastas não-conteúdo + caches no swarm — CONCLUÍDO (2026-08-24)

## Objetivo
Estender a lição do S24 (repo == vault) ao **watcher** de arquivos e ao **swarm**,
evitando re-indexação/varredura desnecessária quando `tests/`/`.git`/`node_modules`
mudam (CI, cache).

## Entregas

### S25-A — `watcher.handle` ignora `VAULT_SKIP_DIRS` (P30)
`80_SYSTEM/MCP/watcher.py`: importa `prune_vault_dirs`/`VAULT_SKIP_DIRS` de
`80_SYSTEM/SCRIPTS/constants` (fail-safe: se não importar, usa no-op/set vazio e
continua). `handle(path)` retorna cedo se `_is_skip_path(path)` (qualquer segmento
em `VAULT_SKIP_DIRS`). O fallback de polling (sem `watchdog`) também aplica
`prune_vault_dirs(dirs)` nos `os.walk`.

### S25-B — `swarm` usa caches memoizados
`80_SYSTEM/SCRIPTS/swarm.py`:
- `_agent_correlator` usa `suggest_cached` (em vez de `suggest`) — memoizado por mtime/TTL.
- `_agent_guardian` usa `validate_cached` (em vez de `validate`) — memoizado.

Evita re-varredura do vault inteiro a cada `/swarm`.

## Testes / Verificação
- `tests/test_watcher_debounce.py` — caso `skip_dirs_not_logged`: paths em `tests/`,
  `node_modules/`, `.git` NÃO são logados (anti-regressão: reverter o `handle` faz
  esses paths aparecerem no log → falha).
- `run_all`: **34/34 suítes verdes**; `py_compile` OK.
- `watchdog` ausente localmente → watcher cai no fallback de polling (tratado).
