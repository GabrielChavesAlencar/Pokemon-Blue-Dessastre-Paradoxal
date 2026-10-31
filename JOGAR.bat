@echo off
setlocal
cd /d "%~dp0"
if not exist "game\Game.exe" (
  echo [ERRO] Game.exe nao encontrado. Execute BAIXAR_BASE_DECADES.bat.
  pause
  exit /b 1
)
start "" "%~dp0game\Game.exe"
