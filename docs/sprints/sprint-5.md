# Sprint 5 — M3 Observabilidade (métricas + cache)
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: tornar o MCP observável (métricas Prometheus) e reduzir I/O de `/search` via cache TTL.

## Sprint Goal
Expor telemetria do MCP (latência/throughput de `/search`, cache hit/miss) em formato
Prometheus e adicionar cache de consultas com TTL — mantendo fallback funcional
sem dependências obrigatórias (princípio stdlib do repo).

## Histórias associadas (do backlog)
- US-5 (métricas Prometheus) · US-9 (semântica v2.0, parcial: cache de I/O)

## Tasks (engenharia de baixo nível)
| # | Task | Story Points | Dependência |
|---|------|:---:|-------------|
| S5-1 | Endpoint `/metrics` no MCP (texto Prometheus) | 3 | — |
| S5-2 | Contadores thread-safe (requests, search, latência, cache) | 3 | S5-1 |
| S5-3 | Cache de `/search` com TTL em memória (fallback) | 3 | S5-2 |
| S5-4 | Redis opcional (se `REDIS_URL` + lib) como backend de cache | 2 | S5-3 |
| S5-5 | `docker-compose.yml` já tem redis/prom/grafana — validar wiring | 2 | S5-1, S5-4 |
| S5-6 | Testes: `/metrics` + cache hit no `smoke_test.py` | 3 | S5-1, S5-3 |

**Total**: ~16 SP.

## Grafo de dependências
```
S5-1 ─► S5-2 ─► S5-3 ─► S5-4
S5-1 ─┐
S5-4 ─┴─► S5-5
S5-1 ─┐
S5-3 ─┴─► S5-6
```

## Critérios de Aceitação (Gherkin)
- **CA-1**: Dado que o MCP está rodando, Quando `GET /metrics`, Então retorna texto Prometheus com `mcp_requests_total`, `mcp_search_total`, `mcp_search_latency_ms_sum`.
- **CA-2**: Dado que `PROMETHEUS_ENABLED`/env injeta `REDIS_TTL_SECONDS`, Quando `/search` é chamado 2x, Então a 2a vem do cache (campo `cache: memory|redis`) sem erro.
- **CA-3**: Dado que `REDIS_URL` está setado e a lib `redis` existe, Quando `/search` roda, Então o backend de cache é `redis` (senão `memory`).
- **CA-4**: Dado que o `smoke_test.py` roda, Quando valida `/metrics` e `search_cache`, Então ambos PASS.
- **CA-5**: Dado que não há Redis, Quando o server sobe, Então o cache em memória funciona (fallback, sem quebrar).

## Status de execução (2026-08-23)
- [x] S5-1 `/metrics` implementado (Prometheus text)
- [x] S5-2 contadores thread-safe (`_METRICS` + lock)
- [x] S5-3 cache TTL em memória (`_CACHE` + `_CACHE_TTL`)
- [x] S5-4 Redis opcional (`_try_redis`)
- [x] S5-5 compose já tem os serviços; `main()` lê `MCP_HOST`/`MCP_PORT`/`REDIS_TTL_SECONDS`
- [x] S5-6 `smoke_test.py` estendido (metrics + search_cache) → 8/8 PASS
- **Suíte**: smoke 8/8 + debounce 4/4 + e2e 4/4 (ver Sprint 4)
