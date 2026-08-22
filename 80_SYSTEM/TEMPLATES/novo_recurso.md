<%*
const tipo = await tp.system.suggester(["Linguagem","Framework","Ferramenta","Comando","Snippet"], ["linguagens","frameworks","ferramentas","comandos","snippets"]);
if (!tipo) { new Notice("❌ Cancelado"); return; }
const nome = await tp.system.prompt("Nome do recurso");
if (!nome) return;
const descricao = await tp.system.prompt("Descrição breve");
const tags_raw = await tp.system.prompt("Tags (separadas por vírgula)");

const slug = nome.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-");
const tags = (tags_raw || "").split(",").map(t => t.trim()).filter(Boolean);
const path = `50_RESOURCES/${tipo}/${slug}.md`;
const hoje = tp.date.now("YYYY-MM-DD");

tR = `---
tipo: recurso
categoria: ${tipo}
nome: ${nome}
criado: ${hoje}
tags: [recurso/${tipo}, ${tags.map(t => '"' + t + '"').join(", ")}]
---

# 📦 ${nome}

> ${descricao}

## 📋 Metadados
- **Tipo:** ${tipo}
- **Tags:** ${tags_raw}

## 📝 Descrição
${descricao}

## 💻 Uso
\`\`\`
[coloque aqui o código ou comando]
\`\`\`

## 🔗 Relacionados
\`\`\`dataview
LIST
FROM "50_RESOURCES"
WHERE contains(tags, "${tipo}") AND !contains(file.path, "${slug}")
\`\`\`

## 📒 Notas
- Adicionado em ${tp.date.now("YYYY-MM-DD HH:mm")}
`;

new Notice(`✅ Recurso '${nome}' criado`);
%>
