# LIVE TRANSCRIPT — Manutenção Autônoma MEGABRAIN (2026-08-24)

> Registro passo-a-passo exigido pela tarefa. Cada linha: comando → saída resumida → decisão.
> Repo: D:/Programas (Disco D)/Obsidian/cofres/Marcelo IA Skills (branch master, origin up-to-date)
> Verificação canônica: `python tests/run_all.py` (10/10) + FCS browser (P10–P14).

## Iteração 1 — Baseline + revisão de código
- CMD: `git status` / `git log -5`
- OUT: branch master em c5112cb; arquivos 50_METRICS/70_MOCS untracked (métricas do sistema).
- CMD: `python tests/run_all.py`
- OUT: **10/10 suítes verdes**.
- DEC: baseline saudável. Revisar 80_SYSTEM/SCRIPTS (P1–P14).

## Iteração 2 — Revisão P8/P9/P11
- LIDO: graph.py, mcp_obsidian_server.py, semantic.py, compress.py, swarm.py, llm_local.py, governance.py.
- DEC:
  - P9 (normalização path): JÁ OK em semantic._norm_rel, compress.compress_note, mcp._vault_path.
  - P8 (do_GET try/except): rotas v2.0 OK; FALTA envelope total do do_GET. → acrescentar.
  - P11 (/graph O(n²)): SEM cache → implementar cache por mtime.
  - P12: web/dashboard.js + web/dashboard.css existem mas NÃO são referenciados → órfãos do anti-padrão. Remover.

## Iteração 3 — P11: cache de grafo por mtime
- FEITO: graph.py → `_GRAPH_CACHE` (thread-safe) + `_vault_signature()` (mtime+count) + `build_graph_cached(k,limit,ttl)`.
- FEITO: mcp_obsidian_server.py → importa `build_graph_cached`; rota `/graph` usa cache, expõe flag `cached`.
- VERIFY: script temp hermes-verify-graph.py → miss 50ms → hit 2ms (25×), invalida ao tocar arquivo. Removido.
- CMD: `python tests/run_all.py` → **10/10 verde**.

## Iteração 4 — P8: envelope do_GET + P12 cleanup + docs
- FEITO: do_GET envolve todo o corpo em try/except → 500 legível (nunca derruba conexão).
- FEITO: `git rm web/dashboard.js web/dashboard.css` (órfãos P12).
- FEITO: 80_SYSTEM/README.md expandido (tabela scripts + mapa P1–P14); docs/chronogram.md log de manutenção.
- CMD: `py_compile` OK; `run_all` **10/10**.
- GIT: commit 2236ac4 + push origin master (c5112cb..2236ac4).

## Iteração 5 — FCS dashboard + bug P13 descoberto
- FCS: subir MCP (porta 8772) + http.server (8782) em fixture (5 notas, 1 órfão). NÃO matar processos.
- FCS browser_console: grafo(5n/7e), donut(5), heatmap(1), órfãos(1), BFS A→B OK, foco, validate OK, conexão OK.
- BUG P13: `search()` lia `data.results` mas `/search` retorna `hits` → painel sempre "sem resultados".
- FIX: dashboard.html search() → usa `data.hits`, status correto.
- FCS re-verify: Busca "Teste" → 3 resultados reais. SEM erros runtime.
- `wc -c` dashboard.html=24519, termina em </html> (P14 OK).
- GIT: commit 7b21e17 + push (2236ac4..7b21e17).

## Estado final
- 2 commits pushados. 10/10 suítes verdes mantidas. FCS do dashboard validado sem runtime errors.
- Servidores de teste (8772/8782) deixados RODANDO (regra de segurança: NÃO matar processos).
- Próximas melhorias seguras (baixo risco, não feitas): unificar limit 400/600 entre semantic/graph; swarm reusar cache de /stats.

## Iteracao 51-58 — continuation worker 2 (teto 1e6)

- `git status`: working tree tinha `80_SYSTEM/SCRIPTS/graph.py` modificado (pendente do worker 1:
  propagar `limit=` para `related_notes`) + `docs/LIVE_TRANSCRIPT_2026-08-24.md` untracked.
