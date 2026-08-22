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

## 🟠 S8 — Confiança & auditoria — ✅ CONCLUÍDO (22/ago, commits 6e45a85 + ed0b9a4)
- **C10** (IPC duplicado): confirmado que o handler no main é ÚNICO (`dados:salvar-agora`); removido do preload o `salvar()` redundante — sobra `salvarAgora` (usado por app.js:1561). Travado por teste.
- **B10** (hash SHA-256): `src/cripto.js` ganha `sha256Arquivo()` (node:crypto) para detecção de corrupção; testado (determinístico, muda com 1 byte).
- **C5** (lint/Prettier+CI): adicionados `.prettierrc`/`.prettierignore`, script `lint`/`format` no package.json, devDep `prettier`, e job `lint` na CI (`prettier --check`). Codebase formatado (commit 6e45a85).
- **C2** (expandir testes): suíte S8 (`tests/s8-auditoria.test.js`) cobre B10+C10. Total sobe para **151 testes verdes**.
- Próximo: S9 (hábito/engajamento).

## 🟡 S9 — Hábito & retenção — ✅ CONCLUÍDO (22/ago, commit 75a7526)
- **E2** (streak dias sem atraso): `streakDiasSemAtraso(diasComAtraso, hoje)` em dominio.js — conta dias seguidos sem atraso (com guarda anti-loop).
- **E3** (XP consistência): `xpConsistencia(streak)` — bónus não-linear (5 + 2/dia, teto 30d).
- **B5** (ações desbloqueio): `acoesDesbloqueio(estado)` + `desbloqueiosConcluidos(acoes)` — lista de ações que liberam painéis de gamificação.
- Implementado como **funções PURAS** em dominio.js (padrão do projeto); integração UI no app fica para etapa posterior.
- Suíte S9 (`tests/s9-habito.test.js`): 16 testes. Total sobe para **167 verdes**; `npm run lint` passa.
- Próximo: S10 (multiperfis 2.0).
- **S9-D9** — estados vazios instrutivos.

## 🟢 S10 — Multiperfis 2.0 — ✅ CONCLUÍDO (22/ago, commit 05a45b9)
- **Sync de pasta**: `sincronizarPasta(base, destino)` em perfis.js — espelha índice + arquivos de perfil para pasta externa (nuvem/Dropbox), cópia fiel e idempotente.
- **Modo família**: `definirFamiliar(base, id, ativa)` + `perfisFamiliares(base)` — marca/lista perfis compartilhados.
- Implementado como **funções PURAS** (padrão do projeto, com fs real testável); integração UI no app fica para etapa posterior.
- Suíte S10 (`tests/s10-multiperfis.test.js`): 5 testes. Total sobe para **172 verdes**; `npm run lint` passa.
- **FIM do roadmap do brainstorming 16/ago (S7→S10 entregues).** Próximos passos reais: integrar UI destas funções no app (runtime Electron) e/ou retomar itens fora do roadmap (A5 orçamento 50/30/20, H2 Open Finance).
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
