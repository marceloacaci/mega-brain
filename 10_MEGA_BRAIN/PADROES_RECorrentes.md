---
titulo: Padrões Recorrentes
tipo: padroes
tags: [megabrain, padrao, padrao/ui, padrao/verificacao]
atualizado: 2026-08-21
---

# 🔁 PADROES_RECorrentes

Padrões detectados (≥2 ocorrências) ou impostos por preferência. Reutilizar em vez de reinventar.

## P1 — Hover lift-only (UI)
- Todo elemento interativo: hover = `translateY(-1px)` + `box-shadow: var(--shadow-hover)`.
- Nunca alterar cor no hover. Borda `--border` aplicada em TODOS os estados (sem `:not(:hover)` obsoleto).
- Medir `transition` dentro de `setTimeout(300)`.
- Fonte: skill `meubolso-css-pitfalls` (seções 31/37/38).

## P2 — Largura fixa pelo maior rótulo i18n
- Dropdowns/widgets customizados: `width = max(labelPt, labelEn, labelEs)`.
- Reaplicar via `Vue.nextTick` após `render()`, pois `v-html` apaga estilo inline.
- Marcelo verifica medindo `getBoundingClientRect` — se o botão "acompanha o texto selecionado" em vez de ficar travado, ele reclama.

## P3 — Gradiente raised (relevo)
- Padrão `.gear-opt` / `.btn`: metade **clara em cima** = `color-mix(in srgb, <cor> 85%, white)` (0%–50%), cor base embaixo (50%–100%).
- `.gear-cor` (seletor de cor) segue o mesmo: `color-mix(in srgb, var(--sw) 85%, white)` na metade superior.
- Validar o valor computado: `color-mix(85% cor + 15% branco)` para #2d6a4f resulta em `color(srgb 0.3 0.503 0.413)` — conferir por medição, não por string.

## P4 — Verificação FCS obrigatória
- Toda edição de código de sistema passa pelo FCS: servir app real, sondar, medir `getComputedStyle`/`getBoundingClientRect`, usar `?cb=N` anti-cache.
- Claim de "pronto" só após valor medido bater.

## P5 — Nunca destrutivo
- Renomear release/tag = recriar (`gh release create`), não apagar. Remover asset só se pedido.
- Não commitar/push sem confirmação (exceto quando o próprio Marcelo mandou "commitar tudo").

[[PREFERENCIAS_PESSOAIS]]

[[DECISOES]]

[[DECISOES_REUTILIZAVEIS]]
