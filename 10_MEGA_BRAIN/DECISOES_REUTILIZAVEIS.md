---
titulo: Decisões Reutilizáveis
tipo: decisoes
tags: [megabrain, decisao, decisao/git, decisao/ui]
atualizado: 2026-08-21
---

# 🧭 DECISOES_REUTILIZAVEIS

Decisões já tomadas — reaplicar sem questionar.

## D1 — Renomear release/tag do GitHub = RECRIAR, não apagar
- Corpo do release mora no `CHANGELOG.md`; apagar destrói o corpo.
- Fluxo: `gh release create v2.1.0 --title "..." --notes-file CHANGELOG.md --target master`.
- Pedido de "tirar/remover X do título/tag" = renomear (recriar), nunca deletar.

## D2 — Verificação de UI é inegociável
- Sem browser real medindo valor, não afirmar conclusão. (Ver P4 em [[PADROES_RECorrentes]].)

## D3 — Hover não muda cor
- Lift-only em todos os cards/botões/subcards/subbotões de TODAS as páginas; EXCETO cabeçalhos (page-header título e card). (Ver P1.)

## D4 — Largura fixa respeita i18n
- Widget travado no maior rótulo pt/en/es, reaplicado por render. (Ver P2.)

## D5 — Commits em PT-BR, push sob confirmação
- Prefixos `feat:`/`fix:`/`ui:`/`test:`. Push só com OK do Marcelo.

## D6 — Identidade MeuBolso
- Card "Desenvolvido por Marcelo Acácio" mantido; copyright "© 2026 MeuBolso".
