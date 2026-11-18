@echo off
setlocal
cd /d "%~dp0"
echo =========================================================
echo SINNOH J06 - COPIA QA WINDOWS ISOLADA
echo Hashes, direitos, MapIDs, perfil de saves e rollback
echo NUNCA modifica game\ principal, Kanto, Johto ou Hoenn
echo =========================================================
echo.
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0scripts\regions\prepare_sinnoh_playable_j06.py" --project "%~dp0" %*
  set "EXITCODE=%ERRORLEVEL%"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERRO: Python 3 indisponivel. Nenhum executavel foi aberto.
    pause
    exit /b 2
  )
  python "%~dp0scripts\regions\prepare_sinnoh_playable_j06.py" --project "%~dp0" %*
  set "EXITCODE=%ERRORLEVEL%"
)
if not "%EXITCODE%"=="0" (
  echo J06 BLOQUEADA: faltam mapas, hashes, direitos, R07 ou QA verificada.
) else (
  echo Comando J06 concluido. Isso NAO significa Sinnoh jogavel.
)
pause
exit /b %EXITCODE%
