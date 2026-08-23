# Arquitetura de Software — MEGA BRAIN

> Blueprint técnico do sistema de automação do vault Obsidian. Complementa o
> [`README.md`](../README.md) e os diagramas em [`uml/`](uml/).

---

## 1. Padrão de Arquitetura de Software

O MEGA BRAIN adota uma **Arquitetura Hexagonal (Ports & Adapters)** implementada
de forma enxuta, centrada no vault como fonte de verdade e isolando o acesso por
trás de portas (MCP HTTP) e adaptadores (hooks PowerShell, Watcher, Backup).

### 1.1 Justificativa técnica
- **PowerShell 7** para hooks: integra nativamente com o Agendador de Tarefas
  Windows e com o Hermes Agent; sintaxe moderna (`Join-Path`, `ConvertFrom-Json`).
- **Python `ThreadingHTTPServer`** para o MCP: evita dependências pesadas de
  framework; `ThreadingHTTPServer` não bloqueia sob ligações pendentes (crítico
  para `/health` responder mesmo sob carga).
- **Obsidian + Dataview**: formato `.md` com frontmatter é indexável, versionável
  e legível; Dataview cria dashboards vivos sem banco de dados.
- **robocopy** para backup: nativo no Windows, suporta retries e exclusões
  (`.obsidian`, `.trash`) sem instalar ferramentas externas.
- **Git**: versiona o código de automação, permitindo auditoria e rollback.
- **Docker (dev/CI apenas)**: imagem de validação (pwsh + py3.11) para tornar
  lint/SAST/smoke test reproduzíveis — **não** é o runtime de produção (o vault
  vive no Windows com Obsidian).

### 1.2 Padrões de Projeto aplicados
- **Repository / Gateway**: o MCP server isola o acesso ao vault (leitura/escrita)
  por trás de rotas REST, permitindo que o Hermes Agent (ou outra ferramenta)
  opere sem conhecer a estrutura de arquivos.
- **Observer (Watcher)**: `watcher.py` monitora mudanças no vault (debounce 2s)
  e dispara ações de sincronização.
- **Strategy (Modos)**: `config.json` habilita modos (correlacionador, guardião,
  preditivo, métrico, indexador) que alteram o comportamento em runtime.
- **Template Method (Reindex)**: `reindex_hybrid.ps1` tem dois modos (`light`,
  `deep`) que compartilham a montagem do dashboard, variando só o escopo.
- **Facade (Hooks)**: `pre_`/`post_task_hook.ps1` expõem uma interface simples
  (`-Tarefa -Projeto -Resultado -Resumo`) sobre a complexidade do cérebro.
- **Cache-Aside (roadmap M3)**: consultas `/search` podem ser servidas de um
  Redis com TTL, caindo para o índice heurístico em cache miss.

---

## 2. Pipeline de Ingestão Cognitiva (MCE)

O fluxo de ingestão segue 4 camadas. O "chunk" unitário é o **nó de conhecimento**
(nota `.md` + frontmatter), não o arquivo inteiro.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ CAMADA 1 — INGESTÃO DE CONTEXTO (Context Ingestion)                       │
│  • Hermes Agent dispara pre_task_hook.ps1                                 │
│  • Hook lê INDEX_GERAL.md + MOCs relevantes (contexto de entrada)         │
│  • Watcher detecta mudanças externas (debounce 2s) e sinaliza reindex     │
└───────────────────────────────────┬──────────────────────────────────────┘
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAMADA 2 — FATIAMENTO SEMÂNTICO (Semantic Chunking)                       │
│  • Notas divididas por seções (heading H1/H2) + frontmatter→metadados     │
│  • Tokens de janela respeitando limite do modelo (default 4h debounce)    │
│  • Placeholders de dashboard preenchidos por reindex_hybrid.ps1           │
└───────────────────────────────────┬──────────────────────────────────────┘
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAMADA 3 — EXTRAÇÃO DE DNA COGNITIVO (Heuristics & Rules)                 │
│  • Regras (tags, links, `[HERMES-AGENT]` markers) extraem padrões         │
│  • Modos Strategy aplicam heurísticas:                                    │
│      - correlacionador: liga notas por coocorrência de tags               │
│      - guardião: valida integridade de frontmatter                        │
│      - preditivo: sugere arquivos por histórico de horário/projeto        │
│      - métrico: agrega 50_METRICS                                         │
│      - indexador: mantém índice invertido em memória (tags+links)         │
└───────────────────────────────────┬──────────────────────────────────────┘
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAMADA 4 — INDEXAÇÃO HÍBRIDA (Hybrid Index)                               │
│  • Índice HEURÍSTICO (BM25-like sobre texto + grafo de links/tags) — hj   │
│  • Índice VETORIAL (roadmap v2.0): embeddings locais/API → busca semântica│
│  • Saída: INDEX_GERAL.md (dashboard) + .last_light.txt (timestamp)        │
│  • Consulta: MCP /search (cache Redis opcional em M3)                      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Camada 1 — Ingestão de Contexto
1. Hermes Agent inicia tarefa → `pre_task_hook.ps1` consulta `INDEX_GERAL.md` + MOCs.
2. Tarefa executada; ao terminar, `post_task_hook.ps1` registra no daily note.

### 2.2 Camada 2 — Fatiamento Semântico
- Unidade = nota ou subseção sob heading. Frontmatter vira metadado estruturado.
- `reindex_hybrid.ps1` monta o dashboard via placeholders (Template Method).

