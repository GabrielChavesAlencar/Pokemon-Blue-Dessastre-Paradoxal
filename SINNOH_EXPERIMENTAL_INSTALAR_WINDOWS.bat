@echo off
setlocal
cd /d "%~dp0"
set "BLUE_GAME=%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game"
echo ================================================
echo POKEMON BLUE - SINNOH PILOTO WINDOWS EXPERIMENTAL
echo ================================================
echo.
echo Somente COPIA SEPARADA em .blue-work.
echo Seus saves, mapas e o Game.exe original nao serao alterados.
echo.
if not exist "%BLUE_GAME%\Game.exe" (
  echo Nao encontrei o Game.exe em:
  echo "%BLUE_GAME%"
  set /p "BLUE_GAME=Informe a pasta exata que contem Game.exe: "
)
if not exist "%BLUE_GAME%\Game.exe" (
  echo ERRO: Game.exe nao localizado.
  pause
  exit /b 2
)
where py >nul 2>nul
if errorlevel 1 (
  echo ERRO: Python 3.11 ou superior nao encontrado.
  echo Instale o Python e marque "Add Python to PATH".
  pause
  exit /b 2
)
echo.
echo Instalando Sinnoh SOMENTE em nova copia experimental...
py -3 "scripts\regions\install_sinnoh_experimental_windows.py" --game "%BLUE_GAME%" --project "%CD%" --install
if errorlevel 1 (
  echo.
  echo A instalacao foi BLOQUEADA com seguranca.
  echo Leia a mensagem de erro para descobrir o que falta no jogo local.
  pause
  exit /b 2
)
echo.
echo Copia pronta. Abra a pasta .blue-work,
echo entre em game-sinnoh-experimental-XXXXXXXXXXXX
echo e clique em INICIAR_SINNOH_EXPERIMENTAL.bat.
echo.
echo O primeiro inicio compila os PBS apenas no QA.
echo Se nao aparecer a prova de compilacao, pare e veja o erro.
start "" explorer "%CD%\.blue-work"
pause
exit /b 0
