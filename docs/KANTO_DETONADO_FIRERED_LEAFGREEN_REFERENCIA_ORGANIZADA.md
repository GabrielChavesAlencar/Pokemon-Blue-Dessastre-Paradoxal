# Kanto — Guia de progressão FireRed/LeafGreen para o Dessastre Paradoxal

**Projeto:** Pokémon Blue: Dessastre Paradoxal · **Data de organização:** 13/11/2026  
**Fonte de consulta:** [Detonado FireRed/LeafGreen — Pokémon Mythology](https://www.pokemythology.net/detonados/detonado-firered-leafgreen/)  
**Tipo:** síntese factual, índice de eventos e especificação de adaptação. **Não é transcrição do detonado, exportação de seus mapas/imagens ou comprovação de implementação.**

## Objetivo e limites

Organizar o percurso de Kanto, os marcos narrativos, os prêmios, os desafios, os encontros especiais e o pós-jogo de **FireRed/LeafGreen (FRLG)** para orientar a implementação e a auditoria do piloto de Kanto. A descrição de cada evento foi redigida especialmente para este projeto; os dados de equipes, nomes e recompensas são referências factuais do jogo original. Para pormenores gráficos e caminhos exatos ilustrados, consultar o artigo original.

**Três categorias distintas:**
- **FRLG:** funcionamento/recompensas no jogo de referência, não necessariamente no Blue.
- **Blue — requisito:** comportamento desejado neste fangame, sujeito à documentação autoritativa.
- **Blue — status:** somente comprovado por código, testes e jogo real; **a existência deste MD não altera o status**.

### Ordem de precedência dentro do Blue

1. [Plano de regiões v2](PLANO_REGIOES_DESSASTRE_V2.md): circuito, progressão, saves, restrições regionais e pós-jogo global.
2. [Balanceamento e início de Pallet](KANTO_BALANCEAMENTO_PALLET_CARTOES_REGIONAIS.md): engine de níveis, insígnias/esmeraldas e NPC de viagem.
3. [Roadmap dos eventos FireRed](KANTO_ROADMAP_EVENTOS_FIRERED.md), [adaptação de eventos](FIRERED_EVENTOS_COMO_APLICAR_NO_BLUE.md) e [estudo técnico](ESTUDO_EVENTOS_MAPA_POKEMON_FIRERED_RPG_MAKER_XP.md).
4. [Etapa 16 e suas limitações](KANTO_FASE_16.md), [testes E2E](KANTO_CODEX_TESTES_E2E.md) e [música de Kanto](KANTO_PLANO_APLICAR_MUSICAS.md).
5. Este documento: **referência de conteúdo e roteiro de testes**, nunca fonte de MapIDs, flags ou níveis finais.
6. [Times mais fortes documentados](ESTUDO_TIMES_MAIS_FORTES_KANTO_LIDERES_ELITE4_CAMPEOES.md): referência para o **pós-jogo global**; a revanche de FRLG abaixo não a substitui.

**Regras fixas:** manter motor de batalha, equipes-base e ajustes em memória do Decades/Blue; não hardcodar níveis originais em treinadores ou no site; não sobrescrever saves, mapas/áudio do Decades ou instalações de Johto/Hoenn/Sinnoh; não renumerar MapIDs; respeitar o status de mapas de prévia. Unir encontros exclusivos de FireRed e LeafGreen quando compatível com o plano de regiões. Qualquer alteração real exige implementação, regressão e caminhada manual.

---

## 1. Rota principal — visão geral

| # | Local / arco | Marco para prosseguir | Resultado de referência |
|---|---|---|---|
| 01 | Pallet Town / laboratório | Oak intercepta saída norte; seleção do inicial; rival | Primeiro Pokémon e primeira luta |
| 02 | Route 1 → Viridian Mart → Pallet | Retirar Oak's Parcel e entregá-lo a Oak | Pokédex + 5 Poké Balls; mapa com Daisy |
| 03 | Viridian → Route 2 → Viridian Forest | Resolver abertura após a entrega; atravessar floresta | Acesso a Pewter |
| 04 | Pewter Gym → Route 3 → Mt. Moon | Brock; atravessar a caverna Rocket; escolher fóssil | Boulder Badge; Helix ou Dome Fossil |
| 05 | Cerulean → Routes 24/25 → Bill | Misty; rival; Nugget Bridge; auxiliar Bill | Cascade Badge; S.S. Ticket; rota sul liberada |
| 06 | Route 5 / Underground Path → Vermilion | Entrar no S.S. Anne; rival; capitão | HM01 Cut; acesso ao ginásio |
| 07 | Vermilion Gym → Diglett's Cave → Route 2 | Enigma das lixeiras; Surge; obter Flash | Thunder Badge; HM05 Flash |
| 08 | Routes 9/10 → Rock Tunnel → Lavender | Travessia da caverna escura | Acesso a Lavender e Route 8 |
| 09 | Route 8 / Underground Path → Celadon | Tea, Eevee, Erika, base Rocket | Rainbow Badge; Silph Scope |
| 10 | Lavender Pokémon Tower | Rival, Marowak, Rockets, Mr. Fuji | Poké Flute e dois caminhos para Fuchsia |
| 11 | Saffron / Silph Co. | Chá para guardas; Card Key, rival, Giovanni | Lapras, Master Ball e acesso a Sabrina |
| 12 | Saffron Gym | Puzzle de teleportes e Sabrina | Marsh Badge |
| 13 | Routes 12–15 ou 16–18 → Fuchsia | Acordar Snorlax; pescar / bicicleta | Entrada em Fuchsia |
| 14 | Safari Zone + Fuchsia Gym | Gold Teeth, Secret House, Warden e Koga | HM03 Surf, HM04 Strength, Soul Badge |
| 15 | Surf / Cinnabar / Pokémon Mansion | Navegar; ressuscitar fósseis; obter Secret Key | Acesso ao ginásio de Blaine |
| 16 | Cinnabar Gym | Quiz / treinadores e Blaine | Volcano Badge; convite opcional às Sevii 1–3 |
| 17 | Viridian Gym | Giovanni e piso de setas | Earth Badge; oito insígnias |
| 18 | Routes 22/23 → Victory Road | Rival; oito portões; puzzle Strength | Indigo Plateau |
| 19 | Elite Four → campeão Blue/Gary | Cinco batalhas consecutivas | Hall of Fame e conclusão da Liga |
| 20 | Pós-Liga / Sevii 4–7 / opcionais | National Dex, Ruby/Sapphire, Celio | Cerulean Cave e conteúdo adicional |

**Ordem flexível:** o detonado visita Sabrina antes de Koga e oferece dois acessos a Fuchsia. Essas opções **não devem** virar travas artificiais: implementar apenas as dependências realmente necessárias. Sevii 1–3 são uma excursão após Blaine, e o convite de Bill pode ser recusado sem perder a continuidade.

---

## 2. Eventos detalhados por região da história

### 2.1 Pallet Town, Route 1 e encomenda de Oak

**FRLG:** jogador começa no quarto, pode retirar uma Potion no PC; ao tentar sair pelo norte de Pallet, Oak intercepta a caminhada e acompanha o jogador até o laboratório. Três Poké Balls expostas representam Bulbasaur, Charmander e Squirtle. O rival seleciona o inicial com vantagem de tipo e inicia uma batalha quando o jogador tenta sair. A Route 1 contém uma entrega simples de item por NPC. Na primeira visita ao Mart de Viridian, o atendente entrega a encomenda de Oak e não oferece compras convencionais antes do marco. De volta ao laboratório, Oak recebe o pacote, distribui Pokédex e cinco Poké Balls; a irmã do rival oferece o Town Map.

**Blue — contratos de implementação/aceite:**
1. Novo jogo em Kanto surge **no quarto do segundo andar**, não na rua. Viagem **de outra região** chega a Pallet, sem reiniciar a história.
2. Oak aproxima-se na saída norte, conduz o personagem **até o fundo do laboratório, ao lado do rival**, conversa e libera seleção pelas **três Poké Balls na mesa**, não por lista de diálogo.
3. A fala do rival precede a tentativa de saída; ao cruzar o trecho definido após o balcão, ele se aproxima e inicia a primeira batalha. Estado único após vitória **ou derrota**, sem repetição ao recarregar.
4. Primeira entrada no Viridian Mart dispara **abordagem e deslocamento automático até o balcão**, diálogo e recebimento de **Oak's Parcel**. O NPC não pode entregar duas vezes nem bloquear a movimentação.
5. A entrega a Oak concede **Pokédex + cinco Poké Balls** uma única vez. O mapa de Daisy é coletável. **Viridian Forest fica fechada antes desse marco** e se torna acessível depois, incluindo após save/reload.
6. No Pokémon Center, tocar a vinheta de **cura** (ME apropriada) e restaurar a BGM sem alterar o áudio de Decades. Confirmar também no Android/JoiPlay.

**Casos negativos:** retornar ao Mart antes/depois de entregar; inventário cheio; cancelar interação; trocar de mapa durante autorun; derrota para o rival; recuperar save antigo; entrar no laboratório por outro warp; acesso à floresta por entradas alternativas.

### 2.2 Viridian, Forest, Pewter e Mt. Moon

- **Viridian:** velho ensina captura e entrega Teachy TV; Route 22 permite rival opcional e captura de Mankey/Pidgey; a academia da cidade espera o final da história.
- **Viridian Forest:** treinadores Bug Catcher, insetos e Pikachu raro (**5% na referência FRLG**, não substituir probabilidades locais sem auditar a tabela).
- **Pewter:** Brock entrega Boulder Badge e TM39 Rock Tomb. Após a vitória, um NPC entrega Running Shoes na saída para Route 3. Museu de Pewter oferece Old Amber posteriormente, quando Cut estiver disponível.
- **Route 3:** treinadores, Jigglypuff e ponto de cura antes de Mt. Moon.
- **Mt. Moon:** Rockets, Clefairy raro, passagens entre andares e escolha **mutuamente exclusiva** Helix Fossil (Omanyte) ou Dome Fossil (Kabuto), após duelo com o pesquisador; o outro fóssil fica indisponível.
- **Route 4:** tutores de Mega Punch/Mega Kick, itens e chegada a Cerulean. Retornar para revisar os warps de ida e volta quando aplicável.

### 2.3 Cerulean, Bill, Rotas 24/25 e passagem para Vermilion

- **Misty:** Cascade Badge e TM03 Water Pulse.
- Rival na saída norte de Cerulean; recompensa Fame Checker; Nugget Bridge culmina em Nugget e encontro Rocket.
- Em Routes 24/25, Bill precisa que o jogador opere o computador para reverter a transformação; somente após isso recebe o **S.S. Ticket**.
- Policial libera acesso à casa arrombada; Rocket pelo acesso posterior entrega TM28 Dig após ser derrotado. Rota sul abre para Route 5.
- **Route 5:** Day Care e Underground Path até Route 6/Vermilion; acesso direto a Saffron ainda controlado pelos guardas.

### 2.4 Vermilion, navio, ginásio e retorno a Pewter

- Pokémon Center: VS Seeker; casa próxima: Old Rod.
- **S.S. Anne:** embarque por ticket, cabines com treinadores, local de recuperação, confronto com rival e capitão que entrega **HM01 Cut**. Confirmar que o navio permanece inacessível quando não houver ticket.
- **Lt. Surge:** acesso via árvore Cut. Puzzle com dois mecanismos em lixeiras: o segundo fica adjacente ao primeiro; erro reinicia a combinação. Vitória: Thunder Badge e TM34 Shock Wave.
- NPC do fã-clube entrega **Bike Voucher**; a loja de Cerulean troca o voucher pela bicicleta.
- **Route 11:** treinadores e itens opcionais. **Diglett's Cave:** Diglett e Dugtrio; permite acesso ao trecho de Route 2 onde assistente de Oak entrega **HM05 Flash** mediante requisito de Pokédex da referência. Com Cut, entrar no anexo do Museu de Pewter e retirar **Old Amber**.
- Returno por Route 9/10 leva ao Rock Tunnel. Flash facilita exploração; Rock Smash tem obstáculos que só serão resolvidos muito depois.

### 2.5 Lavender, Celadon e a Equipe Rocket

- **Lavender na primeira visita:** Pokémon Tower **não deve ser resolvida sem Silph Scope**. Route 8 e Underground Path levam a Celadon.
- **Celadon:** Eevee no acesso pelos fundos de um prédio; **Tea** oferecido por NPC no edifício residencial para liberar guardas de Saffron; Erika entrega Rainbow Badge e TM19 Giga Drain. **HM02 Fly** é recebido em uma casa acessível por Cut na parte oeste. A ordem Erika/Rocket pode ser flexível.
- **Rocket Hideout:** Rocket em frente a um cartaz no Game Corner revela escada. Base subterrânea possui esteiras/setas, elevador e **Lift Key** entregue por Rocket após derrota; dois Rockets defendem acesso a Giovanni. Vitória contra Giovanni resulta no **Silph Scope**.
- **Retorno a Lavender:** Silph Scope identifica fantasmas; rival aparece na Tower; fantasma de **Marowak** bloqueia acesso e **não é capturável**; vencer Rockets e resgatar Mr. Fuji concede **Poké Flute**.
- A Poké Flute acorda **dois Snorlax distintos** em locais diferentes; registrar estado independente para cada um. Depois da remoção, conferir o **Leftovers escondido** no tile onde estava cada Snorlax.

### 2.6 Saffron e Silph Co.

- Usar Tea para transitar pelos postos dos guardas. Há **Fighting Dojo** (prêmio opcional: escolher um de **Hitmonlee/Hitmonchan**) e ginásio oficial, inicialmente bloqueado.
- Silph Co. tem 11 pavimentos, Rockets, passagens de teleporte e portas fechadas. **Card Key** é encontrada no 5º andar; acesso ao setor da história usa teleportes do 3º andar, com rival e NPC que dá **Lapras**.
- Giovanni enfrenta o jogador no fim do prédio; o presidente entrega **Master Ball** e a ocupação da cidade termina.
- Ginásio de **Sabrina:** puzzle de salas/teleportes, vitória rende Marsh Badge e TM04 Calm Mind.
- Evitar sequência linear rígida de todas as salas: explorar andares secundários é opcional, mas eventos-chave não podem ser saltados via warp inválido.

### 2.7 Fuchsia, Snorlax e Safari

**Dois caminhos:** Cycling Road (Routes 16–18; bicicleta obrigatória) e estradas de Routes 12–15 (vários treinadores/pesca e segundo Snorlax). Casinhas oferecem **Super Rod** na Route 12 e **Good Rod** em Fuchsia. Ditto pode aparecer em trechos de grama na referência.

**Safari Zone em FRLG:** entrada paga (500), sessão de **600 passos** e **30 Safari Balls**; encontros usam opções de bola, isca, pedra ou fuga, sem batalha comum. Ao terminar os passos, retornar ao portão. O objetivo da história é encontrar **Gold Teeth** e, na **Secret House**, receber **HM03 Surf**. Ao devolver os dentes ao **Warden**, receber **HM04 Strength**; pedra na casa libera Rare Candy. São **dois itens independentes e persistentes**, nunca recompensas automáticas de Koga.

**Ginásio Koga:** paredes transparentes/ocultas, Soul Badge e TM06 Toxic. O uso de Surf fora de batalha depende da insígnia correta **de Kanto**, conforme a política regional do Blue.

**Encontros Safari de referência:**
- Frequentes: Nidoran♀, Nidoran♂, Nidorina, Nidorino, Paras, Venonat, Exeggcute, Rhyhorn, Doduo.
- Raros: Parasect, Venomoth, Chansey, Kangaskhan, Tauros; Scyther em FireRed e Pinsir em LeafGreen.
- Super Rod: Goldeen, Seaking, Dratini e Dragonair muito raro. Na fonte, Dragonair é indicado como **1%**, não como taxa global da espécie.

### 2.8 Surf, Cinnabar e Blaine

- Routes 19/20 e **Seafoam Islands** oferecem exploração marítima; a alternativa mais curta é **Route 21**, surfando ao sul de Pallet.
- **Power Plant** no entorno de Route 10 é opção depois de Surf; **Zapdos** aparece lá. Seafoam exige Strength para redirecionar correntezas e chegar a **Articuno**.
- **Cinnabar Fossil Lab:** ressuscitar o Helix/Dome selecionado e **Old Amber**, com espaço disponível na equipe conforme o fluxo original.
- **Pokémon Mansion:** registros narrativos associados a Mewtwo; estátuas alteram portas; obter **Secret Key** para destrancar o ginásio.
- **Blaine:** perguntas do quiz podem substituir confrontos com alguns treinadores; Volcano Badge e TM38 Fire Blast.
- **Bill convida a visitar Sevii Islands 1–3** ao sair do ginásio. Recusar não bloqueia a aventura: a opção fica disponível posteriormente no Centro Pokémon.

### 2.9 Viridian final, Victory Road e Liga

- Retornar a **Viridian**; puzzle de setas do ginásio e última luta contra **Giovanni**: Earth Badge e TM26 Earthquake.
- **Route 22:** batalha final pré-Liga contra rival. **Route 23:** verificação das oito insígnias em portões, sem conceder conquista por aproximação.
- **Victory Road:** rochas com Strength posicionadas sobre interruptores; treinadores e transições internas; rota termina no Indigo Plateau.
- **Liga:** Lorelei → Bruno → Agatha → Lance → Blue/Gary. Curar/preparar antes de entrar; batalhas seguidas sem retorno ao Pokémon Center. Hall of Fame e liberação do circuito regional somente após a vitória legítima.
- No Blue, a conclusão **Kanto → Decades + Johto** vem do Plano de Regiões, não do detonado de FRLG.

---

## 3. Líderes de Kanto — elenco original de referência

**Os níveis citados em FRLG são apenas históricos; NÃO configurá-los como níveis fixos no Blue nem exibi-los como níveis fixos no site.** Usar o cálculo compartilhado do projeto e as espécies/táticas oficiais nos locais em que forem auditadas.

| Ginásio | Líder | Especialidade | Equipe FRLG | Insígnia / TM |
|---|---|---|---|---|
| Pewter | Brock | Pedra | Geodude, Onix | Boulder / TM39 Rock Tomb |
| Cerulean | Misty | Água | Staryu, Starmie | Cascade / TM03 Water Pulse |
| Vermilion | Lt. Surge | Elétrico | Voltorb, Pikachu, Raichu | Thunder / TM34 Shock Wave |
| Celadon | Erika | Planta | Victreebel, Vileplume, Tangela | Rainbow / TM19 Giga Drain |
| Fuchsia | Koga | Veneno | Koffing, Muk, Koffing, Weezing | Soul / TM06 Toxic |
| Saffron | Sabrina | Psíquico | Kadabra, Mr. Mime, Venomoth, Alakazam | Marsh / TM04 Calm Mind |
| Cinnabar | Blaine | Fogo | Growlithe, Ponyta, Rapidash, Arcanine | Volcano / TM38 Fire Blast |
| Viridian | Giovanni | Terra | Rhyhorn, Dugtrio, Nidoking, Nidoqueen, Rhyhorn | Earth / TM26 Earthquake |

**Chefes Rocket fora dos ginásios:** Giovanni no Game Corner/Hideout usa Onix, Rhyhorn, Kangaskhan; na Silph Co., Nidorino, Rhyhorn, Kangaskhan, Nidoqueen. São encontros narrativos diferentes do ginásio, com flags e recompensas próprios.

### Rivais e variantes por inicial

| Ponto | Composição-chave na referência |
|---|---|
| Laboratório | Inicial com vantagem de tipo (Bulbasaur → Charmander; Charmander → Squirtle; Squirtle → Bulbasaur) |
| Route 22 inicial (opcional) | Pidgey e inicial do rival |
| Cerulean norte | Pidgeotto, Rattata, Abra e inicial |
| S.S. Anne | Pidgeotto, Raticate, Kadabra e evolução do inicial |
| Pokémon Tower | Pidgeotto, Kadabra, inicial evoluído e duas opções variáveis entre Gyarados, Exeggcute e Growlithe |
| Silph Co. | Pidgeot, Alakazam, inicial totalmente evoluído e duas opções variáveis entre Gyarados, Exeggcute e Growlithe |
| Route 22 pré-Liga | Pidgeot, Rhyhorn, Alakazam, inicial final e duas opções variáveis |
| Campeão | Pidgeot, Rhydon, Alakazam, inicial final e duas opções de cobertura |

**Composição do campeão por inicial do jogador (FRLG):**
- **Bulbasaur:** Pidgeot, Rhydon, Gyarados, Exeggutor, Alakazam, Charizard.
- **Squirtle:** Pidgeot, Rhydon, Arcanine, Gyarados, Alakazam, Venusaur.
- **Charmander:** Pidgeot, Rhydon, Exeggutor, Arcanine, Alakazam, Blastoise.

**Blue:** reavaliar linha de evolução pelo estágio/level cap real, em vez de manter Rattata em estágios nos quais Raticate seria apropriado; preservar identidade do treinador, sem fazer importação destrutiva dos times PBS.

### Elite Four e campeão — primeira Liga FRLG

| Ordem | Adversário | Equipe-base da referência |
|---|---|---|
| 1 | Lorelei | Dewgong, Cloyster, Slowbro, Jynx, Lapras |
| 2 | Bruno | Onix, Hitmonchan, Hitmonlee, Onix, Machamp |
| 3 | Agatha | Gengar, Golbat, Haunter, Arbok, Gengar |
| 4 | Lance | Gyarados, Dragonair, Dragonair, Aerodactyl, Dragonite |
| 5 | Blue/Gary | Equipe variável por inicial, conforme tabela acima |

O jogo original pode usar cura e held items. A implementação Blue deve reaproveitar o sistema de IA/itens e balanceamento definido para a campanha; **não transportar os níveis originais para o jogador, líderes, Elite Four ou portal**.

---

## 4. HMs, itens obrigatórios e bloqueios

| Recurso | Local / evento de FRLG | Função de campo / dependência |
|---|---|---|
| Oak's Parcel | Viridian Mart, primeira visita | Entregar a Oak; desbloqueia Pokédex, Poké Balls e progressão inicial |
| Pokédex + 5 Poké Balls | Oak, após entrega | Captura e liberação de Viridian Forest no contrato Blue |
| Town Map | Daisy em Pallet | Navegação regional |
| S.S. Ticket | Bill nas Routes 24/25 | Entrada no S.S. Anne |
| HM01 Cut | Capitão do S.S. Anne | Árvores e entradas opcionais; permissão local por insígnia |
| Bike Voucher / Bicycle | Fã-clube Vermilion / loja Cerulean | Cycling Road |
| HM05 Flash | Assistente de Oak na Route 2 | Iluminar Rock Tunnel |
| Tea | Edifício residencial de Celadon | Postos de acesso a Saffron |
| Eevee | Fundos de prédio em Celadon | Pokémon presenteado |
| Lift Key | Rocket no Hideout | Elevador até Giovanni |
| Silph Scope | Giovanni no Rocket Hideout | Identificação dos fantasmas da Pokémon Tower |
| Poké Flute | Mr. Fuji em Lavender | Remover Snorlax das duas rotas |
| HM02 Fly | Casa a oeste de Celadon, por Cut | Viagem a locais visitados |
| Card Key | Silph Co., 5º andar | Abrir portas internas |
| Lapras | NPC da Silph Co. | Pokémon presenteado |
| Master Ball | Presidente da Silph Co. | Prêmio único de resgate |
| Gold Teeth | Safari Zone | Entrega ao Warden |
| HM03 Surf | Secret House do Safari | Navegação em água após permissão regional |
| HM04 Strength | Warden em Fuchsia | Empurrar pedras; requer permissão regional |
| Secret Key | Pokémon Mansion | Abrir ginásio de Cinnabar |
| Helix/Dome Fossil | Mt. Moon | Escolha exclusiva; restauração em Cinnabar |
| Old Amber | Museu de Pewter por Cut | Aerodactyl em Cinnabar |
| HM06 Rock Smash | One Island, Ember Spa | Rochas quebráveis; excursão Sevii |
| HM07 Waterfall | Four Island, Icefall Cave | Subir cachoeiras |

**Regras do Blue:** HMs só funcionam segundo os requisitos da **região ativa**, nunca pela soma indiscriminada das insígnias de outras regiões. Itens e Pokémon especiais não devem ser duplicados ao salvar, recarregar ou voltar à área; evolução da região e contagem global de esmeraldas são sistemas distintos.

---

## 5. Pós-jogo, Ilhas Sevii e locais opcionais

### 5.1 Primeira visita — Ilhas 1, 2 e 3, após Blaine

| Ilha / local | Eventos e conteúdo | Item / desfecho |
|---|---|---|
| One Island / Knot | Celio no Centro Pokémon; ligação entre ilhas; acesso a Ember Spa e Mt. Ember | Meteorite, Tri-Pass, HM06 Rock Smash e oportunidade de Moltres |
| Two Island / Boon | Tutor especial para inicial evoluído; desaparecimento de Lostelle | Frenzy Plant / Blast Burn / Hydro Cannon, conforme inicial |
| Three Island / Kin | Confronto com motoqueiros; Berry Forest; Hypno ameaçando Lostelle | Resgatar Lostelle, devolver Meteorite ao pai e receber Moon Stone |

Após essa missão, Bill pode devolver o jogador a Cinnabar. Viagens futuras às ilhas ficam disponíveis no porto de Vermilion. Evitar copiar os mecanismos antigos de conexão multiplayer como exigência para o save único do Blue.

### 5.2 Após derrotar a Liga — National Dex e gemas de Celio

**FRLG:** Oak concede **National Dex** quando as condições originais são atendidas (a fonte destaca **60 espécies capturadas**). Celio solicita duas gemas para sua máquina. A exigência é **fato histórico de FRLG**, não gatilho automaticamente aprovado para a Pokédex multirregional do Blue.

1. **Ruby:** Mt. Ember, One Island, após confrontos Rockets; entregar a Celio para receber **Rainbow Pass**, liberando ilhas 4–7.
2. **Four Island / Floe:** Day Care; **Icefall Cave**, pisos que quebram, **HM07 Waterfall** e auxílio a Lorelei contra Rockets.
3. **Seven Island / Quest:** **Trainer Tower** opcional (oponentes nivelados pelo time na referência), Tanoby Key e **Tanoby Ruins** com Unown. Puzzle de Strength libera encontros nas ruínas.
4. **Six Island / Fortune:** Dotted Hole; usar Cut e escolher entradas **norte → oeste → leste → sul**; encontrar **Sapphire**, que é roubada por agente Rocket.
5. **Five Island / Chrono:** Rocket Warehouse, com requisito das duas etapas de gemas; enfrentar Rockets e cientista, recuperar **Sapphire** e entregá-la a Celio. Opcionais: **Togepi Egg**, Metal Coat, Memorial Pillar e recompensa TM42 associada a Lemonade.
6. A entrega de Ruby + Sapphire abre as consequências pós-jogo de FRLG (conectividade e entrada da **Cerulean Cave**) **somente se essas regras forem escolhidas formalmente no Blue**.

**Trainer Tower e Tanoby:** são atividades opcionais, não obstáculos para conclusão de Kanto. O detonado lista Unown distribuídos por sete câmaras de Tanoby; a correspondência exata de letras por câmara deve ser auditada com mapas/dados reais antes de configurar encontros.

### 5.3 Lendários e Pokémon especiais na referência

| Local | Pokémon / referência | Condição de acesso |
|---|---|---|
| Mt. Ember, One Island | Moltres (FRLG: nível 50) | Surf, Rock Smash, Strength e puzzle de pedras |
| Seafoam Islands | Articuno (FRLG: nível 50) | Surf + Strength; pedras para controlar correnteza |
| Power Plant, Route 10 | Zapdos (FRLG: nível 50) | Surf e exploração da usina |
| Cerulean Cave | Mewtwo (FRLG: nível 70) | National Dex e arco Ruby/Sapphire concluído |
| Rotas de Kanto | Raikou / Entei / Suicune errante | Pós-Liga, conforme inicial do jogador |
| Navel Rock (evento de distribuição) | Lugia e Ho-Oh | Mystery Ticket; **não** faz parte da campanha comum |
| Birth Island (evento de distribuição) | Deoxys | Aurora Ticket e puzzle do triângulo; **não** faz parte da campanha comum |

**Cão lendário pela escolha inicial em FRLG:** Squirtle → **Raikou**; Bulbasaur → **Entei**; Charmander → **Suicune**. Exclusividades de formas de Deoxys (Ataque/Defesa) variam entre FR/LG; **não liberar bilhetes antigos sem uma decisão de design explícita**.

**Regra de segurança Blue:** lendários, míticos, Ultra Beasts e Pokémon Paradoxo encontrados/capturados seguem a restrição de **oito insígnias locais** para uso na equipe ativa; ao viajar a região ainda não liberada, mover os especiais ao PC conforme o Plano v2 e testar o retorno à região de origem.

### 5.4 Elite Four — revanche de FireRed/LeafGreen (referência, não pós-jogo definitivo Blue)

| Adversário | Equipe de revanche FRLG |
|---|---|
| Lorelei | Dewgong, Cloyster, Piloswine, Jynx, Lapras |
| Bruno | Steelix, Hitmonchan, Hitmonlee, Steelix, Machamp |
| Agatha | Gengar, Crobat, Gengar, Misdreavus, Arbok |
| Lance | Gyarados, Kingdra, Dragonite, Aerodactyl, Dragonite |
| Campeão — inicial Bulbasaur | Heracross, Tyranitar, Gyarados, Exeggutor, Alakazam, Charizard |
| Campeão — inicial Squirtle | Heracross, Tyranitar, Arcanine, Gyarados, Alakazam, Venusaur |
| Campeão — inicial Charmander | Heracross, Tyranitar, Exeggutor, Arcanine, Alakazam, Blastoise |

O detonado relaciona a revanche à sequência pós-Liga e ao resgate de Lorelei em Four Island; requisitos precisos devem ser validados na engine/fonte antes de criar flags. **No Blue, a equipe definitiva mais forte só entra em vigor após concluir todas as campanhas principais**, usando o estudo de times oficiais fortes, não simplesmente a revanche de FRLG.

---

## 6. Encontros, objetos e atividades por área — índice de auditoria

| Área | Conteúdo específico a confirmar | Natureza |
|---|---|---|
| Route 1 | NPC que entrega item, encontros iniciais | História inicial |
| Route 22 | Rival opcional, Mankey/Pidgey, acesso posterior à Liga | Opcional no começo |
| Viridian Forest | Pikachu raro, insetos, treinadores | Progressão |
| Route 3 | Jigglypuff, treinadores e cura em Mt. Moon | Progressão |
| Mt. Moon | Clefairy, Rockets, seleção de fóssil | Obrigatório |
| Route 4 | Tutores Mega Punch / Mega Kick | Opcional |
| Routes 24/25 | Nugget Bridge, Rocket, Bill | Obrigatório |
| Route 5 | Day Care e Underground Path | Progressão |
| S.S. Anne | Cabines, rival, cura e Cut | Obrigatório |
| Route 11 / Diglett's Cave | Treinadores, Diglett/Dugtrio | Conteúdo auxiliar |
| Rock Tunnel | Escuridão, Flash, pedras Rock Smash | Progressão |
| Lavender Tower | Rival, fantasma Marowak, Mr. Fuji | Obrigatório |
| Celadon | Eevee, Tea, Fly, Game Corner/Hideout | Misto |
| Silph Co. | Card Key, Lapras, Master Ball | Obrigatório |
| Routes 12/16 | Dois Snorlax, Leftovers escondidos | Caminhos alternativos |
| Fuchsia/Safari | Gold Teeth, Surf, Strength, espécies raras | Progressão |
| Seafoam/Power Plant | Articuno / Zapdos e fauna temática | Opcional |
| Cinnabar Mansion | Secret Key, estátuas, diários Mewtwo | Obrigatório |
| Victory Road | Strength, treinadores, travas de insígnias | Obrigatório |
| Mt. Ember | Moltres, Ruby no pós-Liga | Misto |
| Icefall Cave | Waterfall, Lorelei | Pós-Liga |
| Dotted Hole | Puzzle direcional e Sapphire roubada | Pós-Liga |
| Rocket Warehouse | Recuperação Sapphire | Pós-Liga |
| Tanoby Ruins | Unown e puzzle Strength | Opcional |
| Cerulean Cave | Mewtwo e encontros altos | Pós-Liga |
| Navel/Birth | Bilhetes distribuídos em eventos antigos | Conteúdo extraordinário, não obrigatório |

**Regra de encontros Blue:** manter habitats plausíveis e tabelas separadas por mapa/método; fundir exclusivos FR/LG apenas por regras já aprovadas. Não assumir que uma taxa citada no detonado representa a tabela total. Pokémon de encontros raros, paradoxos e evoluções devem respeitar balanceamento e a identidade da região.

---

## 7. Matriz sugerida de estados de história (nomes propostos, não flags implementadas)

| Estado simbólico | Deve tornar-se verdadeiro quando... | Teste de persistência |
|---|---|---|
| KANTO_OAK_ESCORT_DONE | Oak levou o jogador ao laboratório | Não repetir autorun |
| KANTO_STARTER_CHOSEN | Poké Ball física selecionada | Não gerar quarto inicial |
| KANTO_RIVAL_LAB_DONE | Primeira batalha encerrada | Derrota/vitória avançam |
| KANTO_PARCEL_COLLECTED | Primeiro evento do Mart concluído | Não duplicar pacote |
| KANTO_PARCEL_DELIVERED | Oak recebeu encomenda | Pokédex/5 bolas uma vez |
| KANTO_FOREST_OPEN | Entrega registrada | Entradas da floresta desbloqueadas |
| KANTO_BILL_HELPED | Máquina do Bill resolvida | Ticket único |
| KANTO_SS_ANNE_CUT | Capitão concedeu Cut | Acesso por ticket respeitado |
| KANTO_HIDEOUT_CLEAR | Giovanni derrotado na base | Silph Scope único |
| KANTO_FUJI_RESCUED | Tower concluída | Poké Flute única |
| KANTO_SNORLAX_ROUTE12_DONE | Snorlax da Route 12 removido | Independente de Route 16 |
| KANTO_SNORLAX_ROUTE16_DONE | Snorlax da Route 16 removido | Independente de Route 12 |
| KANTO_SILPH_CLEAR | Giovanni derrotado na Silph | Master Ball única |
| KANTO_SAFARI_SURF_GIVEN | Secret House concedeu Surf | Não duplicar HM |
| KANTO_WARDEN_TEETH_RETURNED | Gold Teeth entregues | Strength único |
| KANTO_MANSION_KEY | Secret Key obtida | Ginásio abre |
| KANTO_LEAGUE_CLEAR | Campeão derrotado legitimamente | Hall of Fame e circuito |
| KANTO_SEVII_TRI_PASS | Convite e primeira visita confirmados | Retorno ao continente |
| KANTO_CELIO_RUBY | Ruby entregue | Rainbow Pass |
| KANTO_CELIO_SAPPHIRE | Sapphire entregue | Cerulean Cave conforme decisão |

**Observação:** não usar esses identificadores diretamente como switches numéricos. Mapear para o subsistema regional já existente e registrar pré-condições, reversões, recompensas, EventID e MapID **reais** em auditoria separada.

---

## 8. Plano de aplicação e verificação — sem quebrar outras regiões

### Prioridade A — corrigir os primeiros 30 minutos da campanha

- [ ] Início no quarto e circulação casa ↔ rua ↔ laboratório.
- [ ] Oak caminha até a posição correta junto ao rival; seleção física das três Poké Balls.
- [ ] Rival aborda jogador na saída **após o balcão** e batalha uma única vez.
- [ ] Centro Pokémon reproduz a ME de cura e retorna à música do mapa.
- [ ] Viridian Mart ativa entrega na **primeira visita**, com aproximação/deslocamento automático; o NPC oferece compras posteriormente.
- [ ] Retorno ao laboratório dá Pokédex e cinco Poké Balls sem duplicar.
- [ ] Todas as entradas de Viridian Forest permanecem bloqueadas até entregar o pacote.
- [ ] Save/reload em cada etapa, derrota para rival e teste Android de movimentos/eventos.

### Prioridade B — aventura continental completa

- [ ] Brock/Misty/Surge/Erika/Koga/Sabrina/Blaine/Giovanni, insígnias locais únicas e TMs correspondentes.
- [ ] Bill, S.S. Anne, Cut, bicicleta, Flash, Tea e passagem Saffron.
- [ ] Hideout/Lift Key/Silph Scope, Tower/Marowak/Fuji/Poké Flute e dois Snorlax.
- [ ] Silph Co./Card Key/Lapras/Master Ball e Dojo.
- [ ] Safari completo com 600 passos/30 bolas **se aprovado no Blue**; Gold Teeth, Secret House, Surf e Warden.
- [ ] Mansion/Secret Key, enigmas dos ginásios e rotas com Warp/colisões corretos.
- [ ] Oito postos Route 23, Strength Victory Road, Elite Four/campeão/Hall of Fame sem avanço por derrota.

### Prioridade C — opcionais, pós-jogo e integração

- [ ] Fósseis, tutores, presentes, pesca, Bike, Eevee, Leftovers e lendários em áreas auditadas.
- [ ] Sevii 1–3 antes da Liga com recusa de Bill tratada.
- [ ] Sevii 4–7 após Liga, Ruby/Sapphire/Celio, Icefall/Lorelei, Tanoby/Trainer Tower, Mewtwo.
- [ ] Decidir separadamente eventos históricos Mystery/Aurora Ticket, sem inventar distribuição.
- [ ] Testar pré/pós oito insígnias para Pokémon especiais; troca regional e PC/saves intactos.
- [ ] Revisar o guia/portal para exibir **times e insígnias sem níveis fixos**; status de locais experimental/preview correto.

### QA técnico obrigatório por lote

1. **Fonte:** conferir mapas e scripts reais; resolver nome simbólico → MapID instalado; validar entradas, saídas, eventos, colisões, condições e trainer IDs.
2. **Proteção:** backup e isolamento; instalação idempotente; não alterar Decades, Johto, Hoenn, Sinnoh nem estados globais de áudio e batalha.
3. **Fluxo:** testar primeira visita, repetição, derrotas, fuga, inventário/equipe cheios, cancelamento, itens recebidos, música, transições e save/reload.
4. **Balanceamento:** conferir esmeraldas globais/insígnias locais, equipes que evoluem com o estágio e chamadas compartilhadas BlueCampaign/BlueStory.
5. **Plataformas:** teste nativo Windows e teste real JoiPlay/Android (interação por toque, tiles, encontros selvagens, música e salvamento).
6. **Publicação:** manter Kanto como **prototype** até aceite integral; CI não substitui a execução no jogo. Documentar falhas por área e não subir progresso de aceite por documentação.

**Referências adicionais:** [Guia de diálogos FireRed](Guia_Dialogos_Pokemon_FireRed_EN_PT.md), [progresso funcional de Kanto](KANTO_ETAPAS.md), [músicas de Kanto](KANTO_MUSICAS_RESULTADOS.md), [testes Windows](KANTO_TESTE_WINDOWS.md).

---

## 9. Créditos e rastreabilidade

- **Fonte de fatos do percurso e das equipes FRLG:** [Pokémon Mythology — Detonado FireRed/LeafGreen](https://www.pokemythology.net/detonados/detonado-firered-leafgreen/), consultado em 13/11/2026.
- Este documento é uma **organização original de marcos, requisitos e testes** voltada ao Dessastre Paradoxal. Não incorpora a redação integral, imagens, mapas ilustrativos nem os arquivos do site de origem.
- Conflitos entre guia público, mapa efetivamente instalado e regras customizadas devem ser registrados e decididos mediante **dados auditados**, nunca resolvidos por cópia direta.

**Resultado esperado:** um roteiro verificável para levar Kanto do piloto experimental à aventura completa, sem declarar eventos como entregues antes dos testes e sem comprometer as demais regiões.
