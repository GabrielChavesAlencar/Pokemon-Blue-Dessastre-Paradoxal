@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Sinnoh B10 - Isolar saves na Windows Sandbox
set "PY=py -3"
where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [B10 BLOQUEADA] Python 3 nao encontrado.
    pause
    exit /b 2
  )
  set "PY=python"
)
if not exist "%~dp0.blue-work\sinnoh-b09-native-qa\" (
  echo [B10 BLOQUEADA] Nao existe clone B09 nesta pasta.
  echo Antes, execute B07, B08 e SINNOH_B09_COPIA_NATIVA_QA_PRIVADA.bat.
  pause
  exit /b 2
)
set "B01=%USERPROFILE%\Downloads\SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" set "B01=%~dp0SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" (
  echo Informe a localizacao do inventario B01 que voce ja gerou:
  set /p "B01=ZIP B01: "
)
if not exist "%B01%" goto :missing
set "REPORT=%~dp0SINNOH_B10_RELATORIO_%RANDOM%_%RANDOM%.json"
echo [B10] Conferindo B09/B08/B07, 702 mapas, saves e integridade SHA...
echo [B10] Windows Sandbox exige Windows Pro, Enterprise ou Education.
echo [B10] O Windows Home nao e suportado. A ferramenta NAO instala recursos.
%PY% scripts\regions\prepare_sinnoh_b10_save_isolation.py --latest --native-inventory "%B01%" --prepare > "%REPORT%"
if errorlevel 1 goto :failed
for /f "delims=" %%C in ('%PY% -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8'))['config_relative_path'])" "%REPORT%"') do set "WSB_REL=%%C"
if not defined WSB_REL goto :failed
if not exist "%~dp0%WSB_REL%" goto :failed
echo.
echo [B10 OK] Configuracao .wsb preparada, sem executar o Game.exe.
echo [B10] Configuracao: "%~dp0%WSB_REL%"
echo [B10] Envie SOMENTE o relatorio ao chat: "%REPORT%"
echo.
echo A sandbox abrira SEM iniciar o jogo, sem rede e sem clipboard.
echo Dentro dela, voce podera copiar o clone para C:\SinnohB10Game.
choice /C SN /N /M "Abrir agora a WINDOWS SANDBOX (NAO o jogo)? [S/N]: "
if errorlevel 2 goto :cancel
start "" "%~dp0%WSB_REL%"
if errorlevel 1 goto :failed
echo A Windows Sandbox foi solicitada. Nao execute Game.exe no Windows principal.
echo Dentro da Sandbox execute C:\SinnohB10Tools\B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd
echo SOMENTE dentro da VM, abra C:\SinnohB10Game\Game.exe quando decidir testar.
pause
exit /b 0
:cancel
echo Sandbox nao aberta. Arquivo WSB pronto para uso manual posterior.
pause
exit /b 0
:missing
echo [B10 BLOQUEADA] ZIP B01 nao encontrado. Nenhum arquivo do jogo alterado.
pause
exit /b 2
:failed
echo.
echo [B10 BLOQUEADA] Verificacao falhou ou Windows Sandbox indisponivel.
echo O Game.exe nao foi iniciado. Nao use a copia B09 fora da VM.
if exist "%REPORT%" del /q "%REPORT%" >nul 2>nul
pause
exit /b 2
