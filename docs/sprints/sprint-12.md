# Sprint 12 — Hardening v2.0 (Traversal em libs + O(n²) de embeddings + FCS de Órfãos)

**Duração**: contínuo (2026-08-24) | **Estado**: **DONE**
**Tags**: `#sprint` `#seguranca` `#performance` `#fcs` `#qualidade`

## Meta do Sprint (Sprint Goal)

> "O endurecimento de path traversal do S11 cobriu o servidor, mas esqueceu as
> funções de biblioteca que as rotas v2.0 (`/related`, `/compress`) chamam; o
> caminho de embeddings do `/graph` regrediu para O(n²) de I/O; e o painel de
> Órfãos do dashboard estava inútil. Tudo corrigido e provado por testes que
> falham quando a correção é revertida."

O S12 é um sprint de **endurecimento de segunda onda**: aplica o mesmo rigor do S11
aos módulos v2.0 que o S11 não alcançou, e valida o dashboard de fato no browser.

---

## S12-A — Path Traversal em `semantic`/`compress` (continuação do S11)

**Problema.** O S11 endureceu `_vault_path` no `mcp_obsidian_server.py`, mas
`semantic.related_notes`/`suggest` e `compress.compress_note` usavam `_norm_rel`
que **não confinava ao vault**. A rota `/compress?path=../../../x.md` abria
arquivo arbitrário (leak de leitura); `/related` com path traversal também.

**Correção.**
- `semantic.py`: novo `VaultPathError` + `_vault_rel()` (mesmo contrato de
  `mcp_obsidian_server._vault_path`); `_norm_rel` e `related_notes` agora levantam
  `VaultPathError` em traversal.
- `compress.py`: `compress_note` confina via `_vault_rel`.
- `mcp_obsidian_server.py`: rotas `/related` e `/compress` capturam
  `VaultPathError` (por nome de classe) → **400**, igual às rotas de escrita.

**Critérios de Aceitação.**
- **CA-1**: `GET /related?path=../../../Windows/win.ini` → `400`, sem conteúdo externo.
- **CA-2**: `GET /compress?path=../../secret.md` → `400` (ou `404` se não existir),
  sem leitura de arquivo fora do vault.

**Evidência.** `tests/test_security_v2.py` (7 checagens): traversal bloqueado em
`_norm_rel`, `related_notes`, `compress_note`. Reverter o confinamento → teste falha.

## S12-B — `/graph` O(n²) no modo embeddings (regressão do P11)

**Problema.** O P11 consertou o caminho Jaccard de `build_graph` (tokens
pre-computados 1x). Mas o caminho de **embeddings** (quando `OLLAMA_URL` setado)
ainda chamava `related_notes(vault, rel, ...)` **por nota** → re-walk do vault
inteiro para CADA nota = O(n²) de I/O (exatamente o bug do P11, só no branch Ollama).

**Correção.** `graph.build_graph` agora PRE-COMPUTA os embeddings 1x (loop `embeds`)
e faz cosseno pairwise em memória; removido o `related_notes` per-note. Caminho
Jaccard já era O(n); agora embeddings também.

**Evidência.** `tests/test_security_v2.py` checa estaticamente que não há chamada
per-note de `related_notes` e que o grafo gera arestas em modo embeddings stubado.
Reverter → checagem detecta `per-note=True` (teste falharia).

## S12-C — FCS do dashboard: painel de Órfãos

**Defeito achado no FCS (browser).** O painel "Notas Órfãs" mostrava sempre
"nenhuma (grafo totalmente conectado)". Causa: `renderOrphans` contava o grau
**total** do grafo; como arestas `semantic` conectam quase tudo por sobreposição
de tokens, nenhum nó ficava em grau 0 → painel inútil.

**Correção.** `renderOrphans` (web/dashboard.html) agora conta apenas arestas
`kind=='wikilink'` (órfãos estruturais = notas que ninguém linka via `[[...]]`).
Validado no browser: painel passou a listar "• Orfao" num fixture de 4 notas.

**FCS completo (P10–P14).** Servido MCP (porta 8773) + http.server (8783) num
fixture de 4 notas (1 órfão). Via `browser_console`:
- `loadGraph` OK (4 nós / 8 arestas)
- `bfsPath('Nota A','Nota C')` → caminho encontrado
- `focusNode`/`clearFocus` OK
- `search()` → usa `data.hits` (contrato P13 OK; 1 resultado p/ "parcelas")
- `runValidate()` OK · `loadActivity()` OK
- `node --check` do JS inline: OK · tamanho do arquivo: 25003 bytes

**Evidência.** `tests/test_dashboard_orphans.py` (4 checagens): extrai a função
`renderOrphans` DO dashboard.html e roda no node contra grafo fixture; reverter p/
grau total faz o teste falhar (não-tautológico).

---

## Resumo de entregas (S12)

| # | Entrega | Arquivo(s) | Evidência |
|---|---------|-----------|-----------|
| 1 | Traversal confinado em `semantic`/`compress` | `semantic.py`, `compress.py` | `test_security_v2.py` 7/7 |
| 2 | `/graph` embeddings O(n) (sem O(n²)) | `graph.py` | `test_security_v2.py` |
| 3 | Rotas `/related`/`/compress` → 400 em traversal | `mcp_obsidian_server.py` | `test_security_v2.py` |
| 4 | Painel Órfãos por wikilink (FCS) | `web/dashboard.html` | `test_dashboard_orphans.py` 4/4 |
| 5 | FCS browser completo (P10–P14) | — | assertions via `browser_console` |

**Cobertura de testes**: `python tests/run_all.py` → **16/16 suítes verdes**
(era 14/14 no início do S12; +2 suítes novas). CI canônica (GitHub Actions):
5/5 jobs `success` nos commits `6af556e` e `60c1c31`.

[[chronogram]]
[[README]]
