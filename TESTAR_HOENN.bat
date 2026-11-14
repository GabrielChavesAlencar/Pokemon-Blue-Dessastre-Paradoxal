@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo =====================================================
echo    POKEMON BLUE - TESTAR HOENN - QA FASES 01-09/12
echo =====================================================
echo.
if not exist "game\Game.exe" (
  echo [BLOQUEADO] Instale primeiro a base Blue em game\ usando INSTALAR_JOGO.bat.
  echo Nenhum arquivo da instalacao atual foi substituido.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase09\Game.exe" (
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
  py -3 "scripts\regions\hoenn_qa_phase1.py" --prepare --output ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-prep-report.json"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [BLOQUEADO] Instale Python 3.11+ e execute novamente.
    pause
    exit /b 2
  )
  python "scripts\regions\hoenn_qa_phase1.py" --prepare --output ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-prep-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Leia o relatorio em .blue-work\hoenn-qa-fase09-prep-report.json
  echo A instalacao game\ e os saves originais permanecem intactos.
  pause
  exit /b 2
)
if not exist ".blue-work\hoenn-qa-fase09\Game.exe" (
  echo [BLOQUEADO] Copia isolada nao possui Game.exe.
  pause
  exit /b 2
)
echo.
echo [HOENN QA 02/12] Conferindo fisicamente as portas e conexoes PBS...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase2.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-mapas-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase2.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-mapas-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Existe problema estatico de mapas ou conexoes.
  echo Relatorio: .blue-work\hoenn-qa-fase09-mapas-report.json
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
  py -3 "scripts\regions\hoenn_qa_phase3.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-encontros-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase3.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-encontros-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Falha em encontros ou o piloto foi gerado numa fase antiga.
  echo Relatorio: .blue-work\hoenn-qa-fase09-encontros-report.json
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
  py -3 "scripts\regions\hoenn_qa_phase4.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-campo-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase4.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-campo-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Auditoria de field moves e obstaculos falhou.
  echo Relatorio: .blue-work\hoenn-qa-fase09-campo-report.json
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
  py -3 "scripts\regions\hoenn_qa_phase5.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-story-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase5.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-story-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Inconsistencia de evento, batalha ou RXDATA da historia.
  echo Relatorio: .blue-work\hoenn-qa-fase09-story-report.json
  echo Nenhum save original foi alterado.
  pause
  exit /b 2
)
echo [OK] Eventos autorais de historia e equipes PBS conferidos.
echo [PENDENTE] Seafloor, submarino, clima e puzzles exigem Game.exe real.
echo.
echo [HOENN QA 06/12] Conferindo Sootopolis, Cave of Origin e Rayquaza...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase6.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-clima-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase6.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-clima-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Contratos de crise climatica, Wallace ou Rayquaza falharam.
  echo Relatorio: .blue-work\hoenn-qa-fase09-clima-report.json
  echo As copias anteriores e seus saves permanecem intactos.
  pause
  exit /b 2
)
echo [OK] Eventos de clima e gates de Sky Pillar auditados estaticamente.
echo [PENDENTE] Animacao, clima, audio, puzzles e Game.exe precisam de teste real.
echo.
echo [HOENN QA 07/12] Conferindo 8 ginasios e 8 insignias de Hoenn...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase7.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-ginasios-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase7.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-ginasios-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Um lider, evento, insignia ou treinador PBS esta ausente ou incorreto.
  echo Relatorio: .blue-work\hoenn-qa-fase09-ginasios-report.json
  echo Os saves e as copias de Hoenn anteriores permanecem intactos.
  pause
  exit /b 2
)
echo [OK] Nove eventos de lideres e oito equipes PBS auditados estaticamente.
echo [PENDENTE] Batalhas, insignias, puzzles, time dinamico e Game.exe ainda requerem QA real.
echo.
echo [HOENN QA 08/12] Conferindo Victory Road, Wally, pedras e acesso a Liga...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase8.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-victory-road-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase8.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-victory-road-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Wally, entrada da Liga, PBS ou inventario RXDATA diverge da fase 8.
  echo Relatorio: .blue-work\hoenn-qa-fase09-victory-road-report.json
  echo Copias e saves da QA07 e das regioes anteriores nao foram alterados.
  pause
  exit /b 2
)
echo [OK] Wally, 3 andares de Victory Road, pedras seguras e gatilhos auditados.
echo [PENDENTE] Mapas travessaveis, Boulder/Waterfall, batalha e Game.exe real.
echo.
echo [HOENN QA 09/12] Conferindo Elite Four e Campeao Wallace...
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "scripts\regions\hoenn_qa_phase9.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-report.json"
) else (
  python "scripts\regions\hoenn_qa_phase9.py" --copy ".blue-work\hoenn-qa-fase09" --report ".blue-work\hoenn-qa-fase09-report.json"
)
if errorlevel 1 (
  echo.
  echo [BLOQUEADO] Elite Four, Wallace, RXDATA, PBS ou guards nao conferem.
  echo Relatorio: .blue-work\hoenn-qa-fase09-report.json
  echo Copias e saves QA01-QA08 e das demais regioes continuam intactos.
  pause
  exit /b 2
)
echo [OK] Eventos dos 4 membros da Elite, Wallace e passagem ao Hall auditados.
echo [PENDENTE] Batalhas, times dinamicos, portas, visuais e Game.exe reais.
echo.
echo [OK] Pasta de Hoenn preparada e arquivos conferidos.
echo Perfil de save separado: Hoenn QA Fase09.
echo IMPORTANTE: Na primeira abertura o jogo pode compilar e fechar.
echo Se isso ocorrer, execute este BAT outra vez.
echo O Game.exe ainda deve ser testado dentro do jogo.
start "" /D "%CD%\.blue-work\hoenn-qa-fase09" "%CD%\.blue-work\hoenn-qa-fase09\Game.exe"
exit /b 0
