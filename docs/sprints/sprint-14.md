# Sprint 14 — Notas Recentes (novo recurso utilitário + FCS)

**Data:** 2026-08-24
**Tipo:** Feature (read-only, sem superfície de segurança) + cobertura de testes
**Entregue por:** worker autônomo (continuação) — co-autor Hermes Agent

## Sprint Goal

Adicionar ao MEGA BRAIN uma forma rápida de descobrir **o que mudou por último**
no vault, expondo um endpoint `/recent` (somente-leitura) e um painel "Notas
Recentes" no dashboard — tudo validado de fato no browser (FCS, P10–P14).

A escolha de um recurso **novo e read-only** (em vez de mexer em contratos
existentes) segue a auditoria P16: os módulos existentes (S11–S13) já não têm
defeitos endereçáveis — o risco de regressão superaria o benefício de refatorar
rotas maduras.

## Subsprints

### S14-A — Endpoint `/recent` (80_SYSTEM/SCRIPTS/recent.py)
- `recent_notes(vault, limit=10, cutoff_days=None)` → lista até `limit` notas
  `.md` ordenadas por **mtime decrescente**, com `{path, mtime, age_days, type}`.
- Varredura única (`os.walk`), ignora `.obsidian`/`.trash`.
- Mapeamento de tipo de pasta espelha `graph._folder_type` (sem acoplar ao grafo).
- `limit` clampado a `[1, NOTE_LIMIT]` (fail-safe).
- `cutoff_days` opcional filtra notas mais antigas que N dias.
- **Zero superfície de segurança**: não aceita path do usuário, não lê fora do vault.

### S14-B — Rota MCP `GET /recent`
- `mcp_obsidian_server.py` importa `recent_notes`; rota aceita `?limit=N&days=D`,
  envolve em `try/except` → 500 legível (P8). Contabiliza `mcp_requests_total`.

### S14-C — Painel "Notas Recentes" (web/dashboard.html)
- Painel inline (P12) na coluna direita, após Grafana.
- `<select>` de janela (qualquer / 24h / 7d / 30d) + botão Atualizar.
- `loadRecent()` consome `/recent` pelo contrato `{recent:[{path,mtime,age_days,type}]}`
  (P13) e formata "há X min/d". Chamado na inicialização.

### S14-D — Testes não-tautológicos
- `tests/test_recent.py` (13 checagens): ordenação mtime desc, limite, cutoff
  (0.5d exclui nota de 1.16d; 0.0002d isola a mais nova), mapeamento de tipo,
  `age_days` coerente, vault vazio → `[]`, `limit` inválido → 1.
- `tests/e2e_recent.py` (4 checagens): sobe MCP em fixture, valida `GET /recent`
  ordenado, `limit`, campos obrigatórios, mtime desc no payload real.

### S14-E — FCS no browser (P10–P14)
- MCP fresco + http.server em fixture (5 notas com mtime escalonado + 1 de 10 dias).
- `loadRecent()` → 5 itens, 1º = mais recente, "há 0 min", tipo core.
- `<select value=7>` → `VELHA` (10d) **excluída** (hasOld=false).
- `node --check` do JS inline (do ROOT): OK; `wc -c`=27163, termina em `</html>` (P14).
- search()/orphans()/validate() intactos (sem regressão).

## Critérios de Aceitação (Gherkin)

```gherkin
Feature: Notas Recentes
  Como usuário do segundo cérebro
  Quero ver as notas modificadas mais recentemente
  Para focar no que mudou sem varrer o vault manualmente

  Scenario: ordenação por recência
    Given um vault com notas de mtimes distintos
    When GET /recent?limit=10
    Then a resposta lista por mtime decrescente
    And a primeira nota é a mais recente

  Scenario: filtro por janela
    Given uma nota de 10 dias e notas de hoje
    When GET /recent?days=7
    Then a nota de 10 dias está ausente
    And as notas de hoje estão presentes

  Scenario: painel no dashboard
    Given o dashboard conectado ao MCP
    When a página carrega
    Then o painel "Notas Recentes" mostra a nota mais recente
    And selecionar "últimos 7 dias" exclui notas antigas
```

## Métricas (medidas, não estimadas)

| Métrica | Antes | Depois |
|---|---|---|
| Suítes de teste | 19/19 | **21/21** |
| Cobertura de `/recent` | 0 | unit(13) + e2e(4) |
| Tempo de build_graph (vault real) | 0.50s | 0.50s (inalterado) |
| Superfície de ataque nova | — | nenhuma (read-only) |

## Definition of Done

- [x] Endpoint `/recent` implementado e testado (unit + e2e)
- [x] Painel no dashboard + filtro por janela
- [x] `node --check` do JS inline OK (P10); `wc -c`/tail conferidos (P14)
- [x] FCS no browser sem erros de runtime (P13)
- [x] `python tests/run_all.py` → 21/21 verde antes do commit
- [x] Documentação (sprint-14, chronogram, live transcript)

## Dívida remanescente (honesta)

- `/recent` não tem cache (re-varre o vault a cada chamada). Para vaults >1000
  notas, um cache por mtime (como o de `/graph`, P11) seria o próximo passo —
  mantido fora deste sprint por ser otimização, não correção.
- O `<select>` só oferece janelas fixas (1/7/30d); um campo livre de dias é
  possível mas exigiria validação extra no JS (fora do escopo atual).