### 2.3 Camada 3 — DNA Cognitivo
- Heurísticas determinísticas primeiro (tags/links); IA semântica só em v2.0.
- `config.json` habilita modos em runtime (Strategy).

### 2.4 Camada 4 — Indexação Híbrida
- **Heurística (BM25-like)**: busca textual + grafo de links/tags (sem serviço externo).
- **Vetorial (v2.0)**: embeddings opcionais; o MCP expõe `/search` de forma agnóstica
  à fonte do índice, permitindo evoluir de heurística→híbrido sem quebrar clientes.

---

## 3. Segurança e Governança de IA

O MEGA BRAIN processa notas que podem conter dados pessoais. A governança segue
boas-práticas do **OWASP Top 10 for LLM Applications** e princípios de *privacy-by-design*.

### 3.1 Tratamento de Alucinações
- **Fonte única de verdade**: o vault (Markdown versionado), nunca texto gerado solto.
- **Citação obrigatória**: respostas do modo "indexador/preditivo" referenciam o
  caminho da nota de origem (`[[nota]]` ou `path:`), permitindo auditoria.
- **Fallback heurístico**: se o caminho de IA falhar (rate limit/custo), o sistema
  degrada para correlação por tags/links (já implementado).

### 3.2 Segurança contra Injeção de Prompts (Prompt Injection)
- **Isolamento de fronteira**: o MCP server aceita apenas rotas REST bem definidas;
  conteúdo de notas NUNCA é injetado como instrução de sistema do Hermes.
- **Sanitização de entrada**: parâmetros de hooks (`-Tarefa`, `-Projeto`, etc.)
  passam por validação de caracteres e comprimento; paths são normalizados e
  confinados ao `VAULT_ROOT` (defesa contra path traversal).
- **Princípio de menor privilégio**: hooks rodam com o usuário local; sem escalação.

### 3.3 Tratamento e Mascaramento de PII
- `.gitignore` exclui `.obsidian/`, `LOGS/`, `Backups/` e `*.log` do versionamento.
- `.env.example` documenta variáveis **sem** segredos reais; tokens de LLM/Redis
  ficam fora do repo.
- Modo "guardião" (roadmap) valida frontmatter e pode sinalizar campos sensíveis
  em `90_ALERTS` para revisão humana (mascaramento, não deleção automática).

### 3.4 Conformidade OWASP LLM Top 10 (mapeamento)
| OWASP LLM | Mitigação no MEGA BRAIN |
|-----------|--------------------------|
| LLM01 Prompt Injection | Fronteira MCP + sanitização + confinamento de path |
| LLM02 Insecure Output | Citação obrigatória + fallback heurístico |
| LLM03 Training Data Poisoning | Vault versionado (Git) + checksum de INDEX_GERAL |
| LLM04 Model Denial of Service | Cache Redis (TTL) em `/search`; debounce do Watcher |
| LLM05 Supply Chain | Imagem Docker mínima + `py_compile`/PSScriptAnalyzer no CI |
| LLM06 Sensitive Info Disclosure | `.gitignore` + `.env.example` sem segredos + modo guardião |
| LLM07 Insecure Plugin Design | Rotas MCP com schema fixo + validação de payload |
| LLM08 Excessive Agency | Hooks falha-segura (try/catch) + sem autoescalação |
| LLM09 Overreliance | Humano no laço (MOCs, revisão de daily notes) |
| LLM10 Model Theft | Limite de chamadas externas + cache local |

---

## 4. Ambientes
| Ambiente | Descrição |
|----------|-----------|
| **Local** | Vault + MCP server manual (`python mcp_obsidian_server.py`) |
| **Agendado** | Tarefas Windows disparam reindex/backup/watcher sem interação |
| **Validação (CI)** | Contêiner `validate` (pwsh+py3.11) roda lint/SAST/smoke test |
| **Produção** | Vault em uso diário; MCP como serviço de fundo; Redis/Grafana (M3) |

---

## 5. Pipeline CI/CD
Definido em [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml):
- **Lint**: PSScriptAnalyzer (PowerShell) + `py_compile` (Python).
- **SAST**: bandit (Python) + secret-scan (grep de padrões de chave).
- **Testes**: `python tests/smoke_test.py` (sobe MCP em fixture e valida rotas).
- **Build**: imagem multi-stage Docker (alpine) para validação/artefato.

---

## 6. Observabilidade (roadmap M3)
- **Logs JSON**: estruturados por hook/script com campos `ts`, `level`, `op`, `vault`.
- **Métricas**: latência de `/search` e throughput de reindex expostos em
  `/metrics` (formato Prometheus) e coletados por Prometheus → Grafana.
- **Rastreamento**: OpenTelemetry (opcional) para o ciclo sensor→execução.
- **Cache**: Redis com TTL reduz I/O em `/search` (mitiga LLM04).

---

## 7. Testes
- **Unitários**: validação de sintaxe dos `.ps1` (parse em `[scriptblock]`).
- **Integração**: subir MCP server e `curl /health`, `/search`, `/stats`, `/write`.
- **E2E**: rodar `pre_task_hook.ps1` com params PT e confirmar daily note + reindex.
- **Ferramentas**: PSScriptAnalyzer (PowerShell), `pytest`/`py_compile` (Python),
  `curl` (API), `docker compose run validate` (CI).
