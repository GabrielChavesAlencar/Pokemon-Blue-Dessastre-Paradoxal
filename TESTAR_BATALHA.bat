@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Laboratorio de Batalha
set "BLUE_PYTHON="
if not exist "%~dp0.blue-work" mkdir "%~dp0.blue-work"
set "BLUE_CMD_LOG=%~dp0.blue-work\battle-launcher-cmd.log"
echo BLUE CMD ^| %date% %time% ^| %~f0 > "%BLUE_CMD_LOG%"
call :try_python "%~dp0tools\python\python.exe"
if not defined BLUE_PYTHON call :try_python "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
if not defined BLUE_PYTHON for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do call :try_python "%%~fD\python.exe"
if not defined BLUE_PYTHON for /d %%D in ("%ProgramFiles%\Python*") do call :try_python "%%~fD\python.exe"
if not defined BLUE_PYTHON call :try_python "py"
if not defined BLUE_PYTHON call :try_python "python"
if not defined BLUE_PYTHON goto :no_python
echo [INFO] Python: %BLUE_PYTHON%
echo Python: %BLUE_PYTHON% >> "%BLUE_CMD_LOG%"
echo [INFO] Preparando o laboratorio. Aguarde a compilacao na primeira abertura.
if "%~1"=="" goto :open_native_game
"%BLUE_PYTHON%" -X utf8 "%~dp0scripts\battle_lab\launch.py" %*
set "BLUE_EXIT=%errorlevel%"
goto :finish

:open_native_game
"%BLUE_PYTHON%" -X utf8 "%~dp0scripts\battle_lab\launch.py" --prepare-only
set "BLUE_EXIT=%errorlevel%"
if not "%BLUE_EXIT%"=="0" goto :finish
set "BLUE_BATTLE_LAB=1"
set "BLUE_BATTLE_LAB_SMOKE="
echo [INFO] Abrindo Game.exe diretamente pelo Windows.
echo [INFO] Mantenha este CMD aberto; pode minimiza-lo.
start "" /D "%~dp0game" /WAIT "%~dp0game\Game.exe"
set "BLUE_EXIT=%errorlevel%"
echo Native game exit: %BLUE_EXIT% >> "%BLUE_CMD_LOG%"

:finish
echo Launcher exit: %BLUE_EXIT% >> "%BLUE_CMD_LOG%"
if not "%BLUE_EXIT%"=="0" (
  echo [ERRO] O laboratorio nao abriu. Confira a mensagem acima.
  echo Logs: game\Data\blue-battle-launcher.log e blue-battle-lab.log
  pause
)
exit /b %BLUE_EXIT%

:try_python
if defined BLUE_PYTHON exit /b 0
set "BLUE_PROBE=%~dp0.blue-work\python-probe-%RANDOM%-%RANDOM%.txt"
"%~1" -c "import sys; assert sys.version_info >= (3,10); print('BLUE_PYTHON_OK'); print(sys.executable)" > "%BLUE_PROBE%" 2>nul
if errorlevel 1 goto :probe_cleanup
findstr /X /C:"BLUE_PYTHON_OK" "%BLUE_PROBE%" >nul 2>&1
if errorlevel 1 goto :probe_cleanup
for /f "usebackq skip=1 delims=" %%P in ("%BLUE_PROBE%") do if not defined BLUE_PYTHON set "BLUE_PYTHON=%%P"
:probe_cleanup
if exist "%BLUE_PROBE%" del /q "%BLUE_PROBE%" >nul 2>&1
exit /b 0

:no_python
echo [ERRO] Python 3.10 ou superior nao encontrado nas instalacoes locais.
echo Instale em https://www.python.org/downloads/ e abra este arquivo novamente.
pause
exit /b 1
