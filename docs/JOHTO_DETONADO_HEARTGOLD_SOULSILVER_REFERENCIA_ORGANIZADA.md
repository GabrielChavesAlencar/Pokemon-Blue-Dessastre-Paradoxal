# Johto — Detonado HeartGold/SoulSilver organizado para o Dessastre Paradoxal

**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Data de organização:** 13/11/2026  
**Fonte principal:** [Detonado HeartGold/SoulSilver — Pokémon Mythology](https://www.pokemythology.net/detonados/detonado-heartgold-soulsilver/)  
**Objetivo:** roteiro autoral de referência, índice de conteúdo e critérios de adaptação da campanha de Johto.  
**Natureza:** este arquivo **não** é transcrição do artigo, cópia de seus mapas/imagens, dump de diálogos nem evidência de funcionalidades instaladas no Game.exe.

> **Leitura indispensável:** os nomes, espécies, locais, itens e encadeamentos abaixo descrevem o funcionamento de **HeartGold/SoulSilver (HGSS)**. O estado de implementação real do Blue deve ser demonstrado separadamente. As equipes são referências de composição, **não ordens para fixar níveis** no jogo.

## 0. Regras de integração — não quebrar o Blue/Decades

A ordem de precedência é: [Plano de regiões v2](PLANO_REGIOES_DESSASTRE_V2.md) → [implementação definitiva de Johto](JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md) → [etapas de Johto](JOHTO_ETAPAS.md) → [auditoria offline 12/12](JOHTO_OFFLINE_FASE_12_AUDITORIA_INTEGRACAO.md) → este roteiro factual.

- **Uma campanha, um save:** manter todas as conquistas, caixas, golpes, Pokémon e progresso já existentes. Viajar entre regiões não reinicia o jogo.
- **Johto pode ser região inicial.** O jogador novo começa **dentro do quarto/casa de New Bark**. A chegada posterior por NPC/portal deve usar o ponto de viagem, e nunca repetir a escolha do inicial ou recomeçar a narrativa.
- **Motor de batalha do Dessastre/Decades:** não importar lógica de combate de HGSS ou de outro fangame. Equipes-base de referência podem ser cadastradas; IA, progressão, modos e cálculo dos níveis continuam os já existentes.
- **Uma insígnia única de Johto acrescenta uma esmeralda global**, somada às insígnias de outras regiões; a permissão de HMs, porém, depende das **insígnias locais de Johto**.
- **Não usar níveis fixos** dos times HGSS para líderes, treinadores, campeões ou exibição no site. O jogo ajusta os níveis pela função compartilhada e pode escalar espécies/evoluções conforme a progressão, respeitando as regras atuais.
- **Pokémon especiais** (lendários, míticos, Ultra Beasts e Paradoxos) só podem permanecer na party na região ativa quando houver **oito insígnias locais**. Na viagem para região onde não há as oito, enviá-los à Box e impedir retirada para a equipe. O encontro/captura continua sujeito ao roteiro de cada região.
- **Ao vencer a Liga de Johto:** liberar **Kanto + Hoenn** no circuito regional do Blue. Não fazer o desbloqueio depender de vencer mais oito ginásios em Kanto como ocorre no pós-jogo HGSS; Kanto já tem campanha independente no projeto.
- **Pós-jogo global forte:** somente após concluir as dez campanhas principais do circuito, buscar as **equipes oficialmente documentadas mais fortes**, sem substituir times existentes por tabelas de revanche arbitrárias.
- **Isolamento:** não renumerar MapIDs nem sobrescrever mapas, PBS, sprites, áudio, scripts, saves e conteúdo de Decades/Kanto/Hoenn/Sinnoh. Usar namespace JOHTO para flags/variáveis novas e migrações aditivas.
- **Áudio:** BGM por mapa, BGM de encontro/batalha, ME de cura, item/insígnia, fanfarras, fades, música Rocket e lendários; o arquivo de referência não concede licença de redistribuição de recursos da Nintendo ou do site.
- **Situação documentada na auditoria offline:** 12/12 etapas offline concluídas, porém **0/13 fases jogáveis aprovadas e 0/13 testadas no Game.exe** naquela auditoria. Não promover estes números apenas por criar este MD; reavaliar somente com provas novas.

### Legenda de acompanhamento

- **HGSS:** dado factual de referência, ainda não adaptado.
- **REQUISITO BLUE:** comportamento a preservar ou implementar segundo planos internos.
- **VALIDAR NO JOGO:** mapa/evento/flag/áudio/compilação deve ser verificado na instalação real.
- **OPCIONAL:** conteúdo cuja ausência não pode bloquear a Liga.
- **PÓS-JOGO HGSS:** recurso do cartucho original que não redefine o circuito regional do Blue.

---

## 1. Ordem principal completa de Johto

| Etapa | Área | Dependência e ação principal | Resultado / teste |
|---|---|---|---|
| 01 | New Bark Town, casa e laboratório de Elm | Escolher Chikorita, Cyndaquil ou Totodile; receber missão de Mr. Pokémon | Inicial único; PokéGear; saída para Route 29 |
| 02 | Route 29 / Cherrygrove / Route 30 | Passeio do guia local; Running Shoes, Map Card, Apricorn Box | Acesso à casa de Mr. Pokémon |
| 03 | Mr. Pokémon / retorno a New Bark | Receber Mystery Egg e Pokédex de Johto; telefonema de Elm; primeiro duelo com Silver | Entregar ovo, nomear rival e habilitar captura |
| 04 | Routes 30–31 / Violet / Sprout Tower | Limpar acesso à torre e enfrentar Elder Li | TM Flash; liberar desafio ao primeiro ginásio |
| 05 | Violet Gym | Vencer Falkner | Zephyr Badge + TM51 Roost; ovo de Togepi com assistente |
| 06 | Route 32 / Union Cave / Route 33 | Travessia, treinamento e contato com Rocket no poço | Acesso a Azalea; Old Rod |
| 07 | Azalea / Slowpoke Well | Falar com Kurt; expulsar Rockets e Proton | Poço resolvido, Kurt disponível, ginásio aberto |
| 08 | Azalea Gym / rival | Vencer Bugsy e Silver na saída oeste | Hive Badge + TM89 U-turn; caminho a Ilex |
| 09 | Ilex Forest / Route 34 | Recuperar dois Farfetch'd, receber Cut, atravessar floresta | Day Care, Headbutt, Goldenrod acessíveis |
| 10 | Goldenrod City | Explorar loja, rádio, bicicleta e subterrâneo; registrar Radio Card | Whitney retorna ao ginásio |
| 11 | Goldenrod Gym / Routes 35–36 | Vencer Whitney, conversar novamente, obter SquirtBottle | Plain Badge + TM45 Attract; Sudowoodo removido |
| 12 | National Park / Route 37 / Ecruteak | Parque, Pokéathlon opcional, Dance Theater e Burnt Tower | HM Surf; cães lendários despertados |
| 13 | Ecruteak Gym / Route 42 | Vencer Morty; obter Strength na saída leste | Fog Badge + TM30 Shadow Ball; Surf em campo |
| 14 | Routes 38–39 / Olivine Lighthouse | Conhecer Jasmine e o Ampharos enfermo | Inicia busca da SecretPotion |
| 15 | Routes 40–41 / Cianwood | Surfar, encontrar Suicune/Eusine e receber remédio | Acesso ao ginásio de Chuck |
| 16 | Cianwood Gym / Olivine | Vencer Chuck; receber Fly; curar Ampharos; enfrentar Jasmine | Storm Badge + Mineral Badge; Safari libera |
| 17 | Route 42 / Mahogany / Route 43 / Lake of Rage | Evento Red Gyarados; encontrar Lance | Acesso ao esconderijo Rocket |
| 18 | Rocket Hideout / Mahogany Gym | Senhas, Murkrow, Ariana, Electrodes; vencer Pryce | HM Whirlpool; Glacier Badge |
| 19 | Goldenrod Radio Tower / Underground | Disfarce Rocket, Petrel, rival, diretor, Card Key, Proton, Ariana e Archer | Torre salva; Rainbow Wing ou Silver Wing |
| 20 | Route 44 / Ice Path / Blackthorn | Deslizamentos, pedras, HM Waterfall e Kimono Girl | Acesso à cidade do último ginásio |
| 21 | Blackthorn Gym / Dragon's Den | Vencer Clair, atravessar redemoinho, prova do ancião | Rising Badge + TM59 Dragon Pulse |
| 22 | Route 45 / New Bark / Dance Theater | Retorno a Elm, Master Ball, cinco Kimono Girls | Clear Bell ou Tidal Bell |
| 23 | Bell Tower ou Whirl Islands | Ritual Ho-Oh (HG) / Lugia (SS), cumprir encontro obrigatório | Libera caminho ao Indigo Plateau |
| 24 | Route 27 / Tohjo Falls / Route 26 / Victory Road | Surfar para leste, usar Waterfall, checar oito insígnias, rival | Indigo Plateau |
| 25 | Liga de Johto | Will → Koga → Bruno → Karen → Lance | Hall of Fame; primeira conclusão de Johto salva |
| 26 | Circuito Blue / extras | NPC de viagem em New Bark, duas regiões vizinhas, opcionais | Kanto + Hoenn liberadas; pendências opcionais independentes |

**Dependências importantes:** o período de exploração entre Ecruteak, Cianwood e Olivine admite desvios, mas Jasmine exige a cura de Ampharos. Entrar em Mahogany cedo não deve permitir avançar no ginásio antes do evento Rocket. Uma rota aberta geograficamente não equivale a uma missão concluída.

---

## 2. Detonado detalhado por arco, eventos e NPCs

### 2.1 New Bark: início, primeiro Pokémon e PokéGear

**HGSS:** quarto do jogador → mãe (funções iniciais do menu) → laboratório Elm. Ethan/Lyra e seu Marill aparecem no vilarejo; Silver observa a janela externa do laboratório. Três iniciais ficam disponíveis: **Chikorita (Planta), Cyndaquil (Fogo), Totodile (Água)**. Elm pede visita a Mr. Pokémon. Assistente concede **5 Potions** ao sair; o Pokémon principal acompanha o treinador em HGSS. Voltar à mãe concede **PokéGear**; Elm registra contato telefônico.

**Eventos necessários:** introdução no interior; portas da casa; fala de Elm antes e depois da escolha; exclusividade da seleção; primeiro Pokémon entregue à party; inicial restante que dá vantagem de tipo a Silver; funções de acompanhamento apenas se compatíveis com o engine do Blue.

**Validações:** salvar antes/depois da escolha, reentrar no laboratório, iniciar de outra região e retornar a New Bark, cancelar conversas e assegurar que o inicial não seja concedido duas vezes.

### 2.2 Routes 29–30 e Cherrygrove: tutorial e Mystery Egg

- Route 29: encontros comuns com **Pidgey, Rattata e Sentret** de dia, **Hoothoot** à noite; Apricorn disponível após obter a caixa.
- Cherrygrove: guia da cidade apresenta Center, Mart e acesso à Route 30; entrega **Running Shoes**; no caminho adiante entrega componente de **mapa do PokéGear**.
- Route 30: NPC perto da árvore oferece **Apricorn Box**; uma Apricorn por árvore após a renovação diária. Encontros dependentes de versão: Caterpie/Metapod/Spinarak (HG) e Weedle/Kakuna/Ledyba (SS), com janelas de horário.
- Uma dupla de treinadores impede o caminho oeste no início; liberar o corredor quando o evento de retorno permitir.
- Casa de **Mr. Pokémon**: receber **Mystery Egg**; Oak entrega a **Johto Dex**. A chamada de Elm provoca retorno obrigatório a New Bark.
- Na saída de Cherrygrove, **Silver** inicia primeira luta, usando inicial de vantagem. No laboratório, ocorre descoberta do furto, nomeação do rival e entrega do ovo.
- Após conversar com a mãe, sistema de **depósito automático de dinheiro** e presentes por entrega no Mart ficam disponíveis (subsistema opcional se não integrado).
- Ethan/Lyra demonstra captura e concede **5 Poké Balls**. Só aqui habilitar a captura conforme roteiro HGSS.

**Critérios BLUE:** telefonema e rival não se repetem após load; Pokédex da campanha é compatível com a Pokédex global; presentes da mãe não sobrescrevem inventário; treinador não fica travado após autorun.

### 2.3 Violet, Sprout Tower e primeiro ginásio

- Routes 30–31: treinadores, contatos telefônicos opcionais, Bellsprout, entradas iniciais da Dark Cave e acesso às Ruins of Alph.
- Violet City: visita ao Centro Pokémon, NPC de troca de shards por berries, **Vs. Recorder** em HGSS; acesso ao ginásio depende do confronto na Sprout Tower.
- Route 36, perto de Violet: NPC fornece **HM06 Rock Smash**; uso em campo fica atrelado à insígnia local correta.
- **Sprout Tower:** treinadores Sage, Gastly à noite, rival no topo, derrota do ancião **Li** com recompensa **TM70 Flash**.
- **Falkner:** puzzle de passarelas/elevador; recompensa **Zephyr Badge + TM51 Roost**.
- Após a vitória: chamada de Elm; assistente no PokéMart entrega **ovo de Togepi**, exigindo espaço conforme referência. Uma Kimono Girl acompanha a saída; ovo gera Togepi e há retorno opcional a Elm com o recém-nascido.
- Route 32 abre com a primeira insígnia; há **Old Rod** no Centro da rota e oferta de **Lure Balls**. Union Cave conecta à Route 33.

**Prova de aceite:** sem vencer Li não deve haver acesso prematuro ao Falkner; ganhar Zephyr só uma vez; conferir obtenção e incubação do ovo, Center, Mart, interiores, colisões e retorno de cavernas.

### 2.4 Azalea e o poço dos Slowpoke

- Route 33: clima chuvoso; Kurt discute com Rocket na entrada do Slowpoke Well.
- Azalea: Rocket bloqueia ginásio. Conversar com **Kurt**, que investiga os Slowpoke, libera acesso ao poço.
- **Slowpoke Well:** Rockets, itens, luta contra **Proton** (Zubat e Koffing na referência); ao vencer, desaparece o bloqueio da cidade.
- **Kurt:** entrega **Fast Ball**, recebe Apricorn para fabricação de Poké Balls especiais e devolve a bola após o tempo do serviço; neta oferece número de telefone.
- **Bugsy:** ginásio com plataformas/cordas em forma de Spinarak; **Hive Badge + TM89 U-turn**.
- **Silver:** emboscada a oeste de Azalea antes de Ilex; elenco de referência: **Gastly, Zubat e evolução do inicial**.

**Teste negativo:** acessar gym antes de salvar Slowpoke; reencontrar Proton após conclusão; entregar nova Apricorn; salvar durante o fabrico; regressar do Ilex após rival.

### 2.5 Ilex Forest, Cut, Headbutt e Route 34

- Um trabalhador pede ajuda com **dois Farfetch'd**: aproximar-se pelo lado certo, usando posição/orientação e ruídos de galhos para encurralar as aves; concluir **ambos** antes da recompensa.
- Receber **HM01 Cut**, cortar obstáculo e seguir em direção ao norte. Um NPC ensina **Headbutt**; árvores especiais podem produzir encontros (incluindo Pineco, Exeggcute, Aipom ou Heracross, conforme local).
- Encontrar Kimono Girl extraviada; o Pokémon companheiro orienta a saída.
- **Route 34:** treinadores, policial noturno, encontros de Drowzee, Abra e Ditto; apresentação de Ethan/Lyra ao **Day Care**.
- Day Care: dois Pokémon compatíveis podem produzir ovo; telefone do casal, experiência por caminhada, retirada de ovos com espaço disponível.
- Contato de **Picnicker Gina** é fonte de Leaf Stone por chamada na referência.

### 2.6 Goldenrod: cidade, rádio e Whitney

**Pontos de interesse:** Goldenrod Department Store, troca Drowzee → Machop no centro comercial, Game Corner / Voltorb Flip e Coin Case (atividade opcional), Bike Shop e bicicleta, subterrâneo com lojas/serviços, Radio Tower, estação Magnet Train para o pós-jogo.

**Radio Card:** questionário na rádio. Respostas do quiz HGSS: **sim, sim, não, sim, não**. Whitney retorna ao ginásio após completar a visita à torre. Há também **Blue Card / Buena's Password**, programa de rádio de respostas e prêmios; implementar apenas se o sistema de rádio existir no Blue.

**Whitney:** **Clefairy e Miltank**. Após a vitória, Whitney chora e inicialmente não entrega a recompensa; é necessário retornar à conversa. Recompensa final: **Plain Badge + TM45 Attract**. Flower Shop concede **SquirtBottle** depois da insígnia.

**Entrega opcional:** guarda da saída norte fornece Spearow portando carta para NPC da Route 31; missão rende **TM44 Rest** e, ao voltar ao guarda, **HP Up**. Exige espaço e entrega única.

**Regra:** o regador é necessário para Sudowoodo; obter a insígnia sem concluir a conversa final não pode marcar a etapa completa.

### 2.7 Routes 35–37, National Park, Pokéathlon e Sudowoodo

- Route 35: Nidoran, evento raro de **Yanma** (o detonado menciona 1% na referência; auditar a tabela real antes de usar uma probabilidade no Blue).
- **National Park:** eventos e treinadores em dias comuns; concurso de captura de insetos em **terças, quintas e sábados**, prêmio baseado em desempenho, com Sun Stone como prêmio principal da fase inicial. **TM28 Dig** em acesso lateral. Não travar a história por participar do concurso.
- **Pokéathlon:** Magnus introduz a instalação; modalidades de velocidade, força, habilidade, resistência e salto; pontos podem ser trocados por itens; Apriblender cria Aprijuice. Atividade opcional dependente de UI.
- Route 36: **Sudowoodo** bloqueia passagem. Usar SquirtBottle inicia encontro único; após resolução NPC concede **Berry Pots** e berries; berry growing é sistema paralelo opcional.
- Contato **School Kid Alan** pode oferecer Fire Stone.
- Route 37: encontros e caminho para Ecruteak; mantenha horário do dia e eventos telefônicos se implementados.

### 2.8 Ecruteak: Dance Theater, Burnt Tower e Morty

- NPC entrega **Dowsing MCHN / Itemfinder** (localizador de itens invisíveis).
- **Dance Theater:** Rocket importuna uma Kimono Girl; batalha contra o Rocket e recompensa **HM03 Surf** oferecida por espectador. Só se usa Surf fora de batalha após a Fog Badge.
- **Burnt Tower:** encontro com Morty e **Eusine**, rival Silver, área inferior com **Raikou, Entei e Suicune**.
- Despertar as feras: Raikou e Entei tornam-se encontros errantes em Johto; Suicune passa a reaparecer em locais roteirizados. O posicionamento e dano persistente dos roamers precisam ser tratados pelo mecanismo da engine.
- **Morty:** Gastly, dois Haunter e Gengar; puzzle das passarelas escuras e luzes associadas a treinadores. Recompensa **Fog Badge + TM30 Shadow Ball**.
- Saindo de Ecruteak a leste: obtenção de **HM04 Strength** junto ao Mt. Mortar; Whitney/Plain Badge habilita seu uso em campo. Mt. Mortar e Ruins of Alph têm exploração adicional após novos HMs.

**Guarda do BLUE:** não ativar novamente os três lendários toda vez que a Burnt Tower for carregada; usar estados de captura independentes para Raikou, Entei e Suicune.

### 2.9 Olivine, farol, mar e Cianwood

- **Routes 38–39:** treinadores, Magnemite, Miltank, Tauros, Farfetch'd, exclusivos de versão. Lass Dana pode entregar Thunder Stone em ligações.
- **Moomoo Farm:** alimentar Miltank doente com **Oran Berries** (conferir quantidade/ciclo na fonte e no jogo antes de hardcodar); acesso a Moomoo Milk e recompensa apropriada.
- **Olivine Lighthouse:** vários andares e treinadores; para entrar na sala de Jasmine inicialmente deve-se subir pelas escadas e passagem externa; depois o elevador facilita o retorno. **Amphy**, o Ampharos do farol, está doente.
- **Routes 40–41:** Surf rumo a Cianwood, nadadores, Tentacool/Tentacruel, Mantine em HG e quatro **Whirl Islands** bloqueadas por Whirlpool.
- **Cianwood:** encontro Suicune e luta com **Eusine** (Drowzee, Electrode, Haunter); farmácia fornece **SecretPotion** para Jasmine. NPC pode confiar um **Shuckle** ao jogador com espaço livre.
- **Chuck:** desligar o fluxo d'água que o impede de perceber o jogador; Primeape e Poliwrath; recompensa **Storm Badge + TM01 Focus Punch**.
- Esposa de Chuck, do lado de fora, fornece **HM02 Fly** após vitória.
- Retornar ao farol com SecretPotion: Jasmine cura Amphy, iluminação volta, ginásio de Olivine abre. **Jasmine:** Magnemite, Magnemite e Steelix; **Mineral Badge + TM23 Iron Tail**.
- Baoba avisa por telefone a abertura da **Safari Zone**, acessível por Cliff Cave / Routes 47–48, a oeste de Cianwood.

**Dependência exata:** vitória sobre Chuck **não cura** Ampharos automaticamente; a cura exige entrega do remédio no farol. Safari Zone não é condição para Jasmine.

### 2.10 Mahogany, Lake of Rage e esconderijo Rocket

- Pela Route 42, Mt. Mortar é opcional; Mahogany inicialmente tem ginásio bloqueado e presença de Rocket.
- Route 43: posto Rocket pode cobrar dinheiro de passagem (desvio pela grama evita a perda). Chegar ao **Lake of Rage**.
- **Red Gyarados** é encontro fixo shiny; após encontro/captura obter **Red Scale**, trocável por **Exp. Share** com Mr. Pokémon na Route 30. Registro único de recompensa.
- **Lance** identifica transmissão suspeita; encontra o jogador no comércio de Mahogany, revela passagem para o **Rocket Hideout**.
- Esconderijo: alarmes ativados por estátuas de Persian; terminal do cientista desativa alarmes; pisos de encontros (Voltorb, Koffing, Geodude na referência); Lance cura o time.
- Dois membros informam senhas equivalentes a **Slowpoke Tail** e **Raticate Tail**. Após Petrel disfarçado, Murkrow reproduz a voz de autorização e abre outra porta.
- **Ariana + Grunt:** batalha dupla com Lance e Dragonite aliado; finalizar desativando três Electrodes da máquina enquanto Lance cuida dos demais.
- Lance entrega **HM05 Whirlpool**.
- **Pryce:** puzzle deslizante no gelo; Seel, Dewgong, Piloswine; recompensa **Glacier Badge + TM07 Hail**.
- Elm telefona a respeito da invasão da rádio de Goldenrod. Este é o disparador do próximo arco.

**Teste:** não liberar o ginásio por pegar apenas o Red Scale; não permitir Murkrow abrir porta antes da derrota de Petrel; validar dupla no motor nativo e evitar receber HM duas vezes.

### 2.11 Goldenrod ocupada: Radio Tower e subterrâneo

1. Rockets ocupam entradas da torre e saídas da cidade; o jogador recebe **disfarce Rocket** no subterrâneo.
2. Ao tentar subir a rádio, **Silver** reconhece o protagonista e estraga o disfarce; ocorre batalha com Grunt.
3. Subir a torre e enfrentar **Petrel** fingindo ser o diretor. Vitória concede **Basement Key**.
4. Abrir porta subterrânea; lutar com **Silver**; puzzle de três interruptores: **vermelho → verde → azul** na referência.
5. Resgatar o diretor verdadeiro, que entrega **Card Key**. Saída pelo subsolo do Department Store.
6. Voltar à Radio Tower, destrancar acesso interno e vencer **Proton**, **Ariana** e por último **Archer**.
7. Ao vencer Archer, Rockets deixam Goldenrod. Diretor entrega **Rainbow Wing** em HeartGold ou **Silver Wing** em SoulSilver.
8. Telefones, música e NPCs retornam ao estado normal. Itens adicionais de empregados são opcionais.

**Equipes de referência:** Petrel usa múltiplos Koffing e Weezing; Proton usa Golbat e Weezing; Ariana usa Arbok, Vileplume e Murkrow; Archer usa Houndour, Koffing e Houndoom. Não transferir os níveis de HGSS.

**Riscos:** softlock se o disfarce bloquear Fly/saídas após reiniciar, Card Key ausente, portões permanentemente fechados, reabrir missão após teleporte, repetir Wing.

### 2.12 Ice Path, Blackthorn, Clair e Dragon's Den

- Route 44: lago, gramados e treinadores; entrada do **Ice Path**.
- **Ice Path:** puzzles de piso escorregadio e rochas com Strength; coletar **HM07 Waterfall**. Encontros: Swinub, Jynx e Delibird em SoulSilver. Ajudar a última Kimono Girl que ficou presa no gelo.
- **Blackthorn:** casa dos tutores e Move Deleter / Move Relearner, além de tutor de Draco Meteor e golpes dos iniciais; adaptar às tabelas de golpes e serviços atuais.
- **Clair:** ginásio com plataformas que deslizam/giram sobre lava; Gyarados, Dragonair, Dragonair, Kingdra. Depois da vitória, **recusa entregar a insígnia**.
- **Dragon's Den:** Surf + Whirlpool, Dragon Fang no percurso, conversa com o ancião. A prova envolve amizade, estratégia, acolher diversos treinadores, cuidado com o Pokémon e respeito a fortes/fracos; respostas positivas aprovam a avaliação.
- Clair então concede **Rising Badge**; ao sair, oferece **TM59 Dragon Pulse**.
- Voltar ao ancião com espaço livre pode render **Dratini com ExtremeSpeed**, se as respostas/requisitos adequados tiverem sido atendidos.
- Route 45 é rota predominantemente de descida para Route 46, com treinadores, itens, acessos à Dark Cave e espécies distintas em HG/SS.

**Teste crucial:** derrota de Clair não deve contar a oitava insígnia nem habilitar Waterfall/legendaries antes da aprovação do Dragon's Den.

### 2.13 Kimono Girls e guardião da versão

- Elm pede retorno a New Bark, reconhece as oito insígnias e entrega **Master Ball**.
- Ethan/Lyra desvia o jogador da rota da Liga enquanto o confronto das Kimono Girls estiver pendente.
- No **Dance Theater** há cinco combates sequenciais, sem recuperação automática entre eles.
- Referência: **Zuki/Umbreon; Naoko/Espeon; Miki/Flareon; Sayo/Jolteon; Kuni/Vaporeon**.
- Recompensa **Clear Bell** (HeartGold) ou **Tidal Bell** (SoulSilver).
- **HeartGold:** acesso ao ritual no topo da Bell Tower, com Ho-Oh. **SoulSilver:** ritual na câmara inferior das Whirl Islands, com Lugia.
- Após completar o encontro roteirizado (captura ou resolução da batalha, conforme estado real), liberar a saída leste de New Bark em direção à Liga.
- **Variante Blue:** como o projeto funde exclusivos de versões, manter **uma rota narrativa principal configurável e consistente por save**; obter o lendário secundário depois por missão, sem exigir os dois para concluir Johto.

### 2.14 Tohjo Falls, Victory Road e Liga

- Saída leste de **New Bark** para a Route 27; NPC observa a passagem para a porção geográfica de Kanto. **Não** iniciar a campanha independente de Kanto do Blue nesse ponto.
- **Tohjo Falls:** usar Waterfall para atravessar a caverna. Prosseguir Routes 27–26, treinadores, casa com recuperação, pontes e áreas opcionais com Whirlpool.
- Portão da Liga valida as **oito insígnias de Johto**, não o somatório global de esmeraldas.
- **Victory Road HGSS:** caminhos e itens, poucos ou nenhum treinador comum na caverna; **Silver** aguarda perto da saída. Equipe de referência: Sneasel, Golbat, Magneton, Haunter, Kadabra, inicial no estágio final.
- **Indigo Plateau:** cura, loja e sequência **Will → Koga → Bruno → Karen → Lance**; Hall of Fame.
- **Blue:** persistir conclusão de Johto, liberar Kanto + Hoenn no circuito, ativar NPC de viagem na **cidade inicial New Bark**, mantendo local/global Trainer Card e regras de party. Não conceder novamente as recompensas da primeira vitória em uma revanche.

---

## 3. Ginásios de Johto — composição canônica HGSS

**Os níveis originais foram propositalmente omitidos: no Dessastre Paradoxal os níveis são dinâmicos.** A composição abaixo é base de referência; flags de ginásio e nível final dependem da engine.

| # | Cidade | Líder / tipo | Equipe de referência HGSS | Insígnia | TM | Observação |
|---|---|---|---|---|---|---|
| 1 | Violet | Falkner / Voador | Pidgey, Pidgeotto | Zephyr | 51 Roost | Sprout Tower precede gym |
| 2 | Azalea | Bugsy / Inseto | Scyther, Metapod, Kakuna | Hive | 89 U-turn | Slowpoke Well precede gym |
| 3 | Goldenrod | Whitney / Normal | Clefairy, Miltank | Plain | 45 Attract | Conversa adicional após vitória |
| 4 | Ecruteak | Morty / Fantasma | Gastly, Haunter, Haunter, Gengar | Fog | 30 Shadow Ball | Burnt Tower e Dance Theater |
| 5 | Cianwood | Chuck / Lutador | Primeape, Poliwrath | Storm | 01 Focus Punch | Fly entregue pela esposa |
| 6 | Olivine | Jasmine / Aço | Magnemite, Magnemite, Steelix | Mineral | 23 Iron Tail | Depende da SecretPotion |
| 7 | Mahogany | Pryce / Gelo | Seel, Dewgong, Piloswine | Glacier | 07 Hail | Base Rocket resolvida |
| 8 | Blackthorn | Clair / Dragão | Gyarados, Dragonair, Dragonair, Kingdra | Rising | 59 Dragon Pulse | Dragon's Den após batalha |

### Restrições de HMs em Johto (HGSS como referência)

| Técnica | Onde conseguir | Gatilho de campo de referência |
|---|---|---|
| HM01 Cut | Ilex Forest, missão dos Farfetch'd | Hive Badge |
| HM02 Fly | Esposa de Chuck, em Cianwood | Storm Badge |
| HM03 Surf | Ecruteak Dance Theater, Rocket vencido | Fog Badge |
| HM04 Strength | Route 42, perto do Mt. Mortar | Plain Badge |
| HM05 Whirlpool | Lance após desligar máquina Rocket | Glacier Badge |
| HM06 Rock Smash | NPC na Route 36 | Zephyr Badge |
| HM07 Waterfall | Ice Path | Rising Badge |
| HM08 Rock Climb | Professor Oak após 16 insígnias (HGSS) | Pós-jogo HGSS; no Blue, validar política de conteúdo entre regiões |
| TM70 Flash | Elder Li, Sprout Tower | Não é HM em HGSS |

Os HMs pertencem ao inventário e sistema atual do Blue; a permissão de uso deve ser recalculada pela região ativa e insígnias **locais**.

---

## 4. Liga de Johto — equipes de referência

| Ordem | Desafiante | Equipe de referência HGSS |
|---|---|---|
| 1 | **Will** | Xatu, Jynx, Slowbro, Exeggutor, Xatu |
| 2 | **Koga** | Ariados, Forretress, Muk, Venomoth, Crobat |
| 3 | **Bruno** | Hitmontop, Hitmonlee, Hitmonchan, Onix, Machamp |
| 4 | **Karen** | Umbreon, Vileplume, Murkrow, Gengar, Houndoom |
| Campeão | **Lance** | Gyarados, Dragonite, Dragonite, Aerodactyl, Charizard, Dragonite |

- Usar tipos, habilidades, golpes e estratégias documentados apenas como referência para a seleção do treinador; o pacote de batalha Blue tem prioridade.
- Registrar vitórias independentes e em sequência. Uma derrota recomeça o desafio segundo o fluxo atual da Liga, sem apagar insígnias.
- O campeão Lance **não é o mesmo evento** do Lance aliado no esconderijo de Mahogany.
- Ao vencer, registrar Hall of Fame e **completed_johto_league** (nome conceitual, não uma flag real auditada).
- A segunda passagem pela Elite Four HGSS pode ter equipes diferentes; **não** substitui a regra específica de pós-jogo global do Blue.

---

## 5. Itens importantes, presentes e Pokémon únicos

| Local / personagem | Item / Pokémon | Condição / comportamento |
|---|---|---|
| Elm e assistente | Inicial + 5 Potions | Nova campanha Johto, uma vez |
| Mãe do jogador | PokéGear | Primeiro retorno à casa |
| Guia de Cherrygrove | Running Shoes + Map Card | Conhecer cidade / saída |
| Route 30, NPC | Apricorn Box | Permite colher Apricorns |
| Mr. Pokémon / Oak | Mystery Egg + Johto Dex | Primeira visita |
| Ethan/Lyra | 5 Poké Balls | Tutorial de captura após retorno |
| Elder Li | TM70 Flash | Vencer topo da Sprout Tower |
| Assistente de Elm | Ovo de Togepi | Após Falkner, espaço na equipe |
| Centro da Route 32 | Old Rod, Lure Balls | NPCs de pesca |
| Kurt em Azalea | Fast Ball e fabricação Apricorn | Após limpar Slowpoke Well |
| Ilex Forest | HM01 Cut; Headbutt | Recuperar Farfetch'd / conversar com tutor |
| Goldenrod Radio Tower | Radio Card; Blue Card | Quiz e DJ Buena |
| Bike Shop / Goldenrod | Bicycle | Visitar estabelecimento |
| Whitney / Flower Shop | Plain Badge, TM45, SquirtBottle | Diálogo final com Whitney |
| Guarda / Route 31 | Spearow com carta; TM44 Rest; HP Up | Missão de entrega opcional |
| Sudowoodo / Route 36 | Berry Pots e berries | Evento do SquirtBottle resolvido |
| Ecruteak Dance Theater | HM03 Surf | Derrotar Rocket |
| Route 42 | HM04 Strength | NPC fora do Mt. Mortar |
| Cianwood Pharmacy | SecretPotion | Conversar durante doença de Amphy |
| Cianwood, morador | Shuckle | Espaço na equipe |
| Chuck e esposa | Storm Badge, TM01, HM02 Fly | Vencer gym e sair |
| Jasmine | Mineral Badge, TM23 | Entregar remédio e vencer gym |
| Lake of Rage | Red Gyarados / Red Scale | Encontro especial |
| Mr. Pokémon / Route 30 | Exp. Share | Trocar Red Scale |
| Lance / esconderijo | HM05 Whirlpool | Electrodes resolvidos |
| Petrel e diretor | Basement Key, Card Key | Resgatar torre |
| Diretor Radio Tower | Rainbow Wing ou Silver Wing | Vencer Archer |
| Ice Path | HM07 Waterfall | Item no cenário |
| Clair / Dragon's Den | Rising Badge, TM59 | Prova do ancião |
| Ancião Dragon's Den | Dratini com ExtremeSpeed | Requisitos e vaga na equipe |
| Elm | Master Ball | Oito insígnias Johto |
| Kimono Girls | Clear Bell ou Tidal Bell | Vencer cinco duelos |
| Union Cave | Lapras | Evento de sexta-feira e Surf |
| Mt. Mortar | Tyrogue | Encontrar e vencer Karate King; espaço na party |
| Ruins of Alph | Unown Report | Completar quebra-cabeça inicial |

**Outros itens/serviços citados:** Apricorns por dia, pedras evolutivas por chamadas e Pokéathlon, Moomoo Milk, fosséis e itens ocultos, apriballs de Kurt, TM28 Dig no National Park, TM05 Roar acessível com Cut na Route 32, TM36 Sludge Bomb perto da Route 43 e TMs de ginásio. Esta tabela é **índice de itens-chave**, não auditoria tile a tile de todos os itens visíveis/ocultos.

---

## 6. Encontros selvagens, exclusividades e regras de habitat

### 6.1 Encontros ilustrativos por área

| Área | Referências de habitat / condições |
|---|---|
| Route 29 | Pidgey, Rattata, Sentret; Hoothoot à noite |
| Routes 30–31 | Caterpie, Metapod, Spinarak (HG); Weedle, Kakuna, Ledyba (SS); Bellsprout em trechos |
| Sprout Tower | Gastly à noite |
| Route 32 | Mareep, Hoppip, Wooper à noite; Ekans em SS |
| Union Cave | Onix, Zubat, Geodude; Sandshrew em HG; Lapras especial |
| Ilex Forest | Paras, Oddish à noite; Headbutt para outros Pokémon |
| Route 34 | Drowzee, Abra, Ditto |
| Route 35 | Nidoran e Yanma raro |
| Route 36 | Growlithe (HG), Vulpix (SS), Stantler; Sudowoodo fixo |
| Burnt Tower | Koffing, Magmar em parte inferior; Raikou, Entei e Suicune por evento |
| Routes 38–39 | Magnemite, Raticate, Farfetch'd, Miltank, Tauros, Snubbull; Meowth SS |
| Routes 40–41 | Tentacool, Tentacruel, Mantine HG |
| Cliff Cave / Safari Approach | Kingler, Machop, Graveler, Steelix raro, Misdreavus à noite; Seel/Staryu na água |
| Route 43 / Lake of Rage | Girafarig, Pidgeotto, Noctowl à noite; Red Gyarados fixo |
| Route 44 | Tangela, Weepinbell, Lickitung em áreas aquáticas/grama |
| Ice Path | Swinub, Jynx; Delibird SS |
| Route 45 | Gligar/Phanpy HG, Teddiursa/Skarmory SS |
| Routes 26–27 | Doduo, Dodrio e exclusivos conforme versão; água e pesca |
| Victory Road | Rhyhorn, Donphan HG, Ursaring SS |
| Ruins of Alph | Unown conforme quebra-cabeça concluído |

**Fusão Blue:** unir os exclusivos HeartGold/SoulSilver por local coerente, sem apagar espécies originais e sem copiar taxas indiscriminadamente. Dia/noite, pesca, Surf, Rock Smash, Headbutt, swarm, rádio e Safari são métodos distintos. Usar tabelas PBS reais e fazer soma de probabilidades por tabela, validada em 100%.

**Informações não extraíveis com segurança do artigo:** algumas tabelas do Safari exibem espécies apenas como imagens; não presumir espécie ou percentual a partir de um marcador genérico “Image”. Para obter distribuição completa, auditar dados legítimos de HGSS e os encontros do projeto, registrando fonte e permissões.

### 6.2 Pokémon estáticos e roaming

- **Sudowoodo:** Route 36, acionado pelo regador, encontro único, reaparecimento pós-Liga conforme regra de HGSS quando não capturado.
- **Red Gyarados:** Lake of Rage, shiny fixo, Red Scale e troca por Exp. Share.
- **Raikou / Entei:** roamers de Johto após Burnt Tower; persistem danos/status entre encontros na referência, fogem rapidamente e mudam de rota.
- **Suicune:** sequência Burnt Tower → Cianwood → Route 42/Mt. Mortar → Vermilion → Route 14 → Cerulean Cape; Eusine acompanha a história. Separar os locais visitados por flags.
- **Ho-Oh e Lugia:** guardiões de Bell Tower e Whirl Islands, respectivamente, com conteúdo principal dependente de versão na referência.
- **Lapras:** piso inferior de Union Cave nas sextas.
- **Tyrogue:** recompensa de treinador nas profundezas do Mt. Mortar.
- **Dratini:** presente do ancião depois da prova do Dragon's Den.

---

## 7. Conteúdo opcional de Johto — cavernas, mistérios e atividades

### 7.1 Union Cave

Exploração adicional após Surf; andares inferiores com treinadores e itens. **Lapras** aparece às sextas-feiras. As saídas superiores dão acesso a salas adicionais das **Ruins of Alph**. Não transformar esse evento semanal em impedimento da história principal.

### 7.2 Mt. Mortar

Entradas na Route 42; no começo não é possível explorar tudo. **Surf, Strength, Waterfall e Rock Climb** são relevantes para completar diferentes setores. Nas partes profundas, luta com **Karate King Kiyo** pode conceder **Tyrogue** mediante espaço na equipe. Recompensa deve persistir após teleporte/load.

### 7.3 Dark Cave

Várias entradas em Johto, incluindo arredores de Violet e Routes 45–46; Flash para enxergar e outras técnicas para trechos avançados. Preservar warps e entradas que conduzem a saídas distintas.

### 7.4 Bell Tower

Torre de Ecruteak associada a **Ho-Oh**, com puzzles de pisos, escadas e teletransportes. Em **HeartGold**, Rainbow Wing + Clear Bell levam ao ritual principal; em **SoulSilver**, Ho-Oh é conteúdo secundário posterior, mediante Rainbow Wing obtida em Kanto. Os níveis da versão não se aplicam ao Blue.

### 7.5 Whirl Islands

Quatro entradas entre Routes 40–41; requerem Surf/Whirlpool, com navegação subterrânea e quedas entre andares. Em **SoulSilver**, Silver Wing + Tidal Bell permitem o encontro principal com **Lugia**; em HeartGold, Lugia surge na visita posterior mediante Silver Wing obtida em Kanto. Garantir ida, volta e atalhos sem travar o save.

### 7.6 Ruins of Alph

Quatro mosaicos principais: **Kabuto, Aerodactyl, Ho-Oh e Omanyte**. Resolver um mosaico acrescenta formas de Unown à área central; primeiro progresso habilita **Unown Report**. Outras câmaras são alcançadas com Surf e pela Union Cave.

Portas de enigmas da referência:
- **ESCAPE:** usar Escape Rope na câmara de Kabuto.
- **LIGHT:** usar Flash na câmara de Aerodactyl.
- **HO-OH:** levar Ho-Oh como primeiro membro da equipe na câmara correspondente.
- **WATER:** usar/possuir Water Stone conforme evento na câmara de Omanyte.

Após as 26 letras e salas especiais, liberar **Unown “!” e “?”** conforme a progressão correta. O requisito Ho-Oh cruza a restrição de Pokémon especiais do Blue: o puzzle deve validar a possibilidade legítima de acesso na região, sem forçar burlar a Box.

### 7.7 Safari Zone e Baoba

- Acesso pela **Cliff Cave**, Routes 47–48, depois de reabrir a região de Cianwood e evento do telefonema de Baoba.
- Primeira missão: capturar **Geodude** em área solicitada; segunda missão: reconfigurar áreas e conseguir **Sandshrew** no setor apropriado. Registrar qual missão está ativa.
- Áreas rearranjáveis: ambientes de planície, floresta, montanha, pântano, deserto e praia rochosa, com opções extras após a primeira configuração.
- Sistema posterior: **até 30 blocos por área**; categorias **Plains, Forest, Rocks e Water**, além de blocos decorativos; os dias de permanência aumentam eficácia de objetos. O artigo detalha limites, objetos e tabelas, mas exibe muitas espécies exclusivamente por imagem.
- **No Blue:** implementar módulo do Safari somente se houver versão coerente com a engine e persistência; caso não, documentar o modo como pendente, preservando a entrada e sem bloquear a Liga.

### 7.8 Pokéathlon, Bug-Catching Contest e rádio

- **Pokéathlon:** competições por categorias físicas, Apriblender, Aprijuice e loja rotativa por pontos; opcional.
- **Bug-Catching Contest:** no National Park, dias específicos, limite de sessão e avaliação da captura; recompensas como Sun Stone; rota alternativa normal quando não há evento.
- **PokéGear:** mapa, telefone, programas de rádio, ligações de NPCs, revanches e notificações; o **Blue Card** da DJ Buena dá prêmios em programa periódico.
- **Hoenn Sound / Sinnoh Sound:** canais pós-National Dex que alteram encontros enquanto o rádio toca; verificar tabelas por mapa antes de integrar, para não violar habitats já existentes.
- **Apricorn / Kurt / Berry Pots / Day Care:** serviços com timers persistentes; testes precisam simular reload, relógio, inventário cheio e passagem de região.

---

## 8. Treinadores recorrentes, telefonemas e revanches

**Silver:** aparece no começo da jornada, após Bugsy, Burnt Tower, subterrâneo de Goldenrod e Victory Road; encontros posteriores no pós-jogo têm regras próprias. O inicial utilizado por ele evolui conforme a progressão. Todos os combates devem usar flags distintas.

**Rocket executives:** Proton (Slowpoke Well e Radio Tower), Petrel (Mahogany e Radio Tower), Ariana (base de Mahogany e Radio Tower), Archer (fim da torre). A luta em dupla de Mahogany usa Lance como aliado, mas não deve criar equipe permanente para o jogador.

**Telefone e itens de referência:**
- Picnicker **Gina** (Route 34) → Leaf Stone.
- School Kid **Alan** (Route 36) → Fire Stone.
- Lass **Dana** (Route 38) → Thunder Stone.
- Alguns outros contatos entregam pedras, berries, objetos ou oferecem rematches em horários/dias fixos.
- Treinadores com telefone evoluem de equipe conforme a fase da campanha. Não assumir os níveis ou duplicar recompensas quando uma ligação é repetida.

**Líderes:** HGSS usa números de telefone e janelas semanais para reunir líderes no Fighting Dojo de Saffron, onde ocorrem revanches. Isso é **pós-jogo HGSS** e não deve ativar automaticamente as versões mais fortes do Blue antes das dez campanhas concluídas.

### Elencos de revanche de Johto em HGSS (somente composição)

| Líder | Equipe de revanche registrada no detonado |
|---|---|
| Falkner | Staraptor, Noctowl, Swellow, Honchkrow, Pelipper, Pidgeot |
| Bugsy | Scizor, Shedinja, Yanmega, Pinsir, Heracross, Vespiquen |
| Whitney | Girafarig, Lickilicky, Bibarel, Delcatty, Clefable, Miltank |
| Morty | Drifblim, Dusknoir, Sableye, Mismagius, Gengar, Gengar |
| Chuck | Medicham, Hitmonchan, Hitmonlee, Breloom, Primeape, Poliwrath |
| Jasmine | Metagross, Magnezone, Skarmory, Bronzong, Empoleon, Steelix |
| Pryce | Abomasnow, Dewgong, Glalie, Froslass, Walrein, Mamoswine |
| Clair | Gyarados, Dragonair, Aerodactyl, Kingdra, Charizard, Dragonite |

**Atenção:** são as revanches específicas de HGSS. O arquivo de times fortes e a regra do **pós-jogo global** do Blue continuam tendo prioridade para seleção de equipes definitivas.

---

## 9. Pós-jogo do HGSS em Kanto — referência separada da campanha de Kanto do Blue

O detonado de HGSS dedica longa parte ao pós-Liga em Kanto. **No Blue, Kanto é uma região independente e seu roteiro principal segue o documento [KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md).** A lista abaixo é referência histórica para missões ou conteúdo pós-jogo opcional, não para substituir a campanha de Kanto.

| Local / arco de HGSS | Evento de referência |
|---|---|
| Retorno a New Bark / Elm | Receber **S.S. Ticket** após primeira Liga |
| Olivine Port / Oak | Atualização para National Dex e embarque no **S.S. Aqua** |
| S.S. Aqua | Missão a bordo, reencontrar passageiro / neta desaparecida e desembarcar em Vermilion |
| Vermilion | Lt. Surge e Thunder Badge; retorno futuro a Kanto por navio ou trem |
| Saffron | Sabrina e Marsh Badge; Magnet Train ainda depende de missão |
| Celadon | Erika e Rainbow Badge; lojas e Game Corner |
| Fuchsia | Janine e Soul Badge; conexão com Routes 12–15 |
| Cerulean / Power Plant | Roubo da **Machine Part**; perseguição de Rocket; Misty retorna após evento do cabo |
| Saffron / Copycat | Buscar boneca da Copycat em Vermilion para o **Magnet Train Pass**, após reparar usina |
| Lavender Radio Tower | Expansão de rádio para obter a estação **Poké Flute** |
| Route 11 / Snorlax | Acordar Snorlax com Poké Flute; liberar **Diglett's Cave** |
| Pewter | Brock e Boulder Badge; NPC fornece Wing da ave lendária secundária |
| Cinnabar / Seafoam | Cinnabar destruída por erupção; **Blaine** opera ginásio nas Seafoam Islands |
| Cinnabar → Viridian | Encontrar Blue e fazer com que retorne ao ginásio; vencer Earth Badge |
| Oak após oito insígnias de Kanto | Receber **HM08 Rock Climb** e acesso avançado a Mt. Silver |
| Mt. Silver | Confronto final opcional com **Red** após requisito de 16 insígnias do HGSS |

**Ginásios pós-Liga HGSS em Kanto:** Lt. Surge (Raichu, Electrode, Electrode, Magneton, Electabuzz), Sabrina (Espeon, Mr. Mime, Alakazam), Erika (Jumpluff, Tangela, Victreebel, Bellossom), Janine (Crobat, Weezing, Ariados, Venomoth, Weezing), Misty (Golduck, Quagsire, Lapras, Starmie), Brock (Graveler, Rhyhorn, Omastar, Onix, Kabutops), Blaine (Magcargo, Magmar, Rapidash) e Blue (Exeggutor, Machamp, Arcanine, Rhydon, Gyarados, Pidgeot). Verificar equipes e ordens específicas contra as bases canônicas do Blue antes de cadastrar; nenhum nível fixo.

**Conteúdos avançados HGSS:** Articuno (Seafoam), Zapdos (Power Plant após progressão), Moltres (Mt. Silver), Mewtwo (Cerulean Cave), Red (Mt. Silver), rematches de líderes e Elite Four, Battle Frontier, Game Boy Sounds, novos iniciais oferecidos por Oak/Steven e encontro de Kyogre/Groudon/Rayquaza na Embedded Tower conforme versão e Orbs. Todos são opcionais frente à primeira Liga de Johto.

---

## 10. Eventos adicionais e excepcionais do detonado

### 10.1 Suicune e Eusine

O roteiro do lendário tem **encontros de visualização** em várias regiões, em ordem, antes da batalha de captura. Para o Blue, não pular etapas por viajar via NPC entre regiões, nem duplicar Suicune em dois mapas. Se um mapa de Kanto não estiver disponível, manter a quest pendente sem bloquear a Liga de Johto.

### 10.2 Embedded Tower e os lendários do clima

A referência HGSS oferece **Kyogre em HeartGold** por Blue Orb e **Groudon em SoulSilver** por Red Orb, conectando o item de Mr. Pokémon ao acesso da Embedded Tower em Johto. Obter os dois lendários provenientes dessa mecânica permite a Oak conceder **Jade Orb** para Rayquaza. No Blue, são Pokémon especiais e a equipe deve obedecer às oito insígnias **locais** da região ativa.

### 10.3 Iniciais de Kanto e Hoenn

Após requisitos de pós-jogo HGSS, Oak oferece escolha de um inicial de Kanto e Steven oferece um de Hoenn; cada presente tem escolha exclusiva. O Blue tem começo por região e sistemas próprios: **não** atrelar automaticamente recompensas de outras campanhas a essa regra do cartucho.

### 10.4 Red, rematches e novos desafios

Red aparece em **Mt. Silver**, com Pikachu, Venusaur, Charizard, Blastoise, Lapras e Snorlax; batalha de elite opcional após 16 insígnias no HGSS. A revanche da Elite Four possui equipes reforçadas; revanches de treinadores dependem de chamadas e dias da semana. No Blue, tratar Red e esse conjunto como **bônus com requisito auditado**, não condição para liberar Hoenn.

### 10.5 Eventos de distribuição especiais

O artigo também menciona **Pichu com orelha pontuda** associado a Pichu de evento, e **Celebi** ativando viagem temporal com cenas de Silver e Giovanni. Esses eventos dependiam de distribuição oficial e gatilhos específicos no cartucho. **Não** ativar por padrão, não inventar forma obtível, nem incluir sem definir disponibilidade e direitos dos assets. O arco de Celebi pode servir apenas como referência de missão opcional original.

### 10.6 Battle Frontier HGSS

Área de pós-jogo com múltiplas instalações: **Battle Tower, Battle Hall, Battle Arcade, Battle Factory e Battle Castle**, regras e prêmios próprios. Cada instalação requer sua própria engine de torneio, controle de equipe e persistência; **não** afirmar compatibilidade com o motor do Blue sem testes. Conteúdo separado da campanha principal.

---

## 11. Catálogo de mapas / passagens para conferir no Blue

| Núcleo | Cidades, mapas e interiores que precisam de revisão |
|---|---|
| Começo | New Bark, casa 1F/2F, laboratório Elm, casas de NPC, Routes 29–31, Cherrygrove, Mr. Pokémon |
| Primeiro ginásio | Violet, Pokémon Center, Mart, Sprout Tower (todos andares), Gym, Route 32, Ruins of Alph (entradas) |
| Azalea | Union Cave, Route 33, Azalea, Kurt, Slowpoke Well (todos andares), Gym |
| Goldenrod | Ilex Forest, Route 34, Day Care, Goldenrod, lojas, Game Corner, Bike Shop, Radio Tower, Underground, Gym |
| Norte | Routes 35–37, National Park, Pokéathlon, Sudowoodo, Ecruteak, Dance Theater, Burnt Tower, Bell Tower |
| Costa | Routes 38–41, Moomoo Farm, Olivine, Lighthouse, Cianwood, Pharmacy, Gym, Whirl Islands |
| Oeste | Cliff Cave, Routes 47–48 e Safari Zone |
| Leste | Route 42, Mt. Mortar, Mahogany, Rocket Hideout, Route 43, Lake of Rage, Gym |
| Retorno Rocket | Goldenrod Underground, Warehouse, Radio Tower, loja e elevadores |
| Reta final | Route 44, Ice Path, Blackthorn, Gym, Dragon's Den, Routes 45–46 |
| Liga | Route 27, Tohjo Falls, Route 26, Reception Gate, Victory Road, Indigo Plateau e salas da Elite |
| Extra | Dark Cave, cavernas secundárias, todos warps de Bell Tower/Whirl Islands, Ruins of Alph e Mt. Silver |

**MapIDs reais não são dedutíveis desta lista.** A documentação offline de Johto registra mapa-base 600–681 sob material de auditoria, mas a existência de um ID preparado **não certifica** interior, colisão, áudio, NPC ou lógica de runtime. Cruzar a relação com MapInfos, conexões, gráficos e MapNNN reais antes de marcar jogável.

---

## 12. Ledger conceitual de eventos e requisitos de persistência

Os nomes abaixo são **propostas descritivas**, não switches Ruby já inspecionados.

| Grupo | Estado persistente que precisa existir |
|---|---|
| Abertura | inicial escolhido, PokéGear, missão Elm, Mystery Egg, primeira luta Silver, Pokédex liberada, captura liberada |
| Violet | torre limpa, Li vencido, Falkner vencido, ovo recebido, Togepi entregue/reconhecido |
| Azalea | Kurt avisado, Proton vencido, poço salvo, Bugsy vencido, Silver pós-gym |
| Ilex | Farfetch'd 1 e 2 capturados, Cut recebido, acesso florestal liberado |
| Goldenrod | Radio Card, Whitney derrotada, Plain Badge entregue, SquirtBottle, Sudowoodo resolvido |
| Ecruteak | Rocket do Dance Theater vencido, Surf recebido, Silver Burnt Tower, feras soltas, Morty vencido |
| Olivine/Cianwood | Ampharos doente, SecretPotion obtida, Chuck vencido, Fly entregue, Ampharos curado, Jasmine vencida |
| Mahogany | Gyarados resolvido, Scale trocada, hideout aberto, duas senhas, Petrel, Murkrow, dupla com Lance, Electrodes, Pryce |
| Radio Tower | invasão ativa, disfarce, Petrel impostor, Basement Key, puzzle subterrâneo, diretor solto, Card Key, Proton, Ariana, Archer, Wing |
| Blackthorn | Waterfall coletado, Clair vencida, teste do ancião, Rising Badge, TM Dragon Pulse, Dratini presente |
| Final | Master Ball, cinco Kimono Girls, sino, guardião da versão, passagem Route 27, Silver Victory Road, Elite 4, Lance, Hall of Fame |
| Integração | insígnias locais, esmeraldas globais, duas regiões vizinhas, viagem disponível, party especiais depositada quando preciso |
| Opcionais | roamers, Lapras semanal, Kurt timer, Day Care, Safari, concurso, rádio, Pokéathlon, Pichu/Celebi se explicitamente habilitados |

**Implementação:** eventos devem ser idempotentes, com estado escrito antes de mudar de mapa e sem depender de uma única coordenada hardcoded, exceto gatilhos auditados; salvar/recarregar em cada ponto crítico.

---

## 13. Ordem de implementação e testes para Codex

### Fase A — referência e mapeamento (somente documentação)

- [ ] Relacionar cada etapa deste guia com map IDs **reais** e warps do pacote autorizado.
- [ ] Identificar cada treinador, NPC, item oculto, música e evento em fontes legítimas.
- [ ] Comparar com documentação e implementação já existentes; anotar divergências, sem sobrescrever dados.
- [ ] Classificar: **não preparado / offline / integrável / testado no Game.exe / homologado**.

### Fase B — fluxo mínimo funcional de Johto

- [ ] New Bark 2F → 1F → laboratório → inicial, PokéGear, rival e primeiro save.
- [ ] Route 29–31, Cherrygrove, Mystery Egg e retorno a Elm.
- [ ] Violet, Sprout Tower, Elder Li e Falkner, incluindo cura no Center.
- [ ] Azalea/Slowpoke Well/Bugsy; Ilex e Goldenrod/Whitney.
- [ ] Ecruteak/Morty, Olivine/Cianwood/Chuck/Jasmine.
- [ ] Mahogany/Rocket/Pryce, Radio Tower, Ice Path/Clair/Dragon's Den.
- [ ] Kimono Girls, guardião da versão, Victory Road e Liga.

### Fase C — pós-Liga, riqueza de mundo e integração

- [ ] Safari, Pokéathlon, National Park, phone/rematches, Apricorns e Day Care sem bloquear história.
- [ ] Lendários, locais extras, itens ocultos e música por evento.
- [ ] NPC de viagem em New Bark, liberação Kanto + Hoenn, cards regional/global e restrição de party.
- [ ] Validar conquistas globais sem duplicar esmeraldas nem reexecutar Elite após retorno.

### Matriz mínima E2E

1. Novo jogo começa **no quarto de New Bark**; transição 2F/1F/cidade funciona.
2. Escolha de starter não se repete após save/load nem após troca de região.
3. O rival recebe tipo vantajoso e acompanha a cadeia evolutiva sem congelar nível.
4. Primeiro Center toca ME de cura, restaura BGM; repetir em Windows e Android.
5. Mystery Egg e Pokédex concedidos somente após diálogo correto.
6. Sprout Tower realmente desbloqueia Falkner; ginásio com NPCs/mapa funcional.
7. Oito insígnias de Johto são **oito estados distintos**; cada uma soma uma única esmeralda global.
8. Slowpoke Well abre Bugsy; puzzle Ilex e Cut bloqueiam passagens certas.
9. Whitney exige diálogo final; SquirtBottle e Sudowoodo obedecem estados.
10. Burnt Tower solta Raikou/Entei uma vez e progride Suicune.
11. Surf/Strength/Fly/Whirlpool/Waterfall respeitam **insígnias locais**, não globais.
12. A SecretPotion cura Amphy antes de Jasmine retornar ao ginásio.
13. Lance em batalha dupla usa engine Blue, sem gerar crash.
14. Radio Tower não causa softlock em disfarce, portões, subsolo e chamadas.
15. Clair só concede Rising após Dragon's Den; Dratini não duplica.
16. Cinco Kimono Girls ocorrem na ordem e guardião é resolvível por qualquer modo de inicial do Blue.
17. Victory Road aceita as oito de Johto; a Liga possui cinco combates distintos.
18. Hall of Fame libera **Kanto e Hoenn**, preserva outras regiões e save.
19. Viagem deposita especiais ao entrar em região sem oito insígnias e impede retirada indevida.
20. Retorno a Johto preserva todos os NPCs, itens, puzzles, Pokédex, dados de treinador e HMs.
21. Testar telas **Testar Johto / Testar Kanto** sem colisão de menus; piloto não é campanha certificada.
22. Testar cada mapa no Windows e Android/JoiPlay, com salvamento e atualização incremental.
23. Conferir música de cidade, rota, batalha, Rocket, lendários, vitória, insígnia, cura e fallback.
24. Confirmar visualização no site dos treinadores por **insígnias locais e totais**, sem nível fixo.
25. Executar regressão Decades/Kanto/Hoenn, auditar direitos dos assets e rollback do instalador.

---

## 14. Referências internas e fonte externa

- **Detonado consultado:** https://www.pokemythology.net/detonados/detonado-heartgold-soulsilver/
- [Plano de regiões v2](PLANO_REGIOES_DESSASTRE_V2.md)
- [Implementação definitiva de Johto](JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md)
- [Johto — fases técnicas](JOHTO_ETAPAS.md)
- [Johto — auditoria integrada offline 12/12](JOHTO_OFFLINE_FASE_12_AUDITORIA_INTEGRACAO.md)
- [Johto — pendências após offline 12](JOHTO_PENDENCIAS_APOS_OFFLINE_12_DE_12.md)
- [Johto — testes E2E](JOHTO_TESTES_E2E.md)
- [Kanto — guia FRLG de referência](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md)

**Limites transparentes:** este arquivo consolida a **campanha principal inteira**, líderes, Liga, eventos de progressão, sistemas, áreas opcionais e sumário factual do pós-jogo presente no artigo. Não reproduz passo a passo textual original, imagens, mapas ilustrados, todos os itens ocultos por coordenada, dezenas de tabelas de cada treinador e todas as espécies das tabelas do Safari, cuja parte visual não permite extração textual confiável. Esses dados exigem auditoria separada com o jogo/base e o artigo original. **Este commit é documentação; não altera o jogo ou seu status de jogabilidade.**
