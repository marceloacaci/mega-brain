<%*
// ============================================
// MEGA BRAIN — Template de Novo Projeto (Templater)
// Cria estrutura 30_PROJECTS/<slug>/ com 1 clique.
// ============================================
const nome = await tp.system.prompt("Nome do projeto");
if (!nome) { new Notice("❌ Cancelado"); return; }

const objetivo = await tp.system.prompt("Objetivo principal (1 frase)");
const stack = await tp.system.prompt("Stack principal (ex: Python, Node, Vue)");
const status = await tp.system.suggester(["ativo", "pausado", "concluido"], ["ativo", "pausado", "concluido"]);
const prioridade = await tp.system.suggester(["alta", "media", "baixa"], ["alta", "media", "baixa"]);

const slug = nome.toLowerCase()
  .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

const projetoPath = `30_PROJECTS/${slug}`;
const stackSlug = (stack || "").toLowerCase().split(/[ ,]+/)[0] || "geral";
const tags = [`projeto/${slug}`, `stack/${stackSlug}`, `status/${status}`, `prioridade/${prioridade}`];
const hoje = tp.date.now("YYYY-MM-DD HH:mm");

const files = ["README.md", "CONTEXTO.md", "DECISOES.md", "STACK.md", "APRENDIZADOS.md", "TAREFAS.md"];
for (const f of files) {
  const p = `${projetoPath}/${f}`;
  if (!await tp.file.exists(p)) { await tp.file.create_new("", p, false); }
}

tR = `---
projeto: ${nome}
slug: ${slug}
status: ${status}
stack: ${stack}
prioridade: ${prioridade}
criado: ${hoje}
atualizado: ${hoje}
tags: [${tags.map(t => `"${t}"`).join(", ")}]
---

# 📁 ${nome}

> ${objetivo}

## 🎯 Visão Geral
- **Status:** ${status}
- **Prioridade:** ${prioridade}
- **Stack:** ${stack}
- **Criado:** ${hoje}
- **Slug:** \`${slug}\`

## 🎯 Objetivo
${objetivo}

## 🧱 Stack
${stack}

## 📂 Estrutura
\`\`\`
${projetoPath}/
├── README.md      ← este arquivo
├── CONTEXTO.md    ← contexto e histórico
├── DECISOES.md    ← decisões técnicas tomadas
├── STACK.md       ← dependências e versões
├── APRENDIZADOS.md← padrões e lições aprendidas
└── TAREFAS.md     ← checklist de tarefas
\`\`\`

## 🔗 Links Rápidos
- [[CONTEXTO|Contexto]] · [[DECISOES|Decisões]] · [[STACK|Stack]] · [[APRENDIZADOS|Aprendizados]] · [[TAREFAS|Tarefas]]

## 📊 Dashboard
\`\`\`dataview
TABLE status AS "Status", prioridade AS "Prioridade", criado AS "Criado"
FROM "${projetoPath}"
\`\`\`

## 🕒 Histórico de Atualizações
- **${hoje}** — Projeto criado via MEGA BRAIN
`;

new Notice(`✅ Projeto '${nome}' criado em ${projetoPath}`);
%>
