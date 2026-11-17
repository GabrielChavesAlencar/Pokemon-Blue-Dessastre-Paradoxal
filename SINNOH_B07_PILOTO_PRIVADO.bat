@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Sinnoh B07 - Piloto privado de geometria
where py >nul 2>nul
if errorlevel 1 (
  echo [BLOQUEADO] Python 3 nao encontrado. Nenhum arquivo do jogo foi alterado.
  pause
  exit /b 2
)
set "SOURCE=%USERPROFILE%\Downloads\Pokemon World V18.zip"
if not exist "%SOURCE%" set "SOURCE=%~dp0Pokemon World V18.zip"
if not exist "%SOURCE%" (
  echo Digite o caminho completo do arquivo Pokemon World V18.zip:
  set /p "SOURCE=ZIP doador: "
)
if not exist "%SOURCE%" goto :missing
set "B01=%USERPROFILE%\Downloads\SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" set "B01=%~dp0SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" (
  echo Digite o caminho completo do inventario B01:
  set /p "B01=ZIP B01: "
)
if not exist "%B01%" goto :missing
set "GAMEDATA=%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game\Data"
if not exist "%GAMEDATA%\MapInfos.rxdata" (
  echo Digite o caminho completo da pasta game\Data da instalacao:
  set /p "GAMEDATA=Pasta game\Data: "
)
if not exist "%GAMEDATA%\MapInfos.rxdata" goto :missing
set "RPT=%TEMP%\sinnoh-b07-dryrun-%RANDOM%-%RANDOM%.json"
echo [B07] Calculando a previa sem gravar no jogo...
py -3 scripts\regions\build_sinnoh_b07_private_stage.py --source-zip "%SOURCE%" --native-inventory "%B01%" > "%RPT%"
if errorlevel 1 goto :failed
for /f "delims=" %%H in ('py -3 -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8'))['transaction']['plan_sha256'])" "%RPT%"') do set "PLAN_SHA=%%H"
if not defined PLAN_SHA goto :failed
echo.
echo [B07] SHA do dry-run: %PLAN_SHA%
echo [B07] Criando apenas o stage privado em .blue-work...
py -3 scripts\regions\build_sinnoh_b07_private_stage.py --source-zip "%SOURCE%" --native-inventory "%B01%" --game-data "%GAMEDATA%" --stage --expected-sha "%PLAN_SHA%"
if errorlevel 1 goto :failed
del /q "%RPT%" >nul 2>nul
echo.
echo [OK] Piloto privado criado. Anote o SHA para rollback. O jogo original nao foi alterado.
pause
exit /b 0
:missing
echo [BLOQUEADO] Arquivo/pasta nao encontrado. Nada foi instalado.
pause
exit /b 2
:failed
echo [BLOQUEADO] Falha de auditoria, baseline ou stage. O jogo original permanece intacto.
del /q "%RPT%" >nul 2>nul
pause
exit /b 2
