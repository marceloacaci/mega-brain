# megabrain.ps1 — Wrapper de comandos do MEGA BRAIN (encapsula as rotas do MCP server, porta 8770)
#
# Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File megabrain.ps1 <comando> [args]
#
# Comandos (equivale às rotas REST do MCP server):
#   health                                   → GET  /health
#   search "<texto>"                          → GET  /search?q=
#   read "<caminho/arquivo.md>"              → GET  /read?path=
#   stats                                     → GET  /stats
#   write "<arquivo.md>" "<conteudo>"         → POST /write
#   append "<arquivo.md>" "<conteudo>"        → POST /append
#   link "<nota1.md>" "<nota2.md>"            → POST /link
#   tag "<nota.md>" tag1,tag2                 → POST /tag
#   moc "<topico>"                            → POST /moc
#   rename "<arquivo.md>" "<novo.md>"         → POST /rename
#   move "<arquivo.md>" "<pasta-destino>"     → POST /move
#
# Exemplos:
#   megabrain.ps1 health
#   megabrain.ps1 search "MeuBolso"
#   megabrain.ps1 read "10_MEGA_BRAIN/INDEX_GERAL.md"
#   megabrain.ps1 tag "30_PROJECTS/MeuBolso/README.md" moc,financeiro

param(
    [Parameter(Position = 0, Mandatory = $true)][string]$Comando,
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]$ArgsRest
)

$MCP = "http://localhost:8770"
$SEP = "═══════════════════════════════════════"

function Invoke-MCP {
    param([string]$Method, [string]$Uri, [object]$Body = $null)
    try {
        $params = @{ Method = $Method; Uri = $Uri; TimeoutSec = 8; ErrorAction = 'Stop' }
        if ($Body) { $params.Body = ($Body | ConvertTo-Json -Compress); $params.ContentType = "application/json" }
        $r = Invoke-RestMethod @params
        return $r
    } catch {
        Write-Host "❌ Falha em $Uri : $_" -ForegroundColor Red
        return $null
    }
}

