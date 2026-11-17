@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Unova - Verificar Documentacao E (somente leitura)
echo ================================================================
echo  UNOVA - Documentacao e ferramentas E
echo  Validacao de catalogos e protecoes SEM MODIFICAR O JOGO
echo ================================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
echo [1/4] Conferir 74 areas planejadas...
%PY% scripts\regions\audit_unova_u03_catalog.py
if errorlevel 1 goto :failed
echo.
echo [2/4] Conferir direitos, musicas e treinadores pendentes...
%PY% scripts\regions\audit_unova_e06_e07.py
if errorlevel 1 goto :failed
echo.
echo [3/4] Emitir status real e bloqueios da Barra E...
%PY% scripts\regions\audit_unova_e08_readiness.py
if errorlevel 1 goto :failed
echo.
echo [4/4] Auditoria do ZIP real de Pokemon World V18...
if exist ".blue-work\unova\sources\Pokemon_World_V18.zip" (
    echo ZIP encontrado. Verificando estrutura e RXDATA sem executar scripts...
    %PY% scripts\regions\audit_unova_u02.py --write
    if errorlevel 1 goto :blocked
    %PY% scripts\regions\audit_unova_source_detail.py --write
    if errorlevel 1 goto :blocked
    echo.
    echo [E05] Cruzando 74 areas com nomes reais, sem aprovar MapIDs...
    %PY% scripts\regions\audit_unova_e05_crosswalk.py --write
    if errorlevel 1 goto :blocked
    echo.
    echo [E06] Criando matriz privada de direitos por arquivo...
    %PY% scripts\regions\audit_unova_e06_rights_inventory.py --write
    if errorlevel 1 goto :blocked
    echo.
    echo [E04-E06] Conferindo coerencia de hashes, MapInfos, mapas e direitos...
    %PY% scripts\regions\audit_unova_e04_e06_evidence.py --write
    if errorlevel 1 goto :blocked
) else (
    echo [PENDENTE] ZIP do autor nao fornecido. Nenhum mapa real auditado.
)
echo.
echo [OK] Ferramentas de preparacao validadas.
echo [PENDENTE] Unova ainda NAO esta instalada ou aprovada para jogar.
echo.
pause
exit /b 0
:blocked
echo.
echo [BLOQUEADO] Falta corrigir ou comprovar a fonte real.
echo Nenhum dado de jogo/saves foi modificado.
pause
exit /b 2
:failed
echo.
echo [FALHA] Algum catalogo ou ferramenta nao passou na validacao.
echo Nenhum dado de jogo/saves foi modificado.
pause
exit /b 2
