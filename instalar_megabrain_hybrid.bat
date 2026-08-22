@echo off
chcp 65001 >nul
title MEGA BRAIN - Instalação Híbrida
cd /d "%~dp0"
set VAULT=D:\Programas (Disco D)\Obsidian\cofres\Marcelo IA Skills
set SCRIPTS=%VAULT%\80_SYSTEM\SCRIPTS
echo ============================================
echo    ✦ MEGA BRAIN - Instalação Híbrida
echo    Light 6h + Deep Semanal
echo ============================================
echo.
echo [1/5] Criando estrutura de pastas...
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTS%\setup_megabrain.ps1"
if errorlevel 1 goto :error
echo.
echo [2/5] Migrando para modelo híbrido (se já instalado)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTS%\migrate_to_hybrid.ps1"
if errorlevel 1 goto :error
echo.
echo [3/5] Instalando servidor MCP...
cd /d "%VAULT%\80_SYSTEM\MCP"
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv
    if errorlevel 1 goto :error
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 goto :error
) else (
    call venv\Scripts\activate.bat
)
cd /d "%VAULT%"
echo.
echo [4/5] Criando pasta de backups...
if not exist "D:\Backups\Obsidian" mkdir "D:\Backups\Obsidian"
echo.
echo [5/5] Teste final...
cd /d "%VAULT%\80_SYSTEM\HOOKS_HERMES"
powershell -NoProfile -ExecutionPolicy Bypass -File "post_task_hook.ps1" -Tarefa "Instalacao hibrida" -Projeto "setup" -Resultado "sucesso"
if errorlevel 1 goto :error
echo.
echo ============================================
echo    ✅ INSTALAÇÃO HÍBRIDA COMPLETA!
echo ============================================
echo.
echo ✦ Cronograma:
echo    • Light: a cada 6 horas (atualiza métricas)
echo    • Deep:  domingo 23:00 (análise completa)
echo    • Backup: diário 02:00 + incremental 6h
echo.
echo ✦ Próximas ações:
echo    1. Abrir Obsidian → ativar CSS 'megabrain'
echo    2. Instalar plugins: Dataview, Templater, QuickAdd
echo    3. Verificar tarefas agendadas:
echo       Get-ScheduledTask ^| Where { $_.TaskName -like 'MEGA_BRAIN_*' }
echo.
goto :end
:error
echo.
echo ❌ ERRO durante a instalação!
echo    Verifique os logs em: %VAULT%\80_SYSTEM\LOGS\
echo    (o passo [3/5] cria o venv se falte; se 'python' nao estiver no PATH, instale Python 3.)
exit /b 1
:END
pause
goto :eof
