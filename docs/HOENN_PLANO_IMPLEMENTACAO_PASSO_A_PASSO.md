# Hoenn — plano definitivo, passo a passo, para integrar a região ao Blue Dessastre Paradoxal

**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Data:** 13/11/2026  
**Tipo:** roteiro técnico por fases para execução no repositório, com critérios de aceite e matriz de cobertura.  
**Status real:** **PLANEJAMENTO**. O registro regional de Hoenn existe como **planned**; não há importador, piloto, mapas, eventos ou trilhas Hoenn verificados como instalados nesta entrega.  
**Meta:** Hoenn de Pokémon Emerald integralmente explorável no mesmo motor de batalha do Blue/Decades, com dados complementares de Ruby/Sapphire e opcionais de ORAS, sem destruir Kanto, Johto, Decades, saves ou músicas.

> **Regra 0:** uma fase documentada, um teste sintético verde, um mapa RXDATA importado ou um botão no menu **não significa que o jogador pode atravessar Hoenn**. Separar a conclusão de engenharia da aprovação no Game.exe real. Não afirmar conteúdo pronto ou 100% sem evidência.

## 1. Documentos vinculantes e decisão de fontes

Antes de começar qualquer fase, ler:

1. [HOENN_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](HOENN_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) — escolha fundamentada e licenças. **Eternal Emerald** é o melhor fangame da lista para consulta; **The Pokémon World Project** é o melhor candidato técnico a arquivos RMXP editáveis; o repertório de **Emerald** é a referência musical.
2. [PLANO_REGIOES_DESSASTRE_V2.md](PLANO_REGIOES_DESSASTRE_V2.md) — regras imutáveis de regiões, 8 insígnias, esmeraldas, HMs, viagem, especiais, equipes e pós-jogo mundial.
3. [CIRCUITO_REGIONAL.md](CIRCUITO_REGIONAL.md) — modelo de auditoria e importação segura utilizado por Kanto.
4. [JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md](JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md) — exigências de inventário exaustivo, eventos, NPCs, itens, caminhos físicos e aceite integral.
5. [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md) e [KANTO_ETAPAS.md](KANTO_ETAPAS.md) — duas barras separadas: núcleo técnico e jogabilidade realmente aprovada.
6. [EDITOR_MUSICAS.md](EDITOR_MUSICAS.md), [KANTO_PLANO_APLICAR_MUSICAS.md](KANTO_PLANO_APLICAR_MUSICAS.md) — BlueMusic, associação por mapa/evento, fade, prioridades e fallback.
7. [KANTO_CODEX_TESTES_E2E.md](KANTO_CODEX_TESTES_E2E.md) — padrão de evidências de Game.exe real, capturas, save/reload e regressão.
8. [README.md](../README.md) e [AGENTS.md](../AGENTS.md) — arquitetura, limitações da instalação local e publicação na main sem sobrescrita forçada.

### 1.1. Política de fontes

