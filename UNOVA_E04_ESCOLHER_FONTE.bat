@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Unova E04 - Selecionar fonte original com seguranca
echo =============================================================
echo  UNOVA E04 - ASSISTENTE DE FONTE PRIVADA
echo  Nao altera o jogo, mapas, instalador ou saves
echo =============================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not "%~1"=="" goto :drag
echo Abrindo a publicacao do autor no navegador...
start "" "https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/"
echo Baixe o projeto ZIP original e, se disponivel, Credits.txt.
echo Depois selecione os arquivos na janela do programa.
echo.
%PY% scripts\regions\unova_e04_intake.py --gui
if errorlevel 1 goto :block
goto :audit
:drag
echo Recebi arquivo por arrastar/soltar.
if not "%~2"=="" goto :dragcredits
%PY% scripts\regions\unova_e04_intake.py --zip "%~1"
if errorlevel 1 goto :block
goto :audit
:dragcredits
%PY% scripts\regions\unova_e04_intake.py --zip "%~1" --credits "%~2"
if errorlevel 1 goto :block
:audit
echo.
echo [AUDITORIA] Conferindo metadados, RXDATA, crosswalk e direitos...
call "%~dp0UNOVA_VALIDAR_DOCUMENTACAO.bat"
exit /b %errorlevel%
:block
echo.
echo [BLOQUEADO] Fonte ausente, invalida, alterada ou arquivo recusado.
echo Nenhum arquivo jogavel foi modificado.
echo.
pause
exit /b 2
