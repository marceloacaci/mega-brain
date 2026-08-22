# 🚨 RUNBOOK — MEGA BRAIN (90_ALERTS)

Guia de operação e recuperação do Segundo Cérebro. Em caso de incidente, siga
a ordem abaixo. Todos os comandos assumem o vault em
`D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills`.

---

## 1. MCP server fora do ar (porta 8770)
**Sintoma:** `megabrain.ps1 health` ou `curl http://localhost:8770/health` falha.

```powershell
# Subir manualmente
python "80_SYSTEM/SCRIPTS/mcp_obsidian_server.py" --port 8770
# Verificar
curl http://localhost:8770/health
```

Se a porta estiver em uso por um processo zumbi:
```powershell
# listar quem ocupa 8770 e encerrar
netstat -ano | findstr 8770
taskkill /F /PID <pid>
```

---

## 2. Restaurar backup (corrompimento do vault)
**Sintoma:** notas sumiram ou vault corrompido.

```powershell
# Listar backups disponíveis
Get-ChildItem "D:\Backups\Obsidian\full\" -Filter "*.zip" | Sort-Name -Descending | Select -First 5

# Restaurar o mais recente para uma pasta de teste primeiro
python "80_SYSTEM/SCRIPTS/restore_backup.ps1" -Backup "D:\Backups\Obsidian\full\YYYY-MM-DD.zip" -Dest "C:\temp\megabrain-restore"
```
Só então, se o conteúdo estiver íntegro, substituir o vault.

---

## 3. Reindex travado (lock antigo)
**Sintoma:** reindex não roda e há `.reindex.lock` com >30 min.

```powershell
$lock = "80_SYSTEM\LOGS\.reindex.lock"
if ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalMinutes -gt 30) { Remove-Item $lock }
# Forçar reindex profundo
pwsh -NoProfile -File "80_SYSTEM\SCRIPTS\reindex_hybrid.ps1" -Mode deep
```

---

## 4. Dashboard (INDEX_GERAL.md) desatualizado ou quebrado
**Nunca** editar o `INDEX_GERAL.md` à mão. Regenerar:
```powershell
pwsh -NoProfile -File "80_SYSTEM\SCRIPTS\reindex_hybrid.ps1" -Mode deep
```

---

## 5. Modo preditivo não sugere nada
**Causa comum:** projeto inexistente em `30_PROJECTS/` ou sem notas `.md`.
```powershell
python "80_SYSTEM/SCRIPTS/predictive.py" suggest --project <Projeto>
# deve retornar {"suggested": "..."} ; se null, criar notas no projeto.
```

---

## 6. Contatos e escopos
| Escopo | Artefato |
|--------|----------|
| Backup | `80_SYSTEM/SCRIPTS/backup_vault.ps1`, `restore_backup.ps1` |
| Reindex | `80_SYSTEM/SCRIPTS/reindex_hybrid.ps1` |
| MCP | `80_SYSTEM/SCRIPTS/mcp_obsidian_server.py` |
| Hooks | `80_SYSTEM/HOOKS_HERMES/pre_task_hook.ps1`, `post_task_hook.ps1` |
| Preditivo | `80_SYSTEM/SCRIPTS/predictive.py` |
| Docs | `docs/` (architecture, sprints, brainstorm) |
