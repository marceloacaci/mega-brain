<%*
const hoje = tp.date.now("YYYY-MM-DD");
const dailyPath = `20_DAILY_NOTES/${hoje}.md`;
if (await tp.file.exists(dailyPath)) { new Notice(`⚠️ Daily note de ${hoje} já existe`); return; }

const humor = await tp.system.suggester(["😀 Produtivo","🎯 Focado","😐 Neutro","😴 Cansado","🤔 Reflexivo"], ["produtivo","focado","neutro","cansado","reflexivo"]);

tR = `---
data: ${hoje}
humor: ${humor || "neutro"}
tags: [daily/${tp.date.now("YYYY")}/${tp.date.now("MM")}]
---

# 📓 ${hoje}

> **Humor:** ${humor || "neutro"}

## 🎯 Foco do Dia
- [ ]

## ⏳ Em Andamento
\`\`\`dataview
TASK
FROM "30_PROJECTS"
WHERE !completed AND contains(tags, "prioridade/alta")
\`\`\`

## 🚀 Execuções do Dia
*(preenchido automaticamente pelos hooks)*

## 💡 Aprendizados
-

## 🔗 Links Gerados
\`\`\`dataview
LIST
FROM ""
WHERE file.cday = date("${hoje}")
\`\`\`

## 📊 Resumo do Dia
\`\`\`dataview
TABLE WITHOUT ID length(rows) AS "Qtd"
FROM "20_DAILY_NOTES"
WHERE file.name = "${hoje}"
\`\`\`
`;

new Notice(`✅ Daily note de ${hoje} criada`);
%>

[[novo_moc]]

[[novo_projeto]]

[[novo_padrao]]
