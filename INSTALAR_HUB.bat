@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Instalar Hub de Batalha
echo Feche o jogo antes de instalar. O download da base pode levar varios minutos.
where py >nul 2>&1
if errorlevel 1 goto :python
py -3 -X utf8 "%~dp0scripts\install_game.py" --hub-only --apply
goto :finish
:python
python -X utf8 "%~dp0scripts\install_game.py" --hub-only --apply
:finish
set "BLUE_HUB_INSTALL_EXIT=%errorlevel%"
if not "%BLUE_HUB_INSTALL_EXIT%"=="0" echo [ERRO] Confira a mensagem acima. Sao necessarios Python 3.10+ e Git para Windows.
pause
exit /b %BLUE_HUB_INSTALL_EXIT%
