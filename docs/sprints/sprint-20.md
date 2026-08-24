# Sprint 20 — Endpoint `/links` (links de saída) — CONCLUÍDO (2026-08-24)

## Objetivo
Expor os wikilinks de **saída** de uma nota (o inverso de `/backlinks`) e consumi-lo
num painel do dashboard, completando a visão de grafo de conhecimento.

## Entregas

### S20-A — `links()` em `backlinks.py`
`links(path)` lista os wikilinks de saída de uma nota: resolve alias/heading/pasta,
ignora blocos de código e placeholders `${...}`/`{{...}}`, **não conta auto-link**
(`[[Nota]]` dentro de `Nota.md`), e marca `resolved=False` para alvo inexistente.
`links_cached(vault, ttl)` memoiza por mtime/TTL.

### S20-B — Rota `GET /links`
`/links?path=<rel>` → `200 {targets:[...], cached}`; `400` se ausente/traversal;
`404` se a nota não existe. Import atualizado no `mcp_obsidian_server.py`.

### S20-C — Painel "Links de Saída" no dashboard
`web/dashboard.html` (inline único, P12) ganha painel com input/Ver/Enter que chama
`loadLinks()` consumindo `/links` (P13: chaves corretas, `data.targets`). Nós
resolvidos aparecem azul/clicáveis (drill-down); quebrados em vermelho.
`node --check` OK a partir do ROOT; FCS no browser validou `loadLinks`/`loadBacklinks`.

## Testes (registrados em `tests/run_all.py`)
- `tests/test_links.py` — 13 asserts (alias, código, auto-link, quebrado, cache).
- `tests/e2e_links.py` — 10 asserts, **porta livre** `_free_port()` (elimina zumbi,
  P10/P23 — a porta 8906 fixa estava ocupada por servidor estático zumbi).
- `run_all`: **31/31 suítes verdes**, estável em múltiplas execuções.

## Nota de continuação
O painel `/links` no dashboard teve um escape corrompido no JS inline em uma iteração
intermediária; revertido e re-adicionado com `node --check` verde (P27). API testada
e verde independentemente do painel.
