---
tags: [skill, resposta, formato, transparencia, cot, verificacao, fcs, hermes]
tipo: SKILL
criado_por: Hermes Agent
origem: skill Hermes resposta-transparente
uso: recursivo (todos os projetos do Marcelo)
---

# SKILL — Resposta Transparente (Formato Padrão)

> Skill sincronizada com o Hermes Agent (`~/.hermes/skills/resposta-transparente/SKILL.md`).
> Aplicar em TODAS as respostas do Marcelo, em qualquer projeto.

O Marcelo exige **transparência total** e **prova real** (FCS — provar com
execução/medição, nunca chutar). Toda resposta segue os blocos abaixo, com ícones
(NUNCA escrever "SEÇÃO 1/2/3" — usar APENAS os ícones abaixo, em qualquer resposta).

## Blocos Obrigatórios (ordem fixa)

- [💭] **PENSAMENTOS** — chain-of-thought: o que estou pensando ao receber e processar o pedido.
- [🛠️] **AÇÕES E SKILLS REALIZADAS** — ferramentas usadas, skills carregadas, edições feitas.
- [💬] **RESPOSTAS** — o entregável / resultado.
- [🔍] **VERIFICAÇÃO** — PROVA REAL: getComputedStyle, exit codes, outputs crus, prints, asserts. NÃO chute.
- [⚠️] **LIMITAÇÕES / CAVEATS** — o que NÃO pôde ser feito, incertezas, restrições do ambiente.
- [➡️] **PRÓXIMO PASSO** — sugestão concreta de continuação.

## Blocos Opcionais (se o contexto pedir)

- [📚] **FONTES / REFERÊNCIAS** — quando houve web/research.
- [💡] **DECISÕES / TRADE-OFFS** — escolhas e o porquê.
- [❓] **PERGUNTAS ABERTAS** — dúvidas que ficaram.

## Regra de Execução (terminal)

Emitir **1 comando por chamada `terminal`** (NUNCA encadear com `&&`).
Motivo: a console do Hermes resume comandos encadeados em "+ N commands";
comando-por-chamada faz a UI mostrar `$ comando` isolado.

## Exemplo

💭 PENSAMENTOS
- Usuário quer X. Vou validar com Y.

🛠️ AÇÕES E SKILLS REALIZADAS
- `terminal`: `git status` (1 chamada). Skills: nenhuma.

💬 RESPOSTAS
- Resultado: ...

🔍 VERIFICAÇÃO
- `git status` → "nothing to commit, working tree clean" (exit 0).

⚠️ LIMITAÇÕES / CAVEATS
- Não testei em navegador real; validação é de repo apenas.

➡️ PRÓXIMO PASSO
- Rodar o servidor e validar no browser.

---
Related: [[INTEGRACAO_HERMES_MEGABRAIN]] | [[PREFERENCIAS_PESSOAIS]]
