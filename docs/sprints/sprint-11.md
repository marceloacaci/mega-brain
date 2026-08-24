# Sprint 11 — Hardening de Segurança, Performance e Qualidade de Sinal

**Duração**: 2 semanas | **Estado**: **DONE** (2026-08-24)
**Tags**: `#sprint` `#seguranca` `#performance` `#qualidade`

## Meta do Sprint (Sprint Goal)

> "O MCP não pode ser usado para ler ou escrever fora do vault, o `/graph` responde
> em tempo interativo mesmo no vault real, e o `/validate` só reporta problemas que
> um humano realmente precisa corrigir — tudo provado por testes que falham quando
> a correção é revertida."

Diferente dos sprints anteriores (que adicionaram *capacidades*), o S11 é um sprint de
**endurecimento**: nenhuma rota nova, nenhuma dependência nova. Todo o valor está em
corrigir defeitos reais encontrados por auditoria e medição.

---

## S11-A — Segurança: Path Traversal (crítico)

**Problema encontrado.** `_vault_path(rel)` era `os.path.join(VAULT, rel.strip("/\\"))`,
sem confinar o resultado ao vault. Consequência medida:

| Requisição | Antes | Depois |
|---|---|---|
| `GET /read?path=../secret.md` | `200` + conteúdo do arquivo de fora | `404` |
| `POST /write {"path":"../evil.md"}` | `200`, arquivo criado FORA do vault | `400` |

Afetava por herança todas as rotas que passam por `_vault_path`:
`/read`, `/write`, `/append`, `/link`, `/tag`, `/rename`, `/move`.

**Correção.** Um único ponto de controle:

1. `_vault_path` normaliza separadores, resolve com `os.path.abspath` e exige que o
   caminho final esteja sob o vault (`normcase(fp).startswith(normcase(base) + os.sep)`).
2. Nova exceção `VaultPathError`.
3. `read_note` trata como `None` → `404`; `do_POST` mapeia `VaultPathError` → **400**
   (erro do cliente), não `500`.

**Critérios de Aceitação (Gherkin)**

- **CA-1**: Dado `path=../secret.md`, Quando `GET /read`, Então `404` e o conteúdo do
  arquivo externo NÃO aparece na resposta.
- **CA-2**: Dado `path=../evil.md`, Quando `POST /write`, Então `400` e nenhum arquivo
  é criado fora do vault.
- **CA-3**: Dado um path legítimo, Quando `GET /read` / `POST /write`, Então `200`
  (a correção não quebra o caminho bom).

**Teste**: `tests/e2e_security.py` (5 checagens).
**Validação anti-tautologia**: a correção foi *revertida de propósito* e o teste passou a
falhar 3/5, expondo `{"content": "SEGREDO\n"}` e criando `evil.md` fora do vault. Restaurada
a correção, voltou a 5/5. O teste tem poder de detecção real.

---

## S11-B — Performance: `/graph` de 60s para 0,36s

**Problema encontrado.** `graph.build_graph` chamava `semantic.related_notes(vault, rel)`
para **cada** nota. Cada chamada re-executava `os.walk` no vault inteiro, re-lia todos os
arquivos do disco e re-tokenizava tudo. O custo real não era o Jaccard (CPU) — era
**O(n²) de I/O de disco** (o pitfall P11 atribuía o custo apenas ao Jaccard).

**Correção.**

1. Tokens pré-computados **uma vez por nota**; o Jaccard passa a rodar em memória.
2. Índice `lookup` (stem/título → rel) para wikilinks, substituindo `_match_rel`, que era
   O(n) por link.
3. O caminho com embeddings (`OLLAMA_URL` presente) continua delegando a
   `semantic.related_notes` — comportamento com Ollama preservado.

**Medição no vault real (180 notas, 494 arestas)**

| Métrica | Antes | Depois |
|---|---|---|
| `build_graph(k=3)` | ~60 s | **0,36 s** |

Ganho ≈ **165×**. O `/graph` fica interativo mesmo com o cache do P11 frio, o que remove
a causa do `about:blank` documentada no P11 ao testar o dashboard no browser.

---

## S11-C — Qualidade de sinal: `/validate` de 15 para 4 problemas

**Problema encontrado.** Dos 12 `link_quebrado` reportados no vault real, **11 eram
falsos positivos**:

