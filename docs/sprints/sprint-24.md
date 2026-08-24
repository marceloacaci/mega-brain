# Sprint 24 — Hardening de varredura (VAULT_SKIP_DIRS) + `by_tipo` no `/validate` — CONCLUÍDO (2026-08-24)

## Objetivo
O repo `mega-brain` **É o vault** (working tree versionado). Qualquer `os.walk(vault)`
que lista "notas de conteúdo" também encontra `tests/`, `node_modules/`, `.git`,
`__pycache__` etc. e os trata como notas (P30). Corrigir sistematicamente e agregar
problemas de validação por tipo.

## Entregas

### S24-A — `VAULT_SKIP_DIRS` + `prune_vault_dirs` (P30)
Centralizado em `constants.py`:
```python
VAULT_SKIP_DIRS = {".obsidian",".trash",".git","tests","node_modules",
                   "__pycache__",".claudian",".hypernovum",".makemd",".space"}
def prune_vault_dirs(dirs):
    dirs[:] = [d for d in dirs if d not in VAULT_SKIP_DIRS]
```
Aplicado em **TODOS** os pontos de `os.walk`: `semantic._vault_notes` +
`_vault_mtime_signature`, `graph._vault_signature` + `_iter_notes`, `activity`,
`backlinks` (×2), `predictive`, `recent` (×2), `tags` (×2), `validate_vault` (×2),
`vault_stats` (×2), `mcp_obsidian_server.search`. Módulos que usam o símbolo
importam de `constants` (P24: `graph.py` usava `VAULT_SKIP_DIRS` sem importar).

Evidência (vault real): `GET /search?q=test` → 52 hits, **ZERO** paths em `tests/`
(antes poluía); `/suggest` limpo; `reason()` não sugere `tests/`.

### S24-B — `by_tipo` no `/validate` (P26)
`validate_vault()` devolve `by_tipo {tipo: n}` agregado na MESMA passada (custo zero).
Dashboard: resumo por tipo ordenado desc antes da lista + cap `VLD_CAP = 30`.

### S24-C — Usar o agregado para AGIR: 5 problemas → ZERO (P29)
Os 5 problemas do vault real eram **legítimos** e foram zerados (`ok=true`, problemas=0):
- `livro.md`, `MeuBolso.md`, `nome.md` com **0 bytes** → preenchidas como notas-ponte
  (frontmatter + link ao README canônico). **Mantidas** (wikilinks soltos já apontavam).
- Causa-raiz de `nome.md`: placeholder `[[nome]]` no `PROMPT_MESTRE_v2` → convertido
  para código inline (não se repete).
- `[[pentagon-mind]]` quebrado: a pasta existia, a nota-raiz não → apontar para
  `[[30_PROJECTS/pentagon-mind/README|pentagon-mind]]`.
- Menções em prosa de wikilinks em `docs/` envolvidas em backticks.

## Testes (registrados em `tests/run_all.py`)
- `tests/test_vault_skip_dirs.py` — cria vault com nota de conteúdo + `tests/` +
  `node_modules/`; confirma que `_vault_notes`/`suggest`/`recent`/`tags`/`vault_stats`/
  `validate_vault`/`search` EXCLUEM os dirs proibidos; injeta a regressão (esvazia
  skip + desliga prune) e confirma que os dirs REAPARECEM (senão o teste falha).
- `run_all`: **34/34 suítes verdes** (estável).
