@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul
title Pokemon Blue - Kanto experimental (jogabilidade)
echo.
echo ===============================================
echo   KANTO EXPERIMENTAL - JOGAR E REPORTAR
echo ===============================================
echo [INFO] O jogo abre numa copia .blue-work, com saves separados do Decades.
echo [INFO] Na primeira vez, a fonte de mapas FRLG do autor sera preparada.
echo [INFO] A fonte e conferida por SHA-256 antes de ser extraida.
echo [INFO] A copia principal do jogo e seus saves nao serao alterados.
echo.

rem Blue-Story.exe already installs an isolated portable Python runtime.
rem Prefer it so people downloading the EXE do NOT have to install Python.
set "PYTHON_EXE="
set "PYTHON_EXTRA="
for /d %%D in ("%~dp0tools\python-*") do if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
if defined PYTHON_EXE goto :run

where py >nul 2>&1
if not errorlevel 1 (
  py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_EXTRA=-3"
    goto :run
  )
)
where python >nul 2>&1
if not errorlevel 1 (
  python -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto :run
  )
)
echo [ERRO] Python portatil/3.10+ nao encontrado. Abra Blue-Story.exe para preparar a instalacao.
goto :error

:run
"%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\regions\ensure_source.py"
if errorlevel 1 (
  echo [ERRO] Nao foi possivel preparar os mapas de Kanto.
  echo [AJUDA] Confira a internet, a fonte FRLG e docs\KANTO_TESTE_EXPERIMENTAL.md.
  goto :error
)

"%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\regions\gui_diagnostics.py" --launch-only %*
set "GAME_EXIT=%errorlevel%"
if defined KANTO_FEEDBACK_SCOPE (
  "%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\regions\kanto_feedback.py" --scope "%KANTO_FEEDBACK_SCOPE%"
) else (
  "%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\regions\kanto_feedback.py"
)
echo.
if "%GAME_EXIT%"=="0" (
  echo [OK] Game.exe do piloto foi encerrado sem erro detectado.
) else (
  echo [AVISO] O piloto nao teve inicializacao confirmada. Veja os logs locais.
)
echo [IMPORTANTE] Teste visual e batalhas so ficam aprovados apos jogar de verdade.
echo [INFO] Logs e checklist em .blue-work\kanto-gui-reports.
pause
exit /b %GAME_EXIT%

:error
pause
exit /b 2
