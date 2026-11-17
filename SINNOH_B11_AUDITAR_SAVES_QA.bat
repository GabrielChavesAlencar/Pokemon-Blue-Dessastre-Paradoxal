@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Sinnoh B11 - Auditoria de saves com Windows Sandbox
set "PY=py -3"
where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [B11 BLOQUEADA] Python 3 nao encontrado.
    pause
    exit /b 2
  )
  set "PY=python"
)
if not exist "%~dp0.blue-work\sinnoh-b10-sandbox\" (
  echo [B11 BLOQUEADA] Sessao B10 ausente nesta pasta do projeto.
  echo Rode B07, B08, B09 e B10 primeiro.
  pause
  exit /b 2
)
set "B01=%USERPROFILE%\Downloads\SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" set "B01=%~dp0SINNOH_B01_INVENTARIO_DECADES.zip"
if not exist "%B01%" (
  echo Caminho para o inventario B01 previamente gerado:
  set /p "B01=ZIP B01: "
)
if not exist "%B01%" goto :missing
echo [B11] Registrando hashes das pastas do projeto monitoradas ANTES da sessao.
echo Este snapshot NAO copia nem publica saves, mas monitora apenas locais conhecidos.
set "BEFORE=%~dp0SINNOH_B11_ANTES_%RANDOM%_%RANDOM%.json"
%PY% scripts\regions\audit_sinnoh_b11_host_saves.py --before --latest --native-inventory "%B01%" > "%BEFORE%"
if errorlevel 1 goto :failed
for /f "delims=" %%I in ('%PY% -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))['watch_id'])" "%BEFORE%"') do set "WATCH_ID=%%I"
for /f "delims=" %%C in ('%PY% -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))['config_relative_path'])" "%BEFORE%"') do set "WSB_REL=%%C"
if not defined WATCH_ID goto :failed
if not defined WSB_REL goto :failed
if not exist "%~dp0%WSB_REL%" goto :failed
echo.
echo Snapshot B11: %WATCH_ID%
echo NAO inicie Game.exe no Windows principal.
choice /C SN /N /M "Abrir a WINDOWS SANDBOX isolada agora? [S/N]: "
if errorlevel 2 goto :no_vm
start "" "%~dp0%WSB_REL%"
if errorlevel 1 goto :failed
echo Dentro da VM execute C:\SinnohB10Tools\B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd
echo Depois, SOMENTE na VM, se desejar, abra C:\SinnohB10Game\Game.exe
echo Para verificar os caminhos de save na VM, execute:
echo C:\SinnohB10Tools\B11_DIAGNOSTICAR_DENTRO_DA_SANDBOX.cmd
echo Feche a Sandbox antes de continuar a auditoria de saves do host.
pause
goto :check
:no_vm
echo VM nao iniciada. Ainda sera feita comparacao de hashes do host.
:check
echo.
echo O que voce observou DENTRO DA VM?
echo N=nao executou; F=falhou ao iniciar; R=renderizou mapa; S=criou save na VM
choice /C NFRS /N /M "Escolha N, F, R ou S: "
set "OBS=not_run"
if errorlevel 4 set "OBS=save_inside_vm"
if errorlevel 3 if not errorlevel 4 set "OBS=rendered_map"
if errorlevel 2 if not errorlevel 3 set "OBS=launch_failed"
set "REPORT=%~dp0SINNOH_B11_RELATORIO_%RANDOM%_%RANDOM%.json"
%PY% scripts\regions\audit_sinnoh_b11_host_saves.py --after "%WATCH_ID%" --observation "%OBS%" > "%REPORT%"
if errorlevel 1 goto :failed
echo.
echo [B11] Comparacao de hashes concluida. Isso NAO comprova todos os caminhos de save.
echo Envie SOMENTE este relatorio JSON para o ChatGPT:
echo "%REPORT%"
echo NAO envie private-baseline.json nem seus saves.
pause
exit /b 0
:missing
echo [B11 BLOQUEADA] ZIP B01 ausente. Nada foi instalado.
pause
exit /b 2
:failed
echo [B11 BLOQUEADA] Nao foi possivel concluir a auditoria segura.
echo Nenhum arquivo da instalacao principal foi alterado pelo auditor.
pause
exit /b 2
