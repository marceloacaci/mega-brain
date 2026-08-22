<%*
const topico = await tp.system.prompt("Tópico do MOC");
if (!topico) return;
const slug = topico.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-");
const hoje = tp.date.now("YYYY-MM-DD");

tR = `---
tipo: moc
topico: ${topico}
criado: ${hoje}
atualizado: ${hoje}
tags: [moc, moc/${slug}]
---

# 🗺️ MOC — ${topico}

> Map of Content sobre **${topico}**

## 📑 Índice
\`\`\`dataview
LIST
FROM ""
WHERE contains(file.content, "${topico}") OR contains(tags, "moc/${slug}")
SORT file.name ASC
\`\`\`

## 📂 Por Categoria
\`\`\`dataview
TABLE category AS "Categoria", length(rows) AS "Qtd"
FROM ""
WHERE contains(file.content, "${topico}")
GROUP BY category
\`\`\`

## 🔁 Padrões
\`\`\`dataview
LIST
FROM "10_MEGA_BRAIN"
WHERE contains(file.content, "${topico}")
\`\`\`

## 📁 Projetos
\`\`\`dataview
LIST
FROM "30_PROJECTS"
WHERE contains(file.content, "${topico}")
\`\`\`

## 📦 Recursos
\`\`\`dataview
LIST
FROM "50_RESOURCES"
WHERE contains(file.content, "${topico}")
\`\`\`

---
*Criado em ${tp.date.now("YYYY-MM-DD HH:mm")}*
`;

new Notice(`✅ MOC '${topico}' criado`);
%>
