@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Instalar Sinnoh QA Privado

echo ============================================================
echo  SINNOH - INSTALADOR DE COPIA QA ISOLADA (S12)
echo ============================================================
echo [AVISO] Nenhum arquivo do jogo principal ou save sera alterado.
echo [AVISO] Sem overlay e especificacao auditados, fica bloqueado.
echo.
set "SINNOH_MODE=--install"
if "%~1"=="" goto :run
if /I "%~1"=="--check" (
  set "SINNOH_MODE="
  goto :run
)
echo [ERRO] Use duplo clique para instalar, ou --check para conferir.
goto :blocked

:run
if not exist "scripts\regions\sinnoh_s12_installer.py" (
  echo [ERRO] Instalador S12 ausente nesta pasta.
  goto :blocked
)
where py >nul 2>&1
if errorlevel 1 goto :python
py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :python
py -3 -X utf8 "scripts\regions\sinnoh_s12_installer.py" --auto %SINNOH_MODE%
goto :finish

:python
where python >nul 2>&1
if errorlevel 1 goto :missing
python -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :missing
python -X utf8 "scripts\regions\sinnoh_s12_installer.py" --auto %SINNOH_MODE%
goto :finish

:missing
echo [ERRO] Python 3.10+ nao encontrado no Windows.
goto :blocked

:blocked
set "SINNOH_EXIT=2"
goto :status

:finish
set "SINNOH_EXIT=%errorlevel%"
if not "%SINNOH_EXIT%"=="0" (
  echo [BLOQUEADO] Consulte .blue-work\sinnoh-qa-spec.json e o overlay auditado.
  echo [SEGURO] Nenhum Game.exe sera iniciado. Nenhum save sera migrado.
) else (
  echo [OK] Se foi instalada uma copia, use SINNOH_JOGAR_EXPERIMENTAL.bat.
  echo [INFO] A instalacao QA nao certifica regiao jogavel.
)

:status
echo.
echo [SINNOH S12] Codigo de saida: %SINNOH_EXIT%
if /I not "%SINNOH_QA_NO_PAUSE%"=="1" pause
exit /b %SINNOH_EXIT%
