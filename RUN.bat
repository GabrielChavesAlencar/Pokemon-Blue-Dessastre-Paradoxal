@echo off
setlocal
cd /d "%~dp0"
title Pokemon Blue Dessastre Paradoxal - Blue Studio
where py >nul 2>&1
if %errorlevel%==0 (
    py -3 "server\main.py"
) else (
    where python >nul 2>&1
    if %errorlevel%==0 (
        python "server\main.py"
    ) else (
        echo [ERRO] Python 3 nao encontrado.
        echo Instale Python 3.10 ou superior: https://www.python.org/downloads/
    )
)
echo.
pause
