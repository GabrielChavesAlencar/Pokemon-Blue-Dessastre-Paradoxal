@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ARCHIVE=.blue-work\johto-source\original.zip"
set "SOURCE=.blue-work\johto-source"
set "PROJECT=.blue-work\johto-source\project"
set "AUDIT=.blue-work\johto-audit.json"
set "INVENTORY=.blue-work\johto-content-inventory.json"

where py >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [JOHTO][BLOQUEADO] Python 3 nao foi encontrado.
    exit /b 2
  )
  set "PY=python"
)
if not exist "%ARCHIVE%" (
  echo [JOHTO][BLOQUEADO] Arquivo original nao encontrado: %ARCHIVE%
  echo Obtenha legitimamente o Map Pack e guarde-o nesse caminho.
  echo Nao sera feito download automatico nem modificacao do jogo.
  exit /b 2
)
if not exist "game\Data\MapInfos.rxdata" (
  echo [JOHTO][BLOQUEADO] Instalacao game/Data local nao encontrada.
  echo Instale/prepara a base original por seus scripts oficiais e tente novamente.
  exit /b 2
)
if not exist "%PROJECT%\Data\MapInfos.rxdata" (
  %PY% scripts\regions\prepare_johto_source.py --archive "%ARCHIVE%" --output "%PROJECT%"
  if errorlevel 1 exit /b 2
)
%PY% scripts\regions\audit_johto.py --source "%SOURCE%" --archive "%ARCHIVE%" --game "game" --output "%AUDIT%"
if errorlevel 1 exit /b 2
%PY% scripts\regions\inventory_johto.py --source "%SOURCE%" --audit "%AUDIT%" --output "%INVENTORY%"
if errorlevel 1 exit /b 2
echo.
echo [JOHTO] Inventario de mapas e eventos de origem gerado:
echo   %AUDIT%
echo   %INVENTORY%
echo [JOHTO] Apenas analise: mapas, NPCs e musica NAO foram instalados.
echo [JOHTO] PROXIMO: revisar direitos, identificar IDs reais e criar piloto em copia.
exit /b 0
