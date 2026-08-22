---
tipo: aprendizados
projeto: pentagon-mind
criado: 2026-08-21
tags: ["projeto/pentagon-mind", "aprendizados"]
---

# 💡 Aprendizados — PENTAGON-MIND

## FCS (Finish & Verify) pega bug real
- `node --check` em `data/glossary.js` revelou `{ id: "europe": x: 55, ...}` (erro de sintaxe: `:` no lugar de `,`). Sem a verificação, o glossary quebraria silenciosamente no browser. **Sempre rodar `node assets/verify.js` antes de declarar pronto.**

## Ordem de injeção de scripts importa
- O active-link da nav deve rodar *depois* de `nav.js` montar o menu (senão `querySelectorAll('.nav-links a')` retorna vazio). Solução: mover lógica de active para dentro de `nav.js`.

## Windows + Node server = 403 falso
- `path.normalize` mistura `/` e `\`; usar `path.resolve` + `startsWith(ROOT+path.sep)`.

## Imagens: API, não chute
- Nomes de arquivo do Wikimedia chutados falham ~80%. Usar a API (`action=query&titles=...&prop=imageinfo&iiprop=url`) retorna a URL canônica.

## Glossário DRY
- Manter siglas num único `data/glossary.js` evita divergência entre popups e mapa de glossário.

## Conteúdo: ancorar fontes
- Citações verificáveis (Powell, Mattis, Milley, Dugan, Brodie) + referências CRS/DoD/SIPRI dão credibilidade acadêmica ao tom.

## Padrão de UI herdado do MeuBolso — COMPLETO (2026-08-21, 2ª rodada)
Aplicado a MENUS, BOTÕES, CARDS e HOVERS (pacote gear-opt):
- Raised 85/95% (valor VIGENTE MeuBolso §14) em `.card`/`.chip`/`.pill`/`.datasheet summary`/`.btn` + `box-shadow: var(--shadow)`.
- **HOVER RÍGIDO (§15/§22)**: SÓ `border-color:--primary` + `translateY(-1/-2px)` + `box-shadow:--shadow-hover`. NUNCA trocar `color` da fonte.
- `--shadow-hover` no escuro = BRANCO difuso `rgba(255,255,255,.10)` (§22) — sombra preta some no fundo escuro.
- `.btn`/`.btn-primary` (raised --primary, texto #fff); `.nav-toggle` (hamburguer) = gear-opt; `.topbar` com box-shadow sutil.
- Borda branca suave `rgba(255,255,255,.14)` no escuro (§18), ESCOPADA `:not(:hover)` para não travar o hover --primary (§19/§24).
- Scrollbar raised (§2): `::-webkit-scrollbar-thumb` com HEX FIXO (`#4a505a`/`#2c3138`) — color-mix NÃO resolve em scrollbar.
- **Pitfall de verificação**: ler `getComputedStyle` logo após adicionar classe-espelho `.fh` captura o INÍCIO da transição (box-shadow 0.15s) → falso "não aplicou". Esperar `setTimeout(320ms)` (§26b). Validado: chip hover → shadow branca difusa + borda --primary, cor da fonte inalterada.

