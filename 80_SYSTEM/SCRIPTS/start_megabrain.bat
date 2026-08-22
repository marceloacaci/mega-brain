@echo off
REM start_megabrain.bat — garante o servidor MCP MEGA BRAIN na porta 8770.
REM Corre no arranque do Windows (Startup) ou manualmente.
REM Se a porta ja estiver a ouvir, nao faz nada (evita duplo bind).

set VAULT=D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills
set SCRIPT=%VAULT%\80_SYSTEM\SCRIPTS\mcp_obsidian_server.py
set PORT=8770

REM verifica se a 8770 ja responde
curl -s --max-time 3 http://127.0.0.1:%PORT%/health >nul 2>&1
if %errorlevel%==0 (
    echo [MegaBrain] servidor ja esta a correr em %PORT%.
    goto :fim
)

REM porta livre: sobe o servidor (janela minimizada, nao bloqueia)
echo [MegaBrain] a iniciar servidor MCP na porta %PORT%...
if exist "%SCRIPT%" (
    start "" /min python "%SCRIPT%" --port %PORT%
    timeout /t 2 >nul
    curl -s --max-time 3 http://127.0.0.1:%PORT%/health >nul 2>&1
    if %errorlevel%==0 ( echo [MegaBrain] OK — vivo em http://127.0.0.1:%PORT% ) else ( echo [MegaBrain] AVISO: nao respondeu. )
) else (
    echo [MegaBrain] ERRO: %SCRIPT% nao encontrado.
)

:fim
pause
