@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
echo ===============================================================
echo   POKEMON BLUE - VERIFICAR / CORRIGIR QUARTO DE JOHTO
echo ===============================================================
echo.
echo Pasta real do Game.exe: "%CD%\game\Game.exe"
echo Esta ferramenta NAO baixa imagens de terceiros, NAO apaga saves.
echo Feche o jogo ANTES de prosseguir.
echo.
set "PYTHON="
for /d %%P in ("%CD%\tools\python-*") do (
  if exist "%%~fP\python.exe" set "PYTHON=%%~fP\python.exe"
)
if not defined PYTHON (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON=py -3"
)
if not defined PYTHON (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
  echo [ERRO] Runtime Python nao encontrado. Execute Blue-Story.exe atualizado.
  pause
  exit /b 1
)
if not exist "scripts\regions\diagnose_johto_bedroom.py" (
  echo [ERRO] Script do diagnostico ausente. Atualize pelo Blue-Story.exe.
  pause
  exit /b 1
)
if not exist "game\Game.exe" (
  echo [ERRO] Game.exe nao encontrado nesta pasta.
  echo Voce pode ter aberto outra copia do jogo.
  pause
  exit /b 1
)
echo.
echo Verificando hash, mapas e posicao da escada...
%PYTHON% scripts\regions\diagnose_johto_bedroom.py --apply
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo [JOHTO] A correcao foi recusada: mapas alterados ou eventos incompatíveis.
  echo [JOHTO] Coletando os tres mapas reais SEM incluir saves.
  %PYTHON% scripts\regions\export_johto_map_diagnostics.py
  if errorlevel 1 echo [JOHTO] Nao foi possivel gerar o ZIP privado.
  echo.
  echo Envie no ChatGPT o ZIP:
  echo "%CD%\.blue-work\JOHTO_DIAGNOSTICO_MAPAS.zip"
  echo Nao copie os mapas sobre a instalacao e NAO apague saves.
)
echo.
echo Diagnostico salvo em: "%CD%\.blue-work\johto-bedroom-diagnostic.json"
echo Se aparecer OLD_OR_DIFFERENT_BEDROOM ou FAILED, compartilhe esse JSON.
echo Se aparecer LAYOUT_HGSS_APPLIED, abra o GAME.EXE DESTA PASTA.
echo OBS: Os moveis HGSS originais exigem os PNGs externos dos autores.
echo.
pause
exit /b %RESULT%
