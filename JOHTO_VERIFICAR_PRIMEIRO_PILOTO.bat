@echo off
setlocal EnableExtensions
cd /d "%~dp0"
REM Diagnostico de 12 eventos + spawn e conexao da Rota 29.
REM NAO altera game/, NAO aprova 1/13 e NAO executa Game.exe.
set "STAGE=.blue-work\johto-staging-interiors"
set "EVENTS=.blue-work\johto-new-bark-bound.json"
set "PBS=.blue-work\johto-connections-preview.txt"
set "OUT=.blue-work\johto-phase04-acceptance.json"

if not exist "%STAGE%\johto-stage.json" (
  echo [JOHTO][BLOQUEADO] Faltam os tres interiores no stage.
  echo Primeiro execute JOHTO_PREPARAR_NEW_BARK.bat auditar e depois montar,
  echo apos revisar templates e hashes de suas salas nativas.
  exit /b 2
)
if not exist "%EVENTS%" (
  echo [JOHTO][BLOQUEADO] Faltam IDs e hashes vinculados: %EVENTS%.
  exit /b 2
)
if not exist "%PBS%" (
  echo [JOHTO][BLOQUEADO] Faltam conexoes compiladas da fonte ZIP original.
  echo Execute JOHTO_PREPARAR_PRIMEIRA_FASE.bat.
  exit /b 2
)
if exist "%OUT%" (
  echo [JOHTO][BLOQUEADO] Relatorio anterior preservado: %OUT%
  echo Renomeie o anterior para executar outra auditoria.
  exit /b 2
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\regions\inspect_johto_pilot_readiness.py --preview "%STAGE%" --spec "%EVENTS%" --connections "%PBS%" --with-connections --output "%OUT%"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [JOHTO][BLOQUEADO] Python 3 nao encontrado.
    exit /b 2
  )
  python scripts\regions\inspect_johto_pilot_readiness.py --preview "%STAGE%" --spec "%EVENTS%" --connections "%PBS%" --with-connections --output "%OUT%"
)
if errorlevel 1 exit /b 2
echo.
echo [JOHTO] Revise o checklist de pendencias em %OUT%.
echo [JOHTO] Ainda e necessario QA em Game.exe isolado para 1/13.
exit /b 0
