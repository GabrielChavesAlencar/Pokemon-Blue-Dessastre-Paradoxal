@echo off
setlocal EnableExtensions
cd /d "%~dp0"

REM Inspeciona o Map079 real do ZIP v1, SEM precisar game/ instalado.
REM Gera apenas um relatorio JSON de 4 entradas candidatas, nada jogavel.

if not exist ".blue-work\johto-source\original.zip" (
  echo [JOHTO][BLOQUEADO] Falta .blue-work\johto-source\original.zip
  echo Use o ZIP v1 original enviado ao chat; nao coloque seus assets no GitHub.
  exit /b 2
)
if exist ".blue-work\johto-new-bark-exterior-audit.json" (
  echo [JOHTO][BLOQUEADO] Relatorio anterior preservado.
  echo Renomeie-o manualmente antes de uma nova auditoria.
  exit /b 2
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\regions\audit_johto_new_bark_exterior.py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [JOHTO][BLOQUEADO] Python 3 indisponivel.
    exit /b 2
  )
  python scripts\regions\audit_johto_new_bark_exterior.py
)
if errorlevel 1 exit /b 2
echo [JOHTO] Verificacao real de tiles concluida. Nenhuma porta foi aprovada.
echo [JOHTO] Analise: .blue-work\johto-new-bark-exterior-audit.json
echo [JOHTO] Confirme casa/lab e sprites no piloto antes de montar eventos.
exit /b 0
