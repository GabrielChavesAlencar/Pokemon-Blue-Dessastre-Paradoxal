@echo off
setlocal
set "REPO=%~dp0"
set "PYTHON=python"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 set "PYTHON=py -3"
echo =======================================================
echo SINNOH J04 - 16 PORTAIS / 5 NPCs / 3 POKE BOLAS
echo Compilacao apenas em stage privado autorizado.
echo Nenhum Game.exe ou save sera alterado.
echo =======================================================
echo Sem parametros, confirma as lacunas e impede instalar.
echo Passe --input-label, --input-sha, --game-data, --spec,
echo --reservations e --sprite-review apenas com dados reais.
%PYTHON% "%REPO%scripts\regions\compile_sinnoh_playable_j04.py" --project "%REPO%" %*
set "STATUS=%ERRORLEVEL%"
if not "%STATUS%"=="0" echo J04 BLOQUEADA: FALTAM MAPAS OU OUTRA EVIDENCIA FISICA.
echo Codigo de saida: %STATUS%
pause
exit /b %STATUS%
