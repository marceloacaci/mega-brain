---
tipo: decisoes
projeto: pentagon-mind
criado: 2026-08-21
tags: ["projeto/pentagon-mind", "decisoes"]
---

# ⚖️ Decisões Técnicas — PENTAGON-MIND

## 1. Imagens: bundle local, não links externos
- **Decisão:** baixar 59 imagens reais (Wikimedia Commons API) para `assets/img/` e referenciar via `window.PM_MEDIA`.
- **Por quê:** evita quebras offline e dependência de hotlink; fallback placeholder via `common.js`.
- **Alternativa rejeitada:** `<img src="https://upload.wikimedia.org/...">` direto (quebra sem rede, CORS, rotatividade de URL).

## 2. Trump 2 como administração separada
- **Decisão:** `trump` (2017–2021) e `trump2` (2025–2029) são entradas distintas na ontologia.
- **Por quê:** preserva a timeline histórica e permite comparar posturas; evita colapso de dados.

## 3. Ano-âncora 2026
- **Decisão:** todas as projeções orçamentárias/doutrinárias referenciam 2026.
- **Por quê:** pedido explícito de atualização contemporânea (Trump 2, Irã 2025, reindustrialização).

## 4. Glossário como dados, não HTML
- **Decisão:** `data/glossary.js` guarda siglas + tradução + gloss; `js/glossary.js` gera popups e a seção #glossario-map.
- **Por quê:** DRY — uma fonte alimenta popups inline em todas as páginas e o mapa do site.

## 5. Servidor: normalização de caminho
- **Decisão:** `path.resolve(__dirname,'..')` + checagem `startsWith(ROOT+sep)` em `serve.cjs`.
- **Por quê:** no Windows, `path.normalize` converte `/` em `\`, causando 403 falso. Corrigido com `path.resolve`.

## 6. Traduções de citações
- **Decisão:** cada citação iipsis litteris (EN) recebe `<span class="quote-translation">` (PT) abaixo.
- **Por quê:** atende requisito de tradução das frases em inglês.
