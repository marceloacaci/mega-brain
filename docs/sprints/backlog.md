# Backlog do Produto — MEGA BRAIN

> Backlog priorizado (MoSCoW) com Épicos e Histórias de Usuário no formato
> "Como [Ator], eu quero [Funcionalidade] para que [Valor]". Critérios de Aceitação
> em Gherkin (Dado que... Quando... Então...).

## Épicos
| ID | Épico | Prioridade |
|----|-------|-----------|
| E1 | Automação Estável (hooks + MCP + dashboard) | Must |
| E2 | Observabilidade & Backup | Must |
| E3 | Inteligência & Extensibilidade (modos + rotas) | Should |
| E4 | Resiliência (failover + integridade) | Should |
| E5 | Evolução Semântica (v2.0: embeddings/cache) | Could |
| E6 | Qualidade & Onboarding (testes + docs) | Must |

---

## Histórias de Usuário

### E1 — Automação Estável
- **US-1** Como *usuário do Hermes Agent*, eu quero que um hook registre minha tarefa no daily note automaticamente, para que eu não perca contexto.
  - **Dado que** o Hermes concluiu uma tarefa no Projeto X
  - **Quando** `post_task_hook.ps1 -Tarefa t -Projeto X -Resultado ok -Resumo s` é disparado
  - **Então** uma entrada é adicionada em `20_DAILY_NOTES/AAAA-MM-DD.md` com status de sucesso

- **US-2** Como *Hermes Agent*, eu quero consultar o vault via HTTP (`/search`, `/read`, `/write`), para que eu opere sem conhecer a estrutura de arquivos.
  - **Dado que** o MCP server está rodando na porta 8770
  - **Quando** envio `GET /search?q=parcela`
  - **Então** recebo JSON com hits contendo o termo em seu contexto

- **US-3** Como *mantenedor*, eu quero que `INDEX_GERAL.md` seja gerado por script, para que ninguém o edite à mão.
  - **Dado que** o último reindex foi há mais de 4h
  - **Quando** `Invoke-LightReindexIfNeeded` roda
  - **Então** `INDEX_GERAL.md` é regenerado e `.last_light.txt` atualizado

### E2 — Observabilidade & Backup
- **US-4** Como *usuário*, eu quero backup rotativo (full + incremental) do vault, para que eu possa recuperar de corrupção.
  - **Dado que** existem backups de mais de `BACKUP_RETENTION_DAYS` dias
  - **Quando** `backup_vault.ps1` executa
  - **Então** os antigos são removidos e um novo zip é criado em `D:\Backups\Obsidian\full\AAAA-MM-DD`

- **US-5** Como *SRE*, eu quero métricas de latência de `/search` em Prometheus, para que eu detecte degradação (roadmap M3).
  - **Dado que** `PROMETHEUS_ENABLED=true`
  - **Quando** uma chamada `/search` completa
  - **Então** a métrica `mcp_search_latency_seconds` é incrementada

### E3 — Inteligência & Extensibilidade
- **US-6** Como *usuário*, eu quero que o modo preditivo sugira um arquivo antes da tarefa, para que eu ganhe contexto relevante.
  - **Dado que** há histórico de tarefas no Projeto X
  - **Quando** `pre_task_hook.ps1` roda no modo preditivo
  - **Então** ele sugere o arquivo mais correlacionado (por tags/horário)

- **US-7** Como *desenvolvedor*, eu quero rotas `rename`/`move` via MCP, para que eu reorganize o vault sem quebrar links.
  - **Dado que** `40_AREAS/old.md` existe
  - **Quando** `POST /rename {"path":"40_AREAS/old.md","new_name":"new.md"}`
  - **Então** o arquivo passa a ser `40_AREAS/new.md` com o mesmo conteúdo e o antigo não existe

### E4 — Resiliência
- **US-8** Como *usuário*, eu quero failover de backup para um segundo destino, para que eu não perca dados se o primário falhar.
  - **Dado que** o destino primário está inacessível
  - **Quando** `backup_vault.ps1` executa
  - **Então** ele usa o destino secundário definido em `config.json`

### E5 — Evolução Semântica (v2.0)
- **US-9** Como *usuário avançado*, eu quero busca semântica por embeddings, para que eu encontre notas por significado, não só por palavra.
  - **Dado que** o índice vetorial está construído
  - **Quando** `GET /search?q=...&mode=semantic`
  - **Então** os resultados consideram proximidade de significado

### E6 — Qualidade & Onboarding
- **US-10** Como *contribuidor*, eu quero um smoke test automatizado, para que eu valide o MCP antes de abrir PR.
  - **Dado que** rodei `python tests/smoke_test.py`
  - **Quando** o MCP sobe num fixture
  - **Então** todos os checks (health/write/read/search/stats/rename/move) retornam PASS

---

## Critérios de Aceitação (padrão Gherkin) — exemplos transversais
- **Performance**: Dado que o vault tem < 5000 notas, Quando `/search` é chamado, Então responde em < 500ms (sem cache) ou < 50ms (com cache Redis).
- **Segurança**: Dado que um parâmetro contém `../`, Quando o hook sanitiza, Então o path é confinado a `VAULT_ROOT`.
- **Resiliência**: Dado que `.last_light.txt` está corrompido, Quando `Invoke-LightReindexIfNeeded` roda, Então ele força reindex (não aborta).
