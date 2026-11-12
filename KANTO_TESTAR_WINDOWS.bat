@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Piloto de Kanto - Teste Windows
echo.
echo ==== KANTO - ABERTURA E TESTE MANUAL ====
echo [INFO] O teste usa uma copia em .blue-work e saves separados.
echo [INFO] Seus saves e sua instalacao principal nao serao substituidos.
echo.

where py >nul 2>&1
if not errorlevel 1 (
  py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    py -3 -X utf8 "scripts\regions\gui_diagnostics.py" %*
    goto :done
  )
)
where python >nul 2>&1
if not errorlevel 1 (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if not errorlevel 1 (
    python -X utf8 "scripts\regions\gui_diagnostics.py" %*
    goto :done
  )
)
echo [ERRO] Python 3.10+ nao encontrado.
echo [DICA] Consulte docs\KANTO_TESTE_WINDOWS.md
set "EXIT_CODE=2"
goto :finish

:done
set "EXIT_CODE=%errorlevel%"
:finish
echo.
if "%EXIT_CODE%"=="0" (
  echo [OK] Diagnostico de inicializacao executado.
  echo [IMPORTANTE] A etapa 02 so termina apos validar controles e batalhas manualmente.
) else (
  echo [PENDENTE] A janela nao foi confirmada. Consulte os logs em .blue-work\kanto-gui-reports.
)
echo [INFO] Instrucoes e checklist em docs\KANTO_TESTE_WINDOWS.md
pause
exit /b %EXIT_CODE%
