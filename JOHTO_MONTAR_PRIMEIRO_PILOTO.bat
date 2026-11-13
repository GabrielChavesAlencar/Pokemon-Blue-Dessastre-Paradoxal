@echo off
setlocal EnableExtensions
cd /d "%~dp0"
REM Montagem experimental independente, apenas apos comprovacao de 12 eventos.
REM NUNCA instala ou sobrescreve game/, Kanto, Decades ou saves.
if not exist ".blue-work\johto-staging-interiors\johto-stage.json" (
  echo [JOHTO][BLOQUEADO] Tres interiores ainda ausentes.
  echo Execute JOHTO_PREPARAR_NEW_BARK.bat auditar e depois montar.
  exit /b 2
)
if not exist ".blue-work\johto-new-bark-bound.json" (
  echo [JOHTO][BLOQUEADO] Falta especificacao de eventos auditados.
  exit /b 2
)
if exist ".blue-work\johto-pilot" (
  echo [JOHTO][BLOQUEADO] Copia experimental anterior preservada.
  exit /b 2
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\regions\assemble_johto_first_playable.py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [JOHTO][BLOQUEADO] Python 3 nao instalado.
    exit /b 2
  )
  python scripts\regions\assemble_johto_first_playable.py
)
if errorlevel 1 exit /b 2
echo.
echo [JOHTO] Copia experimental pronta em .blue-work\johto-pilot\
echo [JOHTO] Proximo: testar a campanha no Game.exe DA COPIA e verificar save/reload.
echo [JOHTO] Sem prova do jogo em funcionamento: JOGAVEIS 0/13, TESTADAS 0/13.
exit /b 0
