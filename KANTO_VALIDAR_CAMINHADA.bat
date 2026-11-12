@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Kanto: teste real de caminhada
echo.
echo ===== KANTO ETAPA 02 - CAMINHADA REAL =====
echo [INFO] A copia experimental preserva os saves de Decades.
echo [INFO] Teste controles, portas, treinadores e ida e volta sem atalhos.
echo [IMPORTANTE] CI nao comprova a caminhada humana; relate S/F/N apos jogar.
echo [INFO] O relatorio fica apenas em .blue-work\kanto-gui-reports.
echo.
set "KANTO_FEEDBACK_SCOPE=caminhada"
call "%~dp0KANTO_JOGAR_EXPERIMENTAL.bat" %*
exit /b %errorlevel%
