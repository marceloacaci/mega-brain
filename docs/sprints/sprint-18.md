# Sprint 18 — Correções de Sinal + Cache de `/stats` — CONCLUÍDO (2026-08-24)

## Objetivo
Eliminar um defeito de **qualidade de sinal** descoberto por auditoria contra o vault
REAL (método P16) e fechar uma **assimetria de performance** entre os endpoints de
polling do dashboard: `/recent`, `/tags`, `/graph` e `/validate` já eram cacheados por
mtime/TTL (P11-style), mas `/stats` re-varria o vault inteiro a cada chamada.

## Entregas

### S18-A — `tags._normalize` remove aspas de frontmatter (defeito real)
`tags.py` extrai tags de frontmatter (`tags: [...]`) e inline (`#tag`). O frontmatter
gerado pelo Obsidian pode vir como `tags: ["projeto/pentagon-mind", 'urgente']` — o
parser **não stripava as aspas**, então a nuvem de tags exibia `"projeto/pentagon-mind"`
(com aspas) como uma tag distinta. Confirmado no vault real: `tag_counts('.')` devolvia
`'\"projeto/pentagon-mind\"'` (9 ocorrências) com aspas.

Correção: `_normalize` agora `tag.strip().strip('"').strip("'").strip().lower()`.

Evidência (vault real pós-fix): `projeto/pentagon-mind: 9` (limpo, sem aspas).
Anti-tautologia: `tests/test_tags.py` (+4 asserts) — reverter `_normalize` faz o teste FALHAR.

### S18-B — `vault_stats.count_by_dir_cached` (P11-style)
`vault_stats.py` ganhou `count_by_dir_cached(vault, ttl)` (cache thread-safe, invalida
por assinatura de mtime do vault OU TTL — mesmo padrão de recent/tags). `_vault_mtime_signature`
local. A rota `GET /stats` do MCP passou a usá-lo e expõe a flag `cached` no JSON; o
contrato `{total, by_dir}` foi preservado.

Evidência (spin-up MCP real): `/stats` #1 `cached:false` total=283, #2 `cached:true`
total=283. Anti-tautologia: `tests/test_shared_modules.py` (+3 asserts) — miss→hit→
invalidação ao mexer `.md`.

## Testes (registrados em `tests/run_all.py`)
- `tests/test_tags.py` — +4 asserts (quote-strip duplo/simples, normalização).
- `tests/test_shared_modules.py` — +3 asserts (cache de /stats).
- `tests/run_all.py`: **27/27 suítes verdes** (mantido).

## Verificação de fato (FCS — P10/P13/P14)
1. `node --check` do `<script>` inline extraído, do ROOT: `rc=0`.
2. Browser com vault fixture temp (7 notas), MCP 8820 + `http.server 8821`:
   - `tags` -> `['tag1:2']` (quote-strip ao vivo, sem aspas).
   - `stats` #1 `cached:false`, #2 `cached:true`.
   - `search('tag1')` -> 2 hits via `data.hits` (contrato P13 OK).
   - `backlinks(B)` -> `['A']`; órfãos (grau wikilink 0) corretos; ping OK(5/5).
   - 0 erros JS no `browser_console`; screenshot confirma layout coerente sem overlap.

## Próximos passos sugeridos
- Endpoint `/orphans-in` (sem nenhum backlink) reusando `backlinks.py` (já sugerido em S17).
- Ligar painel de backlinks ao clique nos nós do grafo (drill-down hoje é por lista).
