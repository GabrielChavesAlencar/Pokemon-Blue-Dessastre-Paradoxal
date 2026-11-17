@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Unova U07 - Contratos iniciais de Nuvema (sem instalar)
echo ==============================================================
echo  UNOVA U07 - AUDITOR DE EVENTOS DA CAMPANHA WHITE
echo  13 contratos planejados, nenhuma alteracao no Game.exe ou saves
echo ==============================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
echo [1/2] Conferindo areas, NPCs, historias e recompensas unicas...
%PY% scripts\regions\audit_unova_u07_events.py --simulate-demo --write
if errorlevel 1 goto :blocked
echo.
echo [2/2] Testando regressao simulada: progressao/reentrada/batalhas...
%PY% -m unittest discover -s tests -p "test_unova_u07_events.py" -v
if errorlevel 1 goto :blocked
echo.
echo [OK] Contratos validados apenas com dados simbolicos.
echo Relatorio: .blue-work\unova\audit\u07-events-contract-preview.json
echo Nenhum MapID foi reservado e nenhum evento foi instalado no jogo.
pause
exit /b 0
:blocked
echo.
echo [BLOQUEADO] Contratos invalidos. Jogo e saves permanecem intactos.
pause
exit /b 2
