@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title POKEMON BLUE - UNOVA MAPIDS AUTOMATICO A04 + A05
echo ============================================================
echo  POKEMON BLUE - UNOVA MAPIDS - EXECUCAO AUTOMATICA
echo  1. Encontrar instalacao Pokemon Blue/Decades
echo  2. Analisar MapInfos / MapNNN (A04)
echo  3. Comparar reservas Sinnoh e Unova (A05)
echo  4. Abrir resultado no Bloco de Notas
echo ============================================================
echo Nao altera nenhum arquivo do jogo ou save.
echo.
set "PYRUN="
where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYRUN=py -3"
)
if not defined PYRUN (
    where python.exe >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
        if not errorlevel 1 set "PYRUN=python"
    )
)
if not defined PYRUN goto :no_python
%PYRUN% scripts\regions\unova_auto_mapids.py --open-summary
set "STATUS=%ERRORLEVEL%"
if "%STATUS%"=="0" goto :done
echo.
echo [BLOQUEADO] Leia o diagnostico aberto no Bloco de Notas.
echo Se nao abrir, procure:
echo .blue-work\unova\audit\LEIA_AQUI_UNOVA_MAPIDS.txt
echo Nenhum arquivo do jogo foi modificado.
goto :done
:no_python
echo [BLOQUEADO] Python 3.11 ou mais recente nao foi encontrado.
echo Instale Python 3.11+ ou use o Python incluido no seu ambiente de desenvolvimento.
echo O programa nao baixa nem executa instaladores automaticamente.
set "STATUS=2"
:done
echo.
if "%STATUS%"=="0" (
    echo [OK] Analise A04 + A05 finalizada; MapIDs ainda NAO reservados.
) else (
    echo [ATENCAO] Auditoria nao finalizada; nenhum mapa alterado.
)
echo Esta janela fecha automaticamente. O resumo permanece salvo.
timeout /t 8 /nobreak >nul
exit /b %STATUS%
