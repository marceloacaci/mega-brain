---
projeto: MeuBolso
tipo: tarefas
status: ativo
tags: [projeto/meubolso, tarefas, roadmap]
criado: 2026-08-22
---

# 📋 TAREFAS — MeuBolso (próximas etapas)

> Baseado em `docs/CRONOGRAMA-3-MESES.md` (S1–S6 ✅ FEITO → v2.1.0) e
> `docs/BRAINSTORM-MELHORIAS.md` (rodada 16/ago/2026). O ciclo S1–S6 está
> 100% entregue (126/126 testes Vitest). Próximo salto = **confiança nos
> números** e **retenção pelo hábito**.

## 🔴 S7 — Integridade numérica (prioridade 0) — ✅ CONCLUÍDO (22/ago, commit 04d599f)
- **C11** (centavos): já resolvido no código (`somaDinheiro`/`numDinheiro` em centavos); travado por teste.
- **C12** (fuso BR): `hoje()` agora delega a `hojeLocal()` (src/dominio.js, data local sem UTC); removido comentário stale que dizia "UTC". Travado por teste (23h30 Brasília = dia corrente).
- **E4** (NÍVEIS × nivelDe): tabela não-linear + `nivelDe()` iterando a tabela; travado por teste (600XP→n6, 1600XP→n10).
- Suíte de regressão: `tests/s7-regressao.test.js` (145 testes no total, verdes).
- Próximo: S8 (auditoria).

## 🟠 S8 — Confiança & auditoria
- **S8-C10** — unificar handlers IPC duplicados (`dados:salvar` == `dados:salvar-agora`).
- **S8-C5** — ESLint/Prettier + CI (gate de cobertura).
- **S8-B10** — hash SHA-256 do arquivo para detectar corrupção antes de exibir.
- **S8-C2** — expandir suíte de testes de domínio.

## 🟡 S9 — Hábito & retenção
- **S9-E2** — streak de dias sem atraso (mecânica de hábito de alto impacto).
- **S9-E6** — resumo mensal.
- **S9-D3** — notificação nativa de vencimento (já entregue em S5-3; confirmar cobertura).
- **S9-D9** — estados vazios instrutivos.

## 🟢 S10 — Multiperfis 2.0
- **S10-B11** — sync por pasta (OneDrive/Dropbox) com detecção de conflito.
- **S10-H5** — modo família leve (convite de perfil).
- **S10-E5** — níveis além do 10.

## 🎨 Correções de UI descobertas na auditoria (22/ago)
- **UI-1 (P3 doc-stale) — RESOLVIDO (22/ago):** mantém-se **70%** (ajustado de 85% no working tree). DECISOES/README atualizados para 70%.
- **UI-2 (P1 hover) — RESOLVIDO (22/ago, commit 645a660):**
  - `.btn-icon.danger:hover` era CSS MORTO (0 elementos com `.danger` no app) → removido.
  - `.notif-dd-item.active:hover` recoloria (`color:#fff`) → corrigido para `box-shadow` (lift-only).
  - `.fab-mobile:hover` mantido: FAB mobile de cor primária (igual a `.btn-primary`), só dispara em mobile (display:none no desktop). Documentado como exceção intencional.
- **UI-3 (gear-opt ícone):** já havia comentário no CSS a remover o recolorir; confirmado que `.gear-opt:not(.active):hover` não recoloria ícone (usa só box-shadow). Sem ação necessária.

## ⛔ Fora do roadmap (decisão consciente)
- A5 (orçamento 50/30/20), H2 (Open Finance), C4/C7 (Vite + SFCs) — mudam a proposta "offline/minimalista".
