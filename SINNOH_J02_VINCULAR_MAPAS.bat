@echo off
setlocal
set "REPO=%~dp0"
set "PY=python"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 set "PY=py -3"
set "GAME_DATA=%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game\Data"
if not exist "%GAME_DATA%\MapInfos.rxdata" (
  set "GAME_DATA=%REPO%game\Data"
)
echo =====================================================
echo SINNOH J02 - VINCULACAO DE MAPAS REAIS - SEM INSTALAR
echo =====================================================
echo Sem fonte e plano: imprime 4 referencias e 5 lacunas.
echo Para auditar 9 mapas no seu computador:
echo SINNOH_J02_VINCULAR_MAPAS.bat "FONTE.zip" ".blue-work\sinnoh-jogavel\bindings.json"
if "%~1"=="" (
  %PY% "%REPO%scripts\regions\bind_sinnoh_playable_j02.py" --project "%REPO%"
) else if "%~2"=="" (
  echo ERRO: fonte informada sem o arquivo local de bindings.
  exit /b 2
) else (
  %PY% "%REPO%scripts\regions\bind_sinnoh_playable_j02.py" --project "%REPO%" --source "%~1" --game-data "%GAME_DATA%" --bindings "%~2"
)
set "STATUS=%ERRORLEVEL%"
if not "%STATUS%"=="0" echo FALTAM MAPAS / RESERVAS OU EVIDENCIAS. NADA FOI INSTALADO.
echo Resultado J02: %STATUS%
pause
exit /b %STATUS%
