@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue Dessastre Paradoxal - Atualizar e Abrir

set "REPO_URL=https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git"
set "REPO_CHECK=github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal"

echo.
echo ==== POKEMON BLUE DESSASTRE PARADOXAL - BLUE STUDIO ====
echo.
call :find_git
if errorlevel 1 goto :no_git
if not exist ".git" goto :bootstrap

rem Evitar atualizacoes de repositorios desconhecidos.
"%GIT%" remote get-url origin 2>nul | findstr /I /C:"%REPO_CHECK%" >nul
if errorlevel 1 (
  echo [AVISO] Origin nao corresponde a este projeto. Atualizacao cancelada.
  echo [DICA] Verifique com: git remote -v
  goto :start_editor
)

rem O script antigo ignorava qualquer branch diferente de main.
rem Agora corrigimos isso sem reset/force nem descartar edicoes.
"%GIT%" symbolic-ref --quiet --short HEAD 2>nul | findstr /X /C:"main" >nul
if not errorlevel 1 goto :pull_main

echo [INFO] A branch local nao e main. Preparando migracao segura...
echo [INFO] Buscando a branch main do GitHub...
"%GIT%" fetch origin main
if errorlevel 1 (
  echo [AVISO] Nao foi possivel buscar main. Mantendo arquivos locais.
  goto :start_editor
)

rem Nunca trocar branch com alteracoes locais pendentes: preservar tudo.
set "STATUS_FILE=%TEMP%\blue-studio-status-%RANDOM%-%RANDOM%.txt"
"%GIT%" status --porcelain > "%STATUS_FILE%"
if errorlevel 1 (
  if exist "%STATUS_FILE%" del /q "%STATUS_FILE%" >nul 2>&1
  echo [AVISO] Falha ao verificar alteracoes locais.
  goto :bootstrap
)
for %%A in ("%STATUS_FILE%") do if %%~zA GTR 0 (
  del /q "%STATUS_FILE%" >nul 2>&1
  echo [AVISO] Existem alteracoes locais nesta branch.
  echo [INFO] Abrindo o editor nesta mesma pasta, sem criar outro clone.
  goto :bootstrap
)
del /q "%STATUS_FILE%" >nul 2>&1

"%GIT%" show-ref --verify --quiet refs/heads/main
if errorlevel 1 goto :create_main
echo [INFO] Mudando para a branch local main...
"%GIT%" switch main
if errorlevel 1 goto :switch_failed
goto :pull_main

:create_main
echo [INFO] Criando main a partir de origin/main...
"%GIT%" switch -c main --track origin/main
if errorlevel 1 goto :switch_failed
goto :pull_main

:switch_failed
echo [AVISO] Git nao permitiu mudar de branch. Nenhum reset sera feito.
echo [INFO] Abrindo o editor nesta mesma pasta.
goto :bootstrap

:pull_main
echo [INFO] Buscando atualizacoes em origin/main...
"%GIT%" pull --ff-only origin main
if errorlevel 1 (
  echo.
  echo [AVISO] O pull nao pode ser concluido com fast-forward.
  echo [INFO] Alteracoes locais preservadas. Mantendo esta mesma pasta.
  goto :bootstrap
)
echo [OK] Arquivos do editor atualizados pela main do GitHub.
goto :start_editor

:no_git
echo [AVISO] Git nao instalado: https://git-scm.com/downloads/win
echo [INFO] Abrindo editor local, sem atualizacao.
goto :start_editor

:bootstrap
echo [AVISO] Atualizacao indisponivel. Abrindo o editor nesta mesma pasta.
echo [INFO] Nenhuma pasta duplicada sera criada.
goto :start_editor

:start_editor
if "%BLUE_STUDIO_NO_SERVER%"=="1" (
  echo [TESTE] Atualizacao verificada sem abrir o servidor.
  exit /b 0
)
if not exist "server\main.py" (
  echo [ERRO] server\main.py nao encontrado.
  pause
  exit /b 1
)
where py >nul 2>&1
if errorlevel 1 goto :try_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :try_python
echo [INFO] Abrindo Blue Studio no navegador...
py -3 -X utf8 "server\main.py"
goto :finish

:try_python
where python >nul 2>&1
if errorlevel 1 goto :no_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto :no_python
echo [INFO] Abrindo Blue Studio no navegador...
python -X utf8 "server\main.py"
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
