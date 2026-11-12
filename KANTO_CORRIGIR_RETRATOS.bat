@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Kanto - corrigir retratos dos treinadores
echo.
echo === REPARAR RETRATOS DE KANTO ===
echo [INFO] Corrige somente retratos Kanto ausentes em Graphics\Trainers.
echo [INFO] Nao modifica saves, mapas, PBS, equipes, itens nem o PC.
echo.
if not exist "game\Data\blue-kanto-start.txt" (
  echo [ERRO] Kanto ainda nao esta instalado no jogo principal.
  goto :error
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -X utf8 "scripts\regions\install_kanto.py" --repair-portraits
  if errorlevel 1 goto :error
  choice /C SN /N /M "Aplicar reparo de retratos ausentes? [S/N] "
  if errorlevel 2 goto :cancel
  py -3 -X utf8 "scripts\regions\install_kanto.py" --repair-portraits --apply
  if errorlevel 1 goto :error
  goto :success
)
where python >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python nao encontrado.
  goto :error
)
python -X utf8 "scripts\regions\install_kanto.py" --repair-portraits
if errorlevel 1 goto :error
choice /C SN /N /M "Aplicar reparo de retratos ausentes? [S/N] "
if errorlevel 2 goto :cancel
python -X utf8 "scripts\regions\install_kanto.py" --repair-portraits --apply
if errorlevel 1 goto :error
:success
echo.
echo [OK] Reparo concluido. Abra ABRIR_JOGO.bat e confira os retratos.
pause
exit /b 0
:cancel
echo [INFO] Cancelado sem modificar arquivos.
pause
exit /b 0
:error
echo [ERRO] Reparo nao aplicado. Confira docs\KANTO_ETAPAS.md.
pause
exit /b 1
