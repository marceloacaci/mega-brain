# Sprint 21 — Referência de API + teste de contrato não-tautológico — CONCLUÍDO (2026-08-24)

## Objetivo
A doc de API costuma apodrecer silenciosamente e reintroduzir os bugs do P13
(`/search` devolve `hits`, não `results`). Travar a doc com um teste que sobe o MCP
real num fixture e valida, por rota: status, chaves obrigatórias e menção no doc.

## Entregas

### S21-A — `docs/api-reference.md` (25 rotas)
Contrato de **TODAS** as rotas, **DERIVADO do código** (`self._send(...)` e
`parse_qs(...)` reais de `mcp_obsidian_server.py`), não de memória. Documenta query
params, chaves de resposta, status codes, flag `cached` e convenções de `path`/traversal.
Destaca armadilhas P13: `/search`→`hits`+`ctx`; `/metrics`→texto Prometheus;
`graph.nodes[].id` já é o path reutilizável em `/backlinks`/`/links`.

### S21-B — `tests/e2e_api_contract.py`
Guard-rail contra doc mentirosa: valida 12 rotas GET (status, chaves obrigatórias),
menção da rota no doc, `404 unknown endpoint` e traversal (`/read`→404 vs
`/backlinks`|`/links`→400). **Provado não-tautológico**: injetar `hits`→`results` no
server faz o teste acusar 3 FALHAS; restaurar volta a verde.

## Testes (registrados em `tests/run_all.py`)
- `tests/e2e_api_contract.py` — suite S21, valida doc vs MCP real.
- `run_all`: **31/31 → 32/32 suítes verdes** após S21.
- README aponta para `docs/api-reference.md`.
