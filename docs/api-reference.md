# API Reference — MCP MEGA BRAIN (porta 8770)

Referência **derivada do código** (`80_SYSTEM/SCRIPTS/mcp_obsidian_server.py`), não de
memória: cada contrato abaixo foi extraído das chamadas `self._send(...)` e
`parse_qs(...)` reais das rotas. Serve para quem consome o MCP (dashboard, Hermes Agent,
scripts) **acertar o nome da chave de primeira** — o P13 registra vários bugs que
passaram no CI só porque o cliente leu `data.results` quando a rota devolve `hits`.

- Servidor: `ThreadingHTTPServer` stdlib, sem dependências obrigatórias.
- Subir: `python 80_SYSTEM/SCRIPTS/mcp_obsidian_server.py --vault <VAULT> --port 8770`
  (env equivalentes: `MCP_HOST`, `MCP_PORT`, `MEGABRAIN_VAULT`, `REDIS_TTL_SECONDS`).
- Toda rota GET é envolvida em `try/except` → erro vira **JSON com status legível**, não
  queda de conexão (P8).
- Rota desconhecida → `404 {"error": "unknown endpoint"}`.

## Convenções

| Convenção | Detalhe |
| --- | --- |
| `path` (query/JSON) | caminho **relativo ao vault** (`10_MEGA_BRAIN/Nota.md`); aceita `/` ou `\` |
| Path traversal | `path` sai do vault → **400** na escrita e nas rotas novas, **404** em `/read` |
| Flag `cached` | rotas cacheadas devolvem `cached: true/false` (invalidação por mtime do vault OU TTL) |
| Cache | memória sempre; Redis **opcional** se `REDIS_URL` + lib `redis` presentes |

---

## Leitura & busca

### `GET /health`
→ `200 {"ok": true, "vault": "<path absoluto>"}`. Use como readiness probe.

### `GET /search?q=<termo>`
→ `200 {"query": ..., "hits": [...], "cache": "memory"|"redis"}`
**Atenção:** a chave é `hits` (NÃO `results`) e cada item traz `ctx` (NÃO `snippet`) — P13.

### `GET /read?path=<rel>`
→ `200 {"path": ..., "content": ...}` · `404` se ausente **ou** se o path escapar do vault.

### `GET /stats`
→ `200 {"total": int, "by_dir": {...}, "cached": bool}`

### `GET /recent?limit=10&days=<n>`
→ `200 {"recent": [{"path","mtime","age_days","type"}], "cached": bool}`
`days` filtra por idade (omitido = qualquer idade).

### `GET /tags?limit=20`
→ `200 {"tags": [{"tag","count"}], "cached": bool}` — ordenado por `count` desc.

### `GET /activity`
→ `200 {"daily_dir": "<path>"|"(ausente)", "by_date": {"YYYY-MM-DD": n}}` (heatmap).

---

## Grafo & conexões

### `GET /graph?k=3&limit=600`
→ `200 {"nodes": [{"id","label","type"}], "edges": [...], "cached": bool}`
`id` = **caminho relativo** da nota (é exatamente o que `/backlinks` e `/links` esperam).
`k` = arestas semânticas por nó. Cacheado por assinatura do vault (P11/P16.2).

### `GET /backlinks?path=<rel>`
→ `200 {"path","title","total","backlinks":[{"path","title","count"}],"cached"}`
Quem **aponta para** a nota. `400` sem `path`/traversal · `404` nota inexistente.
Ignora wikilink em bloco de código, resolve alias/heading/pasta, não conta auto-link.

### `GET /links?path=<rel>`
→ `200 {"path","title","total","links":[{"target","resolved","note","title","count"}],"cached"}`
Para **onde a nota aponta** (`resolved:false` = link quebrado). `400`/`404` idem acima.

### `GET /orphans-in`
→ `200 {"total_notas","total_orfas","by_dir":{"<pasta>":n},"orphans":[{"path","title"}],"cached"}`
Notas que **ninguém linka**. Uma passada O(n) — não confundir com "grau 0" do `/graph`,
que também considera links de saída e arestas semânticas.
`by_dir` agrega as órfãs por pasta-raiz: no vault real são **313 órfãs de 370 notas
(84,6%)**, então a lista crua é inutilizável na UI e o resumo por pasta é o que indica
onde atacar (o dashboard mostra `by_dir` + as 40 primeiras).

---

## Governança & telemetria

### `GET /validate`
→ `200 {"ok","total_notas","by_tipo":{"<tipo>":n},"problemas":[{"tipo","path","msg"}],"cached"}`
Estrutura, frontmatter e `[[links]]` quebrados. Ignora exemplos em blocos de código (P16.3).
`by_tipo` agrega os problemas por tipo (`nota_vazia`, `link_quebrado`, …) na mesma passada,
para o consumidor saber **o que** consertar sem varrer a lista (o dashboard mostra o resumo
+ os 30 primeiros).

### `GET /metrics`
→ `200` **texto Prometheus** (não JSON): `mcp_requests_total`, `mcp_search_total`,
`mcp_search_latency_ms_sum`, `mcp_search_cache_hits|miss`, `mcp_notes_total`,
`mcp_cache_backend`, `mcp_cache_entries`.

---

## v2.0 (IA) — todas com fallback heurístico offline

Sem `OLLAMA_URL`, cada rota usa fallback determinístico (Jaccard/heurística) e continua
100% funcional.

| Rota | Query/Body | Resposta |
| --- | --- | --- |
| `GET /related?path=<rel>&k=5` | `path`, `k` | `200 {"path","related":[{"path","score"}],"cached"}` — notas semanticamente próximas; `cached:true` em hit (S19) |
| `GET /suggest?q=<termo>&k=5` | `q`, `k` | `200 {"query","suggestions":[{"path","score"}],"cached"}` — sugestões para o termo; `cached:true` em hit (S19) |
| `GET /compress?path=<rel>&max_tokens=2000` | `path`, `max_tokens` | texto comprimido; `404` se nota ausente |
| `POST /swarm` | `{"query":..., "agents":[...]}` | saída dos 5 agentes; **bloqueia prompt injection** |
| `POST /reason` | `{"prompt":...}` | raciocínio; **mascara PII** na saída |

---

## Escrita (POST, `Content-Type: application/json`)

Body inválido → `400 {"error": "bad json"}`. Traversal → `400 {"error": "path invalido: ..."}`.

| Rota | Body | Resposta |
| --- | --- | --- |
| `POST /write` | `{"path","content"}` | `{"written": <path>}` |
| `POST /append` | `{"path","content"}` | `{"appended": <path>}` (prefixa `\n`) |
| `POST /link` | `{"note1","note2"}` | `{"linked": ...}` |
| `POST /tag` | `{"note","tags":[...]}` | `{"tagged": ...}` |
| `POST /moc` | `{"topic"}` | `{"moc": ...}` |
| `POST /rename` | `{"path","novo"}` | `{"renamed": <novo>}` |
| `POST /move` | `{"path","destino"}` | `{"moved": <novo>}` |

---

## Checklist ao consumir o MCP (evita os bugs do P13)

1. Confira o **nome exato** da chave nesta tabela antes de escrever `data.X` no JS.
2. Trate `!response.ok` exibindo `data.error` — todas as rotas devolvem `error` em falha.
3. Rotas cacheadas: use `cached` para saber se o dado é fresco.
4. Depois de mexer no dashboard, valide no browser (FCS) — o CI **não** executa o JS inline.
