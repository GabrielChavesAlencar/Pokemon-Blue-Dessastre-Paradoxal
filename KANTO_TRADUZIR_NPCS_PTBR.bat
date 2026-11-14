@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul
title Pokemon Blue - traduzir NPCs novos de Kanto

echo.
echo ======================================================
echo  TRADUZIR NPCS DE KANTO PARA PORTUGUES BRASILEIRO
echo ======================================================
echo [INFO] A fonte FRLG original e os saves nao serao alterados.
echo [INFO] As traducoes ficarao SOMENTE em .blue-work.
echo [INFO] A primeira execucao pode baixar o modelo en-pt do Argos.
echo [INFO] O jogo principal Decades nao sera modificado.
echo.

rem Prefer a system Python with pip; accept Blue's bundled portable Python
rem only if no system interpreter is installed.
set "PYTHON_EXE="
set "PYTHON_EXTRA="
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_EXTRA=-3"
    goto :ready
  )
)
where python >nul 2>&1
if not errorlevel 1 (
  python -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto :ready
  )
)
for /d %%D in ("%~dp0tools\python-*") do if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
if defined PYTHON_EXE goto :ready
echo [ERRO] Python 3.10+ nao encontrado. Abra Blue-Story.exe para preparar a instalacao.
goto :error

:ready
if not exist ".blue-work\frlg-source\Essentials FRLG\Data\MapInfos.rxdata" (
  echo [ERRO] Fonte FRLG ausente. Execute KANTO_JOGAR_EXPERIMENTAL.bat primeiro.
  goto :error
)
"%PYTHON_EXE%" %PYTHON_EXTRA% -c "import argostranslate" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Instalando o tradutor offline Argos Translate no Python selecionado.
  "%PYTHON_EXE%" %PYTHON_EXTRA% -m pip install argostranslate
  if errorlevel 1 (
    echo [ERRO] Nao foi possivel instalar Argos Translate.
    echo [AJUDA] Instale Python 3 do site python.org com pip e execute este BAT novamente.
    goto :error
  )
)
"%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\regions\translate_kanto_npcs.py" --install-model
if errorlevel 1 goto :error
echo.
echo [OK] Catalogo PT-BR local criado. Reconstruindo Kanto isolado.
call "%~dp0KANTO_JOGAR_EXPERIMENTAL.bat" --rebuild
exit /b %errorlevel%

:error
echo.
echo [AJUDA] Confira docs\KANTO_NPCS_PORTUGUES.md.
pause
exit /b 2
