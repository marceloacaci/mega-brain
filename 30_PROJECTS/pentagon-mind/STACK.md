---
tipo: stack
projeto: pentagon-mind
criado: 2026-08-21
tags: ["projeto/pentagon-mind", "stack"]
---

# 🧱 Stack — PENTAGON-MIND

## Front-end (estático, sem build)
- **HTML5** (5 páginas, `lang="pt-BR"`)
- **CSS3** — `css/styles.css` (design system "command-center", variáveis CSS, dark/technical)
- **JavaScript vanilla** — sem framework; injeção DRY de nav/footer via `js/nav.js`

## Dados & Glossário
- `data/ontology.json` — esquema relacional (administrations, doctrines, conflicts, weaponSystems, crossRefs)
- `data/glossary.js` — `window.PM_GLOSSARY` (siglas), `window.PM_THREAT_LEGEND` (pins do mapa)
- `js/glossary.js` — engine de popups inline + geração do mapa de ameaças e glossário
- `js/ontology.js` — loader que expõe `window.PM_ONTOLOGY`

## Imagens
- `assets/img/media.js` — registry `window.PM_MEDIA` (slug → caminho local)
- 59 imagens reais (domínio público/Governo EUA) baixadas via `assets/download_images.py`
- `js/common.js` — fallback de imagem (placeholder) por delegação de evento

## Servidor & Verificação
- `assets/serve.cjs` — HTTP server Node (porta 8726), normalização de caminho para evitar 403 no Windows
- `assets/verify.js` — checagens estáticas (páginas, registry, JSON válido, node --check, fiação de glossário)

## Comandos
```bash
cd C:/Users/Marcelo/Desktop/EUA
node assets/serve.cjs        # servir em http://127.0.0.1:8726/
node assets/verify.js        # validação estática
```