- `python tests/run_all.py` -> **10/10 verdes** (baseline confirmada antes de mexer).
- ANALISE P11: `build_graph` chamava `semantic.related_notes(vault, rel)` para CADA nota.
  Cada chamada re-caminhava o vault inteiro com `os.walk` + re-lia + re-tokenizava TODOS os
  arquivos => O(n^2) de I/O em disco (nao apenas O(n^2) de CPU no Jaccard). Era a causa real
  dos ~60s do `/graph` no vault de ~180 notas.
- CORRECAO (sem mudar contrato da rota `/graph`):
  1. Tokens pre-computados UMA vez por nota (dict `tokens`), Jaccard calculado in-memory.
  2. `_match_rel` (O(n) por wikilink) trocado por dict `lookup` (stem/title -> rel), O(1).
  3. Caminho com embeddings (OLLAMA_URL setado) continua delegando a `semantic.related_notes`
     — fallback e comportamento com Ollama preservados.
- BENCHMARK no vault REAL (180 notas): antes ~60s -> **0.36s** (nodes=180, edges=494,
  wikilink=209). Ganho ~165x. `/graph` agora e snappy mesmo sem o cache do P11.
- `python tests/run_all.py` pos-mudanca -> **10/10 verdes**.

## Iteracao 59-70 — Endurecimento de rotas: PATH TRAVERSAL (S11)

- AUDITORIA das rotas do MCP: `_vault_path(rel)` era
  `os.path.join(VAULT, rel.strip("/\\"))` — SEM confinamento ao vault.
- VULNERABILIDADE REAL confirmada com script temp
  (`%TEMP%/hermes-verify-trav.py`): `path=../../../Windows/win.ini` resolvia para
  `D:\Programas (Disco D)\Windows\win.ini` (fora do vault). Impacto:
  * `GET /read?path=../secret.md` -> LEITURA arbitraria de arquivo do disco.
  * `POST /write {"path":"../evil.md"}` -> ESCRITA arbitraria fora do vault.
  Afetava tambem /append /link /tag /rename /move (todas passam por _vault_path).
- CORRECAO (central, 1 ponto): `_vault_path` agora normaliza, resolve com
  `os.path.abspath` e exige que o resultado esteja sob o vault
  (`os.path.normcase(...).startswith(base + os.sep)`), senao levanta
  `VaultPathError` (nova excecao). `read_note` trata como None (404) e o
  `do_POST` mapeia `VaultPathError` -> **400** (nao 500).
- NOVO TESTE `tests/e2e_security.py` (5 checagens, padroes P3/P5/P7/P9):
  read legitimo 200 / read traversal 404 sem vazar / write traversal 400 /
  nenhum arquivo criado fora do vault / write legitimo 200.
- PROVA DE QUE O TESTE PEGA A REGRESSAO: reinjetei o `_vault_path` antigo ->
  o teste FALHOU 3/5 expondo `{'content': 'SEGREDO\n'}` e criando `evil.md`
  fora do vault (rc=1). Restaurado -> rc=0. Teste tem valor real, nao e tautologico.
- `tests/run_all.py`: suite registrada -> **11/11 verdes** (era 10/10).

## Iteracao 71-85 — VERIFICACAO FCS DO DASHBOARD NO BROWSER (P10-P14)

- Fixture temp via `tempfile.mkdtemp` (P9/P11): 6 notas (A->B->C com wikilinks,
  1 orfao isolado, 2 daily notes) em `%TEMP%/mb_dash_99ggcjvk`.
- MCP na porta FRESCA 8774 + `python -m http.server 8784` em `web/` (portas
  confirmadas livres antes de subir — gotcha de porta zumbi do P10).
  `/health` retornou JSON `{"ok":true}` (nao HTML 404) => porta correta.
