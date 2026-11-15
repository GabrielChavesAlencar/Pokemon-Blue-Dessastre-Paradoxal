@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Integrar Hoenn na campanha Decades
echo.
echo === HOENN NA BUILD PRINCIPAL (Decades + Kanto) ===
echo [INFO] Feche o Game.exe antes de instalar.
echo [INFO] O instalador nao mexe nos saves e faz backup dos arquivos alterados.
echo.
if not exist "game\Game.exe" (
  echo [ERRO] A pasta game com Decades nao foi encontrada aqui.
  echo Abra este BAT na raiz do repositorio que contem game\Game.exe.
  pause
  exit /b 2
)
where py >nul 2>nul
if not errorlevel 1 (
  set "PYTHON=py -3"
  goto :run
)
where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python 3.11+ necessario para integrar os mapas.
  pause
  exit /b 2
)
set "PYTHON=python"
:run
echo [1/3] Auditar e integrar os 199 mapas Hoenn na instalacao principal...
if "%~1"=="" (
  %PYTHON% -X utf8 scripts\regions\install_hoenn.py --apply
) else (
  echo [INFO] Usando o ZIP fornecido arrastado para este BAT.
  %PYTHON% -X utf8 scripts\regions\install_hoenn.py --archive "%~1" --apply
)
if errorlevel 1 goto :failed
echo.
echo [2/3] Conferir todos os marcadores, mapas e hashes...
%PYTHON% -X utf8 scripts\regions\install_hoenn.py --verify-installed
if errorlevel 1 goto :failed
echo.
echo [3/3] Preparar recompilacao dos PBS e plugins na campanha principal...
%PYTHON% -X utf8 scripts\launch_game.py --game-dir game --prepare-only
if errorlevel 1 goto :failed
echo.
echo [OK] Arquivos de Hoenn integrados e recompilacao solicitada.
echo Abra o jogo principal novamente. Se compilar e fechar, reabra.
echo Hoenn devera aparecer como VIAJAR no Agente Regional.
echo Ainda e necessario testar no Game.exe real (Windows/Android).
pause
exit /b 0
:failed
echo.
echo [BLOQUEADO] Hoenn nao foi validada; nao force os mapas ou o menu.
echo Veja a mensagem de erro acima e os backups em .blue-backups.
echo DICA: coloque o ZIP original na raiz do projeto, ou arraste-o
echo para este BAT. O cache auditado de TESTAR_HOENN.bat tambem pode servir.
pause
exit /b 2
