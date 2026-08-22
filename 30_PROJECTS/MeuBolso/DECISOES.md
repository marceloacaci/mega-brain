---
projeto: MeuBolso
tipo: decisoes
tags: [projeto/meubolso, decisao]
---

# 🧭 DECISÕES — MeuBolso

- **Renomear release/tag** = recriar via `gh release create`, nunca apagar (corpo mora em CHANGELOG.md).
- **Hover** = só lift (`translateY(-1px)` + shadow). Sem mudança de cor.
- **Largura fixa** de dropdown = maior rótulo pt/en/es, reaplicada por render (`Vue.nextTick`).
- **Relevo raised**: metade clara em cima = `color-mix(in srgb, <cor> 70%, white)` (0%–50%), cor base embaixo (50%–100%). Valor atual: **70%** (ajustado de 85% em 22/ago/2026; mais subtil, decide-se manter).
- **Commits PT-BR** (`feat:`/`fix:`/`ui:`/`test:`); **push sob confirmação**.
- Último commit relevante: `dc66875` (S7 dropdown + raised).
