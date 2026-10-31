@echo off
setlocal
cd /d "%~dp0"
title Pokemon Blue Dessastre Paradoxal - Personalizar titulo do jogo
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "server\prepare_game.py"
) else (
    python "server\prepare_game.py"
)
if errorlevel 1 (
    echo Falha ao personalizar. Consulte a mensagem acima.
)
pause
