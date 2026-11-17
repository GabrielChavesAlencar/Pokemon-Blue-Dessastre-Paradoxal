@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Unova SP04 - Catalogo de NPCs de Black e White
echo ==============================================================
echo  UNOVA SP04 - CATALOGO DE PERSONAGENS E SPRITES
echo  NAO altera Graphics, mapas, jogo, Blue-Story ou saves
echo ==============================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if "%~1"=="" goto :latest
echo [SP04] Conferindo o relatorio SP03 arrastado...
%PY% scripts\regions\audit_unova_sp04_npcs.py --audit "%~1" --write
if errorlevel 1 goto :blocked
goto :done
:latest
echo [SP04] Buscando ultimo relatorio privado SP03.
echo Se nenhum ZIP tiver sido auditado, o resultado sera somente planejamento.
%PY% scripts\regions\audit_unova_sp04_npcs.py --latest --write
if errorlevel 1 goto :blocked
:done
echo.
echo [OK] Catalogo privado em:
echo   .blue-work\unova\audit\npc-catalog\
echo Os candidatos precisam de revisao visual, autorizacao e teste nativo.
echo Nenhum sprite ou NPC foi instalado.
echo.
pause
exit /b 0
:blocked
echo.
echo [BLOQUEADO] Dados inconsistentes, fonte SP03 invalida ou catalogo alterado.
echo Nenhum arquivo jogavel/saves foi modificado.
pause
exit /b 2
