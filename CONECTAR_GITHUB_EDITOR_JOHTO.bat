@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Autenticar GitHub - Editor de Johto
echo ===================================================
echo     CONECTAR GITHUB AO EDITOR DE MAPAS JOHTO
echo ===================================================
echo.
set "GH="
if exist "%CD%\tools\gh\gh.exe" set "GH=%CD%\tools\gh\gh.exe"
if not defined GH (
 where gh >nul 2>nul
 if not errorlevel 1 set "GH=gh"
)
if not defined GH (
 echo GitHub CLI nao encontrada. Instalando versao portatil oficial...
 powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\INSTALAR_GH_PORTATIL.ps1" -InstallRoot "%CD%\tools\gh"
 if errorlevel 1 (
   echo [ERRO] Falha ao instalar a GitHub CLI.
   pause
   exit /b 1
 )
 set "GH=%CD%\tools\gh\gh.exe"
)
echo.
echo Verificando autenticacao da sua conta GitHub...
"%GH%" auth status >nul 2>nul
if errorlevel 1 (
  echo.
  echo Uma pagina no navegador sera aberta para autenticar sua conta.
  echo O GitHub pode pedir para confirmar um codigo mostrado no terminal.
  echo.
  "%GH%" auth login --hostname github.com --git-protocol https --web
  if errorlevel 1 (
    echo [ERRO] Login nao finalizado.
    pause
    exit /b 1
  )
)
echo.
"%GH%" auth status
echo.
echo [OK] GitHub autenticado. Retorne ao Map Studio e clique em
echo Verificar GitHub, depois em Publicar este mapa na main.
echo.
pause
