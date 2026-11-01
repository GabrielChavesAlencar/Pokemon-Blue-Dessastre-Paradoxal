@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Instalacao
echo Feche o jogo antes de instalar. O download inicial pode levar varios minutos.
where py >nul 2>&1
if errorlevel 1 goto :python
py -3 -X utf8 "%~dp0scripts\install_game.py" --apply
goto :finish
:python
python -X utf8 "%~dp0scripts\install_game.py" --apply
:finish
if errorlevel 1 echo [ERRO] Veja a mensagem acima. Sao necessarios Python 3.10+ e Git para Windows.
pause
