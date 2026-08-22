---
titulo: Stacks Mapeadas
tipo: stacks
tags: [megabrain, stack, stack/frontend, stack/automacao]
atualizado: 2026-08-21
---

# 🗺️ STACKS_MAPeadas

Tecnologias, versões e compatibilidades conhecidas.

## MeuBolso (app principal)
- **Runtime:** Electron (desktop Windows) + Node.js.
- **UI:** Vue 3 (views clássicas carregadas via `<script>`, usam `v-html` + re-render).
- **Estilo:** `styles.css` próprio + Bootstrap (`vendor/bootstrap.min.css`), com variáveis CSS por tema (`[data-theme="dark"]`).
- **Ícones:** `icons.js` define `window.ICON` (SVGs inline).
- **i18n:** `src/i18n/{pt,en,es}.js` expostos via `window.I18N` / `t()`.
- **Build/test:** `npm run test` (Vitest, ~127 testes), `npm start` (Electron), `npm run dist:win`.
- **Versionamento:** v2.1.0; releases no GitHub (`marceloacaci/meubolso`).

## Automação / Segundo Cérebro
- **Hermes Agent** (CLI, Windows, bash/MSYS) — ferramenta deste cofre.
- **Obsidian** — vault `Marcelo IA Skills`; Dataview; snippets CSS em `.obsidian/snippets/`.
- **PowerShell** — hooks `pre_task_hook.ps1` / `post_task_hook.ps1` (Windows).
- **Python 3.11** — MCP server local (`mcp_obsidian_server.py`), `watchdog` opcional.
- **Node** — `chokidar` opcional para watcher de arquivos.

## Convenções de path
- Vault: `D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills` (espaços no caminho — usar aspas/citar em shell).
- Hermes skills: `C:\Users\Marcelo\AppData\Local\hermes\skills\`.
- Home do usuário: `C:\Users\Marcelo`.
