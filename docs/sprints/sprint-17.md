# Sprint 17 — Backlinks (`/backlinks`) — CONCLUÍDO (2026-08-24)

## Objetivo
Responder, via MCP e no dashboard, a pergunta mais usada de um segundo cérebro depois
da busca: **"quem aponta para esta nota?"**. O `/graph` já existia, mas devolve o grafo
INTEIRO (custoso) quando o usuário quer apenas a vizinhança de *entrada* de UMA nota.

## Entregas

### `80_SYSTEM/SCRIPTS/backlinks.py` (novo)
| Função | Contrato |
| --- | --- |
| `backlinks(vault, path, limit=NOTE_LIMIT)` | `{path, title, total, backlinks:[{path,title,count}]}` |
| `backlinks_cached(vault, path, limit, ttl=60)` | `(dict, foi_cacheado)` — invalida por mtime do vault OU TTL |

Regras de resolução de wikilink (espelham `graph.py` + P16.3):
- alias `[[Nota|apelido]]`, heading `[[Nota#secao]]`, prefixo de pasta `[[10_MEGA_BRAIN/Nota]]`
  e sufixo `.md` são todos normalizados para o mesmo alvo;
- casamento por **stem** (nome do arquivo) OU **título** (`# H1`);
- `_strip_code()` remove blocos ``` e `` `inline` `` — wikilink em código é EXEMPLO de
  documentação, não link real (foi a causa dos falsos positivos do `/validate` em S11);
- placeholders `${...}` / `{{...}}` (Excalidraw/templates) ignorados;
- auto-link não conta; ordenação `count` desc, depois `path` asc.

Segurança: `path` vem do usuário → `vault_path()` (`VaultPathError` em traversal — P16).
Cache: thread-safe, chave `(vault, path, limit)`, teto de 64 entradas (limpa ao encher).

### Rota `GET /backlinks?path=<rel>` (MCP)
| Situação | Status |
| --- | --- |
| OK | `200` + payload com flag `cached` |
| `path` ausente / traversal | `400` |
| nota inexistente | `404` |
| erro interno | `500` com mensagem (try/except por rota — P8) |

### Dashboard (`web/dashboard.html` — arquivo ÚNICO inline, P12)
Painel **"Backlinks (quem aponta para a nota)"**: input (Enter funciona) + botão *Ver*,
lista as fontes com contagem `N×`, e **drill-down** — clicar numa fonte carrega os
backlinks dela. Erros 400/404 exibem `data.error` em vez de falhar silenciosamente.

### Testes (registrados em `tests/run_all.py`)
- `tests/test_backlinks.py` — 17 asserts: alias, heading, pasta, código NÃO conta,
  placeholder, auto-link, ordenação, `FileNotFoundError`, `VaultPathError`,
  cache miss → hit → invalidação por escrita.
- `tests/e2e_backlinks.py` — 11 asserts na rota real (porta fixa 8903, stderr visível P7,
  server repo-relative P5): payload, cache, 400 sem path, 404, traversal nunca 200.

**Suíte: 25/25 → 27/27 verdes.**

## Verificação de fato (FCS — P10/P13/P14)
1. `node --check` do `<script>` inline extraído, rodado a partir do ROOT do repo: `rc=0`.
2. Tamanho real no disco conferido após cada patch (`wc -c` = 30862) e tail intacto — sem
   versão stale (P14).
3. Browser com vault fixture temp (4 notas, 1 órfã), MCP 8905 + `http.server 8916`:
   resultados corretos, nota isolada, 404, traversal (400), path vazio e drill-down —
   todos validados via `browser_console`; nenhum erro JS novo.

## Pitfall novo descoberto
`python -m http.server <porta>` **sem `--bind 127.0.0.1`** subiu IPv6-only nesta máquina
(`Serving HTTP on :: port ...`), e o browser/curl em `http://127.0.0.1:<porta>` recebia
`ERR_EMPTY_RESPONSE`. Ao servir o dashboard para FCS, **sempre** use
`python -m http.server 8916 --bind 127.0.0.1`.

## Próximos passos sugeridos
- Ligar o painel de backlinks ao clique nos nós do grafo (hoje é drill-down por lista).
- Endpoint `/orphans-in` (notas sem nenhum backlink) reusando `backlinks.py`.
- Cachear `/stats`, seguindo o mesmo padrão de invalidação por mtime.
