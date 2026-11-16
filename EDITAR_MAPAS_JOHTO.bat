@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Johto Map Studio - Blue Dessastre Paradoxal
echo ===============================================================
echo    JOHTO MAP STUDIO - EDITOR VISUAL DE MAPAS NO WINDOWS
echo ===============================================================
echo.
if not exist "game\Game.exe" (
  echo [ERRO] Game.exe nao encontrado nessa instalacao.
  echo Instale o jogo principal usando Blue-Story.exe primeiro.
  pause
  exit /b 1
)
if not exist "game\Data\Tilesets.rxdata" (
  echo [ERRO] Dados nativos do jogo ausentes.
  pause
  exit /b 1
)
if not exist "scripts\regions\johto_map_editor.py" (
  echo [ERRO] Editor nao encontrado. Atualize o Blue-Story.exe.
  pause
  exit /b 1
)
set "PYTHON="
for /d %%P in ("%CD%\tools\python-*") do (
  if exist "%%~fP\python.exe" set "PYTHON=%%~fP\python.exe"
)
if not defined PYTHON (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON=py -3"
)
if not defined PYTHON (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
  echo [ERRO] Python nao foi encontrado. Execute Blue-Story.exe.
  pause
  exit /b 1
)
echo.
echo Pasta do jogo: "%CD%\game"
echo Editor: http://127.0.0.1:8771
echo.
echo  - Feche Game.exe antes de salvar o mapa.
echo  - O editor cria backups automaticamente.
echo  - Para publicar na main: instale GitHub CLI e execute gh auth login.
echo  - O GitHub recebe somente patches JSON, nunca saves ou RXDATA.
echo.
echo Para encerrar o editor, feche esta janela ou pressione Ctrl+C.
echo.
%PYTHON% scripts\regions\johto_map_editor.py --game-dir game --port 8771
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
 echo.
 echo [ERRO] Editor nao iniciou. Confira a porta 8771 e a instalacao.
 pause
)
exit /b %RESULT%
