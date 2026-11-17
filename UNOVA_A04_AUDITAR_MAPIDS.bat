@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Unova A04 - Auditoria de MapIDs Decades Kanto Johto Hoenn Sinnoh
echo ==============================================================
echo   UNOVA A04 - INVENTARIO DE MAPIDS - SOMENTE LEITURA
echo   Nao altera Data/MapInfos, mapas, Scripts nem saves
echo ==============================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if "%~1"=="" goto :guide
echo [A04] Verificando Data do Decades e overlays regionais recebidos...
echo.
%PY% scripts\regions\audit_unova_a04_mapids.py --base-data "%~1" --write
if errorlevel 1 goto :blocked
goto :success
:guide
echo Abrindo seletor da pasta real do Decades e overlays opcionais...
%PY% scripts\regions\audit_unova_a04_mapids.py --gui --write
if errorlevel 1 goto :blocked
goto :success
:success
echo.
echo [OK] Inventario de ocupacao gerado em:
echo   .blue-work\unova\audit\a04-mapids-HASH.json
echo ATENCAO: ainda NAO foram reservados MapIDs para Unova!
echo Os nomes das regioes e a completude dos overlays requerem revisao.
echo.
pause
exit /b 0
:blocked
echo.
echo [BLOQUEADO] MapInfos ausente, fonte insegura ou auditoria incompleta.
echo O jogo principal e os saves permanecem intactos.
pause
exit /b 2
