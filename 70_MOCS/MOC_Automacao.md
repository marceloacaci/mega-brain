---
tipo: moc
tags: [moc, automacao]
---

# ⚙️ MOC_Automacao

Hooks, PowerShell, watchers e MCP que ligam Hermes Agent ↔ Obsidian.

## Componentes
- `80_SYSTEM/HOOKS_HERMES/pre_task_hook.ps1` — consulta o cérebro antes de toda tarefa.
- `80_SYSTEM/HOOKS_HERMES/post_task_hook.ps1` — captura pós-tarefa e atualiza índices.
- `80_SYSTEM/SCRIPTS/mcp_obsidian_server.py` — API local (`obsidian.search/read/write/link/tag/moc`).
- `80_SYSTEM/LOGS/metricas.json` — contadores de tarefas/projetos/reuso.

## Fluxos
- Pré-tarefa → ler INDEX_GERAL + MOCs + PADRÕES + PREFERÊNCIAS.
- Pós-tarefa → atualizar daily note, projeto, índices, detectar padrões.

## Conexões
- [[MOC_Python]] · [[MOC_DevOps]] · [[INDEX_GERAL]]
