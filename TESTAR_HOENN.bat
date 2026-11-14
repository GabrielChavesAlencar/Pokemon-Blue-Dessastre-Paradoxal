@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo =====================================================
echo    POKEMON BLUE - TESTAR HOENN - QA FASES 01-05/12
echo =====================================================
echo.
if not exist "game\Game.exe" (
  echo [BLOQUEADO] Instale primeiro a base Blue em game\ usando INSTALAR_JOGO.bat.
  echo Nenhum arquivo da instalacao atual foi substituido.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase05\Game.exe" (
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
  py -3 "scripts\regions\hoenn_qa_phase1.py" --prepare --output ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-prep-report.json"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [BLOQUEADO] Instale Python 3.11+ e execute novamente.
    pause
    exit /b 2
  )
  python "scripts\regions\hoenn_qa_phase1.py" --prepare --output ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-prep-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Leia o relatorio em .blue-work\hoenn-qa-fase05-prep-report.json
  echo A instalacao game\ e os saves originais permanecem intactos.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase05\Game.exe" (
  echo [BLOQUEADO] Copia isolada nao possui Game.exe.
  pause
  exit /b 2
)
echo.
echo [HOENN QA 02/12] Conferindo fisicamente as portas e conexoes PBS...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase2.py" --copy ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-mapas-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase2.py" --copy ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-mapas-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Existe problema estatico de mapas ou conexoes.
  echo Relatorio: .blue-work\hoenn-qa-fase05-mapas-report.json
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
  py -3 "scripts\regions\hoenn_qa_phase3.py" --copy ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-encontros-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase3.py" --copy ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-encontros-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Falha em encontros ou o piloto foi gerado numa fase antiga.
  echo Relatorio: .blue-work\hoenn-qa-fase05-encontros-report.json
  echo Os saves antigos e a copia de Hoenn da fase anterior ficam intactos.
  pause
  exit /b 2
)
echo [OK] Novos encontros base e catalogo de eventos auditados.
echo [PENDENTE] NPCs, treinadores, placas e historia ainda exigem QA real.
echo.
echo [HOENN QA 04/12] Conferindo HMs regionais e obstaculos da fonte...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase4.py" --copy ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-campo-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase4.py" --copy ".blue-work\hoenn-qa-fase05" --report ".blue-work\hoenn-qa-fase05-campo-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Auditoria de field moves e obstaculos falhou.
  echo Relatorio: .blue-work\hoenn-qa-fase05-campo-report.json
  echo Os saves das fases anteriores permanecem intactos.
  pause
  exit /b 2
)
echo [OK] Contratos de campo estaticos auditados.
echo [PENDENTE] Surf, Dive, Waterfall, Strength e gelo exigem QA real.
echo.
echo [HOENN QA 05/12] Conferindo Aqua, Magma, Archie e Seafloor...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase5.py" --copy ".blue-work\hoenn-qa-fase05"
) else (
  python "scripts\regions\hoenn_qa_phase5.py" --copy ".blue-work\hoenn-qa-fase05"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Inconsistencia de evento, batalha ou RXDATA da historia.
  echo Relatorio: .blue-work\hoenn-qa-fase05-report.json
  echo Nenhum save original foi alterado.
  pause
  exit /b 2
)
echo [OK] Eventos autorais de historia e equipes PBS conferidos.
echo [PENDENTE] Seafloor, submarino, clima e puzzles exigem Game.exe real.
echo.
echo [OK] Pasta de Hoenn preparada e arquivos conferidos.
echo Perfil de save separado: Hoenn QA Fase05.
echo IMPORTANTE: Na primeira abertura o jogo pode compilar e fechar.
echo Se isso ocorrer, execute este BAT outra vez.
echo O Game.exe ainda deve ser testado dentro do jogo.
start "" /D "%CD%\.blue-work\hoenn-qa-fase05" "%CD%\.blue-work\hoenn-qa-fase05\Game.exe"
exit /b 0
