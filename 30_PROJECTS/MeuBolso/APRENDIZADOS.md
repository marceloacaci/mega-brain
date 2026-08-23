---
projeto: MeuBolso
tipo: aprendizados
tags: [projeto/meubolso, aprendizado]
---

# 💡 APRENDIZADOS — MeuBolso

- Electron não hot-reload: app rodando com CSS/JS antigo mostra regressões que não existem no disco. Sempre reiniciar `npm start` após editar.
- `color-mix(in srgb, <cor> 85%, white)` na metade superior = relevo padrão `.gear-opt`/`.gear-cor`.
- `getComputedStyle` converte `color-mix(... 85% ...)` no valor calculado (ex.: `color(srgb 0.3 0.503 0.413)`); checar por matemática, não por substring "85%".
- Verificação FCS: servir + `browser_console` medindo `getBoundingClientRect`/`getComputedStyle` + `?cb=N`.

[[PADROES_RECorrentes]]
