# 🧠 MEGA BRAIN — Segundo Cérebro Obsidian

> Projeto de automação de conhecimento pessoal: transforma um cofre Obsidian num
> **Segundo Cérebro vivo** onde tudo o que é feito no Hermes Agent é automaticamente
> indexado, correlacionado, capturado e aprendido — de forma silenciosa e proativa.

---

## 1. Visão Geral

### Objetivo
Tornar o cofre Obsidian um **cérebro central** que:
- **Indexa** automaticamente qualquer tarefa/conhecimento gerado no Hermes Agent.
- **Correlaciona** padrões, preferências e decisões entre projetos.
- **Captura** contexto (daily notes, MOCs, métricas) sem intervenção manual.
- **Aprende** continuamente via modos (correlacionador, guardião, preditivo, métrico, indexador).

### Escopo
- Automação do vault via **hooks PowerShell** disparados pelo Hermes Agent.
- **MCP server** (Model Context Protocol) em Python para leitura/escrita/busca no vault.
- **Dashboard** `INDEX_GERAL.md` gerado por script (nunca editado à mão).
- **Backups** rotativos e **reindex** agendados (light 6h + deep semanal).

### Público-alvo
- Usuários do **Hermes Agent** que querem memória de longo prazo persistente.
- Praticantes de **PKM** (Personal Knowledge Management) com Obsidian.
- Desenvolvedores que desejam um "segundo cérebro" versionável e automatizado.

---

## 2. Arquitetura de Alto Nível

```
┌─────────────────┐         hooks (PowerShell)        ┌──────────────────────┐
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
            │ MCP HTTP :8770                                       │ Dataview (plugin)
            ▼                                                      ▼
┌──────────────────────┐                              ┌──────────────────────┐
│  MCP SERVER (Python)  │                              │  INDEX_GERAL.md       │
│  ThreadingHTTPServer  │                              │  (dashboard gerado)   │
│  /health /search /... │                              └──────────────────────┘
└───────────┬───────────┘
            │ reindex_hybrid.ps1 (-Mode light|deep)
            ▼
┌──────────────────────┐   ┌──────────────────┐   ┌──────────────────────────┐
│  Watcher (Python)     │   │  Scheduler (Win) │   │  Backup (robocopy)        │
│  monitora mudanças    │   │  tarefas 6h/deep  │   │  full + incremental      │
└──────────────────────┘   └──────────────────┘   └──────────────────────────┘
```

Detalhes em [`docs/architecture.md`](docs/architecture.md).

---

## 3. Tecnologias Principais

| Camada | Tecnologia | Papel |
|--------|-----------|-------|
| Orquestração | **Hermes Agent** | Executa tarefas e dispara hooks |
| Automação | **PowerShell 7** (Windows) | Hooks pré/pós-tarefa, scripts de reindex/backup |
| API do vault | **Python 3.10+** (`ThreadingHTTPServer`) | MCP server HTTP na porta 8770 |
| Knowledge Base | **Obsidian** + plugin **Dataview** | Armazenamento e dashboard vivo |
| Backup | **robocopy** | Cópias full + incremental |
| Agendamento | **Agendador de Tarefas Windows** | Reindex light/deep, backups, watcher |
| Versionamento | **Git** | Histórico do vault (este repositório) |

---

## 4. Roadmap (3–6 meses)

| Mês | Foco | Entregas |
|-----|------|----------|
| **M1** | Consolidação | Hooks estáveis, MCP 9 rotas, dashboard gerado, backup rotativo |
| **M2** | Inteligência | Modo preditivo (sugestão de arquivos), correlação semântica leve |
| **M3** | Observabilidade | Métricas enriquecidas, alertas (90_ALERTS), saúde executável |
| **M4** | Extensibilidade | Novas rotas MCP sob demanda, templates de captura |
| **M5** | Resiliência | Failover de backup, validação de integridade do vault |
| **M6** | Polimento | Documentação, onboarding, testes automatizados do pipeline |

---

## 5. Setup Local

### Pré-requisitos
- Windows 10/11 com **PowerShell 7** (`pwsh`).
- **Python 3.10+** com `pip`.
- **Obsidian** com plugin **Dataview** instalado.
- **Hermes Agent** configurado.
- Agendador de Tarefas Windows (admin para registrar tarefas).

### Instalação
```powershell
# 1. Clonar
git clone https://github.com/marceloacaci/mega-brain.git
cd mega-brain

# 2. Subir o MCP server (porta 8770)
python "80_SYSTEM/SCRIPTS/mcp_obsidian_server.py" --port 8770

# 3. Verificar saúde
curl http://localhost:8770/health
# → {"ok": true, "vault": "..."}

# 4. (Opcional) registrar tarefas agendadas e watcher
pwsh -NoProfile -ExecutionPolicy Bypass -File "80_SYSTEM/SCRIPTS/install_tasks.ps1"
```

### Uso rápido (wrapper)
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "80_SYSTEM/SCRIPTS/megabrain.ps1" health
pwsh -NoProfile -ExecutionPolicy Bypass -File "80_SYSTEM/SCRIPTS/megabrain.ps1" search "MeuBolso"
```

---

## 6. Guia de Contribuição

### Branch Strategy
- `master`: estável, espelha o vault em produção.
- `feature/<nome>`: novas funcionalidades de script/hook.
- `fix/<nome>`: correções.
- PRs para `master` com revisão.

### PR Template
```
## O que muda
## Por quê
## Como testar (ex.: rode o hook com params PT: -Tarefa -Projeto -Resultado -Resumo)
## Checklist
- [ ] Testado no vault local
- [ ] Sem quebra de hooks (try/catch falha-segura)
- [ ] Documentado em docs/ se aplicável
```

### Código de Conduta
- Respeito mútuo; linguagem construtiva.
- Mudanças em `INDEX_GERAL.md` **não** são feitas à mão — edite `reindex_hybrid.ps1`.
- Nomes de parâmetros de hooks em **português** (`-Tarefa`, `-Projeto`, `-Resultado`, `-Resumo`).

---

## 7. Próximos Passos (sugestão ao Product Owner)
1. **Priorizar** testes automatizados do pipeline (hooks + reindex) — ver [`docs/sprints`](docs/sprints/).
2. **Expandir** rotas MCP conforme demanda (ex: `rename`, `move`).
3. **Enriquecer** dashboard com mais blocos Dataview validados.
4. **Documentar** runbook de recuperação de backup (90_ALERTS).

---

## Estrutura do Repositório
```
mega-brain/
├── 00_INBOX/               # Capturas brutas
├── 10_MEGA_BRAIN/          # Cérebro central (Hermes escreve)
├── 20_DAILY_NOTES/         # Diário automático
├── 30_PROJECTS/            # Projetos (PARA)
├── 40_AREAS/               # Áreas da vida
├── 50_METRICS/             # Métricas de execução
├── 50_RESOURCES/           # Conhecimento reutilizável
├── 60_ARCHIVE/             # Arquivados
├── 70_MOCS/                # Maps of Content
├── 80_SYSTEM/              # Scripts, hooks, MCP, templates
├── 90_ALERTS/              # Alertas
├── docs/                   # Documentação técnica (este projeto)
├── assets/                 # Wireframes, diagramas
└── README.md               # Este arquivo
```

> Documentação detalhada: [`docs/architecture.md`](docs/architecture.md),
> [`docs/uml/`](docs/uml/), [`docs/sprints/`](docs/sprints/), [`docs/brainstorm.md`](docs/brainstorm.md).
