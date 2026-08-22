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

## 🔴 S7 — Integridade numérica (prioridade 0)
- **S7-C11** — dinheiro em centavos inteiros (evita deriva de float; hoje `0.1+0.2≠0.3`).
- **S7-C12** — `hoje()` em fuso de Brasília (corrige vencimentos com 1 dia de defasagem perto da meia-noite).
- **S7-E4** — alinhar tabela `NIVEIS` × `nivelDe()` (nível correto em todo o XP).
- Suíte de regressão do domínio. `npm run test` deve continuar verde.

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
- **UI-2 (P1 exceções):** `.btn-primary:hover` muda `background` (permitido, botão colorido), mas `.btn-icon.danger:hover`, `.fab-mobile:hover`, `.notif-dd-item.active:hover` mudam cor — confirmar se são intencionais ou violar P1.
- **UI-3:** `.gear-opt:not(.active):hover` recoloria ícone para `var(--text)` — já há comentário no CSS a remover isso; verificar se restou.

## ⛔ Fora do roadmap (decisão consciente)
- A5 (orçamento 50/30/20), H2 (Open Finance), C4/C7 (Vite + SFCs) — mudam a proposta "offline/minimalista".
