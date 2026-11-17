@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title UNOVA A05 - MapIDs candidatos (sem reservar ou instalar)
echo ==============================================================
echo    UNOVA A05 - PLANEJAMENTO DE MAPIDS
echo    Nunca escreve MapInfos, Game.exe, mapas ou saves
echo ==============================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if "%~1"=="" goto :interactive
echo [A05] Comparando com o relatorio A04 selecionado...
%PY% scripts\regions\audit_unova_a05_candidates.py --a04-report "%~1" --write
if errorlevel 1 goto :blocked
goto :done
:interactive
echo [A05] Selecione opcionalmente um A04 privado gerado pela ferramenta A04.
echo Se nao tiver A04, sera usado apenas o inventario historico B01/B04.
echo.
%PY% scripts\regions\audit_unova_a05_candidates.py --gui --write
if errorlevel 1 goto :blocked
:done
echo.
echo [OK] Relatorio privado criado em:
echo    .blue-work\unova\audit\a05-candidates-HASH.json
echo IMPORTANTE: 518-599 sao somente candidatos. NAO estao reservados.
echo Sinnoh 442-517 e Hoenn 700-999 continuam protegidos.
echo.
pause
exit /b 0
:blocked
echo.
echo [BLOQUEADO] Fonte A04 invalida, divergente ou arquivo inseguro.
echo Nenhum mapa, save ou arquivo do jogo foi alterado.
pause
exit /b 2
