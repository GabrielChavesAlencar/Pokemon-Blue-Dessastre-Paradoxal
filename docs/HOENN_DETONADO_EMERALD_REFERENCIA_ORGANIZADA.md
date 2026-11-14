# Hoenn — detonado de Pokémon Emerald organizado para o Dessastre Paradoxal

**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Data:** 13/11/2026  
**Referência principal:** [Detonado de Pokémon Emerald — Pokémon Mythology](https://www.pokemythology.net/detonados/detonado-emerald/)  
**Natureza:** compilação AUTORAL de fatos de jogo, matriz de eventos, equipes, desbloqueios e verificações técnicas. Não reproduz o texto, as imagens, os mapas ilustrados nem os diálogos do artigo.

> **Limite:** as informações referentes ao cartucho Pokémon Emerald NÃO provam que os eventos estejam implementados no jogo local. Este documento não instala mapas, músicas, treinadores nem eventos. Para trajetos exatos ilustrados, detalhes de quebra-cabeças e eventuais correções do detonado, consultar a fonte original e comparar com o jogo Emerald.

## 0. Como usar esta referência no projeto

Este arquivo complementa, sem substituir:

- [HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) — implementação e critérios de aceite da região.
- [HOENN_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](HOENN_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) — fontes técnicas de mapas/áudio, direitos e limitações.
- [HOENN_PREPARACAO_ZIP_E_RECURSOS.md](HOENN_PREPARACAO_ZIP_E_RECURSOS.md) — materiais a auditar.
- [PLANO_REGIOES_DESSASTRE_V2.md](PLANO_REGIOES_DESSASTRE_V2.md) — regras globais de regiões e progressão.
- [CIRCUITO_REGIONAL.md](CIRCUITO_REGIONAL.md) — circuito, progresso e viagens.
- [KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md) e [JOHTO_DETONADO_HEARTGOLD_SOULSILVER_REFERENCIA_ORGANIZADA.md](JOHTO_DETONADO_HEARTGOLD_SOULSILVER_REFERENCIA_ORGANIZADA.md) — convenções dos outros roteiros.

**Etiquetas:** **EMERALD** = referência do jogo; **BLUE REQUISITO** = adaptação desejada; **VALIDAR** = demanda auditoria de arquivos e teste real; **OPCIONAL** = não bloquear a campanha; **PÓS-LIGA** = conteúdo habilitado após Hall of Fame, salvo indicação diferente.

### Regras inegociáveis do Blue

1. Manter a engine, IA, combate, moves, habilidades, Mega/Z/Tera/Dynamax, Pokédex, PC, interface, saves e escalonamento de nível/BST do Blue/Decades; Emerald fornece o **conteúdo de mundo**, não a engine.
2. Uma insígnia HOENN inédita acrescenta uma unidade à contagem GLOBAL de esmeraldas. Os requisitos de HM e o bloqueio de Pokémon especiais usam **oito insígnias LOCAIS de Hoenn**, nunca a soma global.
3. As equipes e níveis escritos adiante são **valores históricos de Emerald**, para comparação/auditoria. Níveis não devem ser fixados no site nem sobrepor os cálculos de batalha do Blue; evoluções e escala dinâmica seguem o balanceamento atual.
4. Hoenn é região inicial possível somente quando instalada e aprovada. O novo jogo começa na casa/caminhão de Littleroot conforme a abertura implementada. Chegar a Hoenn por viagem não pode reiniciar essa abertura nem entregar outro inicial.
5. A primeira vitória na Liga de Hoenn libera **Johto e Sinnoh** pelo circuito documentado. O NPC de viagem fica na cidade inicial da região, respeitando o desbloqueio pós-Liga. Não substituir o circuito pelo navio de Emerald.
6. Pokémon lendários, míticos, Ultra Beasts e Paradoxos na party precisam das oito insígnias LOCAIS; ao viajar para região sem as oito, devem ir à Box e ficar impedidos de voltar à party. Captura e autorização de party são eventos diferentes.
7. Só após a conclusão das dez campanhas principais do circuito, habilitar o **pós-jogo global forte** do Blue; revanches históricas Emerald podem coexistir como conteúdo regional, mas não substituem a seleção global.
8. Usar flags, variáveis, mapas, switches, encontros e treinadores namespaced para HOENN, com migração de save aditiva; preservar Decades, Kanto, Johto e Sinnoh, incluindo Android.
9. Associar músicas via BlueMusic por ambiente, rival, ginásio, Equipes Magma/Aqua, lendários, Hall of Fame, cura e fanfarras. A referência musical não autoriza distribuir OSTs nem mapas de terceiros.
10. Para declarar qualquer evento pronto, exigir prova no Game.exe real, save/reload, portal/retorno e regressões. Documento e teste sintético não são prova de Hoenn jogável.

---

## 1. Linha de progressão — campanha completa

| ID | Local e percurso | Acontecimento/condição em Emerald | Resultado esperado |
|---|---|---|---|
| H01 | Littleroot Town — caminhão, casa, quarto | Mudança, relógio, casa do rival, Birch ameaçado por Zigzagoon | Escolha de Treecko, Torchic ou Mudkip |
| H02 | Route 101 → Oldale → Route 103 | Primeira batalha Brendan/May, retorno ao laboratório | Pokédex, Poké Balls, Running Shoes |
| H03 | Oldale → Route 102 → Petalburg | Norman conhece o jogador; Wally aprende a capturar Ralts | Ginásio de Norman aguarda quatro insígnias |
| H04 | Route 104 → Petalburg Woods | Encontrar empregado Devon e enfrentar recruta Aqua | Great Ball; floricultura e Wailmer Pail |
| H05 | Rustboro — ginásio de Roxanne | Desafio de Pedra | Stone Badge; Cut utilizável |
| H06 | Route 116 → Rusturf Tunnel | Resgatar Peecko e recuperar Devon Goods | Devon Corp., PokéNav, Letter e missão de entrega |
| H07 | Route 104 → barco de Mr. Briney → Dewford | Desembarque; Old Rod; ginásio escuro de Brawly | Knuckle Badge; Flash utilizável |
| H08 | Granite Cave | Encontrar Steven e entregar Letter | HM Flash recebido na entrada; TM Steel Wing de Steven |
| H09 | Dewford → Slateport, via barco | Museu, Capitão Stern, dois recrutas Aqua | Devon Goods entregues; museu liberado |
| H10 | Route 110 → rival → Mauville | Itemfinder; Rock Smash, bicicleta e Wally no ginásio | Ginásio elétrico disponível |
| H11 | Mauville — Wattson | Cercas elétricas e terceiro ginásio | Dynamo Badge; Rock Smash utilizável |
| H12 | Route 117 → Verdanturf → Rusturf Tunnel | Libertar casal entre pedras e conectar o túnel | HM Strength; atalho Rustboro–Verdanturf |
| H13 | Route 111/112 → Fiery Path → Route 113 → Fallarbor | Equipe Magma bloqueia Cable Car; cinzas e equipe de Cozmo | Soot Sack; conhecer o conflito pelo meteorito |
| H14 | Route 114 → Meteor Falls | Magma rouba meteorito; Aqua intervém | Magma deixa o bloqueio do teleférico |
| H15 | Mt. Chimney, pelo Cable Car | Confronto com Maxie; recuperar meteorito | Jagged Pass liberada para Lavaridge |
| H16 | Jagged Pass → Lavaridge | Ginásio termal de Flannery | Heat Badge; Strength utilizável; Go-Goggles |
| H17 | Route 111 — deserto e Mirage Tower | Área opcional aberta pelo Go-Goggles | Fóssil Root OU Claw; segundo só após Liga |
| H18 | Retorno a Petalburg | Norman passa a aceitar a luta com quatro insígnias | Balance Badge; HM Surf da família de Wally |
| H19 | Rotas reabertas com Surf | Backtracking, New Mauville opcional | Acesso para Route 118–119 |
| H20 | Route 118 → 119 → Weather Institute | Derrotar Shelly/Team Aqua; Castform | Ponte liberada; duelo rival; HM Fly |
| H21 | Fortree → Route 120 | Steven e Kecleon bloqueando passagem/ginásio | Devon Scope, Winona, Feather Badge, Fly utilizável |
| H22 | Routes 120–121 → Lilycove | Rival diante da loja, Contest, PokéBlock Case | Safari Zone liberada; praia leste ainda bloqueada |
| H23 | Route 122 → Mt. Pyre | Aqua leva Red Orb; Magma já levou Blue Orb | Magma Emblem; novo esconderijo habilitado |
| H24 | Jagged Pass → Magma Hideout | Magma Emblem abre entrada; Tabitha e Maxie | Groudon despertado; Maxie derrotado |
| H25 | Slateport Harbor → Lilycove Aqua Hideout | Aqua rouba submarino; teletransportes e Admin | Master Ball opcional; Wailmer deixam o mar livre |
| H26 | Route 124 → Mossdeep — ginásio | Tate & Liza em Double Battle | Mind Badge; Dive utilizável |
| H27 | Mossdeep Space Center | Contra Magma; dupla jogador + Steven contra Maxie/Tabitha | HM Dive dado na casa de Steven |
| H28 | Routes 126/128, fundo do mar | Dive para acesso a Sootopolis e Seafloor Cavern | Localizar submarino da Equipe Aqua |
| H29 | Seafloor Cavern | Shelly/Archie; Kyogre desperta | Crise climática entre Kyogre e Groudon |
| H30 | Sootopolis → Cave of Origin | Falar com Steven e Wallace; indicar Sky Pillar | Missão para despertar Rayquaza |
| H31 | Pacifidlog → Route 131 → Sky Pillar → Sootopolis | Acordar Rayquaza; intervir na crise | HM Waterfall; ginásio de Juan liberado |
| H32 | Sootopolis — Juan | Puzzle do gelo de água | Rain Badge; Waterfall utilizável; 8 insígnias |
| H33 | Route 128 → Ever Grande → Victory Road | Cachoeira, caverna, Wally e treinadores | Chegada à Liga de Hoenn |
| H34 | Liga Pokémon | Sidney → Phoebe → Glacia → Drake → Wallace | Hall of Fame, campeão e pós-Liga |
| H35 | Littleroot e regiões desbloqueadas | S.S. Ticket, TV Latias/Latios, National Dex; NPC Blue | Pós-Liga regional; Johto e Sinnoh pelo circuito Blue |

**Caminhos opcionais não devem bloquear a etapa seguinte:** Trick House, Desert/Mirage Tower, Battle Tents, Contest, New Mauville, Abandoned Ship, Safari Zone, Shoal Cave, Trainer Hill e Battle Frontier (exceto requisitos próprios dessas áreas).

---

## 2. Eventos da história detalhados e contratos de implementação

### 2.1 Littleroot, rival e primeiros objetivos

**EMERALD**
- A mudança começa no caminhão; a mãe pede a exploração da casa e o ajuste do relógio. O jogador pode retirar uma Potion no PC do quarto.
- Na casa vizinha, o jogador encontra a Poké Ball do rival e conhece Brendan/May.
- Ao avançar pela Route 101, Birch está em perigo diante de um Zigzagoon; a escolha entre **Treecko / Torchic / Mudkip** ocorre nas três Poké Balls da maleta, associadas ao combate de resgate.
- Birch conduz ao laboratório. Em Oldale, há Centro Pokémon e NPC que fornece Potion. A subida pela Route 103 inicia primeira batalha de rival, cujo inicial tem vantagem de tipo.
- O retorno ao laboratório concede Pokédex e Poké Balls; a mãe fornece Running Shoes ao deixar Littleroot. A saída oeste de Oldale, antes impedida, passa a funcionar após o marco inicial.

**BLUE REQUISITO:** sequência distinta de novo jogo e viagem; entrada/spawn auditados; inicial escolhido em objeto de mundo, não por menu arbitrário; evento do resgate único; nenhuma duplicação de itens ou Pokémon ao salvar/reabrir. Rival conserva a lógica de tipo, mas o combate usa o balanceamento Blue.

### 2.2 Petalburg, floresta e Rustboro

**EMERALD**
- Norman é o pai do protagonista e não aceita o primeiro desafio antes de quatro insígnias. Wally demonstra captura de um Ralts; Scott aparece posteriormente.
- Route 104 reúne cabana e barco de Mr. Briney. Petalburg Woods inclui treinadores de insetos, empregado da Devon e primeiro recruta Aqua; a recompensa do resgate é uma Great Ball.
- A Pretty Petal Flower Shop apresenta berries, plantio e Wailmer Pail. Há itens ocultos em trechos da Route 104.
- Em Rustboro, uma casa fornece HM01 Cut e a Poké School oferece uma interação/recompensa. Roxanne é o primeiro ginásio.
- Após a vitória, o empregado Devon tem mercadoria roubada; na Route 116/Rusturf Tunnel, o jogador enfrenta Aqua e resgata o Wingull Peecko.
- Devon Corp. reúne entrega dos itens recuperados, PokéNav e missão de levar **Letter a Steven** e **Devon Goods a Stern em Slateport**. O Match Call passa a registrar contatos, com possibilidade de revanches.
- Mr. Briney só deve prestar a travessia correspondente depois de o resgate de Peecko estar resolvido.

**VALIDAR:** colisões/autoruns em floresta, NPC Devon, fuga do ladrão, resgate, carta, carga, disponibilidade do barco e retorno seguro à Route 104.

### 2.3 Dewford, Slateport e Mauville

**EMERALD**
- Em Dewford, pescador fornece Old Rod; Brawly usa ginásio inicialmente escuro, iluminado progressivamente após vencer treinadores.
- Na entrada da Granite Cave, NPC fornece HM05 Flash. Steven recebe a Letter na caverna e entrega TM47 Steel Wing. O presidente da Devon recompensa o retorno pela entrega da carta com Exp. Share.
- Mr. Briney leva à praia de Slateport. Há treinadores de praia e Soda Pop House (sequência de três batalhas com prêmio de Soda Pop).
- Aqua ocupa o Oceanic Museum; primeiro falar no estaleiro/Shipyard para avançar a entrega. No segundo andar, Stern recebe os Devon Goods e ocorre combate contra dois recrutas Aqua. Um membro Aqua pode fornecer TM46 Thief.
- Slateport possui Battle Tent (batalha por Pokémon de aluguel), mercado de Harbor Mail e porto que será relevante mais tarde.
- Na Route 110, o jogador encontra Trick House, a passagem sob Cycling Road e mais um duelo com Brendan/May, que entrega Itemfinder.
- Em Mauville: entregar Harbor Mail à menina concede Coin Case; NPC fornece HM06 Rock Smash; loja permite escolher e depois trocar Mach Bike ou Acro Bike; Wally desafia o jogador diante do ginásio de Wattson.
- O ginásio elétrico exige alternar cercas ao pisar nos painéis. Depois de Wattson, Rock Smash pode ser usado em campo.
- Cycling Road requer bicicleta; Route 117 tem Day Care e conduz a Verdanturf. No Rusturf Tunnel, Rock Smash remove as pedras entre o casal e rende HM04 Strength; Devon entrega Repeat Ball em uma visita posterior.

**BLUE REQUISITO:** entrega de carta e carga como flags independentes; janela correta para museu; bloqueios naturais de acesso ao ginásio; bicicleta salva corretamente; escolha entre modelos reversível; quebra de rochas não pode travar passagem.

### 2.4 Vulcão, meteorito, Lavaridge e deserto

**EMERALD**
- Saindo ao norte de Mauville, há casa da família Winstrate (quatro lutas sequenciais); um membro da família aparece mais tarde em Victory Road.
- Fiery Path serve como desvio quando Magma impede o Cable Car. Route 113 contém cinza vulcânica, Soot Sack e um NPC que fabrica flautas com cinzas acumuladas.
- Em Fallarbor: Lanette no Centro Pokémon; Move Tutor mediante Heart Scale; item oculto na cratera; TM28 Dig na casa próxima à entrada da futura Desert Underpass.
- No Meteor Falls, Magma captura o meteorito de Professor Cozmo. Aqua interfere, e os Magma abandonam o bloqueio do teleférico.
- Mt. Chimney permite confrontar Maxie e recuperar o Meteorite. O meteorito pode ser levado depois a Cozmo por uma TM de recompensa.
- Jagged Pass guarda local que, futuramente, abrirá Magma Hideout. Não abrir antes do Magma Emblem.
- Lavaridge oferece ovo Wynaut (precisa de espaço na party), Herb Shop e Charcoal; o ginásio de Flannery mistura teleporte entre fontes termais e treinadores escondidos.
- Após a quarta insígnia, o rival entrega Go-Goggles; o deserto da Route 111 fica transitável. Mirage Tower é opcional: Mach Bike e Rock Smash para alcançar Root Fossil (Lileep) ou Claw Fossil (Anorith).

**BLUE REQUISITO:** progresso pelo meteorito deve alterar Cable Car sem afetar outras regiões; porta da Magma Hideout deve depender do emblema; evento do Go-Goggles deve ocorrer uma vez; local do fóssil deve impedir escolher os dois antes do pós-Liga.

### 2.5 Norman, Surf, Weather Institute e Fortree

**EMERALD**
- Norman abre o ginásio após quatro insígnias. Salas do ginásio propõem modificadores de batalha (ex.: X-Attack); vencer libera Surf em campo. Um parente de Wally entrega HM03 Surf em sua casa.
- Retornar à mãe em Littleroot após Norman oferece Amulet Coin. Surf abre trechos aquáticos em Petalburg, Oldale, Route 104, Routes 105–109, rotas próximas de Rustboro/Meteor Falls e Mauville.
- Wattson pode iniciar a missão opcional New Mauville depois do Surf.
- Para continuar a história, atravessar o rio a leste de Mauville (Route 118), encontrar pescador da Good Rod e avançar pelas gramas altas de Route 119.
- Weather Institute está ocupado por Aqua; Shelly é a Admin relevante, e os pesquisadores presenteiam o jogador com Castform (espaço na equipe; documentar fallback para Box no Blue).
- Depois da ponte há uma batalha com o rival; ao vencer, recebe HM02 Fly. Fly em campo só é liberado com Feather Badge, da próxima líder.
- Fortree tem passagens por casas suspensas; Kecleon invisível bloqueia o ginásio e alguns pontos das rotas. Steven revela Kecleon na Route 120 e entrega Devon Scope. Usar o instrumento no bloqueio do ginásio; o ginásio de Winona usa plataformas giratórias.

### 2.6 Lilycove, duas equipes e bases secretas

**EMERALD**
- A caminho de Lilycove (Routes 120–121) há chuva, treinadores, berries e NPCs Aqua anunciando Mt. Pyre.
- Em Lilycove há última luta convencional com Brendan/May na entrada da Department Store. O único Contest principal de Emerald está na cidade; lá se obtém PokéBlock Case para a Safari Zone.
- O bloqueio dos Wailmer na praia leste só termina após a fase adequada da Equipe Aqua.
- Mt. Pyre: explorar prédio funerário e subida externa; Aqua rouba **Red Orb**. Magma tomou **Blue Orb**. Guardiã concede **Magma Emblem**.
- O emblema habilita uma passagem secreta em Jagged Pass. Magma Hideout: Strength, batalhas de Admin Tabitha e Maxie, cena com Groudon acordando e fugindo.
- Slateport Harbor: Stern anuncia o submarino, e Aqua o rouba. Retornar a Lilycove, entrar em Aqua Hideout pela praia e usar teleportadores; encontrar Admin e assistir à fuga do submarino.
- **Colecionável importante:** Master Ball na área de quatro itens de Aqua Hideout (há Electrode e Nugget). Não marcar como item obrigatório da história, mas garantir que o jogador possa alcançá-lo antes do fechamento de acesso.
- Os Wailmer saem do caminho após resolver o esconderijo e o oceano para Mossdeep fica liberado.

**BLUE REQUISITO:** Red/Blue Orbs e Magma Emblem são flags diferentes; ocultar o acesso à base Magma antes do momento certo; Master Ball não duplicável; a saída dos Wailmer não deve depender de possuir a Master Ball.

### 2.7 Mossdeep, crise climática e Sootopolis

**EMERALD**
- Mossdeep: ginásio de Tate & Liza é obrigatoriamente Double Battle, com tapetes, mecanismos e teletransportes. Mind Badge libera Dive.
- Space Center: Magma invade, três recrutas enfrentados em sequência, depois luta em dupla ao lado de Steven contra Maxie e Tabitha. Na casa de Steven recebe HM08 Dive; perto do Space Center há Super Rod.
- Dive permite alcançar Sootopolis via caverna submersa na Route 126. O ginásio ainda estará fechado; visitar a cidade antes da crise é permitido, mas não resolver a oitava insígnia.
- Pelas Routes 127–128, Dive revela o submarino de Stern e a Seafloor Cavern. Dentro: Strength/Rock Smash, Admin Shelly, Archie; **Kyogre desperta**, embora o jogador vença Archie.
- O clima oscila entre chuva e sol intenso; Steven encaminha o jogador a Sootopolis, onde Groudon e Kyogre se confrontam.
- Em Cave of Origin, Wallace pergunta pelo lugar associado ao protetor do céu; a resposta é **Sky Pillar**.
- De Pacifidlog/Route 131, chegar a Sky Pillar; Wallace mostra o acesso. Despertar Rayquaza e voltar a Sootopolis. Rayquaza detém o confronto.
- Depois da resolução, Wallace concede **HM07 Waterfall** e abre seu antigo ginásio, agora ocupado por **Juan**.
- Ginásio de Juan: atravessar cada piso de gelo exatamente uma vez para formar passagem; segunda pisada causa queda ao andar dos treinadores.
- A oitava insígnia dá direito a Waterfall em campo e permite alcançar Ever Grande.

**VALIDAR:** a crise não pode iniciar antes dos eventos Magma e Aqua; salvar durante mudanças de clima deve ser seguro; Rayquaza da cena não equivale à captura; o encontro para capturá-lo ocorre em retorno separado ao Sky Pillar.

### 2.8 Ever Grande, Wally e Liga Pokémon

**EMERALD**
- Ever Grande é acessada pela cachoeira da Route 128. Centro Pokémon antecede Victory Road.
- A travessia original de Victory Road pede **Flash, Rock Smash, Strength, Surf e Waterfall**; não exige Cut, Fly nem Dive para essa travessia.
- Wally aparece com time evoluído próximo da entrada de Victory Road; revanches posteriores existem pelo Match Call.
- A Liga é composta de Sidney (Dark), Phoebe (Ghost), Glacia (Ice), Drake (Dragon) e **Wallace campeão (Water)**. Não usar Steven como campeão da primeira Liga, pois isso seria Ruby/Sapphire.
- Conclusão gera Hall of Fame e retorno narrativo à casa de Littleroot.

**BLUE REQUISITO:** preservar entradas/saídas, corredores e puzzles; impedir Liga com menos de oito insígnias locais; não fazer escalação de equipes baseada em níveis estáticos; gerar marco de primeira conclusão regional uma única vez.

---

## 3. Ginásios, quebra-cabeças, insígnias e HMs

| Ordem | Cidade | Líder | Especialidade / puzzle | Equipe original (espécies; níveis Emerald) | Insígnia | Campo liberado |
|---|---|---|---|---|---|---|
| 1 | Rustboro | Roxanne | Pedra; percurso com treinadores | Geodude 12, Geodude 12, Nosepass 15 | Stone | Cut |
| 2 | Dewford | Brawly | Lutador; escuridão reduzida a cada vitória | Machop 16, Meditite 16, Makuhita 19 | Knuckle | Flash |
| 3 | Mauville | Wattson | Elétrico; cercas e botões | Voltorb 20, Electrike 20, Magneton 22, Manectric 24 | Dynamo | Rock Smash |
| 4 | Lavaridge | Flannery | Fogo; fontes termais e quedas | Numel 24, Slugma 24, Camerupt 26, Torkoal 29 | Heat | Strength |
| 5 | Petalburg | Norman | Normal; salas com bônus de combate | Spinda 27, Vigoroth 27, Linoone 29, Slaking 31 | Balance | Surf |
| 6 | Fortree | Winona | Voador; catracas giratórias | Swablu 29, Tropius 29, Pelipper 30, Skarmory 31, Altaria 33 | Feather | Fly |
| 7 | Mossdeep | Tate & Liza | Psíquico; 2×2, tapetes e teleportadores | Claydol 41, Xatu 41, Lunatone 42, Solrock 42 | Mind | Dive |
| 8 | Sootopolis | Juan | Água; gelo que quebra na segunda pisada | Luvdisc 41, Whiscash 41, Sealeo 43, Crawdaunt 43, Kingdra 46 | Rain | Waterfall |

**Observação:** todos os números da coluna de times são apenas **referência histórica**. No Blue, a equipe-base será adaptada à fórmula existente e às regras de evolução/IA; o site não deve apresentar níveis fixos para times escalonados.

### Catálogo de HMs e itens de movimento

| HM | Onde a referência o obtém | Condição para uso fora de batalha em Hoenn |
|---|---|---|
| HM01 Cut | Casa em Rustboro | Stone Badge (Roxanne) |
| HM05 Flash | NPC na entrada de Granite Cave | Knuckle Badge (Brawly) |
| HM06 Rock Smash | Casa em Mauville | Dynamo Badge (Wattson) |
| HM04 Strength | Casal separado por rochas em Rusturf Tunnel | Heat Badge (Flannery) |
| HM03 Surf | Família de Wally após a batalha com Norman | Balance Badge (Norman) |
| HM02 Fly | Brendan/May após Weather Institute | Feather Badge (Winona) |
| HM08 Dive | Steven em Mossdeep, após Space Center | Mind Badge (Tate & Liza) |
| HM07 Waterfall | Wallace após Rayquaza resolver a crise | Rain Badge (Juan) |

**Outros desbloqueios:** Old Rod (Dewford), Good Rod (Route 118), Super Rod (Mossdeep); PokéNav/Match Call (Devon); Bicycle (Mauville, Mach/Acro), Go-Goggles (Lavaridge), Devon Scope (Route 120), PokéBlock Case (Lilycove), Magma Emblem (Mt. Pyre), Basement Key (Wattson após Surf), Storage Key (Abandoned Ship), S.S. Ticket (Norman após Liga).

### Matriz resumida de bloqueios físicos

- **Rustboro/Norman:** ginásio Petalburg fechado antes de quatro insígnias.
- **Mr. Briney:** barco antes do resgate Peecko fica indisponível para a missão; depois conecta travessias exigidas.
- **Cable Car:** bloqueio Magma durante a fase do meteorito; liberar após Meteor Falls.
- **Route 111 Desert:** tempestade impede passagem antes do Go-Goggles.
- **Fortree Gym:** Kecleon invisível exige Devon Scope.
- **Aqua Hideout/Route 124:** Wailmer só saem após avanço da base Aqua.
- **Sootopolis Gym:** bloqueado até a cena de Rayquaza.
- **Sootopolis:** entrada submersa requer Dive; visita antecipada não quebra narrativa.
- **Ever Grande / Liga:** acesso pela cachoeira e oito insígnias locais.
- **Magma Hideout:** entrada depende de Magma Emblem, não apenas da presença do mapa.
- **Área pós-Liga:** Desert Underpass, rematches, expansão do Safari, Trainer Hill e Battle Frontier seguem requisitos separados.

---

## 4. Liga, rivais e chefes — equipes de referência

### 4.1 Liga Pokémon Emerald

| Adversário | Equipe (espécie e nível original) | Notas |
|---|---|---|
| Sidney | Mightyena 46; Cacturne 46; Shiftry 48; Crawdaunt 48; Absol 49 | Temática Dark |
| Phoebe | Dusclops 48; Banette 49; Banette 49; Sableye 50; Dusclops 51 | Temática Ghost |
| Glacia | Glalie 50; Sealeo 50; Sealeo 52; Glalie 52; Walrein 53 | Temática Ice |
| Drake | Shelgon 52; Flygon 53; Kingdra 53; Altaria 54; Salamence 55 | Temática Dragon |
| Wallace (Campeão) | Tentacruel 55; Ludicolo 56; Whiscash 56; Gyarados 56; Wailord 57; Milotic 58 | Temática Water |

A ordem real da equipe em batalha pode variar; tabela para inventário de Pokémon, não script de ações nem níveis no Blue.

### 4.2 Wally — Victory Road

**Equipe original:** Magneton 41, Delcatty 43, Altaria 44, Roselia 44 e Gardevoir 45. A jornada exige também a demonstração inicial de captura de Ralts em Petalburg, confronto pré-ginásio em Mauville e encontro final em Victory Road. Revanche da Victory Road pelo Match Call, quando disponível, é conteúdo regional.

### 4.3 Steven — batalha especial após a Liga

**Local:** setor específico do Meteor Falls; requer ter vencido a Liga.  
**Equipe:** Claydol 75, Cradily 76, Armaldo 76, Aggron 76, Skarmory 77 e Metagross 78.  
**Regra Blue:** luta especial opcional, não substituir Wallace no Hall of Fame ou no gatilho de conclusão de Hoenn.

### 4.4 Equipes Magma e Aqua

| Personagem | Função de história | Localizações/etapas principais |
|---|---|---|
| Professor Birch | Mentor, resgate, Pokédex, pós-Liga | Littleroot / Route 101 |
| Brendan/May | Rival e entregas | Casa de Littleroot, Route 103, Rustboro, Route 110, Route 119, Lilycove |
| Norman | Pai e quinto líder | Petalburg |
| Wally | Rival secundário | Petalburg, Mauville, Victory Road |
| Scott | Guia de instalações de batalha | Petalburg, escolas/rotas, Battle Tents, S.S. Tidal, Frontier |
| Mr. Briney / Peecko | Viagens de barco e resgate | Route 104, Rusturf Tunnel, navio |
| Presidente Stone / Devon | PokéNav e missões | Rustboro |
| Steven | Recebe carta; Devon Scope; parceria no Space Center; Dive; chefe pós-Liga | Granite Cave, Route 120, Mossdeep, Meteor Falls |
| Stern | Devon Goods, submarino, Scanner | Slateport |
| Professor Cozmo | Meteorito | Meteor Falls/Fallarbor |
| Lanette | Sistema PC | Fallarbor |
| Maxie / Tabitha | Liderança Magma | Mt. Chimney, Magma Hideout, Space Center |
| Archie / Shelly | Liderança Aqua | Mt. Pyre, Weather Institute, Aqua Hideout, Seafloor Cavern |
| Wallace | Orienta solução da crise; campeão da Liga | Cave of Origin, Sky Pillar, Sootopolis, Liga |
| Juan | Oitavo líder, substitui Wallace no ginásio | Sootopolis |

**VALIDAR:** a lista é de encontros relevantes, não inventário completo de cada NPC secundário, coordenadas ou falas. A conferência exaustiva de NPCs/treinadores requer mapas-fonte e PBS reais.

---

## 5. Pós-Liga e recompensas

1. **Casa de Littleroot:** Norman fornece S.S. Ticket; programa de TV conduz à seleção do Pokémon errante. Vermelho → Latias; azul → Latios.
2. **National Dex:** Birch chama o personagem ao laboratório; não exige completar previamente Hoenn Dex.
3. **Casa de Steven em Mossdeep:** obter Beldum (o guia registra nível 5).
4. **Desert Underpass:** no setor de Fallarbor/Fossil Maniac, disponível após a Liga, encontrar o segundo fóssil caso o primeiro tenha sido retirado de Mirage Tower.
5. **Fóssil em Rustboro:** levar Root ou Claw Fossil à Devon Corp.; recuperar Lileep/Anorith quando concluída a restauração. Exigir espaço na party ou fluxo Blue definido e testado.
6. **Rematches de ginásio:** cada líder possui quatro séries progressivas no Match Call; são batalhas em dupla.
7. **Trainer Hill:** abre após a Liga, com 4 andares, pares de treinadores e avaliação de tempo.
8. **Safari Zone:** libera duas novas áreas com espécies de Johto.
9. **S.S. Tidal:** viagens entre Slateport, Lilycove e, depois de Scott reconhecer o treinador, Battle Frontier; dentro existem treinadores, cama de descanso e Leftovers oculto.
10. **Battle Frontier:** sete instalações, sete símbolos prata/ouro e BP, separada da contagem das oito insígnias.
11. **Encontros especiais:** Groudon/Kyogre pelas informações climáticas do Weather Institute; Latios/Latias errantes; Steven; prêmios do Frontier.
12. **Conclusão da Pokédex Hoenn:** Birch pode conceder escolha entre Chikorita, Cyndaquil e Totodile após completar os 200 registros exigidos do Emerald original (com as exceções descritas na referência); **no Blue**, harmonizar com a Pokédex multirregional, sem duplicar inicial de Johto por bug.
13. **Opcionais finais:** concursos de Lilycove, registros da National Dex e colecionáveis.

### Áreas opcionais principais — retorno com novos recursos

| Área | Quando visitar | Conteúdo / mecânica |
|---|---|---|
| Petalburg/Oldale e Routes 104–109 | Após Surf | Itens/treinadores aquáticos e rotas de Mr. Briney |
| New Mauville | Após Surf e Basement Key de Wattson | Gerador, portões azul/verde, Voltorb/Magnemite; TM24 Thunderbolt como prêmio |
| Abandoned Ship (Route 108) | Parcial com Surf; completo com Dive | Storage Key, TM13 Ice Beam, Water Stone, TM18, Luxury Ball, Scanner; troca por DeepSeaTooth ou DeepSeaScale com Stern |
| Shoal Cave (norte de Mossdeep) | Com Surf; exploração por horários | Maré alta/baixa, Shoal Shell x4 + Shoal Salt x4 → Shell Bell; setor gelado, Snorunt |
| Mirage Tower (Route 111) | Após Go-Goggles; Mach Bike + Rock Smash | Um fóssil; torre desmorona após escolha |
| Desert Underpass | Após Liga e fóssil original | Recuperar fóssil restante |
| Granite Cave — área superior | Após conseguir Mach Bike | Rampas e chão quebradiço, itens |
| Meteor Falls — cachoeira | Surf e Waterfall; Steven após Liga | Setor avançado, treinadores, batalha especial |
| Route 119 — cachoeira | Waterfall, itens e mobilidade | Trechos adicionais com Acro Bike |
| Trick House | Desafios por marcos de ginásio | Oito puzzles com prêmios; detalhes adiante |
| Mirage Island | Condição diária rara relacionada aos Pokémon carregados | Wynaut e berries; opcional aleatório |
| Safari Zone | PokéBlock Case; expansão pós-Liga | Quatro áreas tradicionais + duas novas |
| Trainer Hill | Após Liga | Modos Normal, Variety, Unique e Expert |
| Sky Pillar | História e retorno com Mach Bike | Rayquaza da cena; depois encontro capturável |
| Battle Tents | Durante campanha | Slateport (Rental), Verdanturf (comandos automáticos), Fallarbor (avaliação) |
| Battle Frontier / Artisan Cave | Após Liga/viagem | Instalações, BP, Sudowoodo e Smeargle |

### Trick House — oito provas

| Prova | Desbloqueio após | Regra principal | Prêmio do detonado |
|---|---|---|---|
| 1 | Brawly | Abrir caminho com Cut | Rare Candy |
| 2 | Wattson | Botões e passagens alternadas | Timer Ball |
| 3 | Flannery | Botões e Rock Smash | Everstone |
| 4 | Norman | Empurrar pedras com Strength | Smoke Ball |
| 5 | Winona | Cinco respostas corretas consecutivas | TM12 Taunt |
| 6 | Tate & Liza | Catracas semelhantes às de Fortree | Magnet |
| 7 | Juan | Tapetes que movem obstáculos | PP Max |
| 8 | Liga | Piso deslizante com apoios | Escolha entre Blue Tent ou Red Tent |

**Mecânica comum:** um brilho indica a localização escondida de Trick Master na sala inicial; ele revela a passagem após ser encontrado. Treinadores/puzzles e estado da prova devem persistir. A dificuldade do interior não deve impedir a campanha.

### Shoal Cave — janelas temporais de Emerald

- **Maré alta:** aproximadamente 09:00–15:00 e 21:00–03:00, pegar Shoal Shell.
- **Maré baixa:** aproximadamente 03:00–09:00 e 15:00–21:00, pegar Shoal Salt e explorar a caverna de gelo.
- **Recompensa:** 4 Shoal Shell + 4 Shoal Salt trocados com NPC local por Shell Bell.
- **VALIDAR:** o relógio do Blue/Android e o recálculo de maré após save/reload; evitar ficar preso em um warp ao mudar a hora.

---

## 6. Safari Zone — habitats e percentuais citados no detonado

**Entrada:** ter PokéBlock Case de Lilycove. Sessão usa Safari Balls, quantidade de passos limitada e mecânica específica de captura. A tabela é referência **do Emerald original**, não substituição automática das tabelas de encontro atuais do Blue.

### Setores originais

| Setor | Pokémon terrestres e chances informadas | Outros métodos |
|---|---|---|
| Sudeste / Direita | Pikachu 5%; Oddish 40%; Gloom 5%; Doduo 10%; Natu 10%; Wobbuffet 10%; Girafarig 20% | — |
| Sudoeste / Esquerda | Pikachu 5%; Oddish 40%; Gloom 5%; Doduo 10%; Natu 10%; Wobbuffet 10%; Girafarig 20% | Surf: Psyduck; Super Rod: Goldeen/Seaking |
| Noroeste / Mach Bike | Oddish 30%; Gloom 15%; Doduo 15%; Dodrio 5%; Rhyhorn 30%; Pinsir 5% | Surf: Psyduck, Golduck raro; Super Rod: Goldeen/Seaking |
| Nordeste / Acro Bike | Oddish 30%; Gloom 15%; Natu 15%; Xatu 5%; Heracross 5%; Phanpy 30% | Rock Smash: Geodude |

### Setores adicionais após a Liga

| Setor | Pokémon de grama e chance informada | Outros métodos |
|---|---|---|
| Norte | Hoothoot 5%; Ledyba 10%; Aipom 30%; Sunkern 10%; Pineco 5%; Teddiursa 30%; Houndour 5%; Miltank 5% | Rock Smash: Shuckle |
| Sul | Hoothoot 5%; Spinarak 10%; Mareep 30%; Aipom 10%; Sunkern 30%; Gligar 5%; Snubbull 5%; Stantler 5% | Surf: Marill/Wooper e Quagsire raro; pesca: Goldeen/Magikarp/Remoraid e Octillery raro |

**BLUE REQUISITO:** verificar soma de slots por método e por setor antes de importar; manter possíveis adições regionais autorais em camada separada. A referência não fornece as chances completas de *todos* os encontros em Hoenn fora do Safari, portanto não presumir que este arquivo seja um PBS de encontros pronto.

---

## 7. Lendários, míticos e capturas especiais

| Pokémon / grupo | Onde | Gatilho original Emerald | Dados de referência / cuidado |
|---|---|---|---|
| Rayquaza | Sky Pillar, Route 131 | Crise resolvida; retorno ao pilar com Mach Bike | Encontro capturável de nível 70, já antes da Elite |
| Groudon | Terra Cave, rota variável | Pós-Liga; cientista do Weather Institute indica sol extremo | Nível 70; localização muda com condição climática |
| Kyogre | Marine Cave, rota variável | Pós-Liga; cientista indica chuva intensa | Nível 70; passagem por Dive em local variável |
| Regirock | Desert Ruins, Route 111 | Abrir Sealed Chamber com Dig + Wailord/Relicanth; puzzle Rock Smash | Nível 40 |
| Regice | Island Cave, Route 105 | Câmara aberta; caminhar no perímetro horário | Nível 40 |
| Registeel | Ancient Tomb, Route 120 | Câmara aberta; Flash no centro da sala | Nível 40 |
| Latias | Errante por Hoenn | Pós-Liga; escolher cor vermelha na TV | Nível 50; fugirá facilmente |
| Latios | Errante por Hoenn | Pós-Liga; escolher cor azul na TV | Nível 50; fugirá facilmente |
| Latios/Latias oposto | Southern Island | Eon Ticket de evento legado | Encontro de nível 50, não parte obrigatória da campanha |
| Ho-Oh / Lugia | Navel Rock | Mystic Ticket de evento legado | Nível 70 cada |
| Deoxys Speed Forme | Birth Island | Aurora Ticket de evento legado | Nível 30; puzzle do triângulo |
| Mew | Faraway Island | Old Sea Map de evento legado | Nível 30; perseguir Mew em campo |

### Câmara selada e Regis — procedimento de Emerald

1. Possuir Dive, Surf e Dig, além de **Wailord na primeira posição e Relicanth na última** (ordem de Emerald).
2. Partir de Pacifidlog rumo às correntezas ao sul/oeste e localizar a entrada submersa da **Sealed Chamber**; ler inscrições Braille.
3. Usar Dive para entrar e **Dig** na parede indicada; acessar o salão seguinte com o arranjo da equipe.
4. Ler a inscrição final e ativar o terremoto que abre os três templos.
5. **Regirock:** Desert Ruins, seguir duas casas para baixo e duas à esquerda a partir da inscrição e usar Rock Smash.
6. **Regice:** Island Cave, andar uma volta completa junto à parede em sentido horário.
7. **Registeel:** Ancient Tomb, posicionar-se no centro e usar Flash.

**EMERALD:** os Regis podem ser acessados antes de vencer a Liga, desde que os recursos necessários estejam liberados.  
**BLUE:** não confundir disponibilidade do encontro com possibilidade de colocar um lendário na party antes das oito insígnias locais. Para tickets promocionais, criar somente uma regra de obtenção explicitamente aprovada: não inventar distribuição do Eon/Mystic/Aurora Ticket ou Old Sea Map.

---

## 8. Revanches de líderes — quatro séries do Emerald

**Como funciona na referência:** depois da Liga, consultar Match Call; líderes podem convidar para nova batalha no próprio ginásio. Cada líder oferece até **quatro revanches** com equipes incrementais, em formato **duplo**. Os números históricos não são níveis finais do Blue. A composição abaixo é um inventário de espécies de cada série do detonado; consultar o artigo original se for necessário conferir a ordem exata por slot.

| Líder | Revanche 1 | Revanche 2 | Revanche 3 | Revanche 4 |
|---|---|---|---|---|
| Roxanne | Golem, Kabuto, Onix, Nosepass | Omanyte, Golem, Kabutops, Onix, Nosepass | Omastar, Golem, Kabutops, Onix, Nosepass | Aerodactyl, Omastar, Golem, Kabutops, Onix, Nosepass |
| Brawly | Machamp, Meditite, Hitmontop, Hariyama | Machamp, Medicham, Hitmontop, Hariyama | Hitmonchan, Machamp, Medicham, Hitmontop, Hariyama | Hitmonlee, Hitmonchan, Machamp, Medicham, Hitmontop, Hariyama |
| Wattson | Mareep, Electrode, Magneton, Manectric | Pikachu, Flaaffy, Electrode, Magneton, Manectric | Raichu, Ampharos, Electrode, Magneton, Manectric | Electabuzz, Raichu, Ampharos, Electrode, Magneton, Manectric |
| Flannery | Magcargo, Ponyta, Camerupt, Torkoal | Growlithe, Magcargo, Ponyta, Camerupt, Torkoal | Houndour, Growlithe, Magcargo, Rapidash, Camerupt, Torkoal | Arcanine, Magcargo, Houndoom, Rapidash, Camerupt, Torkoal |
| Norman | Chansey, Slaking, Spinda, Slaking | Chansey, Slaking, Kangaskhan, Spinda, Slaking | Slaking, Blissey, Kangaskhan, Spinda, Slaking | Slaking, Blissey, Kangaskhan, Tauros, Spinda, Slaking |
| Winona | Dratini, Tropius, Pelipper, Skarmory, Altaria | Hoothoot, Dragonair, Tropius, Pelipper, Skarmory, Altaria | Noctowl, Tropius, Dragonair, Pelipper, Skarmory, Altaria | Noctowl, Tropius, Pelipper, Dragonite, Skarmory, Altaria |
| Tate & Liza | Slowpoke, Claydol, Xatu, Lunatone, Solrock | Drowzee, Slowpoke, Claydol, Xatu, Lunatone, Solrock | Hypno, Claydol, Slowpoke, Xatu, Lunatone, Solrock | Hypno, Claydol, Slowking, Xatu, Lunatone, Solrock |
| Juan | Poliwag, Whiscash, Walrein, Crawdaunt, Kingdra | Poliwhirl, Whiscash, Walrein, Crawdaunt, Kingdra | Lapras, Whiscash, Poliwhirl, Walrein, Crawdaunt, Kingdra | Lapras, Whiscash, Politoed, Walrein, Crawdaunt, Kingdra |

**BLUE REQUISITO:** registrar composição de referência como presets separados da equipe-base e do pós-jogo global forte; utilizar gatilho regional e Match Call; preservar contagem da insígnia única (revanche NÃO rende outra esmeralda) e animações/músicas de duplas.

---

## 9. Trainer Hill — conteúdo de quatro modos

**Local:** norte de Mauville, perto da família Winstrate. **Gatilho:** após Liga.  
**Regras:** quatro pisos de pares de treinadores; batalhas duplas, prêmios conforme tempo e níveis ligados ao Pokémon mais forte na referência. Entre batalhas não há cura automática.

| Modo | 1º andar (espécies de referência) | 2º andar | 3º andar | 4º andar |
|---|---|---|---|---|
| Normal | Flareon, Magneton, Pinsir, Misdreavus, Claydol, Solrock | Meditite, Heracross, Hitmontop, Mr. Mime, Plusle, Togepi | Vaporeon, Dodrio, Omastar, Nidoqueen, Charizard, Ninetales | Alakazam, Grumpig, Blissey, Tropius, Bellossom, Meganium |
| Variety | Delibird, Clefairy, Pikachu, Corsola, Starmie, Clamperl | Illumise, Spheal, Vigoroth, Jigglypuff, Jynx, Exploud | Wooper, Poliwag, Psyduck, Baltoy, Pineco, Voltorb | Unown K, P, G, O, L, N |
| Unique | Sunflora, Venusaur, Tangela, Magcargo, Rapidash, Moltres | Smeargle ×3, Cubone, Beedrill, Raticate | Cleffa, Wynaut, Magby, Charmeleon, Wartortle, Ivysaur | Houndoom, Stantler, Articuno, Sudowoodo, Slowking, Entei |
| Expert | Snorlax, Miltank, Ursaring, Gengar, Alakazam, Gardevoir | Dusclops, Ninetales, Banette, Swellow, Machamp, Ursaring | Wobbuffet, Exploud, Crobat, Dewgong, Politoed, Marowak | Forretress, Electrode, Exeggutor, Gengar, Dusclops, Misdreavus |

**VALIDAR:** dados de posição e pares completos nos arquivos originais, prêmios exatos por tempo e comportamento no Blue. Não interpretar a tabela como lista de seis Pokémon em um único treinador.

---

## 10. Battle Frontier — sete instalações e recompensas

**Disponibilidade EMERALD:** após vencer a Liga, receber S.S. Ticket e realizar a viagem de navio que apresenta Scott. Frontier Pass registra progresso, símbolos, BP e Battle Record. Existem regras de seleção de três Pokémon, formatos nível 50/Open Level e restrições específicas de espécies na referência. A capacidade multirregional do Blue exige adaptar ou isolar essas regras, não aplicar proibições de Emerald a toda a campanha.

| Instalação | Frontier Brain | Mecânica | Símbolo | Primeiro encontro (prata) | Segundo encontro (ouro) |
|---|---|---|---|---|---|
| Battle Pike | Lucy | 3 portas; 14 salas por série; eventos aleatórios de cura, combate ou status | Luck | 28 salas | 140 salas |
| Battle Dome | Tucker | Torneio de 16; selecionar 2 dos 3 Pokémon; chave simples para Brain | Tactics | 20º adversário, final do 5º torneio | 40º adversário, final do 10º |
| Battle Arena | Greta | Julgamento após 3 turnos: Mind, Skill e Body | Guts | 28ª batalha (7ª do 4º bloco) | 56ª batalha (7ª do 8º) |
| Battle Factory | Noland | Pokémon alugados, com troca opcional após cada vitória | Knowledge | 21ª batalha (7ª do 3º bloco) | 42ª batalha (7ª do 6º) |
| Battle Tower | Anabel | Séries de 7; itens equipados distintos; singles/doubles/multi | Ability | 35ª batalha consecutiva | 70ª consecutiva |
| Battle Palace | Spenser | Pokémon escolhem movimentos conforme natureza/comportamento | Spirits | 21ª batalha | 42ª batalha |
| Battle Pyramid | Brandon | Escuridão, 7 pisos/série, itens da mochila próprios | Brave | 21º piso (3º topo) | 70º piso (10º topo) |

**Nota de contagem:** algumas descrições do guia mencionam o número de adversários concluídos *antes* do Brain (por exemplo, “19 vitórias e Tucker na final”). A tabela acima registra a posição do próprio confronto, não uma regra nova do Blue. Confirmar discrepâncias em testes de Emerald antes de codificar.

### Equipes dos Frontier Brains — prata e ouro

| Brain | Equipe prata | Equipe ouro |
|---|---|---|
| Lucy | Seviper, Shuckle, Milotic | Seviper, Gyarados, Steelix |
| Tucker | Swampert, Salamence, Charizard | Swampert, Latias, Metagross |
| Greta | Heracross, Umbreon, Shedinja | Umbreon, Gengar, Breloom |
| Noland | Equipe de aluguel variável | Equipe de aluguel variável |
| Anabel | Alakazam, Entei, Snorlax | Raikou, Snorlax, Latios |
| Spenser | Crobat, Slaking, Lapras | Arcanine, Slaking, Suicune |
| Brandon | Regirock, Regice, Registeel | Articuno, Zapdos, Moltres |

**Outras regras/recompensas:**
- Battle Pike pode oferecer recuperação, salas com Pokémon, duplas, lutas simples ou problemas de status.
- Battle Arena: Mind avalia intenção ofensiva, Skill eficiência e Body condição atual.
- Battle Factory: três emprestados; permitir trocar um dos Pokémon por um da equipe vencida quando aplicável.
- Battle Tower: opção Single, Double e Multi; encontros com Anabel em Single; premiação progressiva.
- Battle Palace: jogador não escolhe diretamente o golpe; a natureza e o comportamento do Pokémon importam.
- Battle Pyramid: trocar temporariamente a mochila, itens encontrados dentro permanecem próprios da instalação; nenhuma captura interna.
- Acumular Battle Points (BP) e trocar por itens em loja específica; preservar Frontier Pass/recordes.
- Obter os **sete símbolos de prata** rende Lansat Berry de Scott; **sete símbolos de ouro** rendem Starf Berry.
- **Battle Tower:** Scott concede Silver Shield após 50 vitórias consecutivas e Gold Shield após 100.
- Perto do Battle Palace há **Sudowoodo** de nível 40, revelado com Wailmer Pail. A passagem daí permite visitar Artisan Cave, habitat de Smeargle.
- Os símbolos do Frontier NÃO são insígnias de ginásio e não geram esmeraldas globais.

**Situação de implementação:** conteúdo de pós-jogo de grande porte. Dividir por instalação e não afirmar que os sete modos existem apenas porque o mapa principal da Battle Frontier foi importado.

---

## 11. Índice de itens, prêmios e NPCs para auditoria

| Item/recurso | Primeira obtenção relevante | Motivo de teste |
|---|---|---|
| Potion inicial | PC do quarto em Littleroot | Interação única, persistência |
| Running Shoes | Mãe depois da missão de Birch/rival | Corrida habilitada |
| Wailmer Pail | Pretty Petal Flower Shop | Plantar berries, Sudowoodo |
| Great Ball | Empregado Devon após floresta, e recompensa de resgate | Recompensas não duplicadas |
| HM01 Cut | Rustboro | Stone Badge |
| PokéNav/Match Call | Devon Corp. | Comunicação/rematches |
| Letter / Devon Goods | Devon Corp. | Entregas separadas |
| Exp. Share | Mr. Stone após carta entregue | Recompensa opcional |
| Old Rod | Dewford | Pesca |
| HM05 Flash | Granite Cave | Knuckle Badge |
| TM47 Steel Wing | Steven na Granite Cave | Entrega de Letter |
| TM46 Thief | Museu Slateport, membro Aqua | Interação opcional |
| Harbor Mail | PokéMart de Slateport | Troca em Mauville |
| Coin Case | NPC de Mauville | Acesso às moedas |
| HM06 Rock Smash | Mauville | Dynamo Badge |
| Mach Bike / Acro Bike | Loja de Mauville | Seleção e troca |
| Itemfinder | Rival, Route 110 | Itens ocultos |
| HM04 Strength | Rusturf Tunnel | Uso após Heat Badge |
| Soot Sack | Casa na Route 113 | Coletar cinzas |
| TM28 Dig | Fallarbor | Puzzle dos Regis |
| Meteorite | Mt. Chimney | Quest de Cozmo |
| Ovo Wynaut | Lavaridge | Espaço na equipe |
| Charcoal | Lavaridge Herb Shop | NPC/itens |
| Go-Goggles | Rival depois de Flannery | Abrir deserto |
| Root/Claw Fossil | Mirage Tower | Exclusão mútua até pós-Liga |
| HM03 Surf | Parente de Wally pós-Norman | Balance Badge |
| Amulet Coin | Mãe após Norman | Volta a Littleroot |
| Good Rod | Route 118 | Pesca |
| Castform | Weather Institute | Resgate de Aqua |
| HM02 Fly | Rival após Weather Institute | Feather Badge |
| Devon Scope | Steven, Route 120 | Revelar Kecleon |
| PokéBlock Case | Contest de Lilycove | Safari Zone |
| Magma Emblem | Guardiã de Mt. Pyre | Abrir Magma Hideout |
| Master Ball | Aqua Hideout | Itens e Electrode |
| Super Rod | Mossdeep | Pesca |
| HM08 Dive | Steven após Space Center | Mind Badge |
| HM07 Waterfall | Wallace após Rayquaza | Rain Badge |
| Scanner | Abandoned Ship com Dive | Troca por DeepSeaTooth/Scale |
| TM13 Ice Beam | Sala trancada de Abandoned Ship | Storage Key |
| TM24 Thunderbolt | Wattson, missão New Mauville | Desligar gerador |
| S.S. Ticket | Norman após Liga | S.S. Tidal |
| Beldum | Casa de Steven após Liga | Resgate de presente |
| Frontier Pass | Entrada da Battle Frontier | Registrar símbolos e BP |

### Música — associação por situação, não por arquivo

Inventariar faixas sob direitos adequados para: cidades de Hoenn, Route/sea, cavernas, praia, vulcão e clima, ginásios, rival, Birch/Steven, Aqua/Magma e Admin/chefes, cenas de Groudon/Kyogre/Rayquaza, pesca, Safari/Contest/Battle Tent, Liga/Elite/Wallace, Hall of Fame, cura (ME), insígnia, obtenção de item, telefone Match Call, S.S. Tidal, Battle Frontier e Frontier Brain. **Não** derivar nomes de arquivo ou associar música sem verificar o catálogo real do pacote e o sistema BlueMusic.

---

## 12. Especificação de flags/eventos para o Codex

**Importante:** os identificadores a seguir são nomes **conceituais**, não números de switches já reservados, nem prova de que existem no projeto. Durante a importação, mapear os nomes a flags de HOENN em infraestrutura própria, validando o runtime e os MapIDs reais.

| Grupo | Marcos que precisam persistir |
|---|---|
| Abertura | HOENN_INTRO_SEEN, HOENN_STARTER_CHOSEN, HOENN_BIRCH_RESCUED, HOENN_RIVAL_103_WON, HOENN_POKEDEX_GIVEN, HOENN_RUNNING_SHOES |
| Devon | HOENN_DEVON_FOREST, HOENN_PEECKO_RESCUED, HOENN_GOODS_RECOVERED, HOENN_LETTER_GIVEN, HOENN_LETTER_DELIVERED, HOENN_STERN_DELIVERY |
| Ginásios | HOENN_BADGE_STONE, KNUCKLE, DYNAMO, HEAT, BALANCE, FEATHER, MIND, RAIN (ligar às chaves oficiais do projeto) |
| Meteorito | HOENN_CABLE_CAR_BLOCKED, HOENN_COZMO_MET, HOENN_METEORITE_STOLEN, HOENN_MAXIE_CHIMNEY, HOENN_METEORITE_RETRIEVED |
| Meio da jornada | HOENN_GO_GOGGLES, HOENN_SURF_GIVEN, HOENN_CASTFORM_REWARDED, HOENN_DEVON_SCOPE, HOENN_KECLEON_GYM_CLEARED |
| Organizações | HOENN_RED_ORB_STOLEN, HOENN_MAGMA_EMBLEM, HOENN_GROUDON_WOKEN, HOENN_SUBMARINE_STOLEN, HOENN_AQUA_HIDEOUT_CLEAR, HOENN_MASTER_BALL_CLAIMED |
| Crise | HOENN_SPACE_CENTER_CLEAR, HOENN_DIVE_GIVEN, HOENN_SEAFLOOR_CLEAR, HOENN_KYOGRE_WOKEN, HOENN_CRISIS_ACTIVE, HOENN_SKY_PILLAR_VISITED, HOENN_RAYQUAZA_WOKEN, HOENN_CRISIS_RESOLVED |
| Liga | HOENN_WATERFALL_GIVEN, HOENN_VICTORY_ROAD_WALLY, HOENN_LEAGUE_FIRST_CLEAR, HOENN_HALL_OF_FAME |
| Pós-Liga | HOENN_SS_TICKET, HOENN_ROAMER_CHOICE, HOENN_NATIONAL_DEX, HOENN_BELDUM_CLAIMED, HOENN_STEVEN_REMATCH, HOENN_FRONTIER_PASS |
| Opcionais | HOENN_FOSSIL_FIRST_CHOICE, HOENN_SECOND_FOSSIL_CLAIMED, HOENN_TRICK_HOUSE_STAGE, HOENN_NEW_MAUVILLE_OFF, HOENN_SCANNER_TRADED, HOENN_REGI_CHAMBER_OPEN |

**Contrato técnico:** ao carregar save antigo, flags ausentes devem receber default seguro sem reemitir prêmios; usar conclusões efetivas existentes ao migrar, nunca resetar badges/quest. Flags de encontro e captura devem resistir a reload/derrota; manter saídas livres após cutscenes; separar flags da história e os bloqueios locais de party.

---

## 13. Testes necessários — duas barras de aprovação

### Barra A — engenharia/recursos auditados

- [ ] Confirmar fonte, licença e checksums dos recursos reais de Hoenn; conferir MapInfos, Tilesets, gráficos, áudio e PBS.
- [ ] Inventariar **todos** os mapas e interiores, incluindo coordenadas/warps, NPCs, objetos, treinadores, itens, encontros e músicas; este MD não supre esses dados.
- [ ] Isolar IDs de mapas, switches, variáveis, common events e self-switches; não colidir com Decades, Kanto, Johto ou Sinnoh.
- [ ] Criar mapeamento origem→destino e backups antes de staging, com rollback testado.
- [ ] Registrar HOENN no circuito sem disponibilizar destino falso; integrar testes ao menu **Testar Hoenn** apenas quando o piloto existir.
- [ ] Converter equipes para presets e eventos Blue, preservando formulação de batalha em memória.
- [ ] Publicar somente depois de CI/regressão verde e sem substituir Game.exe ou saves locais.

### Barra B — aceite jogável e teste no Game.exe

- [ ] Novo jogo em Hoenn começa no interior correto; viagem posterior não reinicia tutorial.
- [ ] Sequência Birch + três Poké Balls + rival, Pokédex e Running Shoes; teste de derrota, reload e retomada.
- [ ] Devon, Peecko, Letter, Slateport Museum e Stern não duplicam entregas.
- [ ] Os **oito ginásios** abrem nas condições corretas, puzzles funcionam e cada um dá uma insígnia local/uma esmeralda global única.
- [ ] Todos os HMs respondem às insígnias LOCAIS (inclusive quando há muitas esmeraldas de outras regiões).
- [ ] Cable Car/Meteor Falls/Maxie/Jagged Pass e Go-Goggles funcionam por eventos, sem bloqueios acidentais.
- [ ] Weather Institute, Castform, Fly, Kecleon/Devon Scope e Winona funcionam.
- [ ] Mt. Pyre, ambos Orbs, Magma Emblem, duas bases, submarino, Wailmer e Master Ball funcionam.
- [ ] Tate & Liza é batalha dupla, Space Center aceita parceria com Steven, Dive e travessias funcionam.
- [ ] Seafloor Cavern, crise climática, Cave of Origin, Sky Pillar, Rayquaza, Wallace e Juan acontecem na ordem.
- [ ] Victory Road e Liga permitem conclusão; Wallace é campeão; Steven fica opcional após a Liga.
- [ ] Hall of Fame libera Johto/Sinnoh (no circuito Blue) e NPC de viagem inicial; permanece correto após reload.
- [ ] Regiões já existentes continuam jogáveis; saves de Johto/Kanto/Decades não são apagados, nem IDs/sprites/músicas substituídos.
- [ ] Especiais (lendários, míticos, UB, Paradoxos) enviados à Box na entrada em região sem oito insígnias; retirada impedida com mensagem adequada.
- [ ] Músicas BGM/ME, cura, transições, prioridades de evento e fades verificadas auditivamente em PC e Android.
- [ ] Opcional: fósseis, Safari, Contest, Battle Tents, Trick House, New Mauville, Abandoned Ship, Shoal Cave e Trainer Hill.
- [ ] Pós-Liga: Beldum, roaming, Steven, Regis, Groudon/Kyogre, revanches e Frontier por estágios com testes próprios.

**Separar evidências:** (a) dados/arquivos conferidos; (b) testes automatizados; (c) travessia manual no Game.exe; (d) testes no Android. Marcar cada setor apenas pelo estágio realmente atingido. Nunca promover planejamento a entrega jogável.

---

## 14. Lacunas não resolvidas por um detonado

Esta fonte descreve a aventura e muitos colecionáveis, mas **não é dump integral do jogo**. Permanecem por auditar diretamente nos mapas e PBS do projeto-fonte real: lista de todos os NPCs, diálogos exatos e traduções; coordenadas de cada objeto/teleporte; encontros selvagens completos por rota/horário/surf/pesca; todos os itens ocultos; equipes/moves/IVs/items dos treinadores normais; todas as transições; ID físico de músicas e seus direitos; detalhes dos puzzles ilustrados; comportamento real de scripts/RMXP/Essentials e conflitos com sistemas Blue.

**Precedência em conflito:** plano multirregional do Blue → plano técnico Hoenn → recursos auditados e testes do jogo real → fatos Emerald desta referência → artigos ou mapas ilustrados consultivos. Ruby/Sapphire e ORAS são adições separadas, não motivo para alterar o enredo central Emerald sem decisão de projeto.

## 15. Fonte, atribuição e consulta adicional

- [Pokémon Mythology — Detonado Emerald](https://www.pokemythology.net/detonados/detonado-emerald/) — fonte principal consultada para ordem da aventura, equipes de líderes/Liga/revanches, missões, áreas opcionais e pós-jogo.
- [Pokémon Mythology — página de Emerald](https://www.pokemythology.net/emerald/) — índice suplementar de recursos relacionados.
- [Plano técnico de Hoenn](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) — fonte normativa do projeto para implementação e QA.

**Aviso de direitos:** nenhum texto, mapa ilustrado, imagem ou arquivo musical do site foi incorporado. Este Markdown é um índice de referência factual e uma especificação original para organização do desenvolvimento; a consulta do guia completo continua disponível pelo link acima.
