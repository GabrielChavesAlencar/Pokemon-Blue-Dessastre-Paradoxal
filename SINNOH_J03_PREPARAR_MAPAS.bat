@echo off
setlocal
set "REPO=%~dp0"
set "PY=python"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 set "PY=py -3"
echo ==========================================================
echo SINNOH J03 - GEOMETRIA PRIVADA EM STAGING ISOLADO
echo Nao instala nada no jogo principal. Nao acessa saves.
echo ==========================================================
echo A execucao sem argumentos informa os 4 terrenos e 5 lacunas.
echo Para usar recursos autorizados, execute com argumentos:
echo   --source FONTE --game-data DATA --bindings PLANO
echo   --reservations RESERVAS --asset-review DIREITOS
echo Dry-run e padrao; --stage exige --expected-dry-run.
%PY% "%REPO%scripts\regions\prepare_sinnoh_playable_j03.py" --project "%REPO%" %*
set "CODE=%ERRORLEVEL%"
echo Resultado J03: %CODE%
pause
exit /b %CODE%