switch ($Comando.ToLower()) {
    'health' {
        $r = Invoke-MCP GET "$MCP/health"
        if ($r) { Write-Host "✅ MCP ONLINE · vault=$(Split-Path $r.vault -Leaf)" -ForegroundColor Green }
    }
    'search' {
        if (-not $ArgsRest -or -not $ArgsRest[0]) { Write-Host "❌ uso: megabrain search <texto>" -ForegroundColor Red; exit 1 }
        $q = [uri]::EscapeDataString($ArgsRest[0])
        $r = Invoke-MCP GET "$MCP/search?q=$q"
        if ($r) { $r | ConvertTo-Json -Depth 10 }
    }
    'read' {
        if (-not $ArgsRest -or -not $ArgsRest[0]) { Write-Host "❌ uso: megabrain read <caminho/arquivo.md>" -ForegroundColor Red; exit 1 }
        $p = [uri]::EscapeDataString($ArgsRest[0])
        $r = Invoke-MCP GET "$MCP/read?path=$p"
        if ($r) { if ($r.content) { Write-Host $r.content } else { $r | ConvertTo-Json -Depth 10 } }
    }
    'stats' {
        $r = Invoke-MCP GET "$MCP/stats"
        if ($r) { $r | ConvertTo-Json -Depth 10 }
    }
    'write' {
        if (-not $ArgsRest -or -not $ArgsRest[0] -or -not $ArgsRest[1]) { Write-Host "❌ uso: megabrain write <arquivo.md> <conteudo>" -ForegroundColor Red; exit 1 }
        $r = Invoke-MCP POST "$MCP/write" @{ path = $ArgsRest[0]; content = $ArgsRest[1] }
        if ($r) { Write-Host "✅ escrito: $($r.written)" -ForegroundColor Green }
    }
    'append' {
        if (-not $ArgsRest -or -not $ArgsRest[0] -or -not $ArgsRest[1]) { Write-Host "❌ uso: megabrain append <arquivo.md> <conteudo>" -ForegroundColor Red; exit 1 }
        $r = Invoke-MCP POST "$MCP/append" @{ path = $ArgsRest[0]; content = $ArgsRest[1] }
        if ($r) { Write-Host "✅ anexado: $($r.appended)" -ForegroundColor Green }
    }
    'link' {
        if (-not $ArgsRest -or -not $ArgsRest[0] -or -not $ArgsRest[1]) { Write-Host "❌ uso: megabrain link <nota1.md> <nota2.md>" -ForegroundColor Red; exit 1 }
        $r = Invoke-MCP POST "$MCP/link" @{ note1 = $ArgsRest[0]; note2 = $ArgsRest[1] }
        if ($r) { Write-Host "✅ link: $($r.linked)" -ForegroundColor Green }
    }
    'tag' {
        if (-not $ArgsRest -or -not $ArgsRest[0] -or -not $ArgsRest[1]) { Write-Host "❌ uso: megabrain tag <nota.md> tag1,tag2" -ForegroundColor Red; exit 1 }
        $tags = $ArgsRest[1] -split ',' | ForEach-Object { $_.Trim() }
        $r = Invoke-MCP POST "$MCP/tag" @{ note = $ArgsRest[0]; tags = $tags }
        if ($r) { Write-Host "✅ tag: $($r.tagged)" -ForegroundColor Green }
    }
    'moc' {
        if (-not $ArgsRest -or -not $ArgsRest[0]) { Write-Host "❌ uso: megabrain moc <topico>" -ForegroundColor Red; exit 1 }
        $r = Invoke-MCP POST "$MCP/moc" @{ topic = $ArgsRest[0] }
        if ($r) { Write-Host "✅ moc: $($r.moc)" -ForegroundColor Green }
    }
    'rename' {
        if (-not $ArgsRest -or -not $ArgsRest[0] -or -not $ArgsRest[1]) { Write-Host "❌ uso: megabrain rename <arquivo.md> <novo.md>" -ForegroundColor Red; exit 1 }
        $r = Invoke-MCP POST "$MCP/rename" @{ path = $ArgsRest[0]; new_name = $ArgsRest[1] }
        if ($r) { Write-Host "✅ renomeado: $($r.renamed)" -ForegroundColor Green }
    }
    'move' {
        if (-not $ArgsRest -or -not $ArgsRest[0] -or -not $ArgsRest[1]) { Write-Host "❌ uso: megabrain move <arquivo.md> <pasta-destino>" -ForegroundColor Red; exit 1 }
        $r = Invoke-MCP POST "$MCP/move" @{ path = $ArgsRest[0]; new_dir = $ArgsRest[1] }
        if ($r) { Write-Host "✅ movido: $($r.moved)" -ForegroundColor Green }
    }
    default {
        Write-Host $SEP -ForegroundColor Cyan
        Write-Host "  MEGA BRAIN — comandos disponíveis" -ForegroundColor Cyan
        Write-Host $SEP -ForegroundColor Cyan
        Write-Host "  health                         Status do servidor MCP" -ForegroundColor White
        Write-Host "  search <texto>                 Busca no vault" -ForegroundColor White
        Write-Host "  read <arquivo.md>              Lê o conteúdo de uma nota" -ForegroundColor White
        Write-Host "  stats                          Contagem de notas por pasta" -ForegroundColor White
        Write-Host "  write <arquivo.md> <conteudo>  Cria/sobrepõe uma nota" -ForegroundColor White
        Write-Host "  append <arquivo.md> <conteudo> Anexa conteúdo a uma nota" -ForegroundColor White
        Write-Host "  link <n1.md> <n2.md>           Liga duas notas" -ForegroundColor White
        Write-Host "  tag <nota.md> t1,t2            Aplica tags a uma nota" -ForegroundColor White
        Write-Host "  moc <topico>                   Gera MOC do tópico" -ForegroundColor White
        Write-Host "  rename <arquivo.md> <novo.md> Renomeia uma nota" -ForegroundColor White
        Write-Host "  move <arquivo.md> <pasta>     Move uma nota para outra pasta" -ForegroundColor White
    }
}
