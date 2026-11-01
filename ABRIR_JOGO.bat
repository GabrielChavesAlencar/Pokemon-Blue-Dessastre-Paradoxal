@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Campanha
set "BLUE_BATTLE_LAB="
set "BLUE_BATTLE_LAB_SMOKE="
where py >nul 2>&1
if errorlevel 1 goto :python
py -3 -X utf8 "%~dp0scripts\launch_game.py" --prepare-only
goto :prepared
:python
python -X utf8 "%~dp0scripts\launch_game.py" --prepare-only
:prepared
if errorlevel 1 goto :error
start "" /D "%~dp0game" /WAIT "%~dp0game\Game.exe"
if errorlevel 1 goto :error
exit /b 0
:error
echo [ERRO] Nao foi possivel abrir a campanha. Confira a mensagem acima.
pause
exit /b 1
