@echo off
setlocal
cd /d "%~dp0"
echo ====================================================
echo BLUE STUDIO - SINNOH J10 - EDITOR DE MAPAS ORIGINAIS
echo Nao baixa, instala ou envia arquivos para GitHub.
echo Somente servidor local em 127.0.0.1.
echo ====================================================
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%~dp0scripts\regions\serve_sinnoh_j10_editor.py"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERRO: Python 3 nao localizado. Nenhuma alteracao realizada.
    pause
    exit /b 2
  )
  python "%~dp0scripts\regions\serve_sinnoh_j10_editor.py"
)
echo.
echo Editor J10 encerrado. Nenhum game ou save foi acessado.
pause
