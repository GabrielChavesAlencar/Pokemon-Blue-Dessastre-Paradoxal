@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Sinnoh B09 - Copia nativa PRIVADA (sem executar)
set "PY=py -3"
where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [B09 BLOQUEADA] Python 3 nao encontrado.
    echo Nenhum arquivo do jogo foi modificado.
    pause
    exit /b 2
  )
  set "PY=python"
)
if not exist "%~dp0.blue-work\sinnoh-b08-qa\" (
  echo [B09 BLOQUEADA] Falta o QA overlay B08.
  echo Rode primeiro a B07 e depois SINNOH_B08_VERIFICAR_QA_PRIVADO.bat.
  pause
  exit /b 2
)
set "B01=%USERPROFILE%\Downloads\SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" set "B01=%~dp0SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" (
  echo Informe o caminho completo do inventario B01:
  set /p "B01=ZIP B01: "
)
if not exist "%B01%" goto :missing
set "GAMEDIR=%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game"
if not exist "%GAMEDIR%\Data\MapInfos.rxdata" (
  echo Informe a pasta da instalacao que contem Game.exe e Data:
  set /p "GAMEDIR=Pasta game: "
)
if not exist "%GAMEDIR%\Data\MapInfos.rxdata" goto :missing
if not exist "%GAMEDIR%\Game.exe" goto :missing
set "PREVIEW=%~dp0SINNOH_B09_DRYRUN_%RANDOM%_%RANDOM%.json"
echo [B09] Validando B07+B08 e comparando a instalacao de 648 mapas...
%PY% scripts\regions\build_sinnoh_b09_native_qa.py --latest --native-inventory "%B01%" --game-dir "%GAMEDIR%" > "%PREVIEW%"
if errorlevel 1 goto :failed
for /f "delims=" %%H in ('%PY% -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8'))['plan_sha256'])" "%PREVIEW%"') do set "PLAN_SHA=%%H"
if not defined PLAN_SHA goto :failed
echo.
echo [B09] Plano SHA-256: %PLAN_SHA%
echo [B09] O clone sera criado somente em .blue-work\sinnoh-b09-native-qa
echo [AVISO] Copia o Game.exe do SEU computador mas NAO executa.
echo [AVISO] NAO INICIE O CLONE: ainda falta isolar a pasta de saves.
choice /C SN /N /M "Criar agora a copia privada? [S/N]: "
if errorlevel 2 goto :cancel
set "REPORT=%~dp0SINNOH_B09_RELATORIO_%RANDOM%_%RANDOM%.json"
echo [B09] Criando apenas a copia privada, com hashes verificados...
%PY% scripts\regions\build_sinnoh_b09_native_qa.py --latest --native-inventory "%B01%" --game-dir "%GAMEDIR%" --clone --expected-plan-sha "%PLAN_SHA%" > "%REPORT%"
if errorlevel 1 goto :failed
echo.
echo [B09 OK] Copia nativa de QA privada criada.
echo [IMPORTANTE] NAO execute o Game.exe da copia ate isolar os saves.
echo Envie SOMENTE o relatorio JSON ao chat: "%REPORT%"
pause
exit /b 0
:cancel
echo Clonagem cancelada. O dry-run foi salvo em "%PREVIEW%".
pause
exit /b 0
:missing
echo [B09 BLOQUEADA] Pasta game, Game.exe ou ZIP B01 ausente.
echo Nenhum save ou mapa foi modificado.
pause
exit /b 2
:failed
echo.
echo [B09 BLOQUEADA] Stage/overlay ausente, fonte alterada ou colisoes.
echo A instalacao principal nao foi alterada.
pause
exit /b 2
