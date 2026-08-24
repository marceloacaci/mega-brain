# Sprint 23 — Órfãs agregadas por pasta (`by_dir`) — CONCLUÍDO (2026-08-24)

## Objetivo
O endpoint `/orphans-in` (notas sem nenhum backlink, S22-style) devolvia uma lista
crua de centenas de itens — inútil na UI e enganosa (P26). Agregar por pasta-raiz
revela a verdade.

## Entregas

### S23-A — `by_dir` em `backlinks.orphans_in`
`orphans_in(vault)` (uma passada, não laço O(n) — P22) agora devolve também
`by_dir {pasta: n}`. Provado no vault real: **317 órfãs de 374 (85%)**, mas
**266 estavam em `50_METRICS`** (notas auto-geradas que ninguém linka por natureza) —
o grafo real tinha ~51 órfãs acionáveis.

### S23-B — UI capada + resumo
O painel "Órfãs de Entrada" do dashboard (`web/dashboard.html`, inline único P12)
renderiza o resumo por pasta (`"... 10_MEGA_BRAIN: 4 / 70_MOCS: 1"`) + lista capada
em `ORPH_CAP = 40` com rodapé "... e mais N".

## Testes / Verificação
- Verificado por worker irmão (commit `7b71205`/`97b8745`) via FCS no browser
  (portas frescas, fixture 6 notas/1 órfã): `node --check` rc=0; 0 erros JS;
  render do resumo por pasta + lista capada confirmado.
- Não criado commit redundante — implementação do irmão validada como correta.
