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
echo Nao foi selecionada a pasta REAL do Decades.
echo Para auditar, arraste sobre este BAT a pasta game ou Data.
echo.
echo Para comparar varias regioes, use o terminal CMD da pasta do projeto:
echo python scripts\regions\audit_unova_a04_mapids.py --base-data "C:\Jogo\game\Data" --overlay "KANTO=C:\Pilotos\Kanto\Data" --overlay "JOHTO=C:\Pilotos\Johto\Data" --overlay "HOENN=C:\Pilotos\Hoenn.zip" --overlay "SINNOH=C:\Pilotos\Sinnoh\Data" --write
echo.
echo Sem MapInfos real, nenhuma reserva de MapID pode ser certificada.
%PY% scripts\regions\audit_unova_a04_mapids.py --write
goto :blocked
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
