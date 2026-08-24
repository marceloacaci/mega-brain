# Sprint 22 — Cache de `/activity` (heatmap) — CONCLUÍDO (2026-08-24)

## Objetivo
Fechar a cobertura de cache de **todas** as rotas de leitura de polling do dashboard:
`/recent`, `/tags`, `/stats`, `/validate`, `/graph` já eram cacheados; `/activity`
re-varria `20_DAILY_NOTES` a cada chamada.

## Entregas

### S22-A — `activity_cached`
`activity.py` ganhou `activity_counts(vault)` (pura: conta notas por data em
`20_DAILY_NOTES`) e `activity_cached(vault, ttl)` (mtime/TTL, mesmo padrão S14/S15).
A rota `GET /activity` do MCP consome `activity_cached` e expõe a flag `cached`.
Contrato `{by_date, total}` preservado.

### S22-B — Integração com S21
A doc `api-reference.md` e a suite de contrato S21 foram estendidas para cobrir
`/activity` (chaves `by_date`/`total`).

## Testes (registrados em `tests/run_all.py`)
- `tests/test_activity_cache.py` — 9 asserts (miss→hit→invalidação, `ttl=0`, ausente).
- `run_all`: **33/33 suítes verdes** (inclui S21 `e2e_api_contract` do worker irmão).
