# Integração de Kanto no jogo principal Decades

**Atualização:** 15/11/2026. **Estado:** código e importador preparados na `main`; **ainda não há certificado de campanha jogável** em uma instalação real Windows/JoiPlay. A importação modifica somente o `game/` local após consentimento do usuário. Não publica mapas de terceiros no GitHub.

## Resultado esperado

`ABRIR_JOGO.bat` inicia o **Game.exe de Decades**, com a Pokédex, motor de batalha, IA, recursos Blue, inventário, PC e perfis de save originais. **Novo Jogo** apresenta:

- **Decades**: executa o novo jogo original, sem mudar spawn, save nem história.
- **Kanto**: se **142 mapas** do pacote atual, PBS, plugin, traduções e arquivos auxiliares estiverem integrados, inicia o **mesmo Game.exe**, no quarto da casa de Pallet. O estado do save nasce como `initial=KANTO/current=KANTO`, sem novo executável ou pasta de save Kanto.
- Sem Kanto instalado, a opção exibe **instalação necessária** e informa o atalho `KANTO_INSTALAR_NO_JOGO.bat`. Não abre outro piloto silenciosamente e não inicia Decades por engano.
- **Johto/Hoenn/Sinnoh** permanecem pilotos experimentais independentes até a futura integração, sem compartilhar save; demais regiões são indisponíveis.

O menu não pede uma segunda escolha regional durante o Story Mode de Decades. `Continue`, os slots do Auto Multi Save, Mystery Gift, outros modos e saves existentes não são migrados automaticamente.

## Instalação automática pelo site — fluxo principal

**Novo comportamento:** ao baixar e executar **`Blue-Story.exe`** no site, o instalador/atualizador usa `scripts/install_game.py` para preparar Decades e, em seguida, chama `scripts/regions/auto_integrate_kanto.py`. Esse processo substitui a necessidade de abrir **`KANTO_INSTALAR_NO_JOGO.bat`** manualmente em instalações limpas.

O inicializador já confere as revisões da `main` a cada abertura; portanto os scripts de integração seguem as atualizações distribuídas pelo próprio EXE. O Python portátil obtido pelo instalador é reutilizado. `ensure_source.py` obtém a fonte FRLG original fixada e verifica o SHA-256 antes da extração; `install_kanto.py` valida o conjunto e instala os mapas, traduções e eventos em `game/`, com backup e rollback. A recompilação é acionada pelo fluxo existente.

Se Kanto já estiver instalado, a instalação automática **não realoca MapIDs**, não sobrescreve RXDATA e não reinicia saves: apenas verifica a integridade. Correções do plugin `KantoPilot.rb` podem ser sincronizadas por hash, com backup. Se um arquivo foi editado, a atualização automática é recusada para não destruir modificações locais.

**Sem internet, fonte indisponível ou pacote legado (13/25 mapas):** a integração é ignorada com aviso, sem bloquear Decades. O status é visível na saída e no log do inicializador. Uma migração de mapas/saves existentes exige procedimento próprio e não deve ser feita apagando marcadores.

**Plataforma:** este fluxo é para o **Blue-Story.exe no Windows**. O Hub isolado não dispara a montagem regional, e o JoiPlay continua com sua distribuição própria. A integração automática de arquivos **não aprova a campanha jogável**; a validação no Game.exe permanece pendente.

## Preparação no seu PC Windows

1. **Caminho manual opcional para manutenção:** faça uma cópia de segurança dos saves e feche completamente `Game.exe`. Use uma instalação com **Decades/Blue íntegro** e Python 3.10+, Git e espaço em disco.
2. Na raiz do repositório, atualize a `main` (`git pull --ff-only origin main`) e, caso necessário, instale Decades/Blue com `INSTALAR_JOGO.bat`.
3. Se não usar o Blue-Story.exe automático, providencie localmente o **Essentials FRLG 21.1 / 1.1** de TheTinfoilTemplar, na revisão/hash verificados pelo projeto, e extraia em:
   `.blue-work/frlg-source/Essentials FRLG/` (incluindo `Data/MapInfos.rxdata`).
4. Execute **`KANTO_INSTALAR_NO_JOGO.bat`** com o jogo fechado. O atalho monta uma cópia isolada atual, faz **dry-run**, pede confirmação e somente depois instala os mapas/recursos. Usa hashes, backups e rollback em caso de erro; `System.rxdata`, `Scripts.rxdata`, `Game.ini`, `mkxp.json`, `Game.exe` e saves não são importados do doador.
5. Quando o atalho informar que os arquivos estão prontos, execute **`ABRIR_JOGO.bat`**, que aplica os plugins Blue, mescla as traduções verificadas e solicita recompilação do Essentials se necessário. Na primeira abertura, a recompilação pode encerrar o processo; abra novamente.
6. Inicie **Novo Jogo → Kanto**. Escolha nome/personagem na introdução regional, os três iniciais físicos no laboratório e teste o percurso de Oak, Viridian, Pewter, todos os oito ginásios, Liga e viagem posterior usando **um slot novo de teste**. A escolha Kanto não apaga os saves existentes, mas o jogador ainda deve evitar gravar sobre o mesmo slot usado por Decades.

