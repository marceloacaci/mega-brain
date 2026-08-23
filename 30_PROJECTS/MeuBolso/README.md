---
projeto: MeuBolso
status: ativo
stack: Electron + Vue 3 + Node + npm + Obsidian (segundo cérebro)
criado: 2026-08-21
tags: [projeto/meubolso, stack/electron, stack/vue]
---

# 💰 MeuBolso

App de finanças pessoais (desktop Windows). Autor: Marcelo Acácio.

## 🎯 Objetivo
Gestão de dívidas, pagamentos, carteiras, metas, recorrências, juros, relatórios, gamificação e backups locais.

## 🧩 Stack
- Electron + Node; Vue 3 (views clássicas via `<script>`, `v-html`).
- `styles.css` + Bootstrap; temas claro/escuro via `[data-theme]`.
- `icons.js` (`window.ICON`), i18n pt/en/es (`window.I18N`/`t()`).

## 📂 Estrutura
- `views/*.js` — uma view por página (dividas, pagamentos, painel, sobre…).
- `src/i18n/*.js` — traduções.
- `app.js` — lógica central (notificações, render, gear).
- `styles.css` — tema + componentes.

## 🧭 Decisões
- Ver [[DECISOES]] (renomear release = recriar; hover lift-only; largura fixa i18n).
- Commit `dc66875`: feature S7 (dropdown frequência notificações) + polimento raised.

## ⚠️ Erros & Soluções
- Títulos de page-header "sumiam" no app rodando → app iniciado antes dos commits (Electron não hot-reload). Fix: reiniciar `npm start`.
- `.gear-cor` com gradiente fraco (30%) → corrigido para 70% (metade clara em cima), igual ao `.gear-opt`.

## 🔗 Conexões
- [[MOC_JavaScript]] · [[PADROES_RECorrentes]] · [[PREFERENCIAS_PESSOAIS]]

[[STACKS_MAPeadas]]

[[STACK]]

[[CONTEXTO]]
