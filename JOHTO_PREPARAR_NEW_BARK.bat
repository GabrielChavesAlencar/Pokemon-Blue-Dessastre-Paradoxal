@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PREVIEW=.blue-work\johto-staging"
set "REPORT=.blue-work\johto-native-room-candidates.json"
set "LAYOUTS=.blue-work\johto-interior-templates-review.json"
set "ROOMS=.blue-work\johto-staging-interiors"
set "EVENTS=.blue-work\johto-new-bark-bound.json"

where py >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [JOHTO][BLOQUEADO] Python 3 nao instalado.
    exit /b 2
  )
  set "PY=python"
)

if not exist "game\Data\MapInfos.rxdata" (
  echo [JOHTO][BLOQUEADO] Falta game/Data real.
  echo Instale a base Blue pelos passos oficiais, sem alterar saves.
  exit /b 2
)
if not exist "%PREVIEW%\johto-stage.json" (
  echo [JOHTO][BLOQUEADO] Falta staging de geometria auditada.
  echo Etapa anterior: stage_johto.py com ZIP/MapIDs/SHA conferidos.
  exit /b 2
)

if /I "%~1"=="montar" goto MONTAR
if not "%~1"=="" if /I not "%~1"=="auditar" (
  echo Uso: JOHTO_PREPARAR_NEW_BARK.bat [auditar^|montar]
  exit /b 2
)

:AUDITAR
if exist "%REPORT%" (
  echo [JOHTO][BLOQUEADO] Relatorio anterior preservado: %REPORT%
  echo Renomeie-o manualmente caso queira auditar uma nova fonte.
  exit /b 2
)
%PY% scripts\regions\audit_johto_native_rooms.py --game "game" --preview "%PREVIEW%" --output "%REPORT%"
if errorlevel 1 exit /b 2
if not exist "%LAYOUTS%" (
  copy /Y "data\regions\johto-interior-templates.json" "%LAYOUTS%" >nul
  if errorlevel 1 exit /b 2
)
echo.
echo [JOHTO] Relatorio para inspecao visual: %REPORT%
echo [JOHTO] Copia editavel de IDs e hashes: %LAYOUTS%
echo [JOHTO] Revise 3 interiores nativos DIFERENTES e mapas de destino livres.
echo [JOHTO] Depois rode: JOHTO_PREPARAR_NEW_BARK.bat montar
echo [JOHTO] Nada foi instalado ou testado no Game.exe.
exit /b 0

:MONTAR
if not exist "%LAYOUTS%" (
  echo [JOHTO][BLOQUEADO] Execute auditar e revise os templates primeiro.
  exit /b 2
)
if exist "%ROOMS%" (
  echo [JOHTO][BLOQUEADO] Preview de interiores existente. Nada sobrescrito.
  exit /b 2
)
if exist "%EVENTS%" (
  echo [JOHTO][BLOQUEADO] Vinculo de eventos existente. Nada sobrescrito.
  exit /b 2
)
%PY% scripts\regions\build_johto_interiors.py --game "game" --preview "%PREVIEW%" --layouts "%LAYOUTS%" --output "%ROOMS%"
if errorlevel 1 exit /b 2
%PY% scripts\regions\bind_johto_new_bark.py --game "game" --preview "%ROOMS%" --template "data\regions\johto-new-bark-events.json" --output "%EVENTS%"
if errorlevel 1 exit /b 2
echo.
echo [JOHTO] 3 interiores em preview e MapIDs de New Bark vinculados.
echo [JOHTO] Proximo: conferir TODAS as coordenadas e sprites em %EVENTS%.
echo [JOHTO] Game.exe / Kanto / Decades NAO foram modificados.
exit /b 0
