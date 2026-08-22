---
projeto: PENTAGON-MIND
slug: pentagon-mind
status: ativo
stack: HTML, CSS, JavaScript, Node (servidor local)
prioridade: medio
criado: 2026-08-21 21:37
atualizado: 2026-08-21 21:42
tags: ["projeto/pentagon-mind", "stack/html", "stack/js", "status/ativo", "prioridade/medio"]
---

# 📁 PENTAGON-MIND

> Portal web analítico de nível corporativo sobre doutrina militar, tecnologia de defesa e projeções geopolíticas dos Estados Unidos.

## 🎯 Visão Geral
- **Status:** ativo
- **Prioridade:** medio
- **Stack:** HTML/CSS/JS estático + Node (servidor de verificação)
- **Criado:** 2026-08-21
- **Slug:** `pentagon-mind`
- **Local no disco:** `C:\Users\Marcelo\Desktop\EUA`
- **URL local (servidor):** http://127.0.0.1:8726/

## 🎯 Objetivo
Fornecer análise técnica de alta densidade (padrão RAND / CSIS / SIPRI) sobre o aparato militar dos EUA: doutrina evolutiva (passado→contemporâneo→futuro), posturas presidenciais (Bush pai a Trump 2), arsenal/tecnologia e spin-offs civis da DARPA, impactos geopolíticos, e um glossário de siglas com popup, traduções e explainers "em outras palavras".

## 📂 Estrutura (site em `C:\Users\Marcelo\Desktop\EUA`)
```
EUA/
├── index.html                     ← Dashboard / Briefing de Ameaças
├── doutrina.html                  ← Hub do Pensamento Militar Evolutivo
├── politicas-presidenciais.html   ← Nexo de Comando Executivo (6 presidentes + Trump 2)
├── arsenal-tecnologia.html         ← Engenharia de Defesa & Spin-offs
├── impactos-geopoliticos.html      ← Estudos de Caso & Multidomínio
├── css/styles.css                 ← Design system (command-center)
├── js/{common,nav,glossary,ontology}.js
├── data/{glossary,ontology}.js
├── data/ontology.json             ← Esquema relacional (7 adm, 11 conflitos, 20 armas)
└── assets/img/ (59 imagens reais, domínio público/Governo EUA)
```

## 🔗 Links Rápidos
- [[CONTEXTO|Contexto]] · [[STACK|Stack]] · [[DECISOES|Decisões]] · [[APRENDIZADOS|Aprendizados]] · [[TAREFAS|Tarefas]]
- [[GLOSSARIO_SIGLAS|Glossário de Siglas]] · [[ONTOLOGIA|Ontologia Relacional]]
- [[MOC_PENTAGON_MIND|MOC do Projeto]]

## 📊 Dashboard
```dataview
TABLE status AS "Status", prioridade AS "Prioridade", atualizado AS "Atualizado"
FROM "30_PROJECTS/pentagon-mind"
```

## 🕒 Histórico de Atualizações
- **2026-08-21** — Projeto criado e indexado ao MEGA BRAIN; expansão com Trump 2, glossário, popups, explainers e atualização 2026.
