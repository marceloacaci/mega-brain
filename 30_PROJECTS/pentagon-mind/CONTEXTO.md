---
tipo: contexto
projeto: pentagon-mind
criado: 2026-08-21
tags: ["projeto/pentagon-mind", "contexto"]
---

# 📌 Contexto — PENTAGON-MIND

## Origem
Portal encomendado como "PENTAGON-MIND: Doutrina Militar, Tecnologia e Projeções Geopolíticas dos Estados Unidos". Público-alvo: analistas de defesa, acadêmicos de RI e historiadores militares. Tom objetivo, estéril e altamente técnico.

## Escopo (5 módulos)
1. **Arquitetura & rotas** — Dashboard de Briefing, Doutrina, Políticas Presidenciais, Arsenal/Tecnologia, Impactos Geopolíticos.
2. **Conteúdo aprofundado** — Evolução doutrinária (desgaste→manobra→GPC→MDO); comando executivo (Bush 41 → Trump 2); arsenal e spin-offs (ARPANET→TCP/IP, GPS, microchips, Kevlar, medicina de trauma).
3. **Ontologia de dados** — `data/ontology.json` modela relações Administração ↔ Doutrina ↔ Conflito ↔ Sistema de Armas.
4. **Âncoras acadêmicas** — Citações iipsis litteris (Powell, Mattis, Milley, Dugan, Brodie) + referências CRS / DoD Joint Pubs / SIPRI / JFQ / Foreign Affairs.
5. **Glossário & siglas** — `data/glossary.js` com texto completo (EN), tradução (PT) e gloss; popups inline em toda página.

## Decisões de conteúdo
- **Trump 2 (2025–2029)** tratado como administração distinta (`trump2`), com tensão Irã 2025 e reindustrialização de defesa.
- **Trump (1º mandato)** mantido como `trump` (2017–2021) para não colapsar as timelines.
- **Ano-âncora 2026** em todas as projeções orçamentárias e doutrinárias.
- **Imagens reais** baixadas via API Wikimedia Commons para evitar quebras offline; fallback placeholder via `common.js`.
- **Texto padrão BRANCO ABSOLUTO**; destaques em âmbar; explainers "Em outras palavras…" para público não-especialista.

## Convenções de verificação (FCS)
Servidor Node local (`assets/serve.cjs`) + `assets/verify.js` (node) + teste em browser real com leitura de `getComputedStyle`/DOM. Verificação capturou bug real: sintaxe inválida em `data/glossary.js` (`id: "europe":` → `,`).
