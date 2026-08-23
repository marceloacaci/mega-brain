# 🧠 MEGA BRAIN — Segundo Cérebro Obsidian

> Sistema de automação de conhecimento pessoal que transforma um cofre Obsidian num
> **Segundo Cérebro vivo**: tudo o que é feito no Hermes Agent é automaticamente
> indexado, correlacionado, capturado e aprendido — de forma silenciosa e proativa.

Este repositório versiona o **código de automação** do vault (hooks, MCP server,
scripts, documentação de arquitetura e engenharia). O cofre Obsidian em si é o
alvo da automação e reside fora do Git (ver `.gitignore`).

---

## 1. Visão Geral do Produto

| Item | Descrição |
|------|-----------|
| **Propósito** | Atuar como **barramento de ingestão cognitiva** e camada de memória de longo prazo para o Hermes Agent. |
| **Personalidade** | Plugin de orquestração autônoma + motor de ingestão por chunks semânticos (Markdown/frontmatter) + índice vivo (`INDEX_GERAL.md`). |
| **Padrão de conhecimento** | *Open Knowledge Format (OKF)* — notas `.md` com frontmatter versionáveis, legíveis e indexáveis; índice híbrido heurístico (tags + links) com evolução opcional para vetorial. |
| **Orquestração** | Hermes Agent dispara hooks pré/pós-tarefa; um MCP server expõe o vault via HTTP. |

### O que o MEGA BRAIN faz
- **Indexa** automaticamente qualquer tarefa/conhecimento gerado no Hermes Agent.
- **Correlaciona** padrões, preferências e decisões entre projetos (modos: correlacionador, guardião, preditivo, métrico, indexador).
- **Captura** contexto (daily notes, MOCs, métricas) sem intervenção manual.
- **Aprende** continuamente via modos configuráveis em runtime.

### Público-alvo
- Usuários do **Hermes Agent** que querem memória de longo prazo persistente.
- Praticantes de **PKM** (Personal Knowledge Management) com Obsidian.
- Desenvolvedores que desejam um "segundo cérebro" versionável e automatizado.

---

## 2. Arquitetura de Alto Nível

```
┌─────────────────┐      hooks (PowerShell 7)         ┌──────────────────────┐
│  Hermes Agent   │ ───────────────────────────────▶ │  HOOKS_HERMES/        │
│  (orquestrador) │ ◀─────────────────────────────── │  pre_/post_task_hook  │
└─────────────────┘                                   └──────────┬───────────┘
                                                                 │ Invoke-LightReindexIfNeeded
                                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           VAULT OBSIDIAN (MEGA BRAIN)                           │
│  00_INBOX · 10_MEGA_BRAIN · 20_DAILY_NOTES · 30_PROJECTS · 40_AREAS ·         │
│  50_METRICS · 50_RESOURCES · 60_ARCHIVE · 70_MOCS · 80_SYSTEM · 90_ALERTS      │
└───────────┬───────────────────────────────────────────────────┬──────────────┘
            │ MCP HTTP (porta configurável, padrão 8770)         │ Dataview (plugin)
            ▼                                                      ▼
┌──────────────────────┐                              ┌──────────────────────┐
│  MCP SERVER (Python)  │                              │  INDEX_GERAL.md       │
│  ThreadingHTTPServer  │                              │  (dashboard gerado)   │
│  /health /search /... │                              └──────────────────────┘
└───────────┬───────────┘
            │ reindex_hybrid.ps1 (-Mode light|deep) + cache (TTL, opcional)
            ▼
┌──────────────────────┐   ┌──────────────────┐   ┌──────────────────────────┐
│  Watcher (Python)     │   │  Scheduler (Win) │   │  Backup (robocopy)        │
│  monitora mudanças    │   │  tarefas 6h/deep  │   │  full + incremental      │
└──────────────────────┘   └──────────────────┘   └──────────────────────────┘
```

Detalhes técnicos, pipeline MCE e governança de IA: [`docs/architecture.md`](docs/architecture.md).
Diagramas UML (PlantUML): [`docs/uml/`](docs/uml/).

---

## 3. Tecnologias Principais

