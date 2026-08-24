# Sprint 19 — Cache semântico de `/related` e `/suggest` — CONCLUÍDO (2026-08-24)

## Objetivo
Eliminar re-varredura do vault a cada chamada das rotas semânticas (Jaccard/Ollama),
seguindo o padrão P11-style de cache por assinatura de mtime/TTL já usado em
`/recent`, `/tags`, `/stats`, `/activity`, `/validate`, `/graph`.

## Entregas

### S19-A — `related_cached` / `suggest_cached`
`semantic.py` ganhou `related_cached(vault, path, k, limit, ttl)` e
`suggest_cached(vault, query, k, limit, ttl)`. Invalidam por **assinatura de mtime**
do vault (mtime máx. + contagem de `.md`) OU por TTL; chave por `(path/query, k, limit)`.
As rotas `GET /related` e `GET /suggest` do MCP passaram a usá-los e expõem a flag
`cached` no JSON (contrato preservado: `related`/`suggestions`).

### S19-B — Correção de import faltante (P24)
`semantic.py` usava `time.time()` sem `import time` → `NameError` só em runtime
(rotas cacheadas falhavam ao serem exercidas). Adicionado `import time` no topo.
`py_compile` não pega (sintaxe ok); o E2E da rota pega.

### S19-C — Anti-flake de porta (P5/P23)
`e2e_security.py` usava `PORT = 8903` fixa, que colidia com `e2e_backlinks.py`
(servidores zumbis davam FAIL não-determinístico em `run_all`). Migrado para
`_free_port()` (socket bind 0). `run_all` estável em 3 execuções.

## Testes (registrados em `tests/run_all.py`)
- `tests/test_semantic_cache.py` — 12 asserts (miss→hit, invalidação, chave).
- `tests/e2e_semantic_cache.py` — 8 asserts (rotas `/related`+`/suggest` com MCP real).
- `tests/e2e_security.py` — migrado para `_free_port()`.
- `run_all`: **29/29 suítes verdes** (sobe para 31/31 após S20).

## Documentação
- `docs/api-reference.md` atualizado com o contrato exato de `/related` e `/suggest`
  e a flag `cached` (commit `f7f763b`).
