---
titulo: Preferências Pessoais
tipo: preferencias
tags: [megabrain, preferencias, padrao/comunicacao]
atualizado: 2026-08-21
---

# ⚙️ PREFERENCIAS_PESSOAIS

Aplicar **silenciosamente** em toda tarefa. Não perguntar.

## Idioma e estilo
- **PT-BR** em todas as notas, mensagens e logs.
- Comunicação **tersa e específica**; correções diretas ("desfaça a última alteração, você alterou errado").
- Estilo **formal e conciso** quando for para documentos acadêmicos (professores pedem parágrafos curtos, ≤5 linhas).
- Formato de entrega preferencial também em **.docx** para trabalhos de faculdade (ADS).

## Verificação (regra inegociável — FCS)
- Marcelo **exige verificação real em browser/Electron**: servir o app, sondar HTML, ler `getComputedStyle`/`getBoundingClientRect` via `browser_console`, usar `?nocache` (`<link>?cb=N`).
- **Nunca** entregar por suposição. Se não medir o valor real, não afirmar que está pronto.
- Odeia "chutar" — empurra de volta quando o valor não bate com o medido.

## UI — políticas fixas (MeuBolso / front-end em geral)
- **Hover = SÓ lift** (`translateY(-1px)` + `box-shadow: var(--shadow-hover)`). NUNCA muda cor no hover (nem texto, ícone, borda). Borda de repouso continua no hover.
- **Largura fixa de widget/dropdown** = largura do **MAIOR rótulo entre TODAS as traduções** (pt/en/es via `window.I18N`), reaplicada a cada render (views Vue usam `v-html` e apagam estilos inline → reaplicar via `Vue.nextTick` em `render()`).
- Para inspecionar box/spacing de um elemento, ele pede **borda colorida temporária** (ex.: `1px solid #000`) e remove depois de inspecionar.
- Indicadores de UI devem refletir **estado de runtime real**, nunca nominal.

## Convenções de commit / Git
- Commits em PT-BR com prefixo de tipo (`feat:`, `fix:`, `ui:`, `test:`, etc.).
- **NÃO destruir** dados/repo reais sem ordem. Renomear release/tag = **RECRIAR** (`gh release create ...`), nunca apagar.
- Push só com confirmação explícita do Marcelo.

## Identidade
- Nome do autor mantido no card "Desenvolvido por" do MeuBolso; linha de copyright é "© 2026 MeuBolso" (sem nome).
