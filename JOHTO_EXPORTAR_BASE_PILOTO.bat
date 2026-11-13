@echo off
setlocal EnableExtensions
cd /d "%~dp0"

REM Exportacao PRIVADA de dados para continuar a Fase 04 de Johto.
REM O ZIP NAO pode ser enviado ao GitHub; nao inclui exe, scripts ou saves.
if not exist "game\Data\MapInfos.rxdata" (
  echo [JOHTO][BLOQUEADO] Instale primeiro a base Blue/Decades em game/.
  exit /b 2
)
if exist ".blue-work\johto-pilot-inputs.zip" (
  echo [JOHTO][BLOQUEADO] ZIP anterior preservado.
  echo Renomeie o ZIP antigo antes de repetir.
  exit /b 2
)
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
if /I "%~1"=="sprites" (
  %PY% scripts\regions\export_johto_pilot_inputs.py --sprites
) else if "%~1"=="" (
  %PY% scripts\regions\export_johto_pilot_inputs.py
) else (
  echo Uso: JOHTO_EXPORTAR_BASE_PILOTO.bat [sprites]
  exit /b 2
)
if errorlevel 1 exit /b 2

echo.
echo [JOHTO] ENVIE SOMENTE NO CHAT PRIVADO:
echo   .blue-work\johto-pilot-inputs.zip
echo [JOHTO] Nao comite no GitHub; pode conter dados de terceiros.
echo [JOHTO] Nenhum save nem Game.exe foi incluido; jogo original preservado.
exit /b 0