- `/graph?k=3` respondeu INSTANTANEO no fixture (efeito da otimizacao anterior).
- Browser aberto em `dashboard.html?mcp=http://127.0.0.1:8774`. Verificacoes de
  RUNTIME (P13) chamando as funcoes reais no console:
  * `search()` com 'alpha' -> 3 resultados reais (fix de `hits` do worker 1 CONFIRMADO no browser).
  * `bfsPath('A','C')` -> `["10_MEGA_BRAIN/A.md","30_PROJECTS/C.md"]` OK.
  * `focusNode()` + `clearFocus()` -> sem excecao.
  * `runValidate()` -> "Total notas: 6 · Problemas: 2" (pastas ausentes no fixture, esperado).
  * `loadActivity()` -> heatmap com 2 celulas; `getComputedStyle` provou 30.2x30.2px,
    `rgb(59,130,246)`, com `title` "2026-08-23: 1 notas" => VISIVEL de fato, nao vazio.
  * `stat-nodes`=6, `stat-edges`=8, ping OK (5/5), donut com 4 fatias.
- BUG ENCONTRADO no FCS: `renderOrphans()` chamada sem argumento lancava
  `TypeError: Cannot read properties of undefined (reading 'nodes')`. So aparece em
  runtime (nenhum linter/CI pega — exatamente o cenario do P13).
  CORRECAO: `g = g || GRAPH` + guarda `if(!g || !g.nodes)` com mensagem amigavel.
- Validacao pos-fix: `node --check` no `<script>` extraido, rodado do ROOT (P10) -> OK.
  `wc -c web/dashboard.html` = 24637 e TAIL intacto (`</html>`) => write nao truncou (P14).
  Reload no browser: `renderOrphans()` sem arg -> "• Orfao" (sem excecao).
- Inspecao visual (screenshot): grafo, donut, heatmap, orfaos, tabela de ping e
  metricas Prometheus todos renderizando sem overlap/layout quebrado.
- `python tests/run_all.py` -> **11/11 verdes**.
- NOTA: `web/dashboard.html` esta sendo editado tambem por um agente irmao; mantive
  a alteracao MINIMA e cirurgica (3 linhas) para evitar conflito.
- NOTA: servidores em 8774/8784 deixados VIVOS (regra de seguranca: nao matar processos).

## Iteracao 86-100 — validate_vault: falsos positivos + 2x os.walk (S11)

- DIAGNOSTICO contra o vault REAL: `/validate` reportava 15 problemas, dos quais
  **12 eram link_quebrado** — e 11 deles eram FALSOS POSITIVOS:
  * `[[Projeto X]]`, `[[nota1]]`, `[[links]]` etc. estao dentro de blocos ``` ou
    de inline-code em `PROMPT_MESTRE_v2.md`/`docs/` — sao EXEMPLOS de documentacao.
    Confirmado por script que rastreia o estado de fence linha-a-linha (linha 355
    `dentro_de_fence=True`).
  * `[[${app.metadataCache.fileToLinktext(...)}]]` nos scripts do Excalidraw sao
    PLACEHOLDERS de template, nunca notas.
  * `[[Projeto X]]` aparecia 2x na mesma nota -> 2 problemas identicos (ruido).
- CORRECOES em `validate_vault.py`:
  1. `_strip_code()` remove ```/~~~/`inline` antes de procurar wikilinks.
  2. Placeholders (`${...}`, `{{...}}`) ignorados.
  3. `[[pasta/Nota]]` resolve pelo BASENAME (e o que o Obsidian faz) — antes era
     reportado como quebrado.
  4. Dedupe por alvo dentro da mesma nota.
  5. PERF: `_note_names(root, notes)` reusa a lista ja coletada -> elimina o
     SEGUNDO `os.walk` do vault inteiro por chamada de /validate (era 2x I/O).
- RESULTADO no vault real: 15 -> **4 problemas** (3 notas vazias reais +
  1 link quebrado REAL `[[pentagon-mind]]`). Sinal limpo, sem perder deteccao.
- ANTI-REGRESSAO: `tests/e2e_validate.py` continua PASS (detecta `[[NotaInexistente]]`
  de verdade) => nao suprimi demais.
