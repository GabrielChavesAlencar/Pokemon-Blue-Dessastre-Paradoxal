@echo off
setlocal
cd /d "%~dp0"
title Blue Dessastre Paradoxal - Importar Decades
if exist "game\Game.exe" (
    echo [OK] O jogo ja existe na pasta game.
    pause
    exit /b 0
)
where git >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Git nao instalado: https://git-scm.com/downloads
    pause
    exit /b 1
)
if exist "game\.git" (
    echo [AVISO] Existe um clone parcial em game. Corrija-o manualmente antes de importar.
    pause
    exit /b 1
)
if exist "game" (
    dir /a /b "game" | findstr . >nul
    if not errorlevel 1 (
        echo [ERRO] A pasta game nao esta vazia. Remova os arquivos parciais ou use outra pasta.
        pause
        exit /b 1
    )
    rmdir "game" 2>nul
)
echo Baixando a base publica HazyCrazy/Pokemon-Decades para uso LOCAL.
echo IMPORTANTE: download grande ^(~936 MiB de dados de repositorio^).
echo O conteudo original NAO sera publicado no seu GitHub.
choice /c SN /m "Continuar com o download local?"
if errorlevel 2 exit /b 0
git clone --depth 1 --single-branch --branch main https://github.com/HazyCrazy/Pokemon-Decades.git "game"
if errorlevel 1 (
    echo [ERRO] Falha ao clonar. Confira a conexao e o espaco livre.
    pause
    exit /b 1
)
echo.
echo [OK] Base instalada localmente.
echo Personalizando nome da janela do fangame...
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "server\prepare_game.py"
) else (
  python "server\prepare_game.py"
)
echo Execute RUN.bat para editar.
echo A versao de referencia usada na analise foi 3.0.8, commit ff6091b23603b3298ad72a7584b02a51e1d01c0e.
echo O comando acima baixa a branch main mais recente; ela pode mudar futuramente.
pause
