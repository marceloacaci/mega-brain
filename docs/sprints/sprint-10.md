# Sprint 10 — Ativação & Consolidação de Produção (S10-A → S10-B → S10-C)
**Duração**: 3 × 2 semanas (6 semanas) | **Objetivo**: tirar o v2.0 do modo heurístico,
fechar as pontas do repositório e entregar valor visível (dashboard) + governança (segurança).

## Meta do Sprint (Sprint Goal)
"O MEGA BRAIN opera em produção com IA local opcional (Ollama), expõe seu grafo de
conhecimento num dashboard navegável e aplica guardrails de segurança (Prompt Injection
+ PII) antes de qualquer chamada de LLM externo — tudo coberto por testes e CI verde."

## S10-A — Produção & Ativação (semana 1–2)
- `docker-compose.yml`: serviço `ollama` sob `profiles: [ollama]` (sobe com
  `docker compose --profile ollama up`); `mcp` depende dele opcionalmente.
- `.env.example`: `OLLAMA_URL` / `OLLAMA_MODEL` documentados (modo heuristico por padrão).
- `tests/fixture/`: vault mínimo válido para `docker compose up mcp`.
- `tests/e2e_ollama.py`: valida embeddings reais se Ollama presente; **SKIP** se ausente (CI verde offline).
- Push do commit de backlinks (`84023a9`, varredura semântica) + limpeza de `docs/uml*.md` soltos.

## S10-B — Web Dashboard (semana 3–4)
- Rota `GET /graph` no MCP: nós (notas) + arestas (related/sugestões) como JSON.
- `web/dashboard.html`: página estática (Fomantic UI via CDN) consumindo `/graph`,
  `/metrics`, `/search` — grafo de conhecimento + painel de saúde. Sem build step.
- `tests/e2e_dashboard.py`: sobe MCP + valida que o HTML referencia `/graph` e é servido.

## S10-C — Governança & Segurança (semana 5–6)
- `governance.py`: `guardrails_injection(text)` (detecta padrões de Prompt Injection:
  "ignore previous instructions", delimitadores de sistema, tentativas de role-play) e
  `mask_pii(text)` (regex para e-mails, CPF, telefone, tokens/API keys) — antes de LLM externo.
- Swarm (`swarm.py`): `guardian` aplica `guardrails_injection` nas entradas dos agentes.
- `llm_local.reason`: aplica `mask_pii` no prompt antes de chamar Ollama/externo.
- `tests/e2e_governance.py`: injection detectado + PII mascarada.

## Critérios de Aceitação (Gherkin)
```gherkin
Dado OLLAMA_URL configurado e acessivel
Quando GET /related for chamado
Entao usa embeddings reais (modo="ollama") e nao Jaccard

Dado o dashboard aberto
Quando /graph for requisitado
Entao retorna nos+arestas e o HTML os consome

Dado um texto com "ignore previous instructions"
Quando guardrails_injection for aplicado
Entao retorna risco=True e bloqueia a entrada do agente

Dado um prompt contendo um CPF
Quando mask_pii for aplicado
Entao o CPF e substituido por [PII]
```

## Status
- Iniciado 2026-08-23. Execução autônoma S10-A → S10-B → S10-C (push a cada fase).
