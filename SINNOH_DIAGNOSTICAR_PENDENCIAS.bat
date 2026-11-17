@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Sinnoh R07 Diagnostico Seguro

echo ==========================================================
echo  SINNOH - DIAGNOSTICAR MAPIDS E RESERVAS FUTURAS (R07)
echo ==========================================================
echo.
echo [INFO] Esta ferramenta nao instala mapas e nao abre Game.exe.
echo [INFO] Os saves e o Decades principal permanecem intactos.
echo [INFO] Relatorio: .blue-work\sinnoh-diagnostics\r07-reservations.json
echo.
if not exist "scripts\regions\audit_sinnoh_r07_reservations.py" goto :missing_script
where py >nul 2>&1
if errorlevel 1 goto :python
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :python
py -3 -X utf8 "scripts\regions\audit_sinnoh_r07_reservations.py" --project "%CD%" --write
goto :finish

:python
where python >nul 2>&1
if errorlevel 1 goto :missing_python
python -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :missing_python
python -X utf8 "scripts\regions\audit_sinnoh_r07_reservations.py" --project "%CD%" --write
goto :finish

:missing_script
echo [ERRO] Auditor R07 nao encontrado nesta pasta.
goto :blocked
:missing_python
echo [ERRO] Python 3.10+ nao encontrado.
goto :blocked
:blocked
set "SINNOH_EXIT=2"
goto :status
:finish
set "SINNOH_EXIT=%errorlevel%"
if not "%SINNOH_EXIT%"=="0" echo [PENDENTE] Veja os blockers no relatorio; nenhuma instalacao foi executada.
if "%SINNOH_EXIT%"=="0" echo [REVISAO] Reservas conferiveis offline; ainda falta QA nativo.
:status
echo.
echo [SINNOH R07] Codigo de saida: %SINNOH_EXIT%
if /I not "%SINNOH_QA_NO_PAUSE%"=="1" pause
exit /b %SINNOH_EXIT%
