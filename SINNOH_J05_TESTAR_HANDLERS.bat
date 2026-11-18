@echo off
setlocal
cd /d "%~dp0"
echo =======================================================
echo SINNOH J05 - TESTES RUBY OFFLINE DOS HANDLERS
echo Inicial unico, Barry, Rowan, save regional e reentrancia
echo NAO executa Game.exe e NAO acessa saves pessoais.
echo =======================================================
where ruby >nul 2>nul
if errorlevel 1 (
  echo ERRO: Ruby nao encontrado no PATH. Nao executar nenhum jogo.
  pause
  exit /b 2
)
ruby tests\sinnoh_j05_atomic_runtime.rb scripts\regions\SinnohPilot.rb
set "CODE=%ERRORLEVEL%"
if "%CODE%"=="0" (
  echo J05: testes Ruby sinteticos aprovados. NAO significa Game.exe jogavel.
) else (
  echo J05: testes falharam. Corrigir antes de prosseguir.
)
pause
exit /b %CODE%
