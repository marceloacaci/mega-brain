---
tipo: moc
criado: 2026-08-21
tags: [moc, moc/raiz]
---

# 🗺️ MOC Geral

> Map of Content central. Conecta todas as áreas do conhecimento.

## 🎯 Por Projeto
```dataview
LIST
FROM "30_PROJECTS"
SORT file.name ASC
```
- [[MOC_PENTAGON_MIND|PENTAGON-MIND — Doutrina Militar & Geopolítica dos EUA]]

## 🧠 Por Padrão
```dataview
LIST
FROM "10_MEGA_BRAIN"
WHERE contains(tags, "padrao")
```

## 🛠️ Por Stack
```dataview
LIST
FROM "50_RESOURCES"
SORT file.name ASC
```

## 📚 Por Área
```dataview
LIST
FROM "40_AREAS"
```

## 🔗 Conexões Externas
```dataview
LIST
FROM "70_MOCS"
WHERE contains(tags, "moc") AND !contains(tags, "moc/raiz")
```

[[novo_moc]]

[[MOC_Obsidian]]

[[INDEX_GERAL]]
