# Qualidade e Portões de Revisão — MEGA BRAIN

> Barra técnica inegociável exigida de contribuidores. Alinhado ao ecossistema
> detectado: PowerShell 7 (hooks/scripts) + Python 3.11 (MCP) + Obsidian/Dataview.

## 1. Pirâmide de Testes Automatizados

| Nível | Escopo | % alvo do esforço | Ferramental (compatível) |
|-------|--------|:---:|---------------------------|
| **Unitários** | Sintaxe/parse de `.ps1` (`[scriptblock]`); funções puras do MCP (path normalize, sanitização) | 60% | PSScriptAnalyzer, `pytest` (Python stdlib) |
| **Integração** | MCP server sobe e responde `/health`, `/search`, `/stats`, `/read`, `/write`, `/rename`, `/move` | 30% | `tests/smoke_test.py` (urllib, sem deps), `curl` |
| **End-to-End (E2E)** | Hook pré/pós com params PT atualiza daily note + dispara reindex | 10% | PowerShell (`pwsh`), `pytest` orquestando hooks |

### Cobertura mínima (inegociável)
- **Cobertura de testes > 80%** nas rotas MCP e nas funções de sanitização/confinamento de path.
- Todo novo `.ps1` deve passar por parse em `[scriptblock]` (zero erros de sintaxe).
- Todo novo caminho de código do MCP deve ter ao menos 1 caso em `smoke_test.py`.

### Estratégia "fail-fast"
- Hooks são **falha-seguros**: qualquer exceção é capturada (try/catch) e nunca
  aborta a tarefa do Hermes.
- CI bloqueia merge se lint/SAST/test falharem (ver `.github/workflows/ci-cd.yml`).

## 2. Checklist de Code Review (Pull Request)

O revisor só aprova o PR quando **todas** as cláusulas abaixo forem satisfeitas:

### 2.1 Qualidade de código
- [ ] **Cobertura de testes > 80%** nas áreas tocadas (MCP rotas / sanitização).
- [ ] **Linters sem warnings**: PSScriptAnalyzer (PowerShell) e `py_compile` (Python) verdes.
- [ ] **SAST limpo**: `bandit` sem achados High/Medium; `gitleaks` sem vazamento de segredo.
- [ ] **Tratamento global de exceções**: hooks e scripts têm try/catch falha-seguro.
- [ ] **Conventional Commits** respeitado (`feat|fix|docs|refactor|test|ci|chore...`).

### 2.2 Segurança
- [ ] **Ausência absoluta de chaves privadas hardcoded** (tokens, senhas, paths com segredo).
- [ ] Variáveis sensíveis passam por `.env` / segredos de CI (ver `.env.example`).
- [ ] Parâmetros de hook são **sanitizados** (comprimento, caracteres, path confinement a `VAULT_ROOT`).
- [ ] Conteúdo de notas **nunca** vira instrução de sistema do LLM (defesa LLM01).

### 2.3 Arquitetura & dados
- [ ] `INDEX_GERAL.md` **não** é editado à mão — alteração vem de `reindex_hybrid.ps1`.
- [ ] Novas rotas MCP seguem o schema fixo e validam payload (defesa LLM07).
- [ ] Mudanças em estrutura do vault respeitam os folders PARA (00–90).
- [ ] Backup e watcher continuam funcionando (debounce 2s, retention respeitado).

### 2.4 Documentação
- [ ] `docs/` atualizado quando o comportamento muda (architecture/uml/sprints).
- [ ] `.env.example` documenta nova variável (sem valor secreto).
- [ ] README/runbook refletem o novo passo de uso, se aplicável.

## 3. Portões (gates) por ambiente
| Gate | Gatilho | Bloqueia merge? |
|------|---------|:---:|
| Lint + SAST + Smoke test | PR para `master` | Sim (CI obrigatório) |
| Cobertura < 80% | PR para `master` | Sim |
| Segredo detectado (gitleaks) | Qualquer push | Sim |
| Revisão humana + checklist | PR para `master` | Sim |

## 4. Comandos de verificação local (pré-PR)
```powershell
# PowerShell lint
Get-ChildItem 80_SYSTEM -Recurse -Filter *.ps1 | ForEach-Object {
  $null = [scriptblock]::Create((Get-Content $_ -Raw))
}
# Python compile
python -m py_compile 80_SYSTEM/SCRIPTS/mcp_obsidian_server.py
# Smoke test (sobe MCP em fixture)
python tests/smoke_test.py
# SAST Python (se bandit instalado)
bandit -r 80_SYSTEM/SCRIPTS 80_SYSTEM/MCP tests -ll
```

[[README]]

[[architecture]]

[[sprint-1]]
