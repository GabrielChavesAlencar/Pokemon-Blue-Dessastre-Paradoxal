@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul
title Kanto - instalar 64 musicas BGM e ME no jogo
echo.
echo ==================================================
echo   MUSICA DE KANTO - INSTALACAO LOCAL, SEM SOBRESCRITA
echo ==================================================
echo [INFO] Os MP3s versionados estao em assets\music\kanto\
echo [INFO] O jogo local usa game\Audio\BGM e game\Audio\ME.
echo [INFO] Saves, mapas e arquivos originais de Decades nao serao substituidos.
echo.
set "PYTHON_EXE="
set "PYTHON_EXTRA="
for /d %%D in ("%~dp0tools\python-*") do if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
if defined PYTHON_EXE goto :verify
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_EXTRA=-3"
    goto :verify
  )
)
where python >nul 2>&1
if not errorlevel 1 (
  python -c "import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto :verify
  )
)
echo [ERRO] Instale Python 3.10+ ou use o Python portatil do Blue Story.
goto :failure
:verify
echo [1/3] Validando 64 musicas com SHA do Git...
"%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\music\install_kanto_music.py" --audit
if errorlevel 1 goto :failure
echo.
echo [2/3] Prevendo instalacao sem alterar nenhum arquivo...
"%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\music\install_kanto_music.py"
if errorlevel 1 goto :failure
echo.
echo [3/3] Copiando apenas as musicas ausentes...
"%PYTHON_EXE%" %PYTHON_EXTRA% -X utf8 "scripts\music\install_kanto_music.py" --apply
if errorlevel 1 goto :failure
echo.
echo [OK] Musicoteca Kanto instalada. Use Blue Studio ^> Editor de ROM ^> Musicas
echo [IMPORTANTE] A configuracao dos mapas/eventos permanece a original ate voce escolher as faixas.
pause
exit /b 0
:failure
echo.
echo [ERRO] Importacao interrompida; nenhum arquivo de audio preexistente foi sobrescrito.
pause
exit /b 2