### Instalação antiga no mesmo game/

Se `game/Data/blue-kanto-start.txt` já existe, o atalho **não recria nem sobrescreve** MapIDs ou saves. Ele verifica se a versão instalada tem os 142 mapas e dependências necessárias. Um pacote antigo com apenas 13/25 mapas ou arquivos faltantes **é bloqueado**, pois atualizar por cima sem reconciliação pode deixar saves em MapIDs incompatíveis. **Não exclua o marcador manualmente**: preserve a instalação e faça a migração supervisionada em uma cópia descartável/limpa do Blue; um migrador incremental com prova de compatibilidade dos saves ainda precisa ser desenvolvido.

### Regras regionais que não podem ser alteradas

1. A nova partida em Kanto usa a mesma engine Essentials/Blue e nenhum código de combate do FRLG.
2. Uma insígnia local conta **uma única vez** como esmeralda global; não gera badge nativa fictícia de Decades.
3. Level cap, escalonamento de treinadores, IA, EXP compartilhada, Modo Master e pós-jogo Full Power permanecem nas regras Blue, não nos níveis fixos do PBS doador.
4. O acesso por Cut/Surf/Strength e outros obstáculos usa **insígnias locais e os pré-requisitos de Kanto**. Insígnias de outras regiões não servem de atalho. As árvores de Cut usam o efeito visual regional sem alterar a classe Game_Event global.
5. Os Tênis de Corrida são entregues pela mãe **somente após Brock, na passagem para a Rota 3**, uma vez por save regional; não são dados ao começar.
6. O progresso de Kanto fica em `$PokemonGlobal.blue_regions`. **A viagem deixou de depender da Liga:** o agente em **Pallet Town** leva a **Decades**, e o agente em **Cherryhill City** permite voltar a Kanto, mantendo o mesmo save. O NPC de **New Bark Town** fica disponível quando Johto estiver realmente integrada ao jogo principal; pilotos separados não são destinos. As Ligas continuam valendo para conquistas, balanceamento e pós-jogo. Veja [VIAGEM_REGIONAL_LIVRE_NPC.md](VIAGEM_REGIONAL_LIVRE_NPC.md).
7. A regra dos especiais é **oito insígnias locais para a região atual**, não oito esmeraldas globais. Os especiais bloqueados precisam ser depositados com reserva segura de Box ao viajar.
8. Preservar equipe/PC/inventário/saves e a campanha de Decades; antes de disponibilizar uma distribuição integrada, repetir o QA em uma instalação descartável e em save antigo.

## Verificação técnica reproduzível

```powershell
python scripts/regions/install_kanto.py --verify-installed
ruby -c scripts/battle_polish/TitleKanto.rb
ruby -c scripts/battle_polish/RegionStart.rb
ruby -c scripts/regions/KantoPilot.rb
ruby tests/title_kanto_runtime.rb scripts/battle_polish/TitleKanto.rb
ruby tests/region_start_runtime.rb scripts/battle_polish/RegionStart.rb
ruby tests/kanto_running_shoes_runtime.rb scripts/regions/KantoPilot.rb
ruby tests/kanto_cut_tree_runtime.rb scripts/regions/KantoPilot.rb
python -m unittest tests.test_kanto_integrated_locale -v
```

O `--verify-installed` comprova **arquivos de instalação**, não jogabilidade. A CI testa contratos Ruby/Python sem ambiente gráfico; a aprovação de Kanto no projeto principal exige screenshots/evidências de novo jogo, entrada e saída de mapas, tradução PT-BR, Cut, tênis, evolução, todas as insígnias, Liga, save/reload, continuidade com Decades e ausência de regressões. **Não elevar a Barra 2** sem esse aceite real.

## Limites conhecidos

- O GitHub **não contém os RXDATA/tilesets/áudios originais da fonte**, nem o `game/` pessoal. Portanto, a alteração publicada **não pode instalar os 142 mapas no seu computador remotamente**.
- Sem a fonte correta, a montagem aborta e Kanto não é anunciado como disponível na campanha principal.
- Uma migração de um Kanto previamente integrado (13/25 mapas) para o atual catálogo de 142 requer auditoria de MapIDs/saves. O instalador bloqueia a substituição.
- Kanto ainda possui áreas `preview_only` e aceitação integral pendente. Seu menu estar disponível não significa que toda história tenha sido validada jogando.
