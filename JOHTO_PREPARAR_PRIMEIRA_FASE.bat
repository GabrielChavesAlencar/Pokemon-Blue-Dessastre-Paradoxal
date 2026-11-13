@echo off
setlocal EnableExtensions
cd /d "%~dp0"

REM Primeira fase jogavel de Johto: PREPARA terreno e conexoes com seguranca.
REM Nao altera game/ e NAO abre Game.exe com posicoes desconhecidas.

if not exist ".blue-work\johto-source\original.zip" (
  echo [JOHTO][BLOQUEADO] Falta o Map Pack v1 original:
  echo .blue-work\johto-source\original.zip
  echo Coloque nele o ZIP exato enviado ao chat. NAO o publique no GitHub.
  exit /b 2
)
if not exist "game\Data\MapInfos.rxdata" (
  echo [JOHTO][BLOQUEADO] Falta game\Data\MapInfos.rxdata nativo.
  echo Instale o jogo Blue/Decades pela rotina normal, sem mudar os saves.
  exit /b 2
)
if not exist "game\Data\Tilesets.rxdata" (
  echo [JOHTO][BLOQUEADO] Falta game\Data\Tilesets.rxdata nativo.
  exit /b 2
)

where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\regions\prepare_johto_first_playable.py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [JOHTO][BLOQUEADO] Python 3 indisponivel.
    exit /b 2
  )
  python scripts\regions\prepare_johto_first_playable.py
)
if errorlevel 1 (
  echo [JOHTO] Preflight bloqueado: leia a mensagem acima.
  echo [JOHTO] game/ e saves nao foram modificados.
  exit /b 2
)
echo.
echo [JOHTO] Terreno auditado e conexoes reais em .blue-work/.
echo [JOHTO] RELATORIO: .blue-work\johto-first-playable-readiness.json
echo [JOHTO] New Bark e Route 29 ainda exigem interiores e coordenadas.
echo [JOHTO] Barra JOGAVEL continua 0/13 ate prova real no Game.exe.
echo [JOHTO] Barra TESTADA continua 0/13 ate QA de gameplay aprovado.
exit /b 0
