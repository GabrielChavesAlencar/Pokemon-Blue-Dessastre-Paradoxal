@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Sinnoh B08 - Verificar Stage e QA Privado
set "PY=py -3"
where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [B08 BLOQUEADA] Python 3 nao encontrado.
    pause
    exit /b 2
  )
  set "PY=python"
)
if not exist "%~dp0.blue-work\sinnoh-stage\" (
  echo [B08 BLOQUEADA] Nenhum stage B07 encontrado.
  echo Execute SINNOH_B07_PILOTO_PRIVADO.bat antes da B08.
  pause
  exit /b 2
)
set "B01=%USERPROFILE%\Downloads\SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" set "B01=%~dp0SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" (
  echo Informe a localizacao do inventario B01:
  set /p "B01=Caminho do ZIP B01: "
)
if not exist "%B01%" goto :missing
set "GAMEDATA=%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game\Data"
if not exist "%GAMEDATA%\MapInfos.rxdata" (
  echo Informe o caminho da pasta game\Data atual:
  set /p "GAMEDATA=Pasta game\Data: "
)
if not exist "%GAMEDATA%\MapInfos.rxdata" goto :missing
set "REPORT=%~dp0SINNOH_B08_RELATORIO_QA_%RANDOM%_%RANDOM%.json"
echo [B08] Verificando stage B07 e preparando QA isolado...
%PY% scripts\regions\audit_sinnoh_b08_private_qa.py --latest --native-inventory "%B01%" --game-data "%GAMEDATA%" --prepare-qa > "%REPORT%"
if errorlevel 1 goto :failed
echo.
echo [OK] Copia privada em .blue-work\sinnoh-b08-qa
echo Nenhum mapa instalado em game\Data. Overlay NAO e jogo executavel.
echo Envie ao ChatGPT o relatorio: "%REPORT%"
pause
exit /b 0
:missing
echo [B08 BLOQUEADA] Inventario ou pasta do jogo nao encontrados. Nada foi instalado.
pause
exit /b 2
:failed
echo [B08 BLOQUEADA] Stage nao encontrado, modificado ou base atualizada.
if exist "%REPORT%" del /q "%REPORT%" >nul 2>nul
pause
exit /b 2
