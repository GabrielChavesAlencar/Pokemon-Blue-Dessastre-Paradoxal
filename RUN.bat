@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue Dessastre Paradoxal - Atualizar e Abrir

set "REPO_URL=https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git"
set "REPO_CHECK=github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"
set "CLONE_DIR=%~dp0..\Pokemon-Blue-Dessastre-Paradoxal-Git"

echo.
echo ==== POKEMON BLUE DESSASTRE PARADOXAL - BLUE STUDIO ====
echo.
call :find_git
if errorlevel 1 goto :no_git
if not exist ".git" goto :bootstrap

"%GIT%" remote get-url origin 2>nul | findstr /I /C:"%REPO_CHECK%" >nul
if errorlevel 1 (
  echo [AVISO] O remote origin nao corresponde a este projeto. Nada sera atualizado.
  echo [DICA] Verifique: git remote -v
  goto :start_editor
)
"%GIT%" symbolic-ref --quiet --short HEAD 2>nul | findstr /X /C:"main" >nul
if errorlevel 1 (
  echo [AVISO] A branch atual nao e main. Atualizacao ignorada.
  goto :start_editor
)
echo [INFO] Buscando atualizacoes no GitHub...
"%GIT%" pull --ff-only origin main
if errorlevel 1 (
  echo.
  echo [AVISO] Falha no Git pull. Possivel conflito local, login ou rede.
  echo [AVISO] Nenhuma alteracao local sera descartada a forca.
  echo [DICA] Execute git status para diagnosticar.
  echo [INFO] Abrindo a versao local...
) else (
  echo [OK] Atualizado com a branch main do GitHub.
)
goto :start_editor

:no_git
echo [AVISO] Git nao encontrado. Abra: https://git-scm.com/downloads/win
echo [AVISO] O editor iniciara sem sincronizacao.
goto :start_editor

:bootstrap
echo [INFO] Esta pasta foi extraida de um ZIP e nao possui .git.
echo [INFO] Sera criado um clone separado, sem apagar o que voce ja tem:
echo        %CLONE_DIR%
if exist "%CLONE_DIR%\.git" goto :check_clone
if exist "%CLONE_DIR%" (
  echo [AVISO] A pasta de destino ja existe, mas nao contem .git.
  goto :start_editor
)
echo [INFO] Clonando o projeto privado. O Git pode pedir login.
"%GIT%" clone --branch main --single-branch "%REPO_URL%" "%CLONE_DIR%"
if errorlevel 1 (
  echo [AVISO] Nao foi possivel clonar. Abrindo versao local.
  goto :start_editor
)
:check_clone
"%GIT%" -C "%CLONE_DIR%" remote get-url origin 2>nul | findstr /I /C:"%REPO_CHECK%" >nul
if errorlevel 1 (
  echo [ERRO] O clone encontrado aponta para outro repositorio.
  goto :start_editor
)
if not exist "%CLONE_DIR%\RUN.bat" (
  echo [ERRO] O clone nao contem RUN.bat.
  goto :start_editor
)
rem Reutiliza a pasta de jogo local sem mover ou substituir os arquivos.
if not defined BLUE_GAME_DIR if exist "%~dp0game\PBS" set "BLUE_GAME_DIR=%~dp0game"
echo [OK] Usando a copia Git. Seu jogo e seus arquivos originais permanecem intactos.
echo [DICA] Para as proximas execucoes, use "%CLONE_DIR%\RUN.bat".
call "%CLONE_DIR%\RUN.bat"
exit /b %errorlevel%

:start_editor
if not exist "server\main.py" (
  echo [ERRO] Nao encontrei server\main.py.
  pause
  exit /b 1
)
where py >nul 2>&1
if errorlevel 1 goto :try_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :try_python
echo [INFO] Abrindo Blue Studio no navegador...
py -3 "server\main.py"
goto :finish

:try_python
where python >nul 2>&1
if errorlevel 1 goto :no_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :no_python
echo [INFO] Abrindo Blue Studio no navegador...
python "server\main.py"
goto :finish

:no_python
echo [ERRO] Python 3.10+ nao encontrado: https://www.python.org/downloads/
pause
exit /b 1

:finish
set "APP_EXIT=%errorlevel%"
echo.
echo [INFO] Blue Studio encerrado. Codigo de saida: %APP_EXIT%
pause
exit /b %APP_EXIT%

:find_git
set "GIT="
where git >nul 2>&1
if not errorlevel 1 set "GIT=git"
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if not defined GIT exit /b 1
"%GIT%" --version >nul 2>&1
exit /b %errorlevel%
