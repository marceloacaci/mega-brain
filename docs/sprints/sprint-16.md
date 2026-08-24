# Sprint 16 — Endurecimento de `tag()` + Cache de `/validate` (S16-A/B)

**Data:** 2026-08-24
**Tipo:** Bugfix (latent) + performance (cache) + cobertura de testes
**Entregue por:** worker autônomo (continuação) — co-autor Hermes Agent

## Sprint Goal

Continuar o endurecimento incremental SEGURO do MEGA BRAIN (padrão S11–S15):
(1) corrigir um defeito LATENTE real em `tag()` que silenciosamente dropava tags;
(2) aplicar o padrão de cache P11-style (já usado em `/graph`, `/recent`, `/tags`) ao
único endpoint read-only que ainda o ignorava — `/validate` — para evitar re-varredura
do vault a cada poll do dashboard. Tudo com teste não-tautológico e FCS do dashboard.

## Subsprints

### S16-A — Bugfix de `tag()` (defeito latente real)
- A função `tag(note, tags)` do MCP: quando a nota TEM frontmatter mas **SEM** a chave
  `tags:`, o branch `else` criava `tags: []` e **SILENCIOSAMENTE DROPava todas as tags
  pedidas**. Nenhum teste anterior cobria esse caso (CI 23/23 verde mascarava o bug).
- Correção (`mcp_obsidian_server.py`): o branch `else` agora injeta
  `tags: [projeto, urgente]` (as tags pedidas), igual ao branch "sem frontmatter".
- Casos já corretos (verificados): frontmatter **com** `tags:` acrescenta sem duplicar;
  nota sem frontmatter cria bloco; lista vazia não corrompe.
- `tests/test_tag_func.py` (9 checagens) cobre os 4 casos. Anti-tautologia: reverter o
  fix → teste FALHA 3/9 (tags ausentes); restaurado → 9/9.

### S16-B — Cache de `/validate` (padrão P11)
- Dívida: `/validate` era o ÚNICO endpoint read-only sem cache — re-varria o vault
  inteiro a cada poll do dashboard (mesmo custo que `/recent`/`/tags` antes do S14-B/S15-B).
- `validate_vault.py`: nova `_vault_mtime_signature(vault)` + `validate_cached(vault, ttl)`
  (cache thread-safe, invalida por mtime/count do vault OU TTL). Padrão P11 idêntico a
  `recent.recent_notes_cached` / `tags.tag_counts_cached`.
- `mcp_obsidian_server.py`: rota `/validate` agora usa `validate_cached`, envolve em
  try/except (P8) e expõe a flag `cached` no JSON (igual a `/graph`, `/recent`, `/tags`).
  Contrato de payload inalterado: `{ok, total_notas, problemas, cached}`.
- `tests/test_validate_cache.py` (6 checagens): miss→hit→invalida-ao-tocar→ttl=0-força-miss.
- Verificação ao vivo: MCP na porta 8793 → 1º `/validate` `cached:false`, 2º `cached:true`,
  `total_notas=6` estável em ambos.

### S16-C — FCS do dashboard (P10–P14)
- MCP fresco (8791) + http.server (8792) em fixture de 6 notas. `browser_console`:
  `loadGraph` 6n/5e, `renderOrphans` 3 (grau wikilink 0), `bfsPath` OK, `search` via
  `data.hits`, `loadActivity` 2 células, `loadTags` 1 span, `runValidate` 6/5,
  `testConnection` OK (5/5, ping 2.5–7.5ms). 0 erros runtime reais.
- `node --check` inline OK; `wc -c web/dashboard.html`=28323, termina em `</html>` (P14).

## Critérios de Aceitação (Gherkin)

```gherkin
Feature: tag() preserva tags
  Como usuário que aplica tags via MCP
  Quero que tags sejam salvas mesmo se a nota já tem frontmatter sem chave tags:
  Para não perder metadados

  Scenario: frontmatter sem chave tags
    Given uma nota com frontmatter "---\ntipo: moc\n---"
    When tag("note.md", ["projeto", "urgente"])
    Then o frontmatter contém "tags: [projeto, urgente]"

Feature: /validate com cache
  Como dashboard que faz poll de /validate
  Quero resposta cacheada enquanto o vault não muda
  Para não re-varrer 262 notas a cada 15s

  Scenario: segundo acesso em hit
    Given o vault estável
    When GET /validate duas vezes seguidas
    Then a segunda resposta traz "cached": true e o mesmo total_notas
```

## Definition of Done

- [x] `tag()` não dropa tags (test_tag_func 9/9)
- [x] `/validate` cacheado (test_validate_cache 6/6), flag `cached` exposta
- [x] `run_all` 25/25 verdes (era 23/23)
- [x] FCS do dashboard no browser: 0 erros runtime reais
- [x] `node --check` + `py_compile` OK (P10/P14)
- [x] Documentado em sprint-16.md + chronogram.md + live transcript

## Métricas (antes → depois)

| Métrica | Antes | Depois |
|---|---|---|
| `tag()` com fm-sem-tags | dropava tags (silêncio) | injeta tags pedidas |
| `/validate` por poll | re-varre vault (262 notas) | hit em cache (mtime/TTL) |
| Suítes de teste | 23/23 | **25/25** |
| Defeitos latentes em `tag()` | 1 (não pego pelo CI) | 0 (coberto por teste não-tautológico) |

## Riscos / dívida remanescente

- `/stats` do MCP ainda re-contabiliza o vault por chamada (não cacheado). Próximo alvo
  natural de cache P11-style se o dashboard passar a pollá-lo.
- O "JS error" do `browser_console` é o iframe do Grafana apontando para `localhost:3000`
  (não disponível no ambiente de teste) — não é defeito do dashboard.
