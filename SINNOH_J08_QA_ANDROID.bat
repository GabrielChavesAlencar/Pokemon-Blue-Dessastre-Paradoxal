@echo off
setlocal
cd /d "%~dp0"
echo =========================================================
echo SINNOH J08 - PACOTE DELTA ANDROID/JOIPLAY QA PRIVADO
echo Somente arquivos alterados; nenhum save, instalacao,
echo backup total ou release sera modificado.
echo =========================================================
echo.
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0scripts\regions\prepare_sinnoh_playable_j08.py" --project "%~dp0" %*
  set "EXITCODE=%ERRORLEVEL%"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERRO: Python 3 indisponivel. Nenhum arquivo foi instalado.
    pause
    exit /b 2
  )
  python "%~dp0scripts\regions\prepare_sinnoh_playable_j08.py" --project "%~dp0" %*
  set "EXITCODE=%ERRORLEVEL%"
)
echo.
if not "%EXITCODE%"=="0" (
  echo J08 BLOQUEADA: faltam mapas, R07/R08, 43 revisoes Windows, stage Android ou hashes.
) else (
  echo J08 concluiu apenas verificacao/ZIP candidato QA; nao aprova JoiPlay.
)
pause
exit /b %EXITCODE%
