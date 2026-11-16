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
if "%RESULT%"=="3" (
  echo.
  echo [JOHTO] A regiao nao foi instalada nesta copia do Game.exe,
  echo ou faltam os mapas de New Bark. Isto nao e um erro do quarto.
  echo.
  echo Necessario: Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip
  echo Esse ZIP tem os mapas 600-681. O ZIP johto-pilot-inputs NAO tem mapas Johto.
  echo Coloque o ZIP ORIGINAL na pasta Downloads deste usuario Windows,
  echo feche o Game.exe e execute Blue-Story.exe para instalar Johto.
  echo NAO apague saves, NAO extraia mapas manualmente na pasta game.
)
if "%RESULT%"=="2" (
  echo.
  echo [JOHTO] Os mapas existem, mas a correcao nao e segura.
  echo [JOHTO] Preparando diagnostico sem saves.
  %PYTHON% scripts\regions\export_johto_map_diagnostics.py
  if errorlevel 1 (
    echo [JOHTO] Falha ao criar ZIP de diagnostico.
  ) else (
    echo [JOHTO] O ZIP foi criado com o caminho EXATO impresso acima.
    echo [JOHTO] Diagnosticos anteriores sao preservados com nomes numerados.
  )
  echo NAO copie os mapas sobre a instalacao e NAO apague saves.
)
echo.
echo Diagnostico salvo em: "%CD%\.blue-work\johto-bedroom-diagnostic.json"
echo Se aparecer JOHTO_NOT_INSTALLED, instale o pacote offline12 original.
echo Se aparecer OLD_OR_DIFFERENT_BEDROOM ou FAILED, confira o JSON.
echo Se aparecer LAYOUT_HGSS_APPLIED, abra o GAME.EXE DESTA PASTA.
echo OBS: Os moveis HGSS originais exigem os PNGs externos dos autores.
echo.
pause
exit /b %RESULT%
