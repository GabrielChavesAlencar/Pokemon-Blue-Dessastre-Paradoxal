@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Importar Dessastre Paradoxal
where python >nul 2>nul
if not errorlevel 1 (
  python scripts\dessastre_paradoxal\install.py --apply
  goto :done
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\dessastre_paradoxal\install.py --apply
  goto :done
)
echo [ERRO] Instale Python 3.10 ou superior.
:done
pause
