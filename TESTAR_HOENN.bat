@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo =====================================================
echo    POKEMON BLUE - TESTAR HOENN - QA FASE 01/12
echo =====================================================
echo.
if not exist "game\Game.exe" (
  echo [BLOQUEADO] Instale primeiro a base Blue em game\ usando INSTALAR_JOGO.bat.
  echo Nenhum arquivo da instalacao atual foi substituido.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase01\Game.exe" (
  if not exist "The Pokémon World Project - Hoenn.zip" (
    echo [BLOQUEADO] ZIP original nao encontrado na raiz do projeto.
    echo Esperado: The Pokémon World Project - Hoenn.zip
    echo Nao renomeie arquivos RXDATA nem use um map pack diferente.
    pause
    exit /b 2
  )
)
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase1.py" --prepare
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [BLOQUEADO] Instale Python 3.11+ e execute novamente.
    pause
    exit /b 2
  )
  python "scripts\regions\hoenn_qa_phase1.py" --prepare
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Leia o relatorio em .blue-work\hoenn-qa-fase01-report.json
  echo A instalacao game\ e os saves originais permanecem intactos.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase01\Game.exe" (
  echo [BLOQUEADO] Cópia isolada nao possui Game.exe.
  pause
  exit /b 2
)
echo.
echo [OK] Pasta de Hoenn preparada e arquivos conferidos.
echo Perfil de save separado: Hoenn Piloto.
echo IMPORTANTE: Na primeira abertura o jogo pode compilar e fechar.
echo Se isso ocorrer, execute este BAT outra vez.
echo O Game.exe ainda deve ser testado dentro do jogo.
start "" /D "%CD%\.blue-work\hoenn-qa-fase01" "%CD%\.blue-work\hoenn-qa-fase01\Game.exe"
exit /b 0
