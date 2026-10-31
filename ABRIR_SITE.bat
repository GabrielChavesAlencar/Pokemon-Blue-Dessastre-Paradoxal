@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Portal Local
where node >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Instale Node.js 24 para executar o portal.
  pause
  exit /b 1
)
echo O portal ficara disponivel em http://127.0.0.1:4173
echo Mantenha esta janela aberta. Para parar: Ctrl+C.
call npm run dev --prefix site
if errorlevel 1 pause
