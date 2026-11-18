@echo off
setlocal
set "REPO=%~dp0"
set "PYTHON=python"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 set "PYTHON=py -3"
set "GAME_DATA="
if exist "%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game\Data\MapInfos.rxdata" set "GAME_DATA=%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game\Data"
if not defined GAME_DATA if exist "%REPO%game\Data\MapInfos.rxdata" set "GAME_DATA=%REPO%game\Data"
echo ====================================================
echo SINNOH J01 - DIAGNOSTICO DO PILOTO JOGAVEL
echo Apenas leitura. Nenhum arquivo do jogo ou save e alterado.
echo ====================================================
if not defined GAME_DATA (
  echo Instalacao game/Data nao localizada no caminho padrao.
  echo O diagnostico indicara quais entradas estao faltando.
  if "%~1"=="" (
    %PYTHON% "%REPO%scripts\regions\preflight_sinnoh_playable_j01.py" --project "%REPO%"
  ) else (
    %PYTHON% "%REPO%scripts\regions\preflight_sinnoh_playable_j01.py" --project "%REPO%" --source "%~1"
  )
) else (
  echo Inventario do jogo instalado sera verificado em modo read-only.
  if "%~1"=="" (
    %PYTHON% "%REPO%scripts\regions\preflight_sinnoh_playable_j01.py" --project "%REPO%" --game-data "%GAME_DATA%"
  ) else (
    %PYTHON% "%REPO%scripts\regions\preflight_sinnoh_playable_j01.py" --project "%REPO%" --game-data "%GAME_DATA%" --source "%~1"
  )
)
set "STATUS=%ERRORLEVEL%"
if not "%STATUS%"=="0" echo J01: falta fonte, baseline ou integridade. Nenhuma instalacao foi realizada.
echo Status do diagnostico: %STATUS%
pause
exit /b %STATUS%