- Wikilinks dentro de blocos ```` ``` ```` ou de `inline code` — são **exemplos de
  documentação** (`PROMPT_MESTRE_v2.md`, `docs/sprints/*`). Confirmado rastreando o estado
  de fence linha-a-linha: `[[Projeto X]]` na linha 355 está dentro de fence.
- `[[${app.metadataCache.fileToLinktext(...)}]]` nos scripts do Excalidraw são
  **placeholders de template**, nunca notas.
- O mesmo alvo repetido na mesma nota gerava N problemas idênticos (ruído).

**Correção.** `_strip_code()` remove código antes de procurar wikilinks; placeholders
(`${...}`, `{{...}}`) são ignorados; `[[pasta/Nota]]` resolve pelo *basename* (é o que o
Obsidian faz); dedupe por alvo dentro da nota.

**Resultado**: 15 → **4 problemas** (3 notas vazias reais + 1 link quebrado real
`[[pentagon-mind]]`). O `tests/e2e_validate.py` continua PASS, provando que a detecção
de links genuinamente quebrados **não** foi suprimida.

**Teste**: `tests/test_validate_links.py` (6 checagens de unidade).

---

## S11-D — Redução de duplicação e I/O

- `validate_vault`: `_note_names(root, notes)` reusa a lista já coletada, eliminando o
  **segundo `os.walk`** do vault por chamada de `/validate`.
- `swarm`: `_agent_indexer` e `_agent_metric` faziam **um `os.walk` cada**. Novo helper
  `_count_md(vault)` devolve `(total, by_dir)` numa única passada. Equivalência provada:
  `total_notes` = 188 antes e depois, `sum(by_dir.values())` = 188.

---

## S11-E — Dashboard: bug de runtime achado no FCS

`renderOrphans()` chamada sem argumento lançava
`TypeError: Cannot read properties of undefined (reading 'nodes')`. Invisível ao CI —
o JS inline do `dashboard.html` não tem checagem estática (pitfall **P13**).

**Correção**: `g = g || GRAPH` + guarda defensiva com mensagem amigável.

**Verificação de fato no browser (FCS, P10–P14)**, contra vault fixture temporário com
6 notas em porta fresca (MCP 8774 + estático 8784):

| Função exercitada | Resultado |
|---|---|
| `search('alpha')` | 3 resultados reais (confirma o fix de `hits`) |
| `bfsPath('A','C')` | `["10_MEGA_BRAIN/A.md","30_PROJECTS/C.md"]` |
| `focusNode()` / `clearFocus()` | sem exceção |
| `runValidate()` | "Total notas: 6 · Problemas: 2" |
| `loadActivity()` | 2 células; `getComputedStyle` = 30,2×30,2 px, `rgb(59,130,246)` |
| `renderOrphans()` sem arg | "• Orfao" (antes: `TypeError`) |

Além disso: `node --check` do `<script>` extraído a partir do ROOT (P10), tamanho do
arquivo conferido no disco vs `bytes_written` e TAIL terminando em `</html>` (P14).

---

## Definition of Done (DoD) — atingida

- [x] `python tests/run_all.py` → **12/12 suítes verdes** (era 10/10; +2 suítes no S11).
- [x] Cada correção acompanhada de teste que **falha se a correção for revertida**.
- [x] **Verificação canônica** (Princípio 2): run `32688009570` — `completed/success`
      nos **5 jobs** (Testes, Lint, E2E hooks, SAST, Build Docker).
- [x] Dashboard verificado no browser (FCS), não apenas por CI verde.
- [x] Nenhuma dependência nova; princípio stdlib preservado.
- [x] Tudo registrado em `docs/LIVE_TRANSCRIPT_2026-08-24.md`.

## Métricas do Sprint

| Indicador | Antes | Depois |
|---|---|---|
| Vulnerabilidades de path traversal | 7 rotas expostas | 0 |
| `build_graph` (vault real, 180 notas) | ~60 s | 0,36 s |
| Falsos positivos em `/validate` | 11 de 12 | 0 |
| Varreduras `os.walk` por `/validate` | 2 | 1 |
| Varreduras `os.walk` por `run_swarm` | 2 | 1 |
| Suítes de teste | 10 | 12 |

## Riscos e dívida remanescente

- `_strip_code` usa regex, não um parser de Markdown: um bloco de código malformado
  (fence não fechado) pode suprimir wikilinks legítimos até o fim do arquivo. Aceito —
  o modo de falha é *silenciar um aviso*, nunca corromper nota.
- `build_graph` continua O(n²) em **CPU** para o Jaccard (agora em memória). Com `limit=600`
  o custo é aceitável; acima disso, indexar por token invertido seria o próximo passo.
- O caminho com Ollama ainda faz uma chamada de embedding por par de notas — só é exercido
  quando `OLLAMA_URL` está setado, e o `tests/e2e_ollama.py` faz SKIP sem ele.
