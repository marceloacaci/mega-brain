---
tipo: referencia
criado: 2026-08-21
tags: [meta, integracao, hermes, megabrain]
---

# 🔗 Integração Hermes ↔ MEGA BRAIN

Como o Hermes Agent se liga a este vault e atua como Segundo Cérebro.

## Arquitetura
- O vault expõe um servidor MCP HTTP: `80_SYSTEM/SCRIPTS/mcp_obsidian_server.py`.
- Ouve em `http://127.0.0.1:8770` (JSON).
- Hermes = cliente; vault = servidor de conhecimento. Ponte = HTTP/MCP.
- Skill `megabrain-automation` (em `AppData\Local\hermes\skills\productivity`) é o manual do protocolo.

## Endpoints (testados em 2026-08-21)
- `GET  /health`     → status vivo + caminho do vault
- `GET  /search?q=`  → procura substrings nas notas (hits + trecho)
- `GET  /read?path=` → lê conteúdo de uma nota
- `POST /write`      → cria/sobrescreve nota
- `POST /append`     → anexa conteúdo (ex.: daily note)
- `POST /moc`        → cria MOC (mapa de conteúdo)
- `POST /link`       → cria wikilink entre duas notas
- `POST /tag`        → aplica tags no frontmatter
- `GET  /stats`      → contagem real de notas por pasta (adicionado na sessão)

Nota: o servidor usa `ThreadingHTTPServer` e implementa `do_OPTIONS` (CORS preflight) para permitir POST cross-origin a partir de páginas web.

## Automatização — o que é e o que não é
- **Automático (nível vault):** `eindex_hybrid.ps1` reindexa o vault (light 6h + deep semanal) e atualiza o INDEX_GERAL. Agendado via Task Scheduler/watcher.
- **Manual nesta sessão:** Hermes chamou os endpoints à mão; não houve auto-sync de cada mensagem.
- **Futuro (mãos-livres):** hooks em `80_SYSTEM/HOOKS_HERMES` (-Tarefa/-Projeto/-Resultado) capturam contexto e gravam no vault quando o watcher estiver instalado.

## Exemplo real (2026-08-21)
Painel web de teste rodou o ciclo completo no MCP vivo:
1. `/health` → vivo, 2 ms
2. `/search "megabrain"` → 7 notas
3. `/read INDEX_GERAL` → meta-índice real
4. `/write` → `30_PROJECTS/zz_web_teste/note.md`
5. `/append` → daily `2026-08-21.md`
6. `/moc` → `MOC_Web Teste`
7. `/tag` → tags `[web,teste]`
Resultado: 7/7 OK, ficheiros confirmados no disco. (Resíduos de teste apagados a pedido.)

## Prós
- Memória persistente entre sessões (sobrevive a `/new`).
- Contexto estruturado (MOCs, índices) em vez de pastas soltas.
- Fonte de verdade para decisões/padrões/preferências.
- Auditoria: tudo gravado fica visível e editável no Obsidian.
- Sem lock-in: Markdown local + HTTP.

## Capacidades úteis p/ desenvolvimento
- Ler `PADROES_RECorrentes` antes de codar UI/CSS.
- Consultar `DECISOES_REUTILIZAVEIS` para não reabrir discussões.
- MOC por projeto = onboarding rápido de subagents.
- Gravar root cause de bugs no vault (ex.: CORS preflight, IPv6 vs IPv4) para não repetir.
- Daily notes via `/append` = histórico de execução do agente.

## Limites (honestos)
- Dashboard do vault (INDEX_GERAL, MOCs) depende do plugin **Dataview**, ainda não instalado na UI → índices mostram código bruto até instalar. Links `[[ ]]` estáticos já funcionam.
- Captura automática das conversas só entra quando hooks/watcher estiverem prontos.

[[SETUP_MEGABRAIN_HERMES]]

[[AUTOINDEX_STACK]]

[[ROADMAP]]