- NOVO `tests/test_validate_links.py` (6 checagens de unidade): subpath NAO e falso
  positivo / codigo ignorado / template ignorado / link inexistente AINDA reportado /
  dedupe 1x / total_notas correto.
- `tests/run_all.py` -> **12/12 verdes**.

## Iteracao 101-112 — VERIFICACAO CANONICA CI + reducao de duplicacao no swarm

- VERIFICACAO CANONICA (Principio 2 do skill), run `32688009570` (commit 99004bf):
  `gh run view --json jobs` -> **status=completed / conclusion=success**, TODOS os 5 jobs:
  * Testes (smoke MCP + debounce watcher) | success
  * Lint (PowerShell + Python)           | success
  * Testes E2E (hooks PowerShell)        | success
  * SAST (bandit + secret-scan)          | success
  * Build Docker image (multi-stage)     | success
  Ou seja: o fix de path traversal, a otimizacao do grafo e o fix do validate
  estao verdes no CI de verdade, nao apenas localmente.
- REDUCAO DE DUPLICACAO em `swarm.py`: `_agent_indexer` e `_agent_metric` faziam
  CADA UM o seu proprio `os.walk` do vault inteiro (2 varreduras por `run_swarm`).
  Extraido helper `_count_md(vault)` -> devolve `(total, by_dir)` numa unica passada.
- EQUIVALENCIA PROVADA: `total_notes` = 188 antes e depois; `sum(by_dir.values())`
  = 188 (consistente); nenhum agente com 'error'. Comportamento identico.
- `python tests/run_all.py` -> **12/12 verdes**.

## Iteracao 113-120 — Documentacao: Sprint 11 + README

- NOVO `docs/sprints/sprint-11.md` (7817 bytes, tamanho e tail conferidos — P14):
  Sprint 11 "Hardening de Seguranca, Performance e Qualidade de Sinal", seguindo o
  formato dos sprints 1-10 do repo (Sprint Goal, subsprints A-E, Criterios de
  Aceitacao em Gherkin, DoD, tabela de metricas, riscos/divida remanescente).
  Documenta S11-A (path traversal), S11-B (grafo 60s->0.36s), S11-C (falsos
  positivos do validate), S11-D (deduplicacao de os.walk), S11-E (bug FCS do dashboard).
  Inclui a tabela antes/depois com numeros MEDIDOS, nao estimados.
- `80_SYSTEM/README.md`: secao "Sprint 11 — Hardening" + contagem de suites
  atualizada de 10/10 para 12/12.
- Registrada a divida remanescente honestamente: `_strip_code` e regex (nao parser
  Markdown) e `build_graph` continua O(n^2) de CPU (agora em memoria, com limit=600).
- `python tests/run_all.py` -> **12/12 verdes**.
- `git fetch` + `git status`: master sincronizado com origin/master antes do commit.

## Iteracao 121-135 — governance.mask_pii: 2 defeitos reais (S11-F)

- AUDITORIA de `governance.py` com script temp (`%TEMP%/hermes-verify-pii.py`),
  9 casos (positivos + negativos). Dois defeitos REAIS encontrados:
  1. `tel (11) 91234-5678` -> mascarava como `tel ([PII]` (PARENTESE SOLTO): o
     `\(?` opcional casava os digitos mas nao o `(`. Vazava a estrutura do dado
     e a contagem vinha 3 quando havia 4 PII no texto.
  2. `range 1000-2000 itens` -> mascarado como TELEFONE (falso positivo): o padrao
     `9?\d{4}-?\d{4}` nao exigia nem DDD nem o 9 de celular, entao qualquer
     intervalo numerico de 4+4 digitos virava [PII].
- CORRECAO do `_PHONE`: celular (9 + 8 digitos) com ou sem DDD; fixo (8 digitos)
  SOMENTE com DDD; `(?<![\w.])` evita casar dentro de versao/hash.