| Conteúdo | Referência primária | Limite obrigatório |
|---|---|---|
| Mapas editáveis | [The Pokémon World Project](https://github.com/SocomSeal/The-PMon-World-Project), área Hoenn | Está incompleto segundo seu roadmap de 13/10/2026; licença e permissões devem ser auditadas antes de copiar qualquer arquivo |
| Fidelidade à jornada | Pokémon Emerald; [Eternal Emerald](https://eeveeexpo.com/threads/4871/) como referência técnica/visual | O autor de Eternal Emerald solicita autorização para reutilizar mapas; não presumir direito de cópia |
| Variantes de espécie e conteúdo | Ruby + Sapphire | Fundir exclusivos sem duplicar uma mesma área/ginásio ou causar impossibilidades narrativas |
| Pós-jogo opcional | ORAS: Delta Episode e áreas selecionadas | Fase distinta; não substituir a linha Emerald nem misturar os roteiros |
| Composições/ambientes | Catálogo musical de Emerald e Ruby/Sapphire | Áudio usado e distribuído somente com licença ou autorização apropriada |
| Combate, IA, multiplayer, saves | Exclusivamente Blue/Decades | Nunca copiar a engine de um fangame doador |

**Não versionar ZIPs/ROMs/OSTs de terceiros em um repositório público sem direitos.** A existência dos arquivos no GitHub de outro autor não prova uma licença de redistribuição. Inventariar autor, URL, licença, créditos, direitos de gráficos/sons e autorização para cada família de assets. Sem direito verificado, estudar o recurso e **reconstruir com arte e eventos próprios**.

## 2. Estado do repositório que orienta a implementação

**Já existem:**

- **site/public/data/regions.json**: região HOENN com status planned; circuito DECADES → KANTO → JOHTO → HOENN → SINNOH → UNOVA → KALOS → ALOLA → GALAR → PALDEA.
- **HOENN** já possui as oito chaves de conquista **STONE, KNUCKLE, DYNAMO, HEAT, BALANCE, FEATHER, MIND, RAIN**, com os requisitos de movimento de campo correspondentes.
- **scripts/battle_polish/Regions.rb**: estado regional, ligas, vizinhos, conquistas, permissões, total global e regras de Pokémon especiais.
- **scripts/battle_polish/RegionStart.rb**: início em Decades/Kanto e proteção de Johto por prova de instalação; **não tem Hoenn jogável**.
- **scripts/battle_polish/RegionTravel.rb**: fluxo de viagem e planejamento de depósito de especiais; só possui destinos concretos Decades/Kanto/Johto, sujeitos a verificações. Hoenn ainda **não** tem destino físico aprovado.
- **scripts/battle_polish/RegionalPolicy.rb**, **RegionalCards.rb**, **Balance.rb**, **Campaign.rb**, **TrainerAlbum.rb** e componentes da Pokédex/Habitat: reutilizar e estender sem criar lógica paralela.
- **scripts/battle_polish/TitleKanto.rb**: menu experimental Testar Kanto e Testar Johto, preservando os comandos originais. **Testar Hoenn** só poderá ser acrescentado com um lançador isolado e testado, sem modificar os índices nativos.
- **scripts/music/BlueMusic.rb** e fluxos de música existentes: não substituí-los.
- **scripts/regions/** contém ferramentas de Kanto e preparação de Johto, que servem de **padrão**, mas não são importadores genéricos de Hoenn.
- **tests/** contém regressões Python/Ruby/áudio/menu; a pasta local **game/** fica fora do Git.

**Não existem comprovados nesta auditoria:** scripts/regions/audit_hoenn.py, stage_hoenn.py, pilot_hoenn.py, install_hoenn.py, arquivo de origem Hoenn com checksums/MapIDs, mapas Hoenn reais integrados, música Hoenn versionada com direitos, ou um botão Testar Hoenn. Todos são entregáveis futuros.

**Restrição adicional:** Johto reservou e validou em parte de sua infraestrutura **MapIDs 600–999**. Os mapas existentes de Decades, Kanto e Johto precisam ser enumerados na instalação efetiva. **Não escolher automaticamente 1000+ nem copiar a reserva de Johto**: primeiro confirmar o suporte de leitura/escrita da engine e das ferramentas a MapIDs com quatro ou mais dígitos; caso não suportem, projetar convenção de nomes ou expansão do importador e migrar/testar com segurança.

## 3. Regras imutáveis de jogabilidade

1. **Região inicial livre:** Hoenn poderá ser escolhida na nova partida **somente depois** que o início e o roteiro mínimo estiverem funcionando e auditados. Início em Hoenn é diferente de chegada por viagem.
2. **Introdução:** adaptar a abertura Emerald: chegada de caminhão, entrada na **casa de Littleroot**, mãe, quarto e relógio quando aplicável, encontro com Professor Birch e escolha entre **Treecko, Torchic e Mudkip**. O jogador deve começar dentro do cenário correto, nunca aparecer solto do lado de fora por erro de spawn. A posição inicial é uma coordenada real auditada.
3. **Campanha principal:** Emerald é a linha do tempo padrão; o rival é Brendan ou May conforme o personagem escolhido. Os oito líderes são **Roxanne, Brawly, Wattson, Flannery, Norman, Winona, Tate & Liza e Juan**. Em Emerald, **Wallace é o Campeão** e **Steven** constitui uma batalha especial do pós-jogo. Variantes Ruby/Sapphire e ORAS são perfis/documentos separados, não oito ginásios novos.
4. **Conquistas:** cada insígnia inédita de Hoenn acrescenta **exatamente uma unidade** à progressão global de esmeraldas existente, sem contagem duplicada no save/revanche/recarga. A tabela de conquistas **locais** nunca é substituída pelo total global.
5. **Balanceamento:** preservar equipes oficiais como **dados-base**; o Blue calcula níveis, BST, IA, poder de golpes e composição aplicável **em memória na batalha**, inclusive a configuração Master existente. Manter a regra de reforço de quatro Pokémon/cobertura de fraqueza nos treinadores Master quando suportada pelo módulo atual, sem sobrescrever o registro-base do treinador.
6. **Dois cartões de treinador:** um apresenta as **oito insígnias de Hoenn**; outro apresenta o total e as conquistas de **todas** as regiões. Ambos leem o mesmo save do Blue.
7. **Viagem:** ao finalizar a **Liga de Hoenn**, desbloquear **Johto e Sinnoh** conforme o circuito; se ainda não instaladas, mostrar como desbloqueadas **mas em preparação**, sem teleportar. O **NPC regional principal fica em Littleroot**, cidade inicial, e respeita a Liga concluída e os destinos reais. Um atalho na saída da Liga, se existir, deverá usar o mesmo serviço, sem substituir o NPC de Littleroot.
8. **Pokémon especiais:** lendários, míticos, Ultra Beasts e Paradoxos ficam impedidos de ocupar a party em Hoenn até obter **as oito insígnias locais**. Ao viajar, reservar vagas do PC, depositar sem perda e cancelar a viagem se Box cheia ou equipe ficar inválida; PC, capturas, trocas, presentes e recarga devem respeitar o mesmo bloqueio. O Hub de Batalha não herda a restrição da campanha.
9. **HMs locais:** cada uso no mapa depende de movimento/ferramenta e insígnia **de Hoenn**; obter insígnias de Johto ou Decades não substitui requisitos locais.
10. **Mesmo save e engine:** não substituir Game.exe, Scripts.rxdata, System.rxdata, MapInfos.rxdata, Tilesets.rxdata ou toda a pasta game/Data; não remover ou mover MapIDs usados por saves antigos.
11. **Pós-jogo mundial:** equipes canônicas definitivamente mais fortes somente depois das **dez Ligas do circuito** concluídas no save; Hoenn isoladamente não ativa esse modo.
12. **NPCs/eventos/itens:** tudo deve ser verificado contra a região de referência, com histórico de status por mapa; conteúdo ainda sem fonte/implementação deve aparecer como pendência explícita.

### 3.1. Oito insígnias e liberação de movimentos no cenário

| Ordem | Líder | Cidade | Chave Blue | Habilidade de campo associada no catálogo atual |
|---|---|---|---|---|
| 1 | Roxanne | Rustboro | STONE | Cut |
| 2 | Brawly | Dewford | KNUCKLE | Flash |
| 3 | Wattson | Mauville | DYNAMO | Rock Smash |
| 4 | Flannery | Lavaridge | HEAT | Strength |
| 5 | Norman | Petalburg | BALANCE | Surf |
| 6 | Winona | Fortree | FEATHER | Fly |
| 7 | Tate & Liza | Mossdeep | MIND | Dive |
| 8 | Juan | Sootopolis | RAIN | Waterfall |

Observação: esta tabela se refere ao **uso fora de batalha**. A posse dos HMs/itens, a possibilidade de aprender o golpe e as regras da versão Emerald precisam ser checadas no evento real; não conceder automaticamente o HM apenas por derrotar um líder.

## 4. Modelo de dados obrigatório: nunca deixar NPC, item ou mapa invisível ao planejamento

Criar um **registro por mapa físico**, com chaves simbólicas independentes do número RMXP real. Não assumir que um mapa nomeado no doador tenha todos os NPCs e interiores. A fonte de verdade é a área canônica + os eventos efetivamente compilados.

**Campos por mapa (esquema conceitual, não importador já existente):**

~~~json
{
  "region": "HOENN",
  "map_key": "HOENN_LITTLEROOT_PLAYER_HOUSE_1F",
  "canonical_source": "EMERALD",
  "source_project": null,
  "source_map_id": null,
  "destination_map_id": null,
  "map_dimensions": null,
  "tileset_id": null,
  "exits": [],
  "collision_validated": false,
  "npcs": [],
  "trainer_events": [],
  "story_events": [],
  "visible_items": [],
  "hidden_items": [],
  "interactables": [],
  "encounter_methods": [],
  "audio_keys": [],
  "permissions": [],
  "evidence": [],
  "status": "PENDING_INVENTORY"
}
~~~

**Campos por entidade:** id estável (ex.: HOENN_LITTLEROOT_MOTHER_TALK), mapa, x/y, direção, sprite e origem, texto adaptado PT-BR, condições (flags/horário/item/insígnia), páginas, tipo de gatilho (Action/Touch/Autorun/Parallel), pré-requisitos, recompensa, flags de uso único, estados de derrota/vitória, links a mapas/PBS/itens/músicas, evidência de teste e licença de assets.

### 4.1. O que o inventário de cada mapa precisa cobrir

- Todos os **interiores**: casas, andares, lojas, Poké Marts, Centros Pokémon, laboratórios, hotéis, portos, museus, elevadores, ginásios, bases, cavernas, salas escondidas e seus respectivos retornos.
- Todos os NPCs: moradores, treinadores, rivais, assistentes, personagens de missão, comerciantes, Day Care, PC, navios, Pokémon que bloqueiam passagem, NPCs que se movem, mudanças após Liga e interações por horário.
- Todos os objetos: placas, TVs, armários, máquinas, computadores, puzzle de pedras/força, árvores Cut, pedras Rock Smash, correntes marítimas, cachoeiras e pontos de mergulho.
- Todos os itens: no chão, ocultos, dados por NPC, vendidos, obtidos em troca/combate/competição e recompensas únicas; registrar tanto ID de item válido no Blue quanto condição de coleta.
- Todas as batalhas: tipo e nome do treinador, posição, linha de visão, variantes, derrotas, rematches, equipes-base, duplas, rival, Magma/Aqua, ginásios, Elite, lendas e selvagens.
- Todas as travas: encontros que exigem Surf/Dive/Waterfall/Strength, badges, flags, item-chave, navio ou clima, com **teste de retorno para evitar softlock**.
- Todos os áudios: BGM do mapa, BGS ambiente, SE de ação, música de batalha/vitória, ME após evento confirmado, fade e restauração.
- Todas as variantes: Emerald canônico, Ruby/Sapphire exclusivos, ORAS opcional, alterações de pós-Liga; nenhuma mistura sem marcar a fonte e a variante.

**Condição de completude:** para todo mapa e cada categoria, comparar **expected vs actual**, registrar itens desconhecidos como **BLOCKED_INVENTORY**, e nunca trocar desconhecido por zero. Se a fonte não contiver eventos ou NPCs, eles devem ser **reconstruídos e testados**, não presumidos.

## 5. Matriz geográfica de Hoenn — cobertura integral obrigatória

**Incluir todas as rotas 101 a 134 (terrestres, marítimas e áreas subaquáticas correspondentes), além de todas as cidades, andares de interior e localidades especiais da campanha Emerald.** A tabela define **o que auditar e implementar**, não confirma que o doador possui esses mapas.

| Setor | Locais e mapas a conferir | Foco de interação |
|---|---|---|
| Sudoeste/início | Littleroot, Route 101, Oldale, Routes 102–104, Petalburg, Petalburg Woods, Rustboro, Route 115/116, Rusturf Tunnel | Caminhão, casa, Birch, iniciais, rival, Wally, Devon, Roxanne, itens/portas, Cut |
| Costa oeste/ilhas | Routes 105–109, Dewford, Granite Cave, Abandoned Ship/Sea Mauville (variante), Slateport, Museu Oceânico, Stern, porto, SS Tidal | Surf e transporte marítimo, Brawly, Steven, Team Aqua/Magma, cavernas e interiores |
| Centro/planícies | Routes 110–118, Mauville, Cycling Road, New Mauville, Verdanturf, Fiery Path, Desert, Trick House, Day Care | Wattson, bateria, bicicleta, Rock Smash, Strength, itens de rota, quebra-cabeças e serviços |
| Vulcão/norte | Route 111, 112, 113, 114, 115, 117, 118, Fallarbor, Meteor Falls, Mt. Chimney, Jagged Pass, Lavaridge, Fiery Path | Meteorite, Magma/Aqua, cinzas, calor, Flannery, retorno a Norman |
| Floresta/leste | Routes 118–123, Mauville leste, Weather Institute, Route 119, Fortree, Route 120, Lilycove, Route 121, Mt. Pyre, Safari Zone | Castform, Kecleon/Devon Scope, Winona, time rival, Mega/Team bases, marés/chuva conforme roteiros |
| Nordeste/costa | Route 122, 123, 124, 125, 127, Mossdeep, Shoal Cave, Space Center, Meteor Falls acessos remotos | Tate & Liza (dupla), equipes, Dive, marés, itens e rotas marítimas |
| Mar profundo | Routes 124–134, pontos de Dive/submersos, Seafloor Cavern, Route 126, Sootopolis, Cave of Origin, Sky Pillar, Pacifidlog, Sealed Chamber | Correntes, Surf/Dive, Kyogre/Groudon/Rayquaza, crise climática, Juan, submarino, travessias bidirecionais |
| Liga/pós-jogo | Route 128, Ever Grande, Victory Road, Liga, Hall of Fame, Battle Frontier, Artisan Cave, Trainer Hill, Mirage Tower, Desert Underpass, Desert Ruins/Island Cave/Ancient Tomb, Southern Island (se autorizado) | Elite Four, Wallace, Steven, símbolos, pós-Liga, enigmas, rematches, NPCs e recompensas |

**Notas obrigatórias sobre nomes e variantes:**

- **Abandoned Ship** é a referência Emerald para a área marítima; **Sea Mauville** é variação ORAS, não um segundo local automaticamente idêntico.
- Battle Frontier é pós-jogo de Emerald e exige sistemas próprios; não chamar de implementada simplesmente por haver mapas.
- Sky Pillar, Sealed Chamber, três Regis, Shoal Cave, Mirage Tower, Safari Zone, Trick House e concursos não devem ser esquecidos.
- As faixas de rotas da tabela se sobrepõem porque determinadas áreas integram **mais de um arco narrativo**. Cada rota e cada sala deve receber apenas um registro físico por variante, evitando duplicação de mapas e NPCs.
- Quando os dados de Emerald não incluírem um local que existe apenas em outra versão, marcar **OPTIONAL_VARIANT**, jamais tratá-lo como falha obrigatória do Emerald.
- Gerar, na Fase 02, uma **lista expandida exaustiva** por MapKey, com casa por casa, sala por sala, trainers e itens identificados. A tabela acima é matriz de **cobertura macro**, não esse inventário completo.

## 6. Arquitetura e arquivos de trabalho

### 6.1. Preservar e ampliar (existem na main)

- site/public/data/regions.json
- scripts/battle_polish/Regions.rb
- scripts/battle_polish/RegionStart.rb
- scripts/battle_polish/RegionTravel.rb
- scripts/battle_polish/RegionalPolicy.rb
- scripts/battle_polish/RegionalCards.rb
- scripts/battle_polish/TitleKanto.rb
- scripts/battle_polish/Balance.rb
- scripts/battle_polish/TrainerAlbum.rb
- scripts/music/BlueMusic.rb
- scripts/regions/audit.py, stage.py, pilot.py, install_kanto.py (consultar como padrão de segurança, **não copiar sem adaptação**)
- scripts/regions/audit_johto.py, stage_johto.py, install_johto.py (consultar guardas; a importação Johto para game/ ainda é bloqueada na documentação)
- testes Ruby/Python/Playwright já existentes em tests/ e o workflow de regressão.

### 6.2. Criar ao longo das fases (todos os caminhos abaixo são PROPOSTOS)

~~~text
docs/
  HOENN_ETAPAS.md
  HOENN_CATALOGO_MAPAS_NPCS_ITENS_EVENTOS.md
  HOENN_MUSICAS_MAPEAMENTO.md
  HOENN_TESTES_E2E.md
data/
  regions/
    hoenn-source.json
    hoenn-map-plan.json
    hoenn-events.json
    hoenn-encounters.json
    hoenn-trainers.json
    hoenn-item-registry.json
    hoenn-phase04.json ... hoenn-phase14.json
    hoenn-release-proof.schema.json
  hoenn-music.json
  hoenn-music-rules.json
scripts/
  regions/
    audit_hoenn.py
    inventory_hoenn.py
    plan_hoenn.py
    stage_hoenn.py
    build_hoenn_events.py
    pilot_hoenn.py
    install_hoenn.py
    verify_hoenn.py
    export_hoenn.py
    HoennPilot.rb
    HoennStory.rb
    HoennLeague.rb
    HoennPostgame.rb
  music/
    audit_hoenn_music.py
    compile_hoenn_music.py
    install_hoenn_music.py
tests/
  test_hoenn_*.py
  hoenn_*_runtime.rb
  test_title_hoenn.py
  hoenn_gameplay_e2e/ (ferramentas somente se executáveis no ambiente real)
HOENN_JOGAR_EXPERIMENTAL.bat
HOENN_INSTALAR_NO_JOGO.bat
.blue-work/hoenn-source/          (ignorado pelo Git)
.blue-work/hoenn-pilot/           (ignorado pelo Git)
.blue-work/hoenn-reports/         (ignorado pelo Git)
.blue-backups/hoenn-*/           (ignorado pelo Git)
~~~

**Obrigação de cada novo script:**
- Suportar **auditoria/dry-run sem gravações** e escrita apenas sob comando explícito, quando pertinente.
- Proteger caminhos relativos, symlinks, extração de ZIP, arquivos fora do projeto, conflito de IDs, mudança de arquivo desde a auditoria (hash), cópia por cima de recurso existente.
- Registrar origem SHA-256, map_key, MapID fonte/destino, recurso e versão da ferramenta.
- Executar importação em cópia isolada, com backups, escrita atômica, rollback, segunda execução idempotente e relatório de arquivos criados/alterados.
- Não executar scripts Ruby importados de terceiro durante a **auditoria**; ler Marshal/RXDATA como dados através de leitores seguros. Converter os comandos de evento a APIs próprias e **validar o arquivo compilado no Game.exe real**.
- Construir tabelas PBS novas por **mesclagem**, sem substituir Pokémon, golpes, tipos, habilidades, treinadores, encontros ou preferências de outra região.

### 6.3. Registro técnico de mapeamento (exemplo, valores não preenchidos)

~~~json
{
  "schema": 1,
  "region": "HOENN",
  "status": "PLANNED",
  "source": "PENDING_VERIFIED_SOURCE",
  "source_sha256": null,
  "source_rights_confirmed": false,
  "installed": false,
  "maps": {
    "HOENN_LITTLEROOT": {
      "source_map_id": null,
      "destination_map_id": null,
      "physical_asset": null,
      "events_verified": false,
      "native_gameplay_verified": false
    }
  }
}
~~~

**Nunca escrever um ID fictício em MapInfos.rxdata, no título de New Game, no Portal ou no NPC de viagem como se o mapa existisse.** As chaves são simbólicas; números concretos só depois da auditoria e da reserva segura no game/ real.

## 7. Passo técnico obrigatório — executar em TODA fase antes do mapa seguinte

### 7.1. Pré-requisitos e linha de base (PASSO 00 permanente)

1. Atualizar/sincronizar a main por fast-forward, registrar commit e resultados de teste **antes** de mexer.
2. Inventariar a instalação real **game/** e suas dependências, inclusive MapInfos, Tilesets, scripts, PBS, gráficos, áudio, slots de saves, MapIDs e a configuração de plugins. Se game/ não estiver disponível, **bloquear os testes de jogo real**; não fabricar instalação.
3. Guardar backup separado e hashes de todos os arquivos a tocar, além de amostras de saves antigos Decades/Kanto/Johto. Não usar reset --hard/clean sobre arquivos de usuário.
4. Verificar disponibilidade/licenças de mapas, gráficos, músicas, NPC sprites e fontes textuais. Não tratar direito desconhecido como aprovado.
5. Reproduzir a suíte atual Python/Ruby/Playwright e o Game.exe real quando disponível. Anotar falhas anteriores; não esconder regressão.
6. Aplicar mudanças **em piloto isolado**. Só promover para o jogo-mestre por um instalador com verificação, diff, confirmação, backup e rollback testado.
7. Para cada erro: corrigir, repetir a suíte e anotar qual fase ficou pendente. Testes unitários não substituem gameplay no motor.

### 7.2. Ciclo por cada mapa

1. MapKey e nome canônico → localizar mapa editável autorizado.
2. Conferir tamanho, tileset, passabilidade, panorama, autotiles e dependências.
3. Reservar MapID livre e remapear cada referência (transfers, respawn, Fly, Dive, conexões, coordenadas, efeitos de clima, common events).
4. Construir/associar todos os **interiores e suas portas de ida e volta**; garantir que o player não surge dentro de parede.
5. Construir páginas de NPC, treinador e evento com flags/itens/sprites próprios.
6. Registrar itens visíveis/ocultos e lojas; impedir recompensa duplicada por conversa repetida, save/load e revanches.
7. Compilar/adaptar encontros e treinadores PBS, chamando o **mesmo motor de batalha**.
8. Aplicar BGM/BGS/ME/SE **quando houver áudio autorizado**, de acordo com as condições reais dos eventos.
9. Validar colisões, anti-softlock, retorno após derrota, encontro, captura, PCs, saves, warps e fallback musical.
10. Atualizar o manifesto e os resultados no portal somente **quando o mapa existir e tiver dados reais**.

### 7.3. Contratos de eventos e treinadores

- Um evento de batalha deve usar a API de Essentials/Blue **efetivamente identificada na instalação**, com PBS válido, recompensa original quando aplicável, música regional e estados vitória/derrota/cancelamento. Não invocar engine nem plugins de Eternal Emerald/World Project.
- O treinador deve acionar por **linha de visão/proximidade** quando o roteiro assim exigir; não depender apenas do jogador apertar interação. Persistir estado derrotado e permitir revanche somente quando definida.
- Batalhas **duplas** são obrigatórias em eventos que exijam duplas, especialmente **Tate & Liza**; não transformá-las em dois encontros singles que concedem insígnias separadas.
- Definir tabela canônica de equipes por **identidade do NPC, versão, local e encontro**, com IDs únicos; variantes de Ruby/Sapphire e da dificuldade Master são derivadas em tempo de execução.
- Antes de adicionar qualquer espécie ou golpe no PBS, verificar sua existência no catálogo real do Blue. Rejeitar IDs inventados.
- Em Master, usar as configurações correntes de composição e cobertura de fraqueza do Blue em vez de inventar outro escalonador de níveis.
- Nenhum comando Autorun/Parallel pode ficar em loop após a cutscene; flags são persistidas antes de repetir um evento. Testar falha, reload e interrupção.

### 7.4. Itens, encontros e condições ambientais

- Registrar por método **Land, Water/Surf, Old/Good/Super Rod, Rock Smash, cavernas, horários, clima e outros mecanismos realmente suportados pelo Essentials instalado**.
- Somar e validar pesos **por tabela/método**, com raridade e níveis coerentes; combinar exclusivos Ruby/Sapphire em locais/habitats apropriados sem eliminar a ecologia Emerald.
- Lendários e criaturas de história devem ser eventos/quests guardados, não encontros aleatórios comuns.
- Capturas, evolução, presentes e trocas que envolvam especiais precisam respeitar o **bloqueio local de oito insígnias**, mas sem descartar Pokémon.
- Movimentos de campo **Surf, Dive, Waterfall, Rock Smash, Cut, Strength, Flash, Fly** devem ter pré-condições por badge e item, retorno seguro e bloqueio sem insígnia.
- Correntes no mar: testar movimento forçado, destino de cada fluxo e possibilidade de retorno; não ativar automaticamente com evento parado.
- Dive: manter mapa de superfície e submerso com correspondência auditada, entrada/saída em posição válida, efeitos gráficos e restauração de BGM/clima; Dive não é apenas um teleport estático.
- Clima: chuva, sol e transições narrativas da crise de Hoenn não podem alterar permanentemente o clima de outras regiões nem carregar state global incorreto.

## 8. As 16 fases — executar em ordem, sem confundir protótipo e região pronta

Cada fase deve publicar **código próprio + dados/manifestos + testes + documentação de pendências**, sem incluir recursos protegidos sem autorização; fazer **dry-run**, verificar, gerar evidências e só então considerar aprovada. Os mapas externos permanecem fora do Git quando os direitos não autorizarem distribuição.

### FASE 01/16 — Auditorar fonte e direitos reais

**Fazer:**
1. Inventariar The Pokémon World Project por commit/versão; examinar pastas Hoenn Data, Graphics, PBS, Audio **como dados**, sem rodar seus scripts.
2. Auditar também Eternal Emerald como referência; checar autorização expressa se algum mapa específico for incorporado.
3. Confirmar arquivos de origem/mapas editáveis, hash SHA-256, licença por tileset, sprites e sons, dependências e lacunas do pacote.
4. Criar **data/regions/hoenn-source.json**, **scripts/regions/audit_hoenn.py** e teste com fixtures sintéticas. Falta de fonte/permissionamento produz status **BLOCKED_SOURCE** sem criar mapas falsos.
5. Fazer matriz baseline de Decades/Kanto/Johto, índices ocupados e execução dos testes antigos.

**Aceite A:** a auditoria somente leitura é reproduzível, reporta faltas e conflitos sem executar scripts de origem; a fonte selecionada tem permissão de uso pertinente e versão/hash confirmados. **Aceite B:** conferência real dos arquivos e credenciais da origem, sem alegar gameplay.

### FASE 02/16 — Inventário total de Hoenn e eventos de cada mapa

**Fazer:**
1. Cruzar Emerald, Ruby/Sapphire e inventário doador. Criar um registro para **cada cidade, Route 101–134, interior, caverna/andar, mar, área subaquática e área de pós-jogo**.
2. Construir **HOENN_CATALOGO_MAPAS_NPCS_ITENS_EVENTOS.md** + registros estruturados. Para cada mapa registrar NPCs, posições, sprites, itens escondidos, treinadores, diálogos, lojas, cutscenes, puzzles, entradas e saídas.
3. Enumerar todas as dependências de CommonEvents, switches, variáveis, self-switches, referências de MapIDs, TrainerTypes, weather, Surf/Dive e sons. Marcar conflitos de versões e conteúdos ainda sem evidência.
4. Criar relatórios expected/actual por área e tipo; zero itens só pode ser registrado se a fonte realmente confirmar zero.

**Aceite A:** inventário completo conhecido ou explicitamente bloqueado, sem converter UNKNOWN em DONE. **Aceite B:** amostragem dos mapas e interiores no editor/RMXP e comparação com referência autorizada; nenhuma cobertura não auditada chamada de completa.

### FASE 03/16 — Planejador de IDs, mapas conectados e piloto de Hoenn

**Fazer:**
1. Implementar **plan_hoenn.py**, **stage_hoenn.py**, **verify_hoenn.py** e **pilot_hoenn.py** utilizando o padrão seguro de Kanto/Johto.
2. Alocar IDs somente após conferir mapas Decades/Kanto/Johto; remapear tilesets/autotiles, MapInfos, conexões, eventos Transfer Player, variáveis, common events, respawn, Town Map, Fly e pontos Dive.
3. Criar áreas de origem/destino distintas, com hashes e rollback do staging; não copiar arquivos-banco inteiros do doador. Configurar fontes de gráficos autorizadas e passabilidade no editor.
4. Criar testes de mapa órfão, destino inexistente, porta unidirecional, tile bloqueado de spawn, warp recursivo, número de dígitos do MapID e colidência de caminho.
5. Criar **piloto isolado** e perfil de save Hoenn; o jogo principal não muda. Inserir **Testar Hoenn** após as opções de Kanto e Johto, apenas quando lançador e piloto reais existirem; na ausência, avisar e voltar ao menu.

**Aceite A:** geometria preparada com IDs e dependências verificadas, testes de segurança e nenhuma mudança em game/. **Aceite B:** Game.exe do piloto caminha entre dois mapas reais, entra e sai de interiores e salva/recarrega sem mudar Decades/Kanto/Johto. Somente geometria **não** encerra o critério de campanha.

### FASE 04/16 — Littleroot, introdução, Birch e Oldale

**Mapas mínimos:** caminhão/área de chegada, casa do jogador 1F/2F, Littleroot, laboratório de Birch, vizinhos, Route 101, Oldale, Routes 102/103 e interiores pertinentes.

**Fazer:** selecionar origem HOENN, sprites/personagem, mãe/relógio, encontro de Birch, escolha Treecko/Torchic/Mudkip, rival, primeira batalha selvagem e primeiros NPCs/itens/lojas, Poké Balls/Pokédex quando o roteiro exigir. Adaptar textos PT-BR próprios com catálogo de origem. Criar marcador de casa para **new game** distinto do marcador de chegada da viagem à cidade inicial.

**Aceite:** iniciar corretamente no cenário de abertura, atravessar quarto/porta/rua, concluir escolha e tutorial, alcançar Oldale, entrar nos interiores, lutar/capturar pelo motor Blue, salvar/recarregar e regressar, sem iniciar em mapa externo ou perder Decades.

### FASE 05/16 — Petalburg, Rustboro, Roxanne e primeira insígnia

**Mapas:** Route 102/104, Petalburg, casa/ginásio de Norman (ainda sem desafiar o líder), Wally e família, Petalburg Woods, Rustboro, Route 115/116, Rusturf Tunnel, Devon Corporation, ginásio e interiores.

**Fazer:** sequência do Wally e Ralts conforme o enredo Emerald, encontros da floresta, equipe Aqua/Magma em eventos adequados, primeiro confronto com Roxanne, Stone Badge única, recompensas/TMs, habilitação local de Cut. O acesso a Norman **permanece condicionado** à progressão, não libera quinta insígnia já.

**Aceite:** chegar pela rota física, vitória/derrota em Roxanne, Stone soma exatamente **uma esmeralda global**, portas e interiores funcionam, treinadores chamam Blue, saves e reentrada não duplicam a conquista.

### FASE 06/16 — Dewford, Brawly e Granite Cave

**Mapas:** Routes 105–109 conforme travessia por barco, Dewford e casas, ginásio, Granite Cave e andares, navio e pontos de entrada/saída.

**Fazer:** transporte com Mr. Briney e retorno seguro, entrega de carta para Steven conforme cronologia, NPCs e itens da ilha, pesca/encounters pertinentes, luta Brawly e Knuckle Badge, condição local de Flash. O barco não deve transportar o player para um MapID ainda não instalado.

**Aceite:** Dewford acessível e retornável, cavernas sem softlock, Brawly com uma única recompensa, carta/quest persiste após reload.

### FASE 07/16 — Slateport, Mauville e Wattson

**Mapas:** Slateport, mercado/porto, Museu Oceânico, Slateport Beach, Routes 109–110, Trick House, Cycling Road, Mauville, Route 117, Verdanturf, Rusturf Tunnel, Day Care, New Mauville conforme desbloqueios.

**Fazer:** entrega de encomendas ao Captain Stern, ataques de equipes, rival, bicicleta/rotas cicláveis, quebra-cabeças, treinadores, encontros, serviço do Day Care, Wattson/Dynamo Badge, Rock Smash local. Conservar travas de New Mauville e demais tarefas que só existem depois.

**Aceite:** história do museu completa, todos os serviços e entradas pertinentes auditados, Wattson registra uma só conquista e caminho até Verdanturf pode ser percorrido sem cortar história.

### FASE 08/16 — Meteor Falls, Mt. Chimney, Lavaridge e Flannery

**Mapas:** Routes 111–115, Desert, Fiery Path, Fallarbor, Route 113 com cinzas, Route 114, Meteor Falls, Cable Car, Mt. Chimney, Jagged Pass, Lavaridge e interiores/gym.

**Fazer:** registrar missão Meteorite, encontros com Magma/Aqua e líderes na ordem Emerald, teleférico/portões, eventos do vulcão, puzzles geográficos, Flannery e Heat Badge, Strength local. Desert só acessível conforme requisito pertinente; não abrir por engano uma saída que salte o ginásio.

**Aceite:** missão Meteorite e passagem Mt. Chimney → Lavaridge com estados consistentes; Flannery concede uma única HEAT; testar derrota, save durante missão e retorno às rotas.

### FASE 09/16 — Retorno a Petalburg, Norman e Surf

**Mapas:** acesso de retorno por Rusturf/Petalburg e respectivas rotas/portas; revalidar interiores que agora mudam de estado.

**Fazer:** habilitar Norman quando eventos prévios estiverem realmente concluídos, integrar seu time PBS-base e rematches, registrar Balance Badge, receber/permissão de Surf de acordo com a história, abrir trajetos marítimos e interiores vinculados sem tornar a travessia obrigatória antes da hora.

**Aceite:** Norman bloqueado antes e acessível depois; uma BALANCE por save; Surf permitido em Hoenn com badge + movimento/ferramenta e bloqueado sem badge; nenhuma mudança nas condições de Surf de outras regiões.

### FASE 10/16 — Weather Institute, Fortree e Winona

**Mapas:** Routes 118–120 e conexões, Weather Institute, Fortree, ginásio, rotas de chuva, pontes, áreas com Kecleon e interiores.

**Fazer:** travessia de Surf, conflito Magma/Aqua do Weather Institute, recompensa Castform, rival e encontros, evento Devon Scope/Kecleon, Winona/Feather Badge, Fly local. Conferir passabilidade em pontes com altura aparente, travessia de vegetação e clima; não tratar chuva como estado global eterno.

**Aceite:** Weather Institute só conclui após sequência válida, Kecleon desbloqueado pelo item/evento correto, Fly respeita insígnias e mapa de destino descoberto, Winona soma uma única FEATHER.

### FASE 11/16 — Lilycove, Mt. Pyre e bases Magma/Aqua

**Mapas:** Routes 121–123, Safari Zone, Lilycove e shopping, Mt. Pyre/andares/superfície, bases dos times, cavernas e portos ligados ao enredo.

**Fazer:** integrar rival em Lilycove, batalhas de Magma/Aqua, itens/eventos do Mt. Pyre, Blue Orb/Red Orb conforme o arco Emerald, furtividade/entradas das bases, cutscenes, NPCs condicionais, lojas e rotas opcionais. Distinguir a narrativa dupla Emerald de variantes Ruby/Sapphire; nunca gerar duas versões contraditórias do mesmo evento no save.

**Aceite:** sequência Mt. Pyre → base(s) não pode ser pulada nem ficar eternamente bloqueada; itens-chave/eventos persistem e não duplicam; saída segura após derrota e salvamento entre cenas.

### FASE 12/16 — Mossdeep, Tate & Liza e mergulho

**Mapas:** Routes 124–125/127 conforme conexão, Mossdeep, Space Center, Shoal Cave, gym, porto e interiores.

**Fazer:** adaptar evento do Space Center com Team Magma, dupla de líderes Tate & Liza, Mind Badge **única**, recebimento de Dive/condição de uso após a sétima insígnia, treinadores do mar, Surf, pesca, cavernas e sistema de maré de Shoal Cave se implementado.

**Aceite:** Tate & Liza disparam uma **batalha dupla real do Blue**, e não dois singles; MIND contabilizada uma vez; Dive só habilita campo quando as condições da Hoenn forem satisfeitas.

### FASE 13/16 — Mar submerso, crise climática, Sootopolis e Juan

**Mapas:** Routes 124–134, setores submersos correspondentes, Route 126/Sootopolis, Seafloor Cavern, Cave of Origin, Sky Pillar, Pacifidlog, correntes e áreas opcionais de mar.

**Fazer:** integrar Surf/Dive/emersão (entradas e saídas correspondentes), correntes da Route 132–134, submarino e Seafloor Cavern, arcos Kyogre/Groudon, chuva/sol, Rayquaza, fim da crise, abertura de Sootopolis, ginásio de Juan, Rain Badge e Waterfall. Mapas de lendários dependem de flags e **batalhas reais da mesma engine**. Proteger o clima do Decades/Kanto/Johto.

**Aceite:** percorrer todas as rotas marítimas e submersas instaladas sem softlock; Dive volta ao ponto apropriado; as mudanças de clima e Rayquaza resolvem a história; Juan/Rain única; save/reload no meio da crise preserva estado coerente.

### FASE 14/16 — Ever Grande, Elite Four, Campeão e pós-jogo

**Mapas:** acesso a Ever Grande, Waterfall, Victory Road/andares, Liga, salas de Sidney, Phoebe, Glacia, Drake e Wallace, Hall of Fame, pontos de retorno, Battle Frontier e acessos relevantes.

**Fazer:**
1. Exigir oito insígnias locais e percurso válido, construir Victory Road, rival/Wally quando aplicável e Elite Four com **Sidney, Phoebe, Glacia e Drake**, seguidos do Campeão **Wallace**.
2. Implementar derrotas, cura/PC/loja conforme local oficial, sequência de salas, salvamento, Hall of Fame e finalização **idempotente** da Liga.
3. Ao concluir a Liga pela primeira vez, gravar HOENN em ligas concluídas, liberar **Johto + Sinnoh**, atualizar cartões, menu e portal, e ativar **o NPC de viagem em Littleroot** (somente com ponto seguro e destino realmente instalado).
4. Cobrir conteúdo Emerald opcional/pós-jogo em catálogo separado: **Steven (Meteor Falls), Battle Frontier e seus símbolos, Regis/Sealed Chamber, Mirage Tower, Desert Underpass, Southern Island somente se houver acesso autorizado, concursos, Safari, Feebas, miragens e demais serviços**. O nível de completude de cada instalação depende de evidência individual.
5. Não colocar os times "mais fortes do mundo" no primeiro clear de Hoenn; só selecionar equipes canônicas documentadas quando o modo mundial de dez Ligas for ativado.

**Aceite:** Elite Four → Wallace → Hall of Fame dispara a Liga **uma vez**, permite permanecer em Hoenn ou viajar quando destino estiver apto, e save antigo ainda abre. Pós-jogo/Frontier só será marcado como concluído após seus próprios mapas, regras, eventos e batalhas estarem testados; não confundir vitória da Liga com "100% Hoenn".

### FASE 15/16 — Músicas, encontros, treinadores, Pokédex e portal completos

**Fazer:**
1. Criar **data/hoenn-music.json** e **docs/HOENN_MUSICAS_MAPEAMENTO.md**; mapear cada faixa **autorizada** por nome exato, destino, tipo, variante, origem, licença, SHA-256, status e regra de prioridade.
2. Classificar **BGM** (cidades, rotas, caves, Surf, Dive, batalhas, cenas), **BGS** (ambientes quando necessário), **ME** (insígnia, evolução/cura/recompensas onde apropriado) e **SE** (ações); seguir o comportamento atual do BlueMusic. Sem áudio autorizado, manter fallback existente e reportar falta.
3. Testar músicas de Littleroot, Oldale, Petalburg, Rustboro, Dewford, Slateport, Mauville, Verdanturf, Fallarbor, Lavaridge, Fortree, Lilycove, Mossdeep, Sootopolis, Pacifidlog, Ever Grande, liga, cavernas, mar, tempestade e Frontier **somente com correspondência comprovada**.
4. Vincular temas de batalha selvagem, treinador, rival, Magma/Aqua, líderes, Elite, Campeão, lendários, vitória e Hall of Fame; confirmar que uma batalha só troca música quando começa de fato e que a faixa é restaurada depois.
5. Implementar prioridade de história e preferências compatíveis: evento de cena real > tema regional confirmado, respeitando os modos de playlist global e as opções do usuário já existentes; validar fade, volume, loop, não sobreposição e silêncio.
6. Exportar encontros/rotas/treinadores **reais** para Pokédex, Habitat Dex, guias, mapa do portal e histórico do Blue. Criar cartões de treinador regional + global sem apagar abas antigas.
7. Reconciliar todos os NPCs e itens do inventário Fase 02 com os presentes no jogo, gerar relatório **expected vs actual** e manter lacunas de quests/áudio/arte como BLOCKED, nunca escondidas.

**Aceite:** todas as músicas/entradas de portal têm referência de mapa/evento real, direitos aprovados quando distribuídas, testes de áudio nativos e regressões do sistema musical de Decades, Kanto e Johto.

### FASE 16/16 — Instalar sem regressão, executar E2E e liberar Hoenn

**Fazer:**
1. Criar **install_hoenn.py**: por padrão somente dry-run, com plano completo de escrita, mapa origem/destino, permissões, diff, hashes, backup, gravação atômica, recuperação após falha, segunda execução idempotente e rollback. --apply somente depois de passar os gates de instalação, nunca como atalho para gerar prova falsa.
2. Criar manifesto de release com SHA-256 da fonte autorizada, MapIDs reais, início, chegada em Littleroot e coordenadas do NPC, contagem de mapas/eventos/PBS, áudio, regressões, evidência Windows e permissões.
3. Instalar numa cópia de teste do Blue com **as outras regiões**; abrir Game.exe e validar nova partida, viagens, PC, save/load, troca de origem, mudança de mapa, Hall of Fame e retorno.
4. Automatizar o Game.exe **real** (não só mocks): comandos de movimentação, capturas de tela, logs, testes de warps, interação, lutas reais e checkpoints de cada ginásio. Se a automação gráfica não estiver disponível, sinalizar **BLOCKED_NATIVE_E2E** e não aumentar a Barra 2.
5. Validar separadamente JoiPlay/Android se a compatibilidade móvel for parte do aceite. Não inferir que passar Windows significa passar Android.
6. Executar regressões atuais de Decades, Kanto, Johto, Blue Studio, multiplayer/Hub, Pokédex/site, músicas, saves antigos e menus.
7. Registrar testes, lacunas, commits, hashes e riscos; ativar seletor HOENN somente quando a instalação tiver os mapas reais e as proteções aprovadas. **Disponibilidade de Hoenn como origem não deve depender de um marcador vazio ou arquivo JSON fabricado.**
8. Publicar na main por fast-forward/commit normal; jamais usar force push para substituir trabalho existente.

**Aceite:** toda a trilha de história Hoenn é jogável do início ao Hall of Fame, mapas do escopo são verificáveis no editor/jogo, sistemas compartilhados permanecem íntegros, e indicadores de QA só sobem com evidência de execução real.

## 9. Inventário musical por tipo de evento (para a Fase 15)

**Identificação de repertório, não arquivos de áudio já instalados.** O catálogo definitivo depende de conferência faixa a faixa com referência original e autorização de uso.

| Categoria | Exemplos de destinos que devem existir no mapeamento |
|---|---|
| Cidades | Littleroot, Oldale/Lavaridge quando compartilharem tema, Petalburg, Rustboro/Mauville/Mossdeep quando compartilharem tema, Dewford, Slateport, Verdanturf, Fallarbor, Fortree, Lilycove, Sootopolis, Pacifidlog, Ever Grande |
| Rotas | Rotas iniciais, Route 104, Route 110, Route 111, Route 113, Route 119 e outras com tema regional compartilhado |
| Interiores | Birch Lab, Pokémon Center, Poké Mart, gyms, museu, Devon, Sky Pillar, Cave of Origin, bases Magma/Aqua, Weather Institute, Shoal Cave, Granite Cave, Mt. Pyre |
| Campo | Surf, Dive, bicicleta, barco, clima/cena especial; restauração da música do mapa original |
| Batalhas | Selvagem, treinador, rival, Team Magma/Aqua, líderes, Elite Four, Wallace, Steven, Kyogre/Groudon/Rayquaza e Regis |
| Vitória e vinheta | Vitórias, obtenção de item/insígnia, cura, evolução, recebimento de Pokémon, Hall of Fame, créditos |
| Pós-jogo | Battle Frontier, Frontier Brain, desafios e recompensas de símbolo, quando esses eventos realmente existirem |

**Formato pretendido**: locais permitidos (áudio com direitos) em game/Audio/BGM/Hoenn, game/Audio/BGS/Hoenn, game/Audio/ME/Hoenn e game/Audio/SE/Hoenn. Não colocar áudio oficial diretamente em assets/music/hoenn no GitHub sem autorização.

**Fallback:** quando a faixa específica não existir ou sua licença for pendente, não desativar mapa nem quebrar batalha; usar a trilha segura existente do Blue/Decades ou conteúdo próprio/permitido, e emitir warning no relatório. Uma vinheta de recompensa toca **apenas depois** da confirmação do evento, não ao entrar no mapa ou abrir diálogo.

## 10. Matriz de testes E2E — mínimo para um "Hoenn 100% jogável"

| Teste | Procedimento comprovável | Aprovação |
|---|---|---|
| Nova partida | Iniciar HOENN pelo seletor já apto; atravessar caminhão/casa/Littleroot | Spawn correto, nenhum erro de MapID, portas de ida e volta |
| Região anterior | Abrir saves antigos Decades, Kanto e Johto e explorar seus mapas | Nenhum dado/perfil/item/treinador/som destruído |
| NPC e itens | Interagir com todos os NPCs/itens registrados em cada MapKey | Expected = actual, falhas explicitadas |
| Caminhada e colisão | Varredura de tiles críticos, portas, escadas, cavernas, saídas e retornos | Sem parede atravessável ou porta sem retorno |
| Treinador real | Aproximar e entrar em linha de visão; perder/ganhar e salvar | Battle Blue inicia; estado e prêmio corretos |
| Selvagem real | Encontro, captura, fuga, evolução, PC e retiradas | PBS/métodos válidos e política regional preservada |
| Ginásios 1–8 | Lutar com líder, ganhar badge, salvar e repetir | 8 chaves locais; exatamente +8 na contagem global derivada, sem prêmio duplicado |
| Master | Começar com esmeraldas globais de outra região e entrar em Hoenn | IA, níveis, quatro Pokémon/cobertura conforme regras existentes; sem mutação do PBS |
| Campo | Cut, Flash, Rock Smash, Strength, Surf, Fly, Dive, Waterfall | Bloqueia antes da condição local; habilita depois, sem ativar em outra região indevidamente |
| Clima/Mar | Chuva/sol extremo, correntes 132–134, Cave of Origin, Dive/emersão | Sem softlock, sem clima vazando para outros mapas |
| Duplas | Tate & Liza e eventos de dupla confirmados | Batalha dupla real e 1 badge MIND |
| Liga | Sidney → Phoebe → Glacia → Drake → Wallace → Hall of Fame | 1 registro de conclusão; Johto + Sinnoh liberadas logicamente |
| Viagem | NPC em Littleroot, PC cheio, só especiais na party e retorno | Bloqueia com segurança; sem perda; destino instalado exigido |
| Pós-jogo | Steven, Regis, Frontier, desafios que fazem parte do escopo | Conteúdo só marcado concluído depois de implementado |
| Áudio | BGM/ME/BGS/SE, loop, fades, prioridades, interrupções, save/load | Tema contextual correto; fallback funciona; outras regiões intactas |
| Portal | Mapas, NPCs, treinadores e Habitat Dex da região atual/global | Dados realmente exportados de instância instalada |
| Android/JoiPlay | Repetir smoke de controles, mapa, batalha, áudio e saves | Aprovado ou declarado pendente (não presumido) |
| Rollback | Simular falha de escrita entre MapInfos/Tilesets/maps/PBS e repetir instalação | Restauração integral; sem duplicação; mapa/save antigo preservado |

### 10.1. Provas aceitas

- **A — automático técnico:** testes Python/Ruby, sintaxe, referências, hashes, fixtures, contratos de instalação, inicialização headless, colisões calculáveis.
- **B — gameplay real:** evidência do processo Game.exe nativo no Windows/ambiente instrumentado, com movimento, interação, luta, música audível ou medição de reprodução, screen/log/estado de save, mais testes de JoiPlay se exigidos.
- **Não aceitos como gameplay:** JSON marcado como true, documentação, print de código, batalha inteiramente simulada, mapa sem eventos, CI que não executou o jogo ou relatório gerado sem observação real.

## 11. Duas barras de progresso — acompanhamento de Hoenn (início do plano)

**Barra 1 — Fases técnicas implementadas e verificadas:** **0/16 (0%)**  
**Barra 2 — Fases integralmente aceitas em gameplay real:** **0/16 (0%)**  

O novo MD **não executa nenhuma fase**. Para cada fase, usar registros abaixo e manter as duas barras independentes:

| Fase | Área | A — técnica | B — jogo real |
|---|---|---|---|
| 01 | Fonte e direitos | [ ] | [ ] |
| 02 | Inventário de mapas/NPCs/itens | [ ] | [ ] |
| 03 | Importação e piloto isolado | [ ] | [ ] |
| 04 | Littleroot/Oldale | [ ] | [ ] |
| 05 | Roxanne | [ ] | [ ] |
| 06 | Brawly | [ ] | [ ] |
| 07 | Wattson | [ ] | [ ] |
| 08 | Flannery | [ ] | [ ] |
| 09 | Norman | [ ] | [ ] |
| 10 | Winona | [ ] | [ ] |
| 11 | Lilycove/Mt. Pyre/Magma-Aqua | [ ] | [ ] |
| 12 | Tate & Liza | [ ] | [ ] |
| 13 | Juan / crise climática | [ ] | [ ] |
| 14 | Liga/pós-jogo | [ ] | [ ] |
| 15 | Música, portal e catálogo | [ ] | [ ] |
| 16 | Instalação/regressão/E2E | [ ] | [ ] |

**Checklist de não-regressão antes de marcar fase concluída:**

- [ ] Nenhum ID de Decades, Kanto ou Johto sobrescrito.
- [ ] Alteração documentada e reversível, source SHA e direitos registrados.
- [ ] Game.exe/Source/MapInfos/Tilesets/Scripts originais não substituídos integralmente.
- [ ] Saves antigos e multiplayer/Hub de Batalha preservados.
- [ ] PBS original de Pokémon, golpes e equipes-base preservado.
- [ ] 8 badges locais separados de contagem global de esmeraldas.
- [ ] NPC de Littleroot e destinos reais não habilitados prematuramente.
- [ ] Música de Hoenn isolada do BlueMusic global e das listas existentes.
- [ ] Evidência de campo, portas, NPCs, itens, batalhas, reload e retorno para cada mapa realmente declarado pronto.
- [ ] CI/testes registram falhas corretamente e **não** confundem fixture com gameplay.

## 12. Prompts operacionais para executar este plano em etapas

### Solicitação inicial, imediatamente após este MD

> Aplique a **Fase 01/16** de docs/HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md. Audite as fontes editáveis de Hoenn, a licença e a instalação real disponível, gere data/regions/hoenn-source.json e auditoria read-only com testes, sem modificar game/. Registre bloqueios, rode as regressões e publique na main apenas código/documentação próprios com prova de testes.

### Para prosseguir com uma fase

> Aplique a próxima fase pendente do plano Hoenn, seguindo docs/HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md e docs/HOENN_ETAPAS.md. Releia o estado real da main, preserve Decades/Kanto/Johto, implemente mapas/eventos/treinadores/itens/músicas reais em piloto isolado quando a fonte estiver auditada, execute os testes apropriados e registre **Barra A** e **Barra B** sem elevar aceite por simulação. Publique o commit e informe bloqueios concretos.

### Para aceitação integral via Game.exe

> Execute a matriz Hoenn E2E da fase atual em **Game.exe real**. Automatize as interações quando possível, inclua movimento, portas, batalhas, item, HM, save/reload, regressões e evidência auditável. Se não houver acesso ao executável ou ambiente GUI/JoiPlay exigido, registre BLOCKED_NATIVE_E2E e **não** aprove a Barra B. Corrija falhas demonstradas antes de avançar.

## 13. Critérios de encerramento definitivo de Hoenn

Hoenn é considerada completa **somente se**:

- [ ] Inventário integral de cidades, Route 101–134, interiores, cavernas, mapas de água e submersos, NPCs, trainers, itens e eventos do escopo Emerald fecha sem UNKNOWN não tratado.
- [ ] Início correto de Hoenn, três iniciais, oito líderes, Elite Four, Campeão e Hall of Fame jogáveis.
- [ ] Fusão de exclusivos Ruby/Sapphire e addons ORAS documentada, coerente e não duplicada.
- [ ] Surf/Dive/correntes/clima e os outros HMs funcionam nas condições locais e não geram softlocks.
- [ ] As oito insígnias somam **uma vez cada** às esmeraldas globais, sem alterar a fórmula de balanceamento.
- [ ] Johto/Sinnoh são liberadas após Liga, mas somente destinos instalados podem ser usados; NPC da cidade inicial funcional.
- [ ] Saves, PC, especiais, mapa global, duas páginas do cartão, Hub e multiplayer do Blue preservados.
- [ ] Portal/Pokédex e trilha musical usam dados reais e recursos autorizados, sem prejudicar faixas de Kanto/Decades/Johto.
- [ ] Conteúdo opcional declarado como implementado (Frontier, Steven, Regis, concursos etc.) passa por seus próprios testes.
- [ ] CI técnica + **jogabilidade real** e rollback da instalação aprovados, com logs/screen/hashes para inspeção.

**Decisão técnica final:** usar fonte editável auditada e autorizada, seguindo Emerald como geografia/roteiro, adaptar dados para o mesmo RPG Maker XP/Essentials e **nunca importar um segundo sistema de batalha**. O próximo trabalho é exclusivamente a **Fase 01**, que prepara a fonte real, licenças e baseline segura sem alterar o jogo.
