@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Laboratorio de Batalha
where python >nul 2>nul
if not errorlevel 1 (
  python scripts\battle_lab\launch.py
  if errorlevel 1 pause
  exit /b
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\battle_lab\launch.py
  if errorlevel 1 pause
  exit /b
)
echo [ERRO] Instale Python 3.10 ou superior para abrir o laboratorio.
pause
exit /b 1
