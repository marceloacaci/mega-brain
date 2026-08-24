# Sprint 13 — Consolidação de Código & Dívida de Refatoração (S12 debt)

**Duração**: contínuo (2026-08-24, worker de continuação) | **Estado**: **DONE**
**Tags**: `#sprint` `#refactor` `#consolidacao` `#qualidade`

## Meta do Sprint (Sprint Goal)

> "A auditoria S11/S12 achou e corrigiu defeitos reais, mas deixou dívida estrutural:
> o teto de notas (600) era um magic number duplicado em semantic+graph; o guard de
> path-traversal (VaultPathError) era copiado 4x; e o /stats do MCP re-walkava o vault
> duplicando swarm._count_md. Consolidar sem mudar nenhum contrato de rota/JSON."

## S13-A — Constante `NOTE_LIMIT` compartilhada

**Problema.** O teto de varredura (600) vivia hardcoded em `semantic._vault_notes`,
`related_notes`, `suggest`, `graph.build_graph`, `_iter_notes`, `_vault_signature`.
Mudar um sem o outro reintroduzia a inconsistência de arestas semanticas (flag P11).

**Correção.** Novo `80_SYSTEM/SCRIPTS/constants.py::NOTE_LIMIT = 600`. `semantic` e
`graph` importam e usam nos defaults. Fonte única de verdade.

**Evidência.** `tests/test_note_limit_consistency.py` (4 checagens) + novo
`tests/test_shared_modules.py` checam `constants.NOTE_LIMIT` e os `__defaults__`.

## S13-B — Guard de path traversal centralizado (`vault_path.py`)

**Problema.** `VaultPathError` + bloco de confinamento copiado em
`mcp_obsidian_server`, `semantic`, `predictive` (e compress delegava). Drift de risco.

**Correção.** Novo `80_SYSTEM/SCRIPTS/vault_path.py` com a única implementação.
`mcp_obsidian_server._vault_path(rel)` e `predictive._vault_path(rel)` viram wrappers
de 1 linha sobre `vault_path.vault_path(VAULT, rel)`; `semantic._vault_rel` delega.
A **classe VaultPathError mantém o nome** (contrato de `type(e).__name__ == "VaultPathError"`
em e2e_security / test_security_v2 / test_predictive_security) — importada, não redefinida.

**Evidência.** `tests/test_shared_modules.py` checa confinamento + nome preservado.
`tests/test_security_v2.py`, `e2e_security.py`, `test_predictive_security.py`
continuam verdes (não-tautológicos: reverter confinamento → falham).

## S13-C — Contagem de notas centralizada (`vault_stats.py`)

**Problema.** A rota `/stats` do MCP fazia seu próprio `os.walk` do vault inteiro,
duplicando `swarm._count_md` (outra varredura). Drift de contagem possível.

**Correção.** Novo `80_SYSTEM/SCRIPTS/vault_stats.py::count_by_dir(vault)` →
`(total, by_dir)` numa única passada. `swarm._count_md` e a rota `/stats` delegam a ele.

**Evidência.** `tests/test_shared_modules.py` checa `count_by_dir == swarm._count_md`
(num total e `by_dir`) num fixture de 4 notas.

## S13-D — Remoção de código morto

- `graph._match_rel` (nunca referenciado após o lookup dict O(1) do P11) — removido.
- `llm_local._HEAD_RE/_LINK_RE/_TAG_RE` (compiladas, nunca usadas) — removidas.
- `compress._is_tag` (nunca usada) — removida.

## FCS do dashboard (P10–P14) revalidado

Servido MCP (porta 40150) + http.server (40151) num fixture de 6 notas (1 órfão).
Via `browser_console`: `loadGraph` (6 nós/7 arestas) · `renderOrphans` (3: 2 daily + Orfão)
· `bfsPath('Nota A','Nota C')` OK · `focusNode`/`clearFocus` OK · `search('alpha')` →
1 hit real (`data.hits`, contrato P13) · `loadActivity` (2 células) · `runValidate`
("vault íntegro ✓", 0 problemas). `node --check` inline OK; `wc -c dashboard.html=25003`,
termina em `</html>` (P14 OK). Sem erros runtime.

## Resumo de entregas (S13)

| # | Entrega | Arquivo(s) | Evidência |
|---|---------|-----------|-----------|
| 1 | `NOTE_LIMIT` único | `constants.py`, `semantic.py`, `graph.py` | `test_note_limit_consistency` + `test_shared_modules` |
| 2 | `vault_path` único | `vault_path.py`, server/semantic/predictive | `test_shared_modules` + testes S11/S12 mantidos |
| 3 | `count_by_dir` único | `vault_stats.py`, swarm, `/stats` | `test_shared_modules` |
| 4 | Código morto removido | `graph`, `llm_local`, `compress` | py_compile + run_all verde |

**Cobertura de testes**: `python tests/run_all.py` → **19/19 suítes verdes**
(era 18/18; +1 `test_shared_modules.py`). CI canônica (GitHub Actions) a confirmar no push.

[[chronogram]]
[[README]]
