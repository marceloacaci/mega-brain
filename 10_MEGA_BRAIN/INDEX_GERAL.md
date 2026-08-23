---
tipo: meta-indice
criado: 2026-08-21
atualizado: 2026-08-22
tags: [meta/index]
---
# 🧠 MEGA BRAIN — Índice Geral

> Dashboard vivo do meu Segundo Cérebro.
> Atualizado automaticamente pelo 
eindex_hybrid.ps1 (light 6h + deep semanal).

## ⏱️ Timestamps
- **Última reindexação:** 2026-08-22 10:40:50
- **Última light:** 2026-08-22T09:23:43.1625581-03:00
- **Última deep:** 2026-08-22 10:40:50
- **Próxima light:** 2026-08-22 15:23:43
- **Próxima deep:** 2026-08-23 23:00:00

## ⏰ Status de Sincronização
- MCP server: ONLINE (8770)
- **Última sincronização:** 2026-08-22T09:23:43.1625581-03:00

## 📊 Visão Geral
- Projetos: 3
- MOCs: 9
- Notas (.md): 78

## 📂 Projetos Ativos
```dataview
TABLE status AS "Status",
      stack AS "Stack",
      criado AS "Criado"
FROM "30_PROJECTS"
WHERE status = "ativo"
SORT criado DESC
```

## 🧩 Stack Mapeada (Top 10)
```dataview
TABLE WITHOUT ID
  stack AS "Stack",
  length(rows) AS "Uso"
FROM "30_PROJECTS"
WHERE stack != ""
FLATTEN stack
GROUP BY stack
SORT length(rows) DESC
LIMIT 10
```

## 🕒 Últimas 7 Execuções
```dataview
TABLE file.link AS "Dia",
      humor AS "Humor"
FROM "20_DAILY_NOTES"
SORT file.name DESC
LIMIT 7
```
## 🔍 Padrões Detectados (Top 10)
```dataview
TABLE categoria AS "Categoria",
      ocorrencias AS "Ocorrências",
      ultima_vez AS "Última"
FROM "10_MEGA_BRAIN"
WHERE contains(tags, "padrao")
SORT ocorrencias DESC
LIMIT 10
```

## Projetos indexados

- [[livro]]
- [[MeuBolso]] — - Electron + Node; Vue 3 (views clássicas via `<script>`, `v-html`).
- `styles.css` + Bootstrap; temas claro/escuro via `[data-theme]`.
- `icons.js` (`window.ICON`), i18n pt/en/es (`window.I18N`/`t()`).
- [[pentagon-mind]]

## 🗂️ MOCs
```dataview
LIST
FROM "70_MOCS"
WHERE contains(tags, "moc")
SORT file.name ASC
```

## 🔔 Alertas Ativos
```dataview
TABLE prioridade AS "Prioridade",
      categoria AS "Categoria",
      file.link AS "Arquivo"
FROM "90_ALERTS"
WHERE !resolved
SORT prioridade DESC
```

## 📈 Histórico de Métricas (últimas 24h)
```dataview
TABLE mode AS "Modo",
      total_notas AS "Notas",
      total_projetos AS "Proj",
      total_mocs AS "MOCs",
      tamanho_mb AS "MB"
FROM "50_METRICS"
WHERE timestamp >= date(now) - dur(24 hours)
SORT timestamp DESC
LIMIT 4
```

## Arquivos de peso máximo
- [[PREFERENCIAS_PESSOAIS]] · [[PADROES_RECorrentes]] · [[DECISOES_REUTILIZAVEIS]] · [[STACKS_MAPeadas]]

## Métricas
- Notas .md: 78 · Projetos: 3 · MOCs: 9
- Última execução (deep): 2026-08-22 10:40:50

[[README]]

[[MOC_JavaScript]]

[[MOC_GERAL]]
