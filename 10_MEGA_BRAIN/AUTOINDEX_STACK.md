---
tipo: stack
criado: 2026-08-21
tags: [megabrain, stack, autoindex, protocolo]
---

# 📚 STACK — Auto-Indexação Autónoma (Hermes ↔ MEGA BRAIN)

Protocolo OBRIGATÓRIO e 100% automático de indexação do Segundo Cérebro.

## Regra de Ouro
> Toda vez que o Hermes Agent toca num artefato, pasta, projeto ou nota
> (nesta ou em qualquer shell/projeto), ele INDEXA automaticamente no MEGA BRAIN
> e REINDEXA TUDO ao concluir a tarefa — SEM PERGUNTAR, 100% autónomo.

## Durante a execução (em tempo real)
Sempre que o Hermes criar/alterar um artefato no vault ou projeto relacionado:
- `POST /write`  → cria nota (ex.: novo projeto `30_PROJECTS/<slug>/README.md`)
- `POST /append` → anexa à daily `20_DAILY_NOTES/<hoje>.md`
- `POST /tag`    → aplica tags no frontmatter
- `POST /link`   → cria wikilink entre notas
- `POST /moc`    → cria/atualiza MOC do tópico/projeto

Isto aplica-se à task corrente E a qualquer subtask (delegate_task, parallel).

## Ao CONCLUIR a tarefa (e subtasks paralelas)
1. Aguardar fim de TODAS as subtasks.
2. Disparar reindex profundo do MEGA BRAIN:
   `powershell -NoProfile -ExecutionPolicy Bypass -File "<VAULT>/80_SYSTEM/SCRIPTS/reindex_hybrid.ps1" -Mode deep`
3. Validar que o `INDEX_GERAL.md` foi reconstruído (ler ficheiro / checar timestamp).
4. Só então declarar tarefa concluída.

## Alcance
- Vale para QUALQUER shell do Hermes (default profile do Marcelo).
- Vale para QUALQUER projeto (MeuBolso, Livro, pentagon-mind, MEGA BRAIN, etc.).
- Vale para subrequisições e subtasks disparadas pelo MEGA BRAIN.
- Objetivo: novo conteúdo disponível IMEDIATAMENTE para a próxima requisição.

## Pré-requisitos (já garantidos)
- Servidor MCP a ouvir em `127.0.0.1:8770` (start_megabrain.bat na Startup).
- Skill `hermes-megabrain` carregada (memória do perfil).
- `reindex_hybrid.ps1` presente em `80_SYSTEM/SCRIPTS/`.

## Limites honestos
- Reindex deep é pesado; em tarefas muito frequentes usar light (6h agendado).
- Conteúdo fora do vault (ex.: ficheiros em Desktop/Livro que não estão no vault)
  só é indexado se gravado no vault via MCP.

[[SETUP_MEGABRAIN_HERMES]]

[[INTEGRACAO_HERMES_MEGABRAIN]]

[[ROADMAP]]
