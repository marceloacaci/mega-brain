<%*
const nome = await tp.system.prompt("Nome do padrão");
if (!nome) return;
const categoria = await tp.system.suggester(["Arquitetura","Código","Git","DevOps","Teste","Segurança","Performance","UX"], ["arquitetura","codigo","git","devops","teste","seguranca","performance","ux"]);
const descricao = await tp.system.prompt("Descrição do padrão");
const linguagem = await tp.system.prompt("Linguagem/Stack (ex: python, javascript)");
const quando = await tp.system.prompt("Quando aplicar (trigger)");

const slug = nome.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-");
const hoje = tp.date.now("YYYY-MM-DD");

tR = `---
tipo: padrao
nome: ${nome}
categoria: ${categoria}
linguagem: ${linguagem}
criado: ${hoje}
ocorrencias: 1
ultima_vez: ${hoje}
tags: [padrao/${categoria}, padrao/${slug}, stack/${linguagem}]
---

# 🔁 ${nome}

## 📋 Metadados
- **Categoria:** ${categoria}
- **Linguagem:** ${linguagem}
- **Ocorrências:** 1
- **Detectado em:** ${tp.file.folder()}

## 📝 Descrição
${descricao}

## ⚡ Quando aplicar
${quando}

## 🧩 Implementação
\`\`\`${linguagem}
// código do padrão
\`\`\`

## ✅ Vantagens
-

## ❌ Desvantagens
-

## 📁 Projetos que usam
\`\`\`dataview
LIST
FROM "30_PROJECTS"
WHERE contains(tags, "padrao/${slug}")
\`\`\`

## 🔗 Referências
-
`;

new Notice(`✅ Padrão '${nome}' registrado`);
%>

[[novo_recurso]]

[[novo_moc]]

[[novo_projeto]]
