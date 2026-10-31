@echo off
setlocal
cd /d "%~dp0"
if not exist "game\Game.rxproj" (
  echo [ERRO] Arquivos do jogo nao encontrados. Execute BAIXAR_BASE_DECADES.bat.
  pause
  exit /b 1
)
start "" "%~dp0game\Game.rxproj"