| Camada | Tecnologia | Papel |
|--------|-----------|-------|
| Orquestração | **Hermes Agent** | Executa tarefas e dispara hooks |
| Automação | **PowerShell 7** (Windows) | Hooks pré/pós-tarefa, reindex, backup |
| API do vault | **Python 3.11** (`ThreadingHTTPServer`) | MCP server HTTP (porta padrão **8770**) |
| Cache de consultas | **Redis** (opcional, roadmap M3) | TTL para `/search` (mitiga I/O) |
| Knowledge Base | **Obsidian** + plugin **Dataview** | Armazenamento e dashboard vivo |
| Backup | **robocopy** | Cópias full + incremental |
| Agendamento | **Agendador de Tarefas Windows** | Reindex light/deep, backups, watcher |
| Telemetria | **Prometheus + Grafana** (roadmap M3) | Métricas de latência/throughput |
| Versionamento | **Git** | Histórico do código de automação (este repo) |
| Container (dev/CI) | **Docker** (imagem de validação) | Lint + SAST + smoke test reproduzíveis |
| CI/CD | **GitHub Actions** | Validação contínua + build de imagem |

---

## 4. Setup Orientado a Contêineres

### 4.1 Pré-requisitos (máquina-alvo / produção)
- Windows 10/11 com **PowerShell 7** (`pwsh`).
- **Python 3.10+** com `pip`.
- **Obsidian** com plugins **Dataview**, **Templater**, **QuickAdd**.
- **Hermes Agent** configurado.
- Agendador de Tarefas Windows (admin para registrar tarefas).
- Opcional: **Redis** (cache TTL) e **Docker** (validação/CI).

### 4.2 Variáveis de ambiente
Copie e preencha (sem segredos reais — veja `.env.example`):
```powershell
Copy-Item .env.example .env
# Edite .env: VAULT_ROOT, MCP_PORT, REDIS_URL, LOG_LEVEL, GRAFANA/PROME_URLs
```

### 4.3 Instalação local (Windows)
```powershell
# 1. Clonar
git clone https://github.com/marceloacaci/mega-brain.git
cd mega-brain

# 2. Subir o MCP server (porta padrão 8770, sobrescreva com MCP_PORT)
python "80_SYSTEM/SCRIPTS/mcp_obsidian_server.py" --port 8770

# 3. Verificar saúde
curl http://localhost:8770/health
# → {"ok": true, "vault": "..."}

# 4. (Opcional) registrar tarefas agendadas + watcher
pwsh -NoProfile -ExecutionPolicy Bypass -File "80_SYSTEM/SCRIPTS/install_tasks.ps1"
```

### 4.4 Uso rápido (wrapper)
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "80_SYSTEM/SCRIPTS/megabrain.ps1" health
pwsh -NoProfile -ExecutionPolicy Bypass -File "80_SYSTEM/SCRIPTS/megabrain.ps1" search "MeuBolso"
```

### 4.5 Seeding do banco / primeiro índice
```powershell
# Gera INDEX_GERAL.md (deep) e zera o timestamp de reindex
pwsh -NoProfile -ExecutionPolicy Bypass -File "80_SYSTEM/SCRIPTS/reindex_hybrid.ps1" -Mode deep
```

### 4.6 Validação em contêiner (CI/ambiente limpo)
```bash
# Imagem de validação: PowerShell 7 + Python 3.11 (ver Dockerfile)
docker compose -f docker-compose.yml run --rm validate
# ou, isolado:
docker build -f Dockerfile -t mega-brain-validate --target validate .
docker run --rm -p 8770:8770 mega-brain-validate
```
> A imagem `validate` roda PSScriptAnalyzer, `py_compile`, smoke test e expõe o MCP
> na porta 8770 (healthcheck nativo). Redis/Grafana são serviços vizinhos no compose
> para validar o caminho de cache e métricas — **não** substituem o vault Obsidian.

---

## 5. Guia de Contribuição Técnico

### 5.1 Trunk-Based Development
- `master`: estável, espelha o vault em produção (este repositório versiona o código).
- `feature/<nome>`: novas funcionalidades de script/hook.
- `fix/<nome>`: correções.
- PRs curtos (≤ 400 linhas de diff ideal) para `master`, com revisão.

### 5.2 Conventional Commits (obrigatório)
```
<tipo>(escopo): <resumo imperativo>

