# Brainstorm — Inovação e Teto de Evolução (MEGA BRAIN)

> Roadmap de inovação disruptiva de longo prazo (v2.0+). Complementa o
> [`docs/brainstorm.md` original](brainstorm.md) com matriz de impacto e gargalos.

## 1. Recursos Avançados (v2.0+)

### 1.1 Modelos de Linguagem de Código Aberto locais
- Rodar embeddings/LLM **locais** (ex.: Ollama, modelo `nomic-embed-text`) para
  busca semântica e sugestão, eliminando custo de API e mantendo dados no disco.
- Mitiga **LLM06** (vazamento de informação) — nada sai da máquina.

### 1.2 Agentes Colaborativos Autônomos (Multi-Agent Swarms)
- Swarm de agentes especializados: *Indexador*, *Correlacionador*, *Guardião*,
  *Preditivo*, *Métrico* operando em paralelo sobre o vault.
- Orquestração leve (sem framework pesado): o Hermes Agent coordena; cada modo é
  um "agente" com contrato de entrada/saída bem definido.

### 1.3 Otimização de custo por janelas de contexto comprimidas
- Compressão de contexto (resumo incremental de daily notes/MOCs) antes de enviar
  ao LLM, reduzindo tokens e latência.
- Cache de consultas (`/search`) com TTL no Redis (já previsto em M3).

### 1.4 Outras ideias (do brainstorm original)
- Correlação semântica com IA (embeddings sugerindo notas relacionadas).
- Integração com Calendário (Google/Outlook) ou export `.ics`.
- Captura por Voz (reuso da transcrição do Hermes).
- Dashboard Web vivo lendo o MCP (reuso das rotas existentes).
- Alertas proativos (`90_ALERTS`) quando métrica cai.
- Exportação para Publish (MOCs como site estático).
- Failover de backup (segundo destino) e validação de integridade.

## 2. Matriz de Impacto vs. Complexidade
| Ideia | Impacto (1–5) | Complexidade (1–5) | Razão (ganho/esforço) | Mitigador open-source |
|-------|:---:|:---:|:---:|------------------------|
| Cache Redis em `/search` (M3) | 3 | 1 | 3.0 | Redis nativo (já em compose) |
| Dashboard Web (MCP) | 4 | 2 | 2.0 | Reuso de rotas HTTP existentes |
| Modo preditivo (heurístico) | 4 | 2 | 2.0 | Tags/links (sem IA) |
| Testes E2E automatizados | 4 | 2 | 2.0 | pytest + smoke_test |
| Correlação semântica (IA) | 5 | 3 | 1.7 | `nomic-embed-text` local |
| Failover de backup | 3 | 1 | 3.0 | robocopy + 2º destino |
| Validação de integridade | 3 | 2 | 1.5 | checksum de frontmatter |
| Captura por voz | 3 | 4 | 0.75 | Transcrição do Hermes |
| Multi-Agent Swarm | 5 | 4 | 1.25 | Orquestração Hermes + modos |
| LLM local (Ollama) | 4 | 3 | 1.3 | Ollama (MIT) |
| Compressão de contexto | 4 | 3 | 1.3 | Resumo incremental |
| Integração calendário | 2 | 3 | 0.67 | Export `.ics` |

## 3. Gargalos Técnicos e Mitigadores
| Gargalo | Impacto | Mitigador (open-source) |
|---------|---------|--------------------------|
| Custo operacional de API (LLM/embeddings) | Alto em escala | LLM/embeddings **locais** (Ollama) + cache TTL |
| Limitação de I/O em buscas de similaridade em larga escala | Latência | Índice invertido em memória + Redis; FAISS para vetores |
| Rate limit de provedores externos | Disponibilidade | Fallback heurístico (tags/links) já implementado |
| Corrupção de `.last_light.txt` | Reindex desnecessário | try/catch falha-segura (já feito) |
| Dataview não instalado | Dashboard bruto | Documentar plugin obrigatório no setup |
| Lock de reindex | Travamento | Watcher respeita `.reindex.lock` < 30min |

## 4. Recomendação PO
Priorizar **Cache Redis** e **Dashboard Web** (alto impacto, baixa complexidade) em M3,
e **Testes E2E** (reduz regressões). IA semântica (v2.0) só após consolidar a base
heurística — evitando custo e dependência externa prematura.

[[architecture]]

[[README]]

[[sprint-9]]
