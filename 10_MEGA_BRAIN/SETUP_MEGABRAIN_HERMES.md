---
tipo: referencia
criado: 2026-08-21
tags: [meta, setup, megabrain, hermes, integracao]
---

# 🛠️ Setup MEGA BRAIN ↔ Hermes Agent (Resumo)

Resumo do estado operacional da integração, gravado em 2026-08-21.

## Arquitetura
- Vault: `D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills`
- Servidor MCP: `80_SYSTEM\SCRIPTS\mcp_obsidian_server.py` → `127.0.0.1:8770` (HTTP/JSON)
- Hermes = cliente; vault = servidor de conhecimento.
- Endpoints: `/health /search /read /write /append /moc /link /tag /stats`

## Componentes ativos
- **Servidor MCP** vivo na 8770 (corrigido com `do_OPTIONS` CORS + `/stats`).
- **Atalho Startup** `MegaBrain.lnk` → `start_megabrain.bat` (sobe o servidor no arranque do Windows).
- **Dataview + Templater** instalados na UI do Obsidian (dashboards renderizam).
- **Skill `hermes-megabrain`** carregada automaticamente (memória do perfil do Marcelo).
- **Stack de auto-indexação** (`10_MEGA_BRAIN/AUTOINDEX_STACK.md`): indexação em tempo real de
  qualquer artefato tocado + reindex completo obrigatório (`reindex_hybrid.ps1 -Mode deep`)
  ao concluir cada task/subtask — 100% autónomo.
- **Tarefas agendadas**: `MEGA_BRAIN_Watcher` (23:30), Reindex Light (6h), Reindex Deep (dom 23h).

## Fluxo automático (em qualquer shell/projeto)
1. Início: skill consulta vault (health + INDEX_GERAL + PADRÕES + PREFERÊNCIAS + DECISÕES + daily).
2. Durante: cada artefato tocado é indexado via MCP (write/append/tag/link/moc).
3. Fim: append na daily + **reindex deep obrigatório** + validação do INDEX_GERAL.
4. Próxima requisição já vê o conteúdo novo.

## Notas de referência no vault
- `10_MEGA_BRAIN/INTEGRACAO_HERMES_MEGABRAIN.md` — arquitetura e benefícios detalhados.
- `10_MEGA_BRAIN/AUTOINDEX_STACK.md` — protocolo de auto-indexação obrigatória.

## Limites conhecidos
- Reindex deep é pesado; tarefas frequentes usam `-Mode light`.
- Conteúdo fora do vault só é indexado se gravado no vault via MCP.
- Conversas do chat NÃO são transcritas; grava-se o registo/resumo da tarefa.

## Validação (2026-08-21)
- Ciclo completo 10/10 na 8770 (health→search→read→write→append→moc→tag→link→stats→read).
- Teste de shell nova: skill carregou e indexou automaticamente.
- Teste de ponta a ponta: artefato tocado → indexado → reindex deep detetou o projeto novo.
