@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Musicas de Kanto - Publicacao GitHub Release
echo ===============================================
echo   KANTO - 64 MUSICAS - PUBLICACAO EM GITHUB
echo ===============================================
echo [AVISO] O repositorio e PUBLICO. Nao publique audios sem direitos.
echo [AVISO] Este programa cria uma Release com o ZIP completo.
echo.
set "ZIP_FILE=%~1"
if not defined ZIP_FILE set "ZIP_FILE=%~dp0pkm msc kanto.zip"
if not exist "%ZIP_FILE%" (
  echo [ERRO] Nao encontrei "%ZIP_FILE%"
  echo [DICA] Arraste o ZIP para este BAT ou deixe o ZIP na raiz do projeto.
  pause
  exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Instale Python 3.10+ ou use o Python portatil do Blue Story.
  pause
  exit /b 2
)
echo [1/3] Verificando o ZIP e a lista de faixas sem publicar...
py -3 -X utf8 scripts\music\publish_kanto_release.py --archive "%ZIP_FILE%"
if errorlevel 1 (
  echo [ERRO] O ZIP nao passou na verificacao.
  pause
  exit /b 2
)
echo [2/3] Verificando autenticacao do GitHub CLI...
where gh >nul 2>&1
if errorlevel 1 (
  echo [ERRO] Instale GitHub CLI (gh) e execute gh auth login.
  pause
  exit /b 2
)
gh auth status
if errorlevel 1 (
  echo [ERRO] Rode gh auth login antes da publicacao.
  pause
  exit /b 2
)
echo.
echo [3/3] A publicacao torna o ZIP inteiro acessivel publicamente.
echo Somente prossiga se tiver permissao para redistribuir o audio.
set /p "CONFIRM=Digite AUTORIZO para publicar as 64 musicas no GitHub: "
if /I not "%CONFIRM%"=="AUTORIZO" (
  echo [CANCELADO] Nenhuma musica enviada.
  exit /b 1
)
py -3 -X utf8 scripts\music\publish_kanto_release.py --archive "%ZIP_FILE%" --publish --confirm-rights
set "CODE=%errorlevel%"
if "%CODE%"=="0" (
  echo [OK] Publicacao solicitada. Confira a URL informada no GitHub.
) else (
  echo [ERRO] A publicacao nao foi confirmada.
)
pause
exit /b %CODE%
