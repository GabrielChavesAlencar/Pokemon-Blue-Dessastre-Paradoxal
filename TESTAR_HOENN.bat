@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo =====================================================
echo    POKEMON BLUE - TESTAR HOENN - QA FASES 01-03/12
echo =====================================================
echo.
if not exist "game\Game.exe" (
  echo [BLOQUEADO] Instale primeiro a base Blue em game\ usando INSTALAR_JOGO.bat.
  echo Nenhum arquivo da instalacao atual foi substituido.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase03\Game.exe" (
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
  py -3 "scripts\regions\hoenn_qa_phase1.py" --prepare --output ".blue-work\hoenn-qa-fase03" --report ".blue-work\hoenn-qa-fase03-prep-report.json"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [BLOQUEADO] Instale Python 3.11+ e execute novamente.
    pause
    exit /b 2
  )
  python "scripts\regions\hoenn_qa_phase1.py" --prepare --output ".blue-work\hoenn-qa-fase03" --report ".blue-work\hoenn-qa-fase03-prep-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Leia o relatorio em .blue-work\hoenn-qa-fase03-prep-report.json
  echo A instalacao game\ e os saves originais permanecem intactos.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase03\Game.exe" (
  echo [BLOQUEADO] Copia isolada nao possui Game.exe.
  pause
  exit /b 2
)
echo.
echo [HOENN QA 02/12] Conferindo fisicamente as portas e conexoes PBS...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase2.py" --copy ".blue-work\hoenn-qa-fase03" --report ".blue-work\hoenn-qa-fase03-mapas-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase2.py" --copy ".blue-work\hoenn-qa-fase03" --report ".blue-work\hoenn-qa-fase03-mapas-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Existe problema estatico de mapas ou conexoes.
  echo Relatorio: .blue-work\hoenn-qa-fase03-mapas-report.json
  echo Nao alteramos game\, saves ou o perfil original.
  pause
  exit /b 2
)
echo [OK] 199 mapas e transferencias auditados por dados.
echo [ATENCAO] Isto NAO equivale a jogar/testar Game.exe.
echo.
echo [HOENN QA 03/12] Conferindo encontros, itens e pendencias de NPCs...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase3.py" --copy ".blue-work\hoenn-qa-fase03"
) else (
  python "scripts\regions\hoenn_qa_phase3.py" --copy ".blue-work\hoenn-qa-fase03"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Falha em encontros ou o piloto foi gerado numa fase antiga.
  echo Relatorio: .blue-work\hoenn-qa-fase03-report.json
  echo Os saves antigos e a copia de Hoenn da fase anterior ficam intactos.
  pause
  exit /b 2
)
echo [OK] Novos encontros base e catalogo de eventos auditados.
echo [PENDENTE] NPCs, treinadores, placas e historia ainda exigem QA real.
echo.
echo [OK] Pasta de Hoenn preparada e arquivos conferidos.
echo Perfil de save separado: Hoenn Piloto.
echo IMPORTANTE: Na primeira abertura o jogo pode compilar e fechar.
echo Se isso ocorrer, execute este BAT outra vez.
echo O Game.exe ainda deve ser testado dentro do jogo.
start "" /D "%CD%\.blue-work\hoenn-qa-fase03" "%CD%\.blue-work\hoenn-qa-fase03\Game.exe"
exit /b 0