tipos: feat | fix | docs | refactor | test | ci | chore | perf | build
ex.: feat(mcp): adiciona rota /rename com preservação de conteúdo
     fix(hook): try/catch falha-segura em .last_light.txt corrompido
     docs(architecture): detalha pipeline MCE e governança de IA
```

### 5.3 Template de Pull Request
```markdown
## O que muda
<!-- resumo de 1–3 linhas -->

## Por quê
<!-- motivo / issue / dor -->

## Como testar
<!-- ex.: rode o hook com params PT: -Tarefa -Projeto -Resultado -Resumo -->
<!-- e o smoke test: python tests/smoke_test.py -->

## Riscos / Rollback
<!-- o que pode quebrar e como reverter -->

## Checklist
- [ ] Testado no vault local (ou fixture via smoke_test)
- [ ] Sem quebra de hooks (try/catch falha-segura)
- [ ] Lint verde (PSScriptAnalyzer sem erros; py_compile ok)
- [ ] Documentado em docs/ se aplicável
- [ ] Sem chaves/segredos hardcoded (ver .env.example)
```

### 5.4 Código de Conduta
- Respeito mútuo; linguagem construtiva.
- Mudanças em `INDEX_GERAL.md` **não** são feitas à mão — edite `reindex_hybrid.ps1`.
- Nomes de parâmetros de hooks em **português** (`-Tarefa`, `-Projeto`, `-Resultado`, `-Resumo`).

---

## 6. Roadmap (3–6 meses)

| Mês | Foco | Entregas |
|-----|------|----------|
| **M1** | Consolidação | Hooks estáveis, MCP 9 rotas, dashboard gerado, backup rotativo |
| **M2** | Inteligência | Modo preditivo (sugestão de arquivos), correlação semântica leve |
| **M3** | Observabilidade | Métricas enriquecidas, alertas (90_ALERTS), cache Redis, Prometheus/Grafana |
| **M4** | Extensibilidade | Novas rotas MCP sob demanda, templates de captura |
| **M5** | Resiliência | Failover de backup, validação de integridade do vault |
| **M6** | Polimento | Documentação, onboarding, testes automatizados do pipeline |

---

## 7. Próximos Passos (sugestão ao Product Owner)
1. **Priorizar** testes automatizados do pipeline (hooks + reindex) — ver [`docs/sprints/`](docs/sprints/).
2. **Expandir** rotas MCP conforme demanda (ex: `rename`, `move`).
3. **Enriquecer** dashboard com mais blocos Dataview validados.
4. **Validar** caminho de observabilidade (Redis cache + Prometheus/Grafana) em M3.
5. **Documentar** runbook de recuperação de backup (90_ALERTS).

---

## Estrutura do Repositório
```
mega-brain/
├── .github/workflows/ci-cd.yml   # Lint + SAST + testes + build Docker
├── .env.example                  # Variáveis (tokens/paths), sem segredos
├── Dockerfile                    # Imagem de validação (pwsh + py3.11)
├── docker-compose.yml            # validate + redis + grafana/prom
├── 00_INBOX/                    # Capturas brutas
├── 10_MEGA_BRAIN/               # Cérebro central (Hermes escreve)
├── 20_DAILY_NOTES/              # Diário automático
├── 30_PROJECTS/                 # Projetos (PARA)
├── 40_AREAS/                    # Áreas da vida
├── 50_METRICS/                  # Métricas de execução
├── 50_RESOURCES/                # Conhecimento reutilizável
├── 60_ARCHIVE/                  # Arquivados
├── 70_MOCS/                     # Maps of Content
├── 80_SYSTEM/                   # Scripts, hooks, MCP, templates
├── 90_ALERTS/                   # Alertas
├── docs/                        # Documentação técnica (arquitetura, uml, sprints)
├── tests/smoke_test.py          # Smoke test do MCP (stdlib)
└── README.md                    # Este arquivo
```

> Documentação detalhada: [`docs/architecture.md`](docs/architecture.md),
> [`docs/uml/`](docs/uml/), [`docs/sprints/`](docs/sprints/),
> [`docs/quality.md`](docs/quality.md), [`docs/brainstorm.md`](docs/brainstorm.md).