- VALIDACAO (todos conferidos):
  * mascara: `(11) 91234-5678`, `11 91234-5678`, `91234-5678`, `+55 11 91234-5678`,
    `(11) 3123-4567` -> `[PII]` limpo, sem parentese solto.
  * NAO mascara: `1.0.0`, `porta 8770 e ttl 300`, `commit 2236ac4 de 2026-08-24`,
    `range 1000-2000`, `porta 8770-8780`, `3123-4567 sem ddd`.
  * combinado email+CPF+telefone+apikey -> count = **4** (era 3).
- NOVO `tests/test_governance_pii.py` (**20 checagens**), inclui anti-regressao de
  injection e de `sanitize_input`.
- `tests/run_all.py` -> **13/13 verdes**.

## Iteracao 136-150 — compress.py: contrato violado (S11-G)

- AUDITORIA de `compress.py`. Dois defeitos REAIS:
  1. **CONTRATO VIOLADO**: `tokens_after` podia ESTOURAR `max_tokens`. O marcador
     `"\n[...truncado]"` era concatenado DEPOIS de calcular o orcamento, entao
     `compress_text(t, max_tokens=20)` devolvia `tokens_after=22`. Quem chama a
     funcao para caber num limite de contexto de LLM recebia mais do que pediu.
  2. `estimate_tokens("")` retornava **1** (texto vazio nao custa token).
- CORRECOES: `budget = max_tokens*4 - len(_TRUNC_MARK)` (marcador entra no
  orcamento); `estimate_tokens("") == 0`.
- EDGE CASE HONESTO: com `max_tokens=1` o proprio marcador custa ~3 tokens, logo e
  impossivel respeitar 1. Em vez de fingir, documentei o piso: constante
  `MIN_TOKENS = 3` + contrato explicito no docstring
  (`tokens_after <= max(max_tokens, MIN_TOKENS)`). O teste valida o teto real.
- VALIDACAO por orcamento: max=5 ->3, max=20 ->19, max=50 ->36, max=200 ->36.
  Todos dentro do teto.
- NOVO `tests/test_compress_contract.py` (**22 checagens**): invariante do teto,
  coerencia `truncated` <-> marcador, headings/wikilinks preservados, duplicadas
  colapsadas, texto vazio, `compress_note` inexistente -> None.
- PROVA ANTI-TAUTOLOGIA: removi o `- len(_TRUNC_MARK)` do budget -> teste FALHOU
  com `after=22 teto=20`. Restaurado -> 22/22.
- `tests/run_all.py` -> **14/14 verdes**.

## Iteracao 151-160 — VERIFICACAO CANONICA FINAL + estado de encerramento

- Run `32688862974` (commit b6d2101, o ultimo do worker): **completed / success**
  nos 5 jobs (Testes, SAST, E2E hooks PowerShell, Lint, Build Docker).
- Todos os 6 commits deste worker fecharam com CI verde (32688201265, 32688368153,
  32688589507, 32688862974 confirmados individualmente).
- Estado final: `python tests/run_all.py` -> **14/14 suites verdes** (worker comecou em 10/10).
- Servidores de teste 8774 (MCP) e 8784 (http.server) deixados VIVOS por design
  (regra de seguranca: NAO matar processos). Vault fixture temporario em
  `%TEMP%/mb_dash_99ggcjvk` — descartavel.
- Scripts temporarios de verificacao removidos ao final (hermes-verify-trav.py,
  hermes-verify-pii.py, hermes-verify-fixture.py, dash_check.js).

### Resumo do que o worker entregou (S11 — Hardening)
| # | Entrega | Evidencia |
|---|---|---|
| 1 | Path traversal fechado em 7 rotas | e2e_security.py 5/5, validado contra regressao |
| 2 | /graph 60s -> 0.36s (180 notas) | medicao direta, 494 arestas |
| 3 | /validate 15 -> 4 problemas (0 falsos positivos) | test_validate_links.py 6/6 |
| 4 | mask_pii: parentese solto + falso positivo numerico | test_governance_pii.py 20/20 |
| 5 | compress: contrato tokens_after <= max_tokens | test_compress_contract.py 22/22 |
| 6 | -1 os.walk em /validate e -1 em run_swarm | equivalencia provada (188 notas) |
| 7 | Bug de runtime do dashboard (renderOrphans) | FCS no browser + node --check |
| 8 | docs/sprints/sprint-11.md + README atualizado | 12 -> 14 suites documentadas |

