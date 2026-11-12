@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Instalar Kanto no jogo principal

echo.
echo ===== INTEGRACAO KANTO NO BLUE =====
echo [INFO] Preserve os saves e feche o jogo antes de continuar.
echo [INFO] Os mapas sao preparados numa copia antes da instalacao.
echo [INFO] Backup automatico em .blue-backups\kanto-...
echo.

if not exist "game\Game.exe" (
  echo [ERRO] Jogo principal nao encontrado. Execute INSTALAR_JOGO.bat.
  goto :error
)
if not exist ".blue-work\frlg-source\Essentials FRLG\Data\MapInfos.rxdata" (
  echo [ERRO] Fonte editavel FRLG ausente.
  echo [DICA] Consulte docs\CIRCUITO_REGIONAL.md e docs\KANTO_ESCOLHA_REGIAO.md.
  goto :error
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -X utf8 "scripts\regions\install_kanto.py"
  if errorlevel 1 goto :error
  choice /C SN /N /M "Aplicar os 13 mapas de Kanto no jogo principal? [S/N] "
  if errorlevel 2 goto :cancel
  py -3 -X utf8 "scripts\regions\install_kanto.py" --apply
  if errorlevel 1 goto :error
  goto :success
)
where python >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Python 3.10+ nao encontrado.
  goto :error
)
python -X utf8 "scripts\regions\install_kanto.py"
if errorlevel 1 goto :error
choice /C SN /N /M "Aplicar os 13 mapas de Kanto no jogo principal? [S/N] "
if errorlevel 2 goto :cancel
python -X utf8 "scripts\regions\install_kanto.py" --apply
if errorlevel 1 goto :error
:success
echo.
echo [OK] Conteudo de Kanto preparado para a campanha principal.
echo [INFO] Reinicie o jogo para compilar os mapas e exibir o seletor regional.
echo [INFO] Inicie com ABRIR_JOGO.bat.
pause
exit /b 0
:cancel
echo [INFO] Instalacao cancelada; nenhum arquivo do jogo foi alterado.
pause
exit /b 0
:error
echo [PENDENTE] Integracao nao confirmada. Consulte docs\KANTO_ESCOLHA_REGIAO.md.
pause
exit /b 1
