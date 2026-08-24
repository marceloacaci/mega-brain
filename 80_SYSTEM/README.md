# 📁 80_SYSTEM

> Configurações, scripts, templates e o MCP server do MEGA BRAIN.
> Código de automação versionado em git (ver `docs/chronogram.md` e `README.md`).

## SCRIPTS (Python 3.11, stdlib — sem deps obrigatórias)

| Script | Papel | Rotas/Contratos |
|--------|-------|-----------------|
| `mcp_obsidian_server.py` | MCP HTTP (`ThreadingHTTPServer`, porta 8770). Expõe o vault como JSON. | `/health /search /metrics /validate /related /suggest /compress /graph /read` + POST `/write /append /link /tag /moc /rename /move /swarm /reason` |
| `graph.py` | Grafo de conhecimento (nós=notas, arestas=wikilinks + Jaccard semântico). | `build_graph()`, `build_graph_cached()` (cache por mtime — **P11**) |
| `semantic.py` | Correlação semântica (`related_notes`, `suggest`). Ollama embeddings opcional + fallback Jaccard. | `_norm_rel()` (normalização cross-platform — **P9**) |
| `compress.py` | Compressão de contexto (`compress_text`, `estimate_tokens`). | `compress_note()` (normalização de path — **P9**) |
| `swarm.py` | Multi-Agent Swarm leve (5 agentes puros: indexer/correlator/guardian/predictive/metric). | `run_swarm()` (aplica `guardrails_injection`) |
| `llm_local.py` | Raciocínio local via Ollama (fallback heurístico). | `reason()` (aplica `mask_pii` antes de LLM — S10-C) |
| `governance.py` | Guardrails de IA (OWASP LLM): Prompt Injection + PII. | `guardrails_injection()`, `mask_pii()`, `sanitize_input()` |
| `validate_vault.py` | Validação contínua (estrutura/frontmatter/links quebrados). | `validate()` |

## Princípios de robustez (pitfalls P1–P14)

- **P8 — `do_GET` nunca derruba conexão**: todo o corpo de `do_GET` está
  envolto em `try/except` que retorna `500 {"error": ...}` legível. Cada rota
  v2.0 (`/related /suggest /compress /graph /activity`) tem seu próprio try/except.
- **P9 — normalização de path com `/`**: `semantic._norm_rel`, `compress.compress_note`
  e `mcp._vault_path` normalizam separadores (`\`→`/`→`os.sep`) antes de `os.path.join`,
  evitando "not found" no Windows.
- **P11 — `/graph` O(n²) mitigado por cache**: `build_graph_cached()` memoiza o
  grafo e o invalida por assinatura do vault (mtime máximo + contagem de notas) ou
  TTL (reusa `_CACHE_TTL`). `/graph?k=N` gera caches distintos por `k`. Acelera o
  dashboard (grafo snappy) e evita recomputar Jaccard a cada requisição.
- **P6 — `run_all.py` pula e2e_backup/e2e_hooks sob `GITHUB_ACTIONS`** (job Windows cobre).
- **P12 — `web/dashboard.html` é ARQUIVO ÚNICO inline** (HTML+CSS+JS). NÃO fatiar em
  `dashboard.js`/`dashboard.css` — quebra `e2e_dashboard.py`. (Os arquivos split
  órfãos foram removidos: só o inline vale.)
- **P13 — JS do dashboard NÃO tem lint estático no CI**: exige verificação FCS no
  browser (`browser_console`) após qualquer edição.
- **P14 — writes grandes**: sempre checar `wc -c` + tail após `write_file`/`patch`.

## Sprint 11 — Hardening (segurança, performance, sinal)

Detalhe completo em `docs/sprints/sprint-11.md`.

- **Segurança (crítico)**: `_vault_path` agora **confina o path ao vault**. Antes,
  `path=../secret.md` permitia LEITURA (`GET /read`) e ESCRITA (`POST /write`)
  fora do vault — afetava `/read /write /append /link /tag /rename /move`.
  Nova exceção `VaultPathError` → `404` na leitura, **400** na escrita.
  Coberto por `tests/e2e_security.py` (validado contra a regressão reinjetada).
- **Performance `/graph`**: `build_graph` pré-computa tokens 1x por nota em vez de
  chamar `related_notes` por nota (que re-lia o vault inteiro a cada chamada).
  Vault real de 180 notas: **~60 s → 0,36 s**. Wikilinks agora usam índice dict.
- **Sinal do `/validate`**: ignora wikilinks em blocos/inline de código e
  placeholders de template, resolve `[[pasta/Nota]]` pelo basename e deduplica.
  Vault real: **15 → 4 problemas** (só os reais). Coberto por
  `tests/test_validate_links.py`; `e2e_validate.py` segue detectando links quebrados.
- **Menos I/O**: `validate_vault` faz 1 `os.walk` (era 2); `swarm._count_md`
  unifica as varreduras de `_agent_indexer` + `_agent_metric` (2 → 1).

## Como rodar / testar

```powershell
# Subir o MCP (porta padrão 8770)
python "80_SYSTEM/SCRIPTS/mcp_obsidian_server.py" --port 8770
# Verificar saúde
curl http://localhost:8770/health

# Suíte completa de testes (12/12 suítes verdes localmente)
python tests/run_all.py
```

CI canônico: `gh run` em `marceloacaci/mega-brain` (lint + SAST + test-linux + test-windows + build).
