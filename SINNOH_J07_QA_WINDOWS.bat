@echo off
setlocal
cd /d "%~dp0"
echo =========================================================
echo SINNOH J07 - QA NATIVA WINDOWS EM COPIA ISOLADA
echo 43 casos Windows G12 + 1 Android reservado para J08
echo Evidencias pendentes de revisao, nunca auto-aprovadas
echo Sem modificar game\ principal nem saves pessoais
echo =========================================================
echo.
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0scripts\regions\prepare_sinnoh_playable_j07.py" --project "%~dp0" %*
  set "EXITCODE=%ERRORLEVEL%"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERRO: Python 3 indisponivel. Nada foi executado.
    pause
    exit /b 2
  )
  python "%~dp0scripts\regions\prepare_sinnoh_playable_j07.py" --project "%~dp0" %*
  set "EXITCODE=%ERRORLEVEL%"
)
echo.
if not "%EXITCODE%"=="0" (
  echo J07 BLOQUEADA: falta copia QA compilada, hashes, rights, MapIDs ou evidencias validas.
) else (
  echo Comando J07 concluido. Isto NAO aprova Sinnoh nativo.
)
pause
exit /b %EXITCODE%
