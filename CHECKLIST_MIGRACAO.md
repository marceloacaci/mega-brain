# ✅ Checklist Final de Migração

| # | Ação | Como |
|---|------|------|
| 1 | Substituir reindex_weekly.ps1 por reindex_hybrid.ps1 | Copiar o script acima |
| 2 | Atualizar install_hooks.ps1 | Substituir pela nova versão ⚠️ *ver nota* |
| 3 | Adicionar trigger no post_task_hook.ps1 | Inserir Invoke-LightReindexIfNeeded ✅ *já feito* |
| 4 | Adicionar verificação no pre_task_hook.ps1 | Inserir bloco de lock check ✅ *já feito* |
| 5 | Atualizar config.json | Adicionar seção auto_reindex.mode = "hybrid" ⚠️ *ver nota* |
| 6 | Atualizar INDEX_GERAL.md | Adicionar seção "Status de Sincronização" ✅ *já feito* |
| 7 | Executar migração | migrate_to_hybrid.ps1 (automatiza tudo) ⚠️ *pendente confirmação* |
| 8 | Validar | Get-ScheduledTask \| Where { $_.TaskName -like 'MEGA_BRAIN_*' } |

## Notas de implementação (estado real em 2026-08-21)

- **Item 2 — `install_hooks.ps1` NÃO EXISTE** no vault. O setup usa `install_tasks.ps1`
  (instala as tarefas MEGA_BRAIN_*). O `migrate_to_hybrid.ps1` (BLOCO 7) foi corrigido
  para chamar `install_tasks.ps1`. Não há `install_hooks.ps1` para atualizar.
- **Item 5 — `config.json` NÃO TEM `mode = "hybrid"`**. O `config.json` atual tem
  `auto_reindex.force_after_hours = 4` mas sem o campo `mode`. Pode ser adicionado
  (BLOCO 5 do utilizador veio truncado, por isso o config está intacto).
- **Itens 3, 4, 6 — JÁ IMPLEMENTADOS E TESTADOS** nesta sessão (hooks com
  Invoke-LightReindexIfNeeded + lock check; INDEX_GERAL.md com Status de Sincronização).
- **Item 7 — EXECUÇÃO PENDENTE DE CONFIRMAÇÃO**. O `migrate_to_hybrid.ps1` é redundante
  com o setup já feito; o passo 2 não remove as tarefas obsoletas
  (MEGA_BRAIN_Backup_Full / MEGA_BRAIN_Backup_Incremental, que ficaram sem trigger).
- **Item 8 — comando de validação** (igual ao do BLOCO 9):
  `Get-ScheduledTask | Where { $_.TaskName -like 'MEGA_BRAIN_*' }`

[[sprint-2]]

[[ROADMAP]]

[[sprint-1]]
