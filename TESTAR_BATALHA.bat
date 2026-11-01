@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Laboratorio de Batalha
set "BLUE_PYTHON="
call :try_python "py"
if not defined BLUE_PYTHON call :try_python "python"
if not defined BLUE_PYTHON call :try_python "%~dp0tools\python\python.exe"
if not defined BLUE_PYTHON call :try_python "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
if not defined BLUE_PYTHON for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do call :try_python "%%~fD\python.exe"
if not defined BLUE_PYTHON for /d %%D in ("%ProgramFiles%\Python*") do call :try_python "%%~fD\python.exe"
if not defined BLUE_PYTHON goto :no_python
echo [INFO] Python: %BLUE_PYTHON%
echo [INFO] Preparando o laboratorio. Aguarde a compilacao na primeira abertura.
"%BLUE_PYTHON%" -X utf8 "%~dp0scripts\battle_lab\launch.py" %*
set "BLUE_EXIT=%errorlevel%"
if not "%BLUE_EXIT%"=="0" (
  echo [ERRO] O laboratorio nao abriu. Confira a mensagem acima.
  echo Logs: game\Data\blue-battle-launcher.log e blue-battle-lab.log
  pause
)
exit /b %BLUE_EXIT%

:try_python
if defined BLUE_PYTHON exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 set "BLUE_PYTHON=%~1"
exit /b 0

:no_python
echo [ERRO] Python 3.10 ou superior nao encontrado nas instalacoes locais.
echo Instale em https://www.python.org/downloads/ e abra este arquivo novamente.
pause
exit /b 1