**CONCLUSAO**: as melhorias SEGURAS de alto valor identificadas por auditoria foram
esgotadas neste ciclo. As proximas exigiriam mudanca de contrato de rota, nova
dependencia, ou reindexacao por token invertido (mudanca arquitetural) — fora do
criterio "incremental e seguro". Divida remanescente registrada em sprint-11.md.

## Continuacao 2026-08-24 (worker delegado) — Sprint 12 (Hardening v2.0 + auditoria)

### Iter 1 — Baseline + auditoria contra VAULT REAL
- CMD: `git log` / `git status` / `node --version` / `python --version`
- OUT: HEAD=623102a; python 3.11.15; node v26.5.0; 6 arquivos 50_METRICS untracked.
- CMD: `python tests/run_all.py` -> **14/14 suítes verdes** (baseline herdado).
- METODO (P16/S11): rodei cada modulo contra o VAULT REAL em script temp e olhei a saida,
  em vez de confiar no verde do run_all.

### Iter 2 — 3 defasagens REAIS encontradas (não pegadas pelo CI 14/14)
1. **Path traversal em /related e /compress (S11 incompleto)**: `semantic.related_notes`
   e `compress.compress_note` usavam `_norm_rel` QUE NAO confinava ao vault; o S11
   endureceu `_vault_path` no server mas ESQUECEU essas funcoes de biblioteca + as
   rotas v2.0. `/compress?path=../../../x.md` abria arquivo arbitrario (leak de leitura).
2. **/graph O(n^2) de I/O no modo embeddings (regressao do P11)**: `build_graph` chamava
   `related_notes(vault, rel, ...)` POR NOTA quando `OLLAMA_URL` setado -> re-walk do
   vault inteiro para cada nota. O P11 consertou o caminho Jaccard mas o de embeddings
   tinha regredido.
3. `compress` contract: confirmado OK (`tokens_after=187 <= 200`); falsa suspeita inicial
   (eu imprimira `len(dict)` por engano).

### Iter 3 — Fixes S12
- `semantic.py`: adicionado `VaultPathError` + `_vault_rel()` (confinamento ao vault);
  `_norm_rel` e `related_notes` agora levantam em traversal. Mesmo contrato de
  `mcp_obsidian_server._vault_path`.
- `compress.py`: `compress_note` confina via `_vault_rel` (VaultPathError em traversal).
- `graph.py`: modo embeddings agora PRE-COMPUTA embeddings 1x (loop `embeds`) e faz
  cosseno pairwise em memoria; removido o `related_notes` per-note. Caminho Jaccard
  ja era O(n); agora embeddings tambem.
- `mcp_obsidian_server.py`: rotas `/related` e `/compress` capturam `VaultPathError`
  (por nome de classe) -> 400 (igual as rotas de escrita), nunca 500 silencioso.

### Iter 4 — Teste de regressão não-tautológico
- NOVO `tests/test_security_v2.py` (**7 checagens**): traversal em `_norm_rel`,
  `related_notes`, `compress_note`; O(n^2) ausente (checagem estatica de que nao ha
  chamada per-note de related_notes + grafo gera arestas em modo embeddings stubado).
- PROVA ANTI-TAUTOLOGIA: reinseri o bug (per-note `related_notes`) -> checagem estatica
  detecta `per-note=True` (teste FALHARIA). Fixado -> 7/7.
- `run_all.py`: +1 suíte -> **15/15 verdes** (era 14/14).

### Iter 5 — Pendente/FCS
- FCS do dashboard no browser (P10–P14): a fazer neste worker.
- Cronograma/sprints em 30_PROJECTS + docs: a fazer.

