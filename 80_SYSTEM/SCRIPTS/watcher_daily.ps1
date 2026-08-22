# watcher_daily.ps1 — heartbeat do MegaBrain
$MCP = "http://127.0.0.1:8770"
$hoje = Get-Date -Format "yyyy-MM-dd"
$body = @{ path = "20_DAILY_NOTES/$hoje.md"; content = "- 🔄 heartbeat MegaBrain 21:26" } | ConvertTo-Json
try { Invoke-RestMethod -Uri "$MCP/append" -Method Post -ContentType "application/json" -Body $body | Out-Null; Write-Host "heartbeat OK" }
catch { Write-Warning "MCP indisponivel: $_" }