## 3ª rodada (2026-08-21): lift+hover+sombras em TODOS os cards/subcards/botões + header
Aplicado degradê `var(--bg)`→`var(--raised-bg-base)` (padrão MeuBolso: claro #fafafa→95%black; escuro #14161a→#14161a) + sombra normal + **lift no hover** (`translateY(-2px)` + `--shadow-hover`) em:
- Cards: `.card`/`.card.raised-card` (já tinha), `.box` (+hover), `.glossary-item` (ambas as seções, +hover), `.stats .stat`, `.matrix-row .who`, `.flow .node` (+hover), `.datasheet summary` (+hover).
- Botões: `.btn`/`.btn-primary`/`.chip`/`.pill`/`.nav-toggle`/`.card-link` (hover lift + sombra branca).
- Header `.topbar`: degradê `var(--bg)`-based + `box-shadow` (86% transparência p/ manter blur) — **SEM hover** (pedido explícito).
- **Bug caçado (§10/§11)**: `.glossary-item` (linha ~381) e `.datasheet summary` tinham `background` sólido posterior que ENGOLIA o gradiente raised → corrigido para gradiente bg-based. Sempre grepar TODAS as regras de uma classe antes de declarar "pegou".
- Validado FCS: `.flow .node`/`.glossary-item` hover → `transform: matrix(1,0,0,1,0,-2)` (lift -2px) + `box-shadow` branca difusa + borda --primary. `node assets/verify.js` → PASSED.

## 4ª rodada (2026-08-21): degradê SUAVE CONTÍNUO + --bg=#14161a
Pedido do usuário: trocar o degradê "dividido 50/50" (com linha de corte) por **suave contínuo**, e `--bg` do portal de #0a0e14 → **#14161a** (ref MeuBolso escuro).
- `--bg: #14161a` no `:root` (antes #0a0e14); `--bg-2: #1a2230`.
- `--raised-grad: linear-gradient(to bottom, color-mix(var(--bg) 85%, white) 0%, var(--bg) 100%)` — CONTÍNUO (sem stop em 50%). Variável `--raised-grad-top` p/ reaproveitar no header.
- Substituídas TODAS as ocorrências do degradê dividido (8 elementos: card, box, glossary-item x2, stats, matrix-row.who, datasheet summary, flow.node) por `var(--raised-grad)`.
- `.topbar`: degradê suave `color-mix(var(--raised-grad-top) 86%, transparent) 0% → color-mix(var(--bg) 86%, transparent) 100%` (mantém blur). SEM hover.
- Removidas variáveis órfãs `--raised-bg-light/-base`, `--raised-surface-light/-base`.
- Validado FCS: `--bg`=#14161a; `.card` backgroundImage = `linear-gradient(color(srgb 0.216 0.223 0.236) 0%, rgb(20,22,26) 100%)` (contínuo, sem parada 50%). `node assets/verify.js` → PASSED.

## 5ª rodada (2026-08-21): popup de termos quebrado (não encapsulava)
Bug: `.term-popup` tinha **DUAS definições** no CSS (linha ~277 e ~350). A 2ª usava `bottom:145%; left:50%; transform:translateX(-50%)` (acima, centralizado) mas seu `.open` não redefinia transform → ao abrir, o `translateY(0)` do `.open` da 1ª anulava a centralização e deslocava o card (`matrix(1,0,0,1,-120,0)`). Media `clientH:20` vs `scrollH:146` = card colapsado/cortado.
- Consolidado em UMA definição: `position:absolute; left:0; top:100%; margin-top:7px` (abaixo da palavra, sem deslocamento), `.open { transform: translateY(0) }`, `white-space:normal; overflow:visible`.
- Removido `overflow:hidden` de `.split` e `.datasheet` (cortavam popups de termos internos). `.stats`/`.threatmap` mantêm hidden (sem termos popups lá).
- Validado FCS: popup aberto → `transform: matrix(1,0,0,1,0,0)` (sem deslocamento), `scrollH 158 == clientH 158` (clipped:false, encapsula os 4 filhos STRONG/tp-full/tp-pt/tp-gloss), `opacity:1; visibility:visible`. `node assets/verify.js` → PASSED.

## 6ª rodada (2026-08-21): bordas arredondadas em cards e botões
Pedido: bordas arredondadas nos cards e botões.
- `--radius: 4px → 10px` no `:root` (DRY: quase todos os cards/botões usam `var(--radius)`).
- Adicionado `border-radius: var(--radius)` a `.card-link` (módulos, não tinha) e `.matrix-row .who` (subcard da matriz, estava 0px).
- `.chip`/`.pill` mantêm 20px (pill-style, já arredondados). Itens com raio fixo (img presidente 3px, legendas 3px, círculos 50%) intencionais.
- Validado FCS: `.card-link`/`box`=`10px`, `--radius`=`10px`; presidências `.chip`=`20px`, `.nav-toggle`=`10px`, `.matrix-row .who` agora `10px` (antes 0). `node assets/verify.js` → PASSED.

## 7ª rodada (2026-08-21): impeccable polish — remover slop (side-tabs / border-accent-on-rounded)
Usuário invocou skill `impeccable` (sem sub-comando). `context.mjs` reportou NO_PRODUCT_MD; detector `detect.mjs` flaggou slop no CSS.
- `detect.mjs` (regex fallback, undercount): 6× `side-tab` (border-left/right >1px) + 2× `border-accent-on-rounded` (border-top 3px em cards arredondados).
- Corrigido: `.box` border-left 3px→1px primary; `.explain`/`.explainer` border-left 3px→1px (ambos os seletores!); `.glossary-item` ×2 border-left 3px→1px accent; `.figcaption` border-left 2px→1px; `.term-popup`/`.pin-popup` border-top 3px → `box-shadow: inset 0 3px 0 0 var(--accent)` (faixa de acento que respeita o raio, elimina o clash).
- Pós-correção: `grep` confirma NENHUMA `border-*: 3px`; `node assets/verify.js` → PASSED.
- Validado FCS: `.explainer` border-left 1px âmbar + radius 10px; popup `border-top-width:1px` + `boxShadow` com `inset 0 3px 0 0 rgb(201,162,39)` (acento topo respeita raio), opacity 1, clipped:false. Linhas 277/324 do detector são FALSO POSITIVO do regex (casa "3px" dentro do `inset 0 3px 0 0`).
- Pendente: `/impeccable init` para capturar PRODUCT.md/DESIGN.md (skill recomenda por não haver contexto).
