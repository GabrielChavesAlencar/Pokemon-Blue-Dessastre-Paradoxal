@echo off
setlocal
cd /d "%~dp0"
title Blue Studio - Testes de Regressao
echo === BLUE STUDIO - TESTES PBS E INTERFACE ===
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m unittest discover -s tests -v
) else (
  python -m unittest discover -s tests -v
)
if errorlevel 1 goto :erro
where node >nul 2>&1
if not errorlevel 1 (
  node --check "web\app.js"
  if errorlevel 1 goto :erro
  node --check "web\navigation.js"
  if errorlevel 1 goto :erro
  node --check "tests\browser_smoke.cjs"
  if errorlevel 1 goto :erro
) else (
  echo [AVISO] Node.js nao encontrado: testes de sintaxe JS pulados localmente.
)
echo.
echo [OK] Testes locais concluidos. O GitHub Actions tambem executa Chromium.
pause
exit /b 0
:erro
echo.
echo [ERRO] Um ou mais testes falharam. Corrija antes de publicar.
pause
exit /b 1
