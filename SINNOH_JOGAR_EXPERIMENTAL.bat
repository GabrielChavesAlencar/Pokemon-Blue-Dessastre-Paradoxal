@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Sinnoh QA Isolado

echo.
echo ============================================================
echo   POKEMON BLUE - TESTAR SINNOH NA COPIA PRIVADA
echo ============================================================
echo.
echo [IMPORTANTE] Nao inicia o Decades principal e nao altera seus saves.
echo [IMPORTANTE] Sem fontes, mapas e instalacao QA verificados, sera bloqueado.
echo.

set "SINNOH_MODE=--start"
if "%~1"=="" goto :validate
if /I "%~1"=="--check" (
  set "SINNOH_MODE="
  goto :validate
)
echo [ERRO] Argumento nao permitido. Use --check ou clique duas vezes.
goto :fail

:validate
if not exist "scripts\regions\launch_sinnoh_qa.py" (
  echo [ERRO] Script de QA ausente na pasta do projeto.
  goto :fail
)

where py >nul 2>&1
if errorlevel 1 goto :try_python
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :try_python
py -3 -X utf8 "scripts\regions\launch_sinnoh_qa.py" --auto %SINNOH_MODE%
goto :finish

:try_python
where python >nul 2>&1
if errorlevel 1 goto :no_python
python -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :no_python
python -X utf8 "scripts\regions\launch_sinnoh_qa.py" --auto %SINNOH_MODE%
goto :finish

:no_python
echo [ERRO] Python 3.10+ nao encontrado.
echo [INFO] Instale Python ou abra o Blue-Story que inclua o runtime.
goto :fail

:fail
set "SINNOH_EXIT=2"
goto :status

:finish
set "SINNOH_EXIT=%errorlevel%"
if not "%SINNOH_EXIT%"=="0" (
  echo.
  echo [BLOQUEADO] O Game.exe principal nao sera usado como alternativa.
  echo [DICA] Confira a copia .blue-work\game-sinnoh-qa-XXXXXXXXXXXX.
)

:status
echo.
echo [SINNOH QA] Codigo de saida: %SINNOH_EXIT%
if /I not "%SINNOH_QA_NO_PAUSE%"=="1" pause
exit /b %SINNOH_EXIT%
