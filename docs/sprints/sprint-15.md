# Sprint 15 — Nuvem de Tags (novo recurso utilitário + FCS)

**Data:** 2026-08-24
**Tipo:** Feature (read-only) + cobertura de testes
**Entregue por:** worker autônomo (continuação) — co-autor Hermes Agent

## Sprint Goal

Expor o **vocabulário de tags** do vault (frontmatter + inline) como uma nuvem
de tags no dashboard, para o usuário descobrir os temas recorrentes do segundo
cérebro sem varrer notas manualmente. Mesmo padrão do S14: recurso novo,
read-only, sem superfície de segurança, validado no browser (FCS).

## Subsprints

### S15-A — Módulo `tags.py`
- `tag_counts(vault, limit=20, top_only=True)` → lista `[{tag, count}]` ordenada
  por count descrescente.
- Extrai tags de:
  - frontmatter bloco (`tags:\n  - x`) e inline (`tags: [a, b]`);
  - tags inline no corpo (`#tag`), com regex que não captura `/` ou pontuação.
- Normaliza para lowercase (união de `MOC` e `#moc`).
- `top_only=True` ignora tags com count==1 (ruído de digitação/acidente).
- Conta **por nota** (uma tag conta 1x por nota, não por ocorrência).
- Reusa `constants.NOTE_LIMIT` como teto de `limit`.

### S15-B — Rota MCP `GET /tags`
- `mcp_obsidian_server.py` importa `tag_counts`; rota `?limit=N`, try/except → 500.

### S15-C — Painel "Nuvem de Tags" (web/dashboard.html)
- Painel inline (P12) na coluna direita, após Notas Recentes.
- `loadTags()` consome `/tags` pelo contrato `{tags:[{tag,count}]}` (P13) e
  renderiza spans com tamanho/opacidade proporcionais à frequência.

### S15-D — Testes não-tautológicos
- `tests/test_tags.py` (10 checagens): frontmatter (bloco+inline), inline no
  corpo, normalização maiúscula, top_only (ignora count==1), ordenação desc,
  limite, vault sem tags → `[]`.
- `tests/e2e_tags.py` (3 checagens): sobe MCP, valida `/tags` ordenado, contém
  tag conhecida (em 2 notas p/ não ser filtrada), limite respeitado.

### S15-E — FCS no browser (P10–P14)
- MCP fresco + http.server em fixture (3 notas com tags sobrepostas).
- `loadTags()` → 4 spans (`#financeiro #moc #projeto #urgente`), igual ao servidor.
- `node --check` inline OK; `wc -c`=28323, termina em `</html>` (P14).
- **Regressão pega e corrigida**: a inserção do bloco `/tags` consumiu a linha
  `if u.path == "/activity":`, deixando `/activity` 404. O `e2e_dashboard` (S10-B)
  falhou → corrigido antes do commit (run_all 22/23 → 23/23).

## Critérios de Aceitação (Gherkin)

```gherkin
Feature: Nuvem de Tags
  Como usuário do segundo cérebro
  Quero ver as tags mais frequentes do vault
  Para descobrir temas recorrentes sem varrer notas

  Scenario: extração de tags
    Given notas com tags em frontmatter e inline
    When GET /tags
    Then a resposta lista tags ordenadas por frequência

  Scenario: normalização
    Given a tag "MOC" e "#moc"
    Then ambas contam como "moc"

  Scenario: painel no dashboard
    Given o dashboard conectado ao MCP
    When a página carrega
    Then a nuvem de tags mostra as tags mais frequentes
```

## Métricas (medidas)

| Métrica | Antes | Depois |
|---|---|---|
| Suítes de teste | 21/21 | **23/23** |
| Cobertura de `/tags` | 0 | unit(10) + e2e(3) |
| Regressão introduzida/corrigida | — | 1 (`/activity` 404, antes do commit) |

## Definition of Done

- [x] `tags.py` + rota `/tags` + painel no dashboard
- [x] `test_tags.py`(10) + `e2e_tags.py`(3) não-tautológicos
- [x] `node --check` inline OK; `wc -c`/tail conferidos
- [x] FCS no browser sem erros de runtime
- [x] `run_all` → 23/23 verde (incluiu correção de regressão de `/activity`)
- [x] Documentação (sprint-15, chronogram, live transcript)

## Dívida remanescente (honesta)

- `tags.py` re-varre o vault a cada `/tags` (sem cache). Um cache por mtime
  (como em `/recent` S14-B) seria o próximo passo — fora deste sprint.
- Não há filtro de idioma; tags em pt e en convivem (esperado para um vault bilíngue).
