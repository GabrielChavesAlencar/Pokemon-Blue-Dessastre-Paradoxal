@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Unova - Auditor de sprites do pack Gen 5 (somente leitura)
echo ===============================================================
echo  UNOVA - AUDITOR DE SPRITES (PNG, GIF, APNG)
echo  Sem instalar ou alterar o Decades, mapas, NPCs ou saves
echo ===============================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if "%~1"=="" goto :gui
if not "%~2"=="" goto :withreference
echo [ZIP] Conferindo arquivo escolhido: %~nx1
%PY% scripts\regions\audit_unova_sprite_pack.py --zip "%~1" --write
if errorlevel 1 goto :blocked
goto :ok
:withreference
echo [ZIP + DECADES] Conferindo sprites com referencia local de leitura...
%PY% scripts\regions\audit_unova_sprite_pack.py --zip "%~1" --reference-dir "%~2" --write
if errorlevel 1 goto :blocked
goto :ok
:gui
echo Escolha o arquivo ZIP do pack na janela do Windows.
echo A comparacao com Graphics/Characters do Decades sera opcional.
echo.
%PY% scripts\regions\audit_unova_sprite_pack.py --gui
if errorlevel 1 goto :blocked
:ok
echo.
echo [SP04] Atualizando catalogo de NPCs a partir do relatorio SP03 mais recente...
%PY% scripts\regions\audit_unova_sp04_npcs.py --latest --write
if errorlevel 1 goto :blocked
echo.
echo [OK] Inventario de sprites salvo somente em:
echo   .blue-work\unova\audit\sprite-packs\
echo [SP04] Catalogo de NPCs disponivel em .blue-work\unova\audit\npc-catalog\
echo ATENCAO: nenhum sprite foi instalado, licenciado ou aprovado para o Game.exe.
echo.
pause
exit /b 0
:blocked
echo.
echo [BLOQUEADO] Fonte invalida, arquivo nao selecionado ou imagem suspeita.
echo Nenhum arquivo do jogo/saves foi alterado.
echo.
pause
exit /b 2
