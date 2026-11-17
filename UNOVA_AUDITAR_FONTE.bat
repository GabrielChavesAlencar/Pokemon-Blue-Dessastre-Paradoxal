@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title UNOVA - Auditoria isolada de fonte (nao instala mapas)
echo ============================================================
echo   UNOVA U02/U03 - AUDITORIA SOMENTE LEITURA
echo   Nenhuma modificacao no Game.exe, mapas ou saves
echo ============================================================
echo.
set "SOURCE=.blue-work\unova\sources\Pokemon_World_V18.zip"
if not exist ".blue-work\unova\sources" mkdir ".blue-work\unova\sources"
if errorlevel 1 (
    echo ERRO: nao consegui preparar a pasta de trabalho isolada.
    pause
    exit /b 2
)
if not "%~1"=="" (
    if /I not "%~x1"==".zip" (
        echo ERRO: arraste apenas o arquivo ZIP original do projeto Pokemon World V18.
        pause
        exit /b 2
    )
    if not exist "%~1" (
        echo ERRO: arquivo arrastado nao encontrado.
        pause
        exit /b 2
    )
    if exist "%SOURCE%" (
        echo ZIP ja existe. Nenhum arquivo foi substituido.
    ) else (
        copy /-Y "%~1" "%SOURCE%" >nul
        if errorlevel 1 (
            echo ERRO: nao foi possivel copiar o ZIP para a pasta isolada.
            pause
            exit /b 2
        )
    )
)
set "PYTHON_CMD=python"
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
echo [U02] Conferindo metadados do ZIP sem extrair arquivos...
%PYTHON_CMD% scripts\regions\audit_unova_u02.py --write
set "U02_EXIT=%errorlevel%"
echo.
echo [U03] Validando catalogo simbolico das areas de Black/White...
%PYTHON_CMD% scripts\regions\audit_unova_u03_catalog.py
set "U03_EXIT=%errorlevel%"
echo.
if not "%U02_EXIT%"=="0" (
    echo [BLOQUEADO] Coloque o ZIP de Pokemon World V18 na pasta:
    echo   %SOURCE%
    echo Link original do autor:
    echo   https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file
    echo Relatorio, quando permitido:
    echo   .blue-work\unova\audit\u02-source.json
)
if not "%U03_EXIT%"=="0" (
    echo [BLOQUEADO] Catalogo simbolico de Unova necessita revisao.
)
echo.
echo Nenhum mapa foi instalado e Unova nao foi habilitada.
pause
if not "%U02_EXIT%"=="0" exit /b 2
if not "%U03_EXIT%"=="0" exit /b 2
exit /b 0
