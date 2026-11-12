@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul
title Pokemon Blue - Kanto experimental (jogabilidade)
echo.
echo ===============================================
echo   KANTO EXPERIMENTAL - JOGAR E REPORTAR
echo ===============================================
echo [INFO] O jogo abre na copia .blue-work com perfil de save separado.
echo [INFO] Sua instalacao Blue/Decades e seus saves principais nao sao alterados.
echo [INFO] Jogar de verdade: o processo continuara aberto ate voce fechar o Game.exe.
echo [INFO] Logs e checklist ficarao somente em .blue-work\kanto-gui-reports.
echo.
where py >nul 2>&1
if not errorlevel 1 goto :run_py
where python >nul 2>&1
if not errorlevel 1 goto :run_python
echo [ERRO] Python 3.10+ nao encontrado; consulte docs\KANTO_TESTE_EXPERIMENTAL.md.
goto :error
:run_py
py -3 -X utf8 "scripts\regions\gui_diagnostics.py" %*
set "GAME_EXIT=%errorlevel%"
py -3 -X utf8 "scripts\regions\kanto_feedback.py"
goto :result
:run_python
python -X utf8 "scripts\regions\gui_diagnostics.py" %*
set "GAME_EXIT=%errorlevel%"
python -X utf8 "scripts\regions\kanto_feedback.py"
goto :result
:result
echo.
if "%GAME_EXIT%"=="0" (
  echo [OK] O jogo foi iniciado ou uma janela de teste foi observada.
) else (
  echo [AVISO] O monitor nao confirmou a inicializacao grafica.
  echo [DICA] Consulte os logs locais em .blue-work\kanto-gui-reports.
)
echo [IMPORTANTE] O checklist e respondido por voce: a janela nao prova jogabilidade.
echo [INFO] Leia docs\KANTO_TESTE_EXPERIMENTAL.md para as rotas da fase 7.
pause
exit /b %GAME_EXIT%
:error
pause
exit /b 2
