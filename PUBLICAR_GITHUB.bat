@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Publicar Pokemon Blue Dessastre Paradoxal no GitHub

call :find_gh
if errorlevel 1 (
  echo [INFO] GitHub CLI nao encontrado. O publicador pode instalar automaticamente.
  echo A instalacao usa primeiro o WinGet e, se necessario, uma copia portatil
  echo baixada da pagina oficial github.com/cli/cli/releases.
  choice /c SN /m "Autorizar a instalacao do GitHub CLI agora?"
  if errorlevel 2 goto :manual_gh
  call :install_gh
  if errorlevel 1 goto :manual_gh
)

call :find_git
if errorlevel 1 (
  echo [INFO] Git nao encontrado. Tentando localizar ou instalar.
  where winget >nul 2>&1
  if errorlevel 1 goto :manual_git
  choice /c SN /m "Autorizar a instalacao do Git for Windows via WinGet?"
  if errorlevel 2 goto :manual_git
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  call :find_git
  if errorlevel 1 goto :manual_git
)

echo.
echo [OK] GitHub CLI encontrado:
"%GH%" --version
if errorlevel 1 goto :manual_gh
echo [OK] Git encontrado:
"%GIT%" --version
if errorlevel 1 goto :manual_git

echo.
echo Repositorio de destino: Pokemon-Blue-Dessastre-Paradoxal
echo Repositorio novo: PRIVADO. Repositorio existente: visibilidade preservada.
echo A pasta game, os saves, ferramentas locais e backups nao serao enviados.
echo Conteudo original de Pokemon Decades nao sera redistribuido.
choice /c SN /m "Criar ou atualizar o repositorio no seu GitHub?"
if errorlevel 2 exit /b 0

"%GH%" auth status >nul 2>&1
if errorlevel 1 (
  echo.
  echo [INFO] Faca login na sua conta GitHub pelo navegador.
  "%GH%" auth login --hostname github.com --git-protocol https --web
  if errorlevel 1 goto :fail
)
"%GH%" auth setup-git
if errorlevel 1 echo [AVISO] Nao foi possivel configurar credenciais do Git automaticamente.

set "GH_TEMP=%TEMP%\blue-studio-gh-user-%RANDOM%-%RANDOM%.txt"
"%GH%" api user --jq .login > "%GH_TEMP%"
if errorlevel 1 (
  if exist "%GH_TEMP%" del /q "%GH_TEMP%" >nul 2>&1
  goto :fail
)
set /p "GH_USER=" < "%GH_TEMP%"
del /q "%GH_TEMP%" >nul 2>&1
if not defined GH_USER (
  echo [ERRO] Nao foi possivel identificar o usuario GitHub.
  goto :fail
)
echo [INFO] Conta detectada: %GH_USER%

if not exist ".git" (
  "%GIT%" init -b main
  if errorlevel 1 goto :fail
)

"%GIT%" add README.md LICENSE .gitignore RUN.bat JOGAR.bat BAIXAR_BASE_DECADES.bat ABRIR_RPG_MAKER.bat PUBLICAR_GITHUB.bat PERSONALIZAR_JOGO.bat server web tests docs examples scripts
if errorlevel 1 goto :fail
"%GIT%" diff --cached --quiet
if errorlevel 1 (
  "%GIT%" -c user.name="%GH_USER%" -c user.email="%GH_USER%@users.noreply.github.com" commit -m "Blue Studio: editor e publicador automatico"
  if errorlevel 1 goto :fail
)

"%GH%" repo view "%GH_USER%/Pokemon-Blue-Dessastre-Paradoxal" >nul 2>&1
if not errorlevel 1 goto :existing_repo

"%GIT%" remote get-url origin >nul 2>&1
if not errorlevel 1 (
  echo [ERRO] Ha um remote origin, mas nao achei o repositorio esperado.
  echo Verifique o destino com: git remote -v
  goto :fail
)
"%GH%" repo create "Pokemon-Blue-Dessastre-Paradoxal" --private --source=. --remote=origin --push
if errorlevel 1 goto :fail
goto :done

:existing_repo
echo [INFO] Repositorio existente encontrado. Preparando push.
"%GIT%" remote get-url origin >nul 2>&1
if errorlevel 1 (
  "%GIT%" remote add origin "https://github.com/%GH_USER%/Pokemon-Blue-Dessastre-Paradoxal.git"
  if errorlevel 1 goto :fail
) else (
  "%GIT%" remote -v | findstr /i /c:"%GH_USER%/Pokemon-Blue-Dessastre-Paradoxal" >nul
  if errorlevel 1 (
    echo [ERRO] O remote origin aponta para outro projeto. Push cancelado.
    goto :fail
  )
)
"%GIT%" push -u origin main
if errorlevel 1 goto :fail

goto :done

:find_gh
set "GH="
where gh >nul 2>&1
if not errorlevel 1 set "GH=gh"
if not defined GH if exist "%ProgramFiles%\GitHub CLI\gh.exe" set "GH=%ProgramFiles%\GitHub CLI\gh.exe"
if not defined GH if exist "%LOCALAPPDATA%\Programs\GitHub CLI\gh.exe" set "GH=%LOCALAPPDATA%\Programs\GitHub CLI\gh.exe"
if not defined GH if exist "%~dp0tools\gh\gh.exe" set "GH=%~dp0tools\gh\gh.exe"
if not defined GH exit /b 1
exit /b 0

:find_git
set "GIT="
where git >nul 2>&1
if not errorlevel 1 set "GIT=git"
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if not defined GIT exit /b 1
exit /b 0

:install_gh
where winget >nul 2>&1
if not errorlevel 1 (
  echo [INFO] Instalando GitHub CLI com WinGet...
  winget install --id GitHub.cli -e --source winget --accept-package-agreements --accept-source-agreements
  call :find_gh
  if not errorlevel 1 exit /b 0
  echo [AVISO] WinGet nao deixou gh acessivel nesta janela. Tentando versao portatil.
)
where powershell >nul 2>&1
if errorlevel 1 exit /b 1
echo [INFO] Instalando a versao portatil de gh na pasta tools\gh...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\INSTALAR_GH_PORTATIL.ps1" -InstallRoot "%~dp0tools\gh"
if errorlevel 1 exit /b 1
call :find_gh
exit /b %errorlevel%

:manual_gh
echo.
echo [ERRO] GitHub CLI ainda nao esta acessivel.
echo Instalacao manual: https://cli.github.com/
echo Ou execute em PowerShell: winget install --id GitHub.cli -e
echo Depois abra este PUBLICAR_GITHUB.bat novamente.
pause
exit /b 1

:manual_git
echo.
echo [ERRO] Git ainda nao esta acessivel.
echo Instalacao manual: https://git-scm.com/downloads/win
echo Ou execute em PowerShell: winget install --id Git.Git -e
echo Depois abra este PUBLICAR_GITHUB.bat novamente.
pause
exit /b 1

:done
echo.
echo [OK] Publicacao concluida!
echo https://github.com/%GH_USER%/Pokemon-Blue-Dessastre-Paradoxal
"%GH%" repo view "%GH_USER%/Pokemon-Blue-Dessastre-Paradoxal" --web
pause
exit /b 0

:fail
echo.
echo [ERRO] A publicacao nao foi concluida. Veja a mensagem exibida acima.
echo Seus arquivos locais foram preservados.
pause
exit /b 1
