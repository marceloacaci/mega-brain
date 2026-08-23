# Sprint 9 — v2.0 Inovação (semântica · compressão · swarm · LLM local)
**Duração**: 2 semanas (10 dias úteis) | **Objetivo**: entregar o teto de evolução do
MEGA BRAIN (ver `docs/brainstorm.md`) com 4 capacidades v2.0, todas com **fallback
heurístico** (sem dependência obrigatória de Ollama/embeddings).

## Meta do Sprint (Sprint Goal)
"O MCP expõe correlação semântica, compressão de contexto, Multi-Agent Swarm e
LLM local — cada um degradando graciosamente para modo heurístico quando Ollama
não está disponível, mantendo 100% de funcionalidade offline."

## Tarefas (baixo nível, Story Points)
| ID | Tarefa | SP | Dependência | Artefato |
|----|--------|:--:|-------------|----------|
| T1 | `semantic.py`: related_notes/suggest (embeddings Ollama opcional, Jaccard fallback) | 3 | — | semantic.py |
| T2 | `compress.py`: compress_text/compress_note (regras + estimativa de tokens) | 2 | — | compress.py |
| T3 | `swarm.py`: 5 agentes (indexer/correlator/guardian/predictive/metric) + run_swarm | 3 | — | swarm.py |
| T4 | `llm_local.py`: reason (Ollama opcional, heuristic fallback) | 2 | — | llm_local.py |
| T5 | Rotas `/related /suggest /compress /swarm /reason` no MCP (try/except) | 2 | T1–T4 | mcp_obsidian_server.py |
| T6 | `tests/e2e_v2.py` (5 checks, fallback) + run_all + CI | 2 | T5 | e2e_v2.py, ci-cd.yml |
| T7 | `docs/sprints/sprint-9.md` + chronogram v2.0 | 1 | T1–T6 | docs |

**Dependências**: T5 depende de T1–T4; T6–T7 dependem de T5.

## Critérios de Aceitação (Gherkin)
```gherkin
Dado o MCP sem OLLAMA_URL configurado
Quando GET /related?path=P for chamado
Entao retorna lista de notas por sobreposicao de tokens (Jaccard) sem erro

Dado uma daily note com ruido
Quando GET /compress?path=D for chamado
Entao tokens_after < tokens_before e estrutura (links/tags) preservada

Dado uma query qualquer
Quando POST /swarm for chamado
Entao os 5 agentes retornam contrato valido (meta.elapsed_ms presente)

Dado um prompt
Quando POST /reason for chamado sem Ollama
Entao source="heuristic" e response nao vazia
```

## Escopo entregue
- `semantic.py` — correlação por cosseno (Ollama) ou Jaccard (fallback).
- `compress.py` — compressão determinística + `estimate_tokens` (~4 chars/token).
- `swarm.py` — orquestração leve de 5 agentes (contrato puro).
- `llm_local.py` — `reason` via Ollama ou heurística estruturada.
- Rotas v2.0 no MCP com try/except (500 legível em vez de drop de conexão).
- `tests/e2e_v2.py` (5/5) + `run_all` (7/7) + CI.

## Status
- Concluído em 2026-08-23. v2.0 funcional em modo fallback (CI Linux + dev Windows).
- Ativação de IA real: setar `OLLAMA_URL` + `OLLAMA_MODEL` no `.env` (docker-compose)
  faz `/related`/`/suggest`/`/reason` usarem embeddings/Ollama automaticamente.

[[sprint-8]]

[[sprint-5]]

[[sprint-4]]
