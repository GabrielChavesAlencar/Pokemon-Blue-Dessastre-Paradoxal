@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title UNOVA SP05 - Cheren: QA privado, NUNCA instalacao
echo ==============================================================
echo  UNOVA SP05 - PILOTO CHEREN EM AMBIENTE ISOLADO
echo  Nao abre Game.exe. Nao altera mapas, arquivos ou saves.
echo ==============================================================
echo.
set "PY=python"
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
echo  [1] Conferir plano e bloqueios, sem sprites
echo  [2] Selecionar ZIP, SP03/SP04, referencia e direitos por janelas
echo.
choice /c 12 /n /m "Escolha 1 ou 2: "
if errorlevel 2 goto :stage
%PY% scripts\regions\unova_sp05_cheren_pilot.py
if errorlevel 1 goto :blocked
goto :finish
:stage
%PY% scripts\regions\unova_sp05_cheren_pilot.py --gui
if errorlevel 1 goto :blocked
echo.
echo [QA] Pacote privado salvo sob .blue-work\unova\qa\sp05-cheren\
echo [IMPORTANTE] O arquivo NAO foi instalado e exige revisao visual,
echo confirmacao da licenca e testes Game.exe/JoiPlay em copia isolada.
:finish
echo.
echo [OK] O jogo principal e os saves permanecem intactos.
pause
exit /b 0
:blocked
echo.
echo [BLOQUEADO] Faltam provas, imagem 4x4 compativel ou alguma verificacao falhou.
echo Nenhum arquivo jogavel foi instalado.
pause
exit /b 2
