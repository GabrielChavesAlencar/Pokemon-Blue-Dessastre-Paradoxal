# Estudo dos eventos de mapa de Pokémon FireRed e guia de implementação no RPG Maker XP

**Aplicação-alvo:** RPG Maker XP + Pokémon Essentials v21.1; compatível conceitualmente com projetos similares.  
**Adaptação considerada:** *Pokémon Blue: Dessastre Paradoxal* (base local Pokémon Decades), sem modificar a campanha Decades.  
**Data da análise:** 12/11/2026.  
**Escopo:** Kanto principal, interiores, rotas, dungeons, Liga, Ilhas Sevii, eventos especiais, infraestrutura e pós-jogo.  
**Fonte técnica primária:** decompilação `pret/pokefirered` — https://github.com/pret/pokefirered.

> **Importante — o que foi analisado:** o índice original contém **425 mapas**, organizados em **43 grupos** (contagem obtida de `data/maps/map_groups.json`). Os esquemas dos eventos e os scripts de diversos mapas representativos foram conferidos diretamente. Este estudo cobre **todas as famílias de eventos**, a sequência da campanha e um checklist das principais áreas. Não afirma que cada uma das milhares de entradas individuais dos 425 mapas foi inspecionada manualmente. O programa auxiliar `extrair_eventos_firered.py` gera **o inventário literal de todos os registros** diretamente da sua cópia atual da decompilação. Ele não interpreta automaticamente todas as condições dos scripts: a validação semântica ainda exige revisão humana.

> **Contexto da main em 12/11/2026:** a Fase 09 adicionou **11 cenários de Celadon**, chegando a **51 mapas geométricos**, mas os eventos da fase 09 permanecem propositalmente desativados. O progresso funcional oficialmente registrado permanece **08/16** e a validação **01/16**. Consulte [Fase 09](KANTO_FASE_09.md), [16 etapas](KANTO_ETAPAS.md) e [guia prático de aplicação](FIRERED_EVENTOS_COMO_APLICAR_NO_BLUE.md). Este estudo **não** autoriza nem executa mudanças nos eventos do jogo.

## Sumário

1. Fontes, estrutura e diferença entre FireRed e RPG Maker
2. Taxonomia completa de eventos
3. Matriz técnica de conversão dos tipos de eventos
4. Catálogo de eventos por cidade, rota, caverna e Ilha Sevii
5. Ordem das missões e dependências
6. Regras de HMs, insígnias, encontros e batalhas
7. Arquitetura de switches, variáveis e saves
8. Passo a passo para recriar/importar eventos em RPG Maker XP/Essentials
9. Exemplos de implementação prontos para adaptar
10. Integração sem conflitos no Blue: Dessastre Paradoxal
11. Testes, critérios de aceite e falhas frequentes
12. Extração automatizada de 425 mapas
13. Checklist de implementação em etapas
14. Fontes e referências

---

# 1. Fontes e arquitetura original

## 1.1 O que existe em FireRed

Pokémon FireRed/LeafGreen são jogos de Game Boy Advance, não projetos RPG Maker. Portanto **não existe uma conversão automática direta** de `map.json`/assembly da decompilação para `MapXXX.rxdata` do RPG Maker XP. É preciso reconstruir layouts/tilesets compatíveis, transpor eventos, reatribuir IDs e reimplementar a lógica em eventos do Essentials/Ruby.

Estrutura técnica primária:

| Fonte no `pret/pokefirered` | Responsabilidade | Destino provável no RPG Maker/Essentials |
|---|---|---|
| `data/maps/map_groups.json` | Lista e agrupamento dos mapas | Catálogo de IDs de mapas e índice de importação |
| `data/maps/<MAPA>/map.json` | Metadados, NPCs, warps, triggers, placas e conexões | `Data/MapXXX.rxdata` + metadados e eventos RXDATA |
| `data/maps/<MAPA>/scripts.inc` | Scripts locais dos eventos | Páginas de evento + scripts Ruby/plugins |
| `data/maps/<MAPA>/text.inc` | Texto referenciado pelos scripts | Diálogos próprios/localizados |
| `data/event_scripts.s` e `data/scripts/` | Scripts globais e padrões compartilhados | Common Events / módulos reutilizáveis Ruby |
| `data/map_events.s`, `asm/macros/map.inc` | Estruturas e geração de eventos | Referência estrutural; **não copiar como código Ruby** |
| `include/constants/map_scripts.h` | Categorias de scripts de mapa | Hooks de entrada/atualização/transição do Essentials |
| Dados de encontro e treinador distribuídos no projeto | Espécies, grupos de batalha, itens e chance | PBS `encounters.txt`, `trainers.txt` e correlatos |
| `data/tilesets` + `data/layouts` | Tiles gráficos, propriedades e layouts | Tilesets/autotiles/collision/terrain tags de RMXP |

### 1.2 Contagem real do catálogo de mapas

A decompilação inspecionada organiza **425** identificadores de mapa em **43 grupos**. Resumo por grandes conjuntos:

| Grupo | Mapas |
|---|---:|
| Troca/batalha/Union Room | 5 |
| Cavernas, andares, barcos, hideouts, ruínas e outros dungeons | 123 |
| Áreas especiais (Trainer Tower, Lost Cave, Navel Rock, Birth Island etc.) | 60 |
| Cidades, rotas, ilhas e áreas externas | 66 |
| Interiores de Pallet, Viridian, Pewter, Cerulean, Lavender, Vermilion, Celadon, Fuchsia, Cinnabar, Indigo, Saffron e rotas | 171 |
| **Total** | **425** |

> A categoria "interiores" inclui interiores das Sete Ilhas e mapas de casas/portarias de rotas. O catálogo contém protótipos/áreas de eventos ou conexão que não precisam estar acessíveis na campanha normal. **425 mapas no índice ≠ 425 mapas diferentes obrigatoriamente jogáveis.**

### 1.3 O que é considerado evento de mapa

Neste estudo, **evento de mapa** significa qualquer comportamento dependente de posição, entrada no mapa, interação, estado de campanha ou jogador. Não se limita aos `object_events` de `map.json`. Encontros aleatórios, uso de HM, transições, comportamento de batalha e eventos globais também fazem parte da experiência.

### 1.4 Estrutura exata de um `map.json`

Os cinco conjuntos principais são:

- `object_events`: NPCs, treinadores, Pokémon estáticos, árvores de Cut, pedras e objetos visíveis; possuem posição, sprite, movimento, script, flag de exibição, possivelmente distância de visão.
- `warp_events`: entrada/saída de prédios, escadas, cavernas e teletransportes, com destino e índice de warp.
- `coord_events`: gatilhos por coordenada e/ou variável; podem ativar cenas apenas em determinado estágio.
- `bg_events`: placas, pontos de investigação, itens ocultos e interações sem sprite convencional.
- `connections`: ligação contínua entre bordas de mapas, com direção e deslocamento; diferente de teleportar por uma porta.

Além desses, cabeçalhos definem clima, música, tipo de mapa, Flash, bicicleta, corrida, escape e exibição do nome.

**Exemplo real:** `data/maps/PalletTown/map.json` tem três `object_events`, três `warp_events`, três `coord_events`, cinco `bg_events` e duas `connections`. Em sua `scripts.inc`, os dois gatilhos na saída norte chamam variantes do evento de Oak para impedir que o jogador saia sem Pokémon e conduzi-lo ao laboratório.

### 1.5 Ciclo de scripts do FireRed

O arquivo `include/constants/map_scripts.h` define:

| Original | Significado | Equivalente recomendado |
|---|---|---|
| `MAP_SCRIPT_ON_LOAD` | Ao carregar/setup do mapa | Preparação de visual/layout; hook específico, evitando Autorun repetido |
| `MAP_SCRIPT_ON_FRAME_TABLE` | Condições de cena em frame | Evento por toque/condição ou hook otimizado de mapa |
| `MAP_SCRIPT_ON_TRANSITION` | Durante a transição para o mapa | Inicializar estados visuais ao entrar |
| `MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE` | Condições após entrar por warp | Cena de entrada específica |
| `MAP_SCRIPT_ON_RESUME` | Retomada do mapa | Refresh sem duplicar recompensas |
| `MAP_SCRIPT_ON_DIVE_WARP` | Variante não utilizada nesse jogo | Não implementar sem caso real |
| `MAP_SCRIPT_ON_RETURN_TO_FIELD` | Retorno ao campo | Reconciliar visuais e bloqueios |

**Advertência:** evento `Parallel Process` rodando a cada frame para verificar toda a história é um anti-padrão. Preferir acionamento por tiles, troca de mapa ou mudança explícita de switch; quando precisar de hook de mapa, executar lógica idempotente.

---

# 2. Taxonomia completa de eventos

As famílias abaixo devem entrar no inventário do projeto. Um mesmo evento pode pertencer a mais de uma família.

| ID | Família | Funcionamento típico | Cuidados na implementação |
|---|---|---|---|
| EVT-01 | Diálogo NPC simples | Conversa ao pressionar ação | Visibilidade, orientação, diálogos variáveis |
| EVT-02 | Diálogo condicional | Mudanças por insígnias, itens, quests | Páginas em ordem de prioridade |
| EVT-03 | Tutorial/narrador | Explica captura, menu, itens | Executar uma vez quando necessário |
| EVT-04 | Placas, livros, computadores e objetos | `bg_events`/interação adjacente | Direção de leitura e colisão |
| EVT-05 | Itens no chão (Poké Bola) | Adiciona item e desaparece | Checagem da Bag cheia e flag persistente |
| EVT-06 | Itens escondidos | Investigar tile sem sprite | Flag por item; integração com Itemfinder |
| EVT-07 | NPC que entrega item/HM/TM | Recompensa por diálogo/quest | Evitar duplicação no reload |
| EVT-08 | Presentes Pokémon/ovos | Checagem de party/Box e espécie | Não perder presente com equipe cheia |
| EVT-09 | Troca com NPC | Entregar espécie e receber outra | Validação de espécie e armazenamento |
| EVT-10 | Compra e serviços | Loja, Centro Pokémon, Day Care, tutor | Reusar rotinas nativas do Essentials |
| EVT-11 | Treinador por visão | Detecta jogador, aproxima, batalha | Visão, colisão, derrota e persistência |
| EVT-12 | Treinador por diálogo | Batalha ao falar | Evitar luta automática na segunda página |
| EVT-13 | Líder, Elite Four, Campeão | Vitória libera progresso | Insígnia local, Hall of Fame, versão de time |
| EVT-14 | Rival com variação de equipe | Batalha por starter, momento, flags | Equipe determinística e estado consistente |
| EVT-15 | Revanches / VS Seeker | Reativação condicionada | Rematches sem duplicar recompensas |
| EVT-16 | Encontro selvagem aleatório | Grama, cavernas, água, pesca | Normalmente PBS/terrain tags, não 1 evento por encontro |
| EVT-17 | Selvagem estático | Snorlax, Electrode e lendários | Captura/derrota/fuga e flags corretas |
| EVT-18 | Inimigo de missão | Rocket Grunt, chefes, bloqueadores | Batalha e movimentação após resultado |
| EVT-19 | Gatilho por pisar (`coord`) | Cena em coordenada | `Player Touch`, ativado apenas na cena prevista |
| EVT-20 | Evento automático de entrada | Oak, rival, Bill e pós-Liga | Autorun com condição de saída garantida |
| EVT-21 | Sequência de cutscene | Mover NPC, diálogos, música, fade | Congelar movimento, restaurar controle |
| EVT-22 | Warp de porta | Casa, loja, ginásio | Warp de ida e volta, direção de saída |
| EVT-23 | Escadas e elevadores | Troca andar/cabine | IDs e coordenadas, opção de cancelamento |
| EVT-24 | Conexão contínua | Caminhar de uma rota para outra | `map_connections`, largura/alinhamento |
| EVT-25 | Teletransportadores | Saffron Gym, Silph Co. | Pares corretos e caminho recuperável |
| EVT-26 | Plataformas de seta/giro | Rocket Hideout, Rocket Warehouse | Movimentação forçada e cancelamento seguro |
| EVT-27 | Portões com requisito | Saffron, Cycling Road, Vitória | Bloquear quando requisito não atendido |
| EVT-28 | Obstáculo Cut | Árvores cortáveis | Permissão de HM/insígnia regional |
| EVT-29 | Obstáculo Rock Smash | Pedras quebráveis | Refresh ao trocar/recarregar mapa |
| EVT-30 | Boulder Strength | Pedra empurrável | Detectar colisão; estado persistente se necessário |
| EVT-31 | Surf/água/mergulho não usado | Entrada e saída de água | Não implementar Dive como necessário para FireRed |
| EVT-32 | Waterfall/corrente | Cachoeiras e correntezas | Restrição HM, direção e movimento contínuo |
| EVT-33 | Flash / escuridão | Rock Tunnel | Escuridão do mapa e desbloqueio pelo campo |
| EVT-34 | Bicicleta / Cycling Road | Acesso por bicicleta e movimento | Conferir posse, liberar desmontar, restrição de mapa |
| EVT-35 | Gelo que quebra/escorrega | Icefall Cave | Reset e transição controlada |
| EVT-36 | Correnteza e pedra que cai | Seafoam Islands | Layout alternativo após bloquear correnteza |
| EVT-37 | Puzzle de placas/botões | Cinnabar Gym, Victory Road | Switch de sala, estado de puzzle e reentrada |
| EVT-38 | Paredes/barreiras mutáveis | Giovanni, Rocket Hideout, Silph | Atualizar tile e colisão em conjunto |
| EVT-39 | Roteiro de ferry/viagem | S.S. Anne, barcos Sevii | Destinos disponíveis, flags de progresso |
| EVT-40 | História e quests | Bill, Poké Flute, Silph Scope, Ruby/Sapphire | Flags globais idempotentes |
| EVT-41 | Hall of Fame e crédito | Elite Four e campeão | Salvar conclusão, não repetir premiações |
| EVT-42 | Pós-jogo e bloqueios | Cerulean Cave, National Dex | Múltiplos requisitos e diálogo explicativo |
| EVT-43 | Minigame/área especial | Safari, Game Corner, Trainer Tower | Regras e recursos opcionais independentes |
| EVT-44 | Pokémon Center/respawn | Cura, ponto de retorno pós-derrota | Atualizar ponto com segurança |
| EVT-45 | Clima, áudio, animação de mapa | Música, BGS, fade, efeito do terreno | Aplicação ao entrar/sair, sem loop de som |
| EVT-46 | Atividade contextual | Pesca, Itemfinder, TV, PC, troca | Distinguir serviço de evento visual |
| EVT-47 | Desbloqueio no mundo | Insígnias, Pokédex, mapa, ferry | Alterar apenas estado de Kanto, não Decades |
| EVT-48 | Evento especial por distribuição | Birth Island / Navel Rock | Separado de progresso obrigatório; habilitação explícita |
| EVT-49 | Evento desativado/protótipo | Mapas de protótipo | Catalogar, **não** liberar automaticamente |
| EVT-50 | Scripts globais reutilizáveis | Comportamento comum de itens, portas, HM | Common Event / plugin com API estável |

## 2.1 Ordenação de importância

**Obrigatório para campanha:** EVT-01–07, 10–14, 16–25, 27–34, 36–42, 44–47 quando presente no fluxo.  
**Conteúdo secundário/postgame:** presentes, trocas, rematches, Safari, Game Corner, Trainer Tower, tutor, Sevii, eventos especiais.  
**Não confundir:** `trainer_type` no JSON identifica tipo de interação/visão, não o time completo; o script e os dados de treinador definem a batalha real.

---

# 3. Como converter eventos FireRed para RMXP/Essentials

| Campo/origem FireRed | Ação no RPG Maker XP/Essentials |
|---|---|
| `object_events[].graphics_id` | Associar sprite de NPC/objeto disponível no `Graphics/Characters` |
| `object_events[].script` | Traduzir referência para página de evento ou chamada de script Ruby |
| `object_events[].flag` | Switch/flag do namespace Kanto ou condição de página |
| `movement_type` e ranges | Autonomous Movement + Custom Move Route, sem travar passagens |
| `trainer_type` e `trainer_sight_or_berry_tree_id` | Evento `Trainer(n)` e alcance equivalente, quando for treinador |
| `warp_events[].dest_map` | `Transfer Player` usando mapa RXDATA de destino |
| `warp_events[].dest_warp_id` | Resolver índice do warp de destino para coordenada real |
| `coord_events[]` | Evento invisível `Player Touch`, ou guardião de cena com condições |
| `coord_events[].var/var_value` | Condição de variável ou `Conditional Branch` |
| `bg_events` tipo `sign` | Evento sem sprite, `Action Button`, texto |
| `bg_events` tipo item oculto | Evento invisível com flag e tag Itemfinder |
| `connections[].direction/offset` | Map Connections do Essentials, com alinhamento e dimensões corretas |
| `MAP_SCRIPT_ON_LOAD` | Atualização visual ao carregar mapa / hook de entrada |
| `MAP_SCRIPT_ON_FRAME_TABLE` | Trocar checagem contínua por gatilho + flag, salvo caso necessário |
| `MAP_SCRIPT_ON_TRANSITION` | Função idempotente na entrada, sem recompensa duplicada |
| `setflag/clearflag` | Mudar o estado persistente de Kanto |
| `setvar/addvar/copyvar` | Variável persistida do arco local |
| `applymovement/waitmovement` | `Set Move Route` + `Wait for Move's Completion` |
| `addobject/removeobject` | Evento com página ativa/inativa, switch e `Erase Event` se temporário |
| `setmetatile` | Troca de tile/estado de porta via evento, tile overlay ou script específico |
| `wildbattle` | `WildBattle.start(...)` / rotina específica do Essentials |
| `trainerbattle` | `TrainerBattle.start(...)` / evento de treinador |
| `playbgm/playse` | BGM/BGS/SE do RMXP e restauração de música |
| `warp` | Transferência segura com transição/fade e retorno |

**Nunca** converter `FLAG_*` do GBA em um número de switch aleatório. Crie tabela de tradução e verificações de colisão.

## 3.1 Páginas do RPG Maker XP: comportamento

- **Action Button:** falar com NPC, placa, pegar item.
- **Player Touch:** entrar em tile que dispara encontro/cena.
- **Event Touch:** treinador que detecta o jogador (com as convenções do Essentials).
- **Autorun:** sequência cinematográfica com *condição que obrigatoriamente desliga/avança*.
- **Parallel Process:** somente rotina leve ou com intervalos, e quando não houver alternativa por evento/hook.
- **Self Switch A/B/C/D:** estado específico daquela instância de evento (ex.: treinador derrotado). Não reutilizar como armazenamento global de uma quest compartilhada por vários mapas.
- **Switch global:** requisito cruzando mapas (ex.: Rocket Hideout resolvida).
- **Variable:** estágio de uma quest, sequência de rival, puzzle, visita.

**Prioridade das páginas:** RMXP seleciona a página válida de maior número. Documente e teste para evitar que a página errada assuma o controle.

---

# 4. Catálogo por cidade, rota e região

> Resumo funcional por localização. **Não é uma transcrição linha a linha de todas as `scripts.inc`.** Para cada objeto/warp/coord/bg individual, execute o extrator do capítulo 12. Os conteúdos indicados são referenciais a validar nos scripts originais ao implementar.

## 4.1 Cidades, ginásios e áreas urbanas

| Área | Eventos e comportamentos prioritários | Dependências e conclusão |
|---|---|---|
| **Pallet Town** | Casa do jogador, introdução, laboratório de Oak, bloqueio da Rota 1, escolha do inicial, rival, Pokédex, diálogos, placas, pós-Liga | Inicial, Pokédex, Poké Balls, National Dex condicional |
| **Viridian City** | Poké Mart com entrega da Oak's Parcel, Centro Pokémon, NPCs, ginásio inicialmente fechado, acesso à Rota 22 | Devolver encomenda no laboratório; Ginásio de Giovanni liberado mais tarde |
| **Pewter City** | Museu, NPC que orienta/bloqueia, Brock, primeiro ginásio, recompensa, caminho da Rota 3 | Boulder Badge, liberação de Flash conforme regras |
| **Cerulean City** | Rival ao norte, Misty, Nugget Bridge via Rotas 24/25, Rocket na casa invadida, passagem pós-evento, loja de bicicleta, guarda da Cerulean Cave | Cascade Badge, missão Bill, encontro Rocket; Cerulean Cave no pós-jogo |
| **Vermilion City** | S.S. Anne, rival no navio, capitão e HM Cut, puzzle de latas do ginásio, Lt. Surge, Fan Club, passagem próxima a Diglett's Cave | S.S. Ticket, Cut obtido, Thunder Badge |
| **Lavender Town** | Pokémon Tower, rival, fantasma de Marowak, Rockets, resgate de Mr. Fuji, Poké Flute | Silph Scope para resolver a torre; Poké Flute para Snorlax |
| **Celadon City** | Department Store, condomínio com presente de Pokémon, Game Corner, entrada secreta Rocket Hideout, Erika, NPCs, bebidas/itens e prêmios | Silph Scope após Giovanni; Rainbow Badge; itens de acesso |
| **Saffron City** | Entrada condicionada aos guardas, Rocket toma a cidade, Silph Co., rival, Giovanni, Master Ball, Dojo com escolha de prêmio, Sabrina e teleportes | Chá para guardas; libertar Silph; Marsh Badge |
| **Fuchsia City** | Safari Zone, Gold Teeth, Secret House HM Surf, Warden HM Strength, Koga, ginásio com paredes invisíveis, pesca e NPCs | Soul Badge e acesso a Surf; Rainbow Badge para Strength |
| **Cinnabar Island** | Pokémon Lab e revival de fósseis, Pokémon Mansion, switches de estátuas, Secret Key, Blaine, Bill e primeira visita Sevii | Volcano Badge; nova etapa de viagem com Bill |
| **Indigo Plateau** | Entrada da Liga, cura, Elite Four Lorelei/Bruno/Agatha/Lance, campeão/rival, Hall of Fame | Oito insígnias, Victory Road, conclusão Kanto |

### Interiores urbanos que precisam de eventos próprios

- **Pallet:** quarto/casa 1F e 2F, casa do rival, Oak's Lab.
- **Viridian:** escola, Market, Centro 1F/2F, casas e Gym.
- **Pewter:** Museu 1F/2F, Gym, Market, Centro 1F/2F e casas.
- **Cerulean:** quatro/cinco casas, Gym, Bike Shop, Market e Centro; separar NPCs de história dos serviços.
- **Lavender:** Centro, Pokémon House, casas, Market e torre.
- **Vermilion:** Fan Club, três casas, Centro, Market, Gym, várias salas do S.S. Anne.
- **Celadon:** Department Store 1F–5F, Roof/Elevator; condomínio 1F–Roof Room; Game Corner/Prize Room; Gym, restaurante, hotel, casas e Centro.
- **Fuchsia:** Safari Gate/Office, Gym, Warden's House, casas, Market e Centro.
- **Cinnabar:** Gym, laboratório (entrada/lobby/pesquisa/experimentos), Centro, Market.
- **Saffron:** Copycat's House 1F/2F, Dojo, Gym, Market, Centro, Mr. Psychic, Trainer Fan Club e Silph Co.
- **Indigo:** Centro 1F/2F e todas as salas da Liga.

## 4.2 Rota por rota — **Rotas 1–25**

| Rota | Eventos que não podem faltar | Observações de implementação |
|---|---|---|
| **1** | NPC funcionário do Mart que entrega **Potion uma vez**, garoto que explica ledges, placa, encontros | `Route1_EventScript_MartClerk`; cuidado com inventário cheio |
| **2** | Acesso à Viridian Forest, Cut trees, portaria de Flash com auxiliar de Oak (10 espécies capturadas), acesso Diglett's Cave | Revisar porta, Cut e `Route2_EastBuilding` |
| **3** | Treinadores, itens, passagem à Rota 4 / Mt. Moon | Treinadores com visão e múltiplas posições |
| **4** | Entrada/saída Mt. Moon, Centro Pokémon, tutores de golpes, saída com desnível para Cerulean | Testar ledges e retorno com Surf mais tarde |
| **5** | Day Care, conexão a Cerulean e Underground Path, acesso à Saffron bloqueado inicialmente | Prioridade de mensagens de guardas |
| **6** | Underground Path, treinadores, entrada de Vermilion e controle de Saffron | Continuidade dos warps |
| **7** | Celadon ↔ Saffron, passagem subterrânea, portaria e guardas | Dependência do Chá de Saffron |
| **8** | Lavender ↔ Saffron, treinadores, Underground Path e portaria | Entradas distintas leste/oeste |
| **9** | Treinadores, árvores Cut, conexão Rock Tunnel | Verificar acesso físico à Rota 10 |
| **10** | Centro, Rock Tunnel, costa Surf e acesso Power Plant, encontros | Flash no túnel; Surf para usina |
| **11** | Treinadores, entrada Diglett's Cave, portaria e NPCs | Itens e observatórios em 2F |
| **12** | Snorlax estático, Poké Flute, ponte e acesso a locais de pesca | Separar flags “acordou”, “lutou” e “sumiu” |
| **13** | Treinadores, corredores de cercas e itens | Alcance de visão em corredores estreitos |
| **14** | Treinadores, conexão Fuchsia, pequenas rotas alternativas | NPCs opcionais não devem bloquear indevidamente |
| **15** | Treinadores, itens, portaria oeste, ligação Fuchsia | Inspecionar quadros/observatório 2F |
| **16** | Snorlax estático, caminho de Fly, entrada Cycling Road e checagem de bicicleta | `Route16_OnTransitionCyclingRoad` e cena do Snorlax |
| **17** | Cycling Road com movimentação forçada/declive, ciclistas e treinadores | Testar movimento, bici e retorno |
| **18** | Portaria/ciclovia, treinadores, Fuchsia | Bloqueio por bicicleta se aplicável |
| **19** | Saída marítima de Fuchsia e chegada às Seafoam Islands | Surf obrigatório em parte do caminho |
| **20** | Seafoam Islands, travessia a Cinnabar, treinadores na água | Correntes devem respeitar estado das pedras |
| **21** | Surf ao sul de Pallet (submapas norte/sul), Pokémon e treinadores aquáticos | Conexões, respawn e encontros Surf |
| **22** | Rival em mais de um estágio, caminho para a Liga | Times por estágio/starter, checagens de progressão |
| **23** | Portões sucessivos de insígnias, água/obstáculos, Victory Road | Verificar **cada** uma das oito insígnias de Kanto |
| **24** | Nugget Bridge, treinadores, Rocket Grunt disfarçado, rival próximo à entrada norte | Sequência de batalhas e prêmio único |
| **25** | Bill, Sea Cottage, treinadores, ajuda a restaurar forma humana e obter S.S. Ticket | Quest interligada com Vermilion e Cerulean |

> Alguns percursos podem ser visitados fora da sequência acima. Não restringir rotas à ordem de desenvolvimento quando o FireRed permite retorno/atalho.

## 4.3 Dungeons e prédios especiais — eventos de maior complexidade

| Local | Evento/puzzle | Estado persistido/regras |
|---|---|---|
| **Viridian Forest** | Treinadores Bug Catcher, itens, encontros, saídas/entradas | Derrotados salvos; mapas conectados à Rota 2 |
| **Mt. Moon 1F/B1F/B2F** | Rockets, fósseis Helix/Dome, cientista, itens e escadas | Apenas um fóssil por escolha; encontro comum |
| **Diglett's Cave** | Traversal para Rota 2, encontros e escadas | Checar retorno e spawn correto |
| **S.S. Anne** | Convés, corredores 1F/2F/3F/B1F, quartos, treinadores, rival, capitão, HM Cut, navio parte | `FLAG_GOT_HM01`, condição para partida; não prender jogador no navio |
| **Rock Tunnel** | Escuridão/Flash, treinadores e escadas 1F/B1F | Flash é opcional para completar passagem |
| **Pokémon Tower 1F–7F** | Rival, canalizadoras, espíritos, Ghost de Marowak e Rockets, Mr. Fuji | Silph Scope, impedir capturar Marowak, concluir quest |
| **Rocket Hideout B1F–B4F** | Entrada no Game Corner, pisos de seta, Rockets, Lift Key, elevador e Giovanni | Esconder barreiras, adquirir Lift Key, entregar Silph Scope |
| **Silph Co. 1F–11F** | Guardas, muitos treinadores, Card Key, portas, warp tiles, rival, Giovanni e Master Ball | Salas distintas, recompensa uma vez, liberar Saffron |
| **Saffron Gym** | Teleportes e Sabrina | Visão correta das salas e retorno garantido |
| **Fuchsia Gym** | Paredes transparentes/invisíveis e Koga | Colisão não deve sumir apenas visualmente |
| **Cinnabar Pokémon Mansion 1F–B1F** | Diário de Mew/Mewtwo, switches das estátuas, portas, Secret Key | Puzzle com estado e reset coerentes |
| **Cinnabar Gym** | Questões/portas, treinadores, Blaine | Responder certo ou batalha; liberar progresso |
| **Safari Zone Center/East/North/West** | Limite de passos/tempo, Safari Balls, Gold Teeth, HM Surf na Secret House, itens | Terminação de sessão e retorno à entrada |
| **Power Plant** | Electrode disfarçados de itens, Zapdos e colecionáveis | Flags por cada Electrode e Zapdos |
| **Seafoam Islands 1F–B4F** | Empurrar pedras/queda entre andares, bloquear correnteza, Articuno | `FLAG_STOPPED_SEAFOAM_B4F_CURRENT`; flags das rochas e lendário |
| **Victory Road 1F–3F** | Pedras Strength sobre botões/pisos, barreiras, treinadores | Cada sala deve validar botão, tile e colisão |
| **Pokémon League** | Elite Four sequencial, campeão, Hall of Fame | Travar progresso até vitória; registrar fim da Liga uma vez |
| **Cerulean Cave 1F/2F/B1F** | Guarda de entrada, Pokémon de alto nível e Mewtwo | Pós-jogo e quest Celio/Network Machine |

## 4.4 Ilhas Sevii — **conteúdo principal e pós-jogo**

**Primeiro arco** ocorre após Blaine com Bill e Celio, envolvendo One, Two e Three Island. O segundo arco usa o pós-Liga/National Dex e expande às demais ilhas. Não misturar essas condições.

| Ilha/área | Eventos importantes | Resultado esperado |
|---|---|---|
| **One Island** | Bill/Celio no Pokémon Center/Network Center, Tri-Pass, ferry, missão Ruby/Sapphire | Arco de ilhas e máquina de rede |
| **Kindle Road / Ember Spa** | NPC entrega HM Rock Smash; campo e encontros | TM/HM sem duplicação |
| **Mt. Ember** | Moltres no cume; caminho de Ruby destravado na missão posterior, Rockets | Ruby recuperada para Celio |
| **Treasure Beach** | Itens, encontros e exploração Surf | Reentrada e respawn de itens apenas onde permitido |
| **Two Island** | Joyful Game Corner, pedido da filha, Cape Brink, Move Tutor | Conduz missão de Lostelle |
| **Three Island** | Gangue de motoqueiros, Berry Forest, Lostelle e Hypno | Resgate conclui primeiro arco Sevii |
| **Four Island** | Breeding Day Care, Icefall Cave, Lorelei e Rockets | HM Waterfall + confronto Rockets |
| **Five Island** | Rocket Warehouse, duas senhas, puzzles de seta, Resort Gorgeous, Lost Cave e NPCs | Recuperar Sapphire de Gideon |
| **Six Island** | Ruin Valley, Dotted Hole, quebra-cabeça Braille, Sapphire roubada | Destrava perseguição ao Rocket Warehouse |
| **Seven Island** | Trainer Tower, Sevault Canyon, Tanoby Key, Tanoby Ruins/Unown e NPCs | Desafios e ruínas exploráveis |
| **Navel Rock** | Lugia/Ho-Oh, Harbour, caminhos e múltiplos andares | Evento especial opcional; não obrigatório na campanha |
| **Birth Island** | Puzzle triangular e Deoxys | Evento especial opcional; ativação independente |
| **Altering Cave / Pattern Bush / Lost Cave** | Encontros e navegação especial | Não confundir conteúdo distribuído/evento com história regular |
| **Cerulean Cave (ligada ao pós-jogo Sevii)** | Remoção do guarda e Mewtwo | Requisitos do pós-jogo observados |

**Caso especial — Sapphire:** a cena da sala de Sapphire em Dotted Hole envolve um NPC que rouba a pedra; por isso, **não** marcar a missão como concluída na primeira interação. Só após Rocket Warehouse e entrega a Celio.

## 4.5 Outras atividades recorrentes a mapear

- **Centros Pokémon:** interação da enfermeira, computador, local de cura e passagem 2F (se compatível).
- **Poké Marts:** catálogo de itens por estágio e, em Viridian, encomenda obrigatória antes de vender normalmente.
- **Day Care:** depósito/retirada, preço, geração de ovos no contexto do jogo.
- **Game Corner e prêmio:** minigame, moedas, balcão de recompensa, acesso ao Rocket Hideout.
- **Move Tutors:** golpes exclusivos, requisitos e se o uso é único.
- **Fósseis:** Mt. Moon entrega fóssil; laboratório de Cinnabar revive.
- **In-game trades:** conferir requisitos de espécies, nickname, atributos e disponibilidade.
- **NPCs que mudam de lugar:** Oak, rival, Rockets, bloqueadores, guardas, Bill e Celio.
- **NPCs que mudam o texto:** após insígnia, após Silph, após vitória na Liga, após National Dex e após Ruby/Sapphire.
- **Objetos que mudam collision:** barreira, portão, porta, rocha, árvore e parede de puzzle.
- **Cheats/debug:** nunca depender de flag de debug para progressão real.

---

# 5. Linha de progresso de Kanto e condições

> Isto é um **grafo de dependências**, não a única ordem de visita. Exemplos: Erika, Koga e Sabrina permitem certa flexibilidade; a ordem narrativa de desenvolvimento não pode eliminar essa flexibilidade.

| Passo lógico | Evento marco | Exige | Desbloqueia | Sugestão de flag Kanto |
|---:|---|---|---|---|
| 01 | Oak intercepta ao sair de Pallet | Sem inicial | Laboratório | `KANTO_OAK_INTERCEPTED` |
| 02 | Escolher inicial + rival no lab | Escolha válida | Rota 1 | `KANTO_STARTER_CHOSEN` |
| 03 | Receber Oak's Parcel | Viridian Mart | Entrega Oak | `KANTO_PARCEL_RECEIVED` |
| 04 | Entregar encomenda / receber Pokédex | Parcel | Pokédex, bolas, continuação | `KANTO_POKEDEX_RECEIVED` |
| 05 | Brock e insígnia | Acesso Pewter | Boulder/Flash | `KANTO_BADGE_BOULDER` |
| 06 | Mt. Moon / fóssil | Acesso Rota 3 | Cerulean | `KANTO_MT_MOON_FOSSIL_SELECTED` |
| 07 | Rival/Nugget Bridge e Bill | Cerulean norte | S.S. Ticket | `KANTO_SS_TICKET_RECEIVED` |
| 08 | Misty | Cerulean Gym | Cascade/Cut | `KANTO_BADGE_CASCADE` |
| 09 | Rocket casa invadida | Estado da cidade | Acesso à saída leste | `KANTO_CERULEAN_ROCKET_DEFEATED` |
| 10 | S.S. Anne: rival e capitão | S.S. Ticket | HM Cut | `KANTO_HM_CUT_RECEIVED` |
| 11 | Lt. Surge | Cut utilizável | Thunder/Fly | `KANTO_BADGE_THUNDER` |
| 12 | Rocket Hideout / Giovanni | Celadon | Silph Scope | `KANTO_SILPH_SCOPE_RECEIVED` |
| 13 | Pokémon Tower / Mr. Fuji | Silph Scope | Poké Flute | `KANTO_POKE_FLUTE_RECEIVED` |
| 14 | Acordar Snorlax R12/R16 | Poké Flute | Abrir rotas | `KANTO_SNORLAX_R12_RESOLVED` etc. |
| 15 | Conseguir Chá e acesso Saffron | NPC de Celadon/guardas | Entradas Saffron | `KANTO_TEA_GATE_OPEN` |
| 16 | Silph Co. / Giovanni | Acesso Saffron | Master Ball, cidade livre | `KANTO_SILPH_LIBERATED` |
| 17 | Erika/Koga/Sabrina conforme acesso | Respectivos ginásios | Rainbow/Soul/Marsh | `KANTO_BADGE_*` |
| 18 | Safari Zone: Gold Teeth e Surf | Entrar no Safari | Strength/Surf | `KANTO_GOLD_TEETH_RETURNED` + itens |
| 19 | Cinnabar Mansion + Blaine | Surf, Secret Key | Volcano, Bill/Sevii inicial | `KANTO_BADGE_VOLCANO` |
| 20 | Ilha 1–3: Bill, Lostelle | Convite Bill | Retorno, missão inicial | `KANTO_SEVII_123_COMPLETE` |
| 21 | Ginásio Viridian / Giovanni | Progresso história/ginásio aberto | Earth Badge | `KANTO_BADGE_EARTH` |
| 22 | Rota 22 e Rota 23 | Oito insígnias | Victory Road | `KANTO_VICTORY_ROAD_OPEN` |
| 23 | Elite Four + rival | Caminho concluído | Hall of Fame | `KANTO_LEAGUE_CLEARED` |
| 24 | National Dex | Liga + requisito oficial (60 espécies capturadas, ver cena Oak) | Arco avançado Sevii | `KANTO_NATIONAL_DEX_UNLOCKED` |
| 25 | Mt. Ember Ruby → Celio | National Dex + missão | Rainbow Pass | `KANTO_RUBY_DELIVERED` |
| 26 | Icefall Cave / Lorelei | Rainbow Pass | Avançar investigação Rocket | `KANTO_ICEFALL_LORELEI_HELPED` |
| 27 | Dotted Hole Sapphire roubada | Progresso avançado | Seguir Rocket Warehouse | `KANTO_SAPPHIRE_STOLEN` |
| 28 | Rocket Warehouse / Sapphire recuperada | Duas senhas | Sapphire entregue | `KANTO_SAPPHIRE_DELIVERED` |
| 29 | Network Machine concluída | Ruby + Sapphire entregues | Condições de pós-jogo e Cerulean Cave | `KANTO_NETWORK_MACHINE_ON` |
| 30 | Cerulean Cave/Mewtwo | Pós-jogo concluído | Lendário opcional | `KANTO_MEWTWO_RESOLVED` |

**Nota:** algumas flags aqui são **nomes propostos para o seu projeto**, não nomes originais do FireRed nem switches já existentes do Essentials. Os pré-requisitos exatos devem ser confirmados com os scripts do mapa e regras específicas de dificuldade do Blue.

## 5.1 Grafo dos principais bloqueios

```text
Pallet início
  -> Oak intercepta -> inicial -> encomenda -> Pokédex
  -> Viridian Forest -> Brock -> Mt. Moon -> Cerulean
  -> Bill / Ticket -> S.S. Anne -> Cut -> Lt. Surge
  -> Celadon Rocket Hideout -> Silph Scope -> Pokémon Tower -> Poké Flute
  -> Snorlax removidos / conexões -> Safari + Silph Co. + ginásios intermediários
  -> Surf -> Cinnabar -> Blaine -> Sevii 1-3 (arco de Bill)
  -> Viridian Gym -> 8 insígnias -> Victory Road -> Liga
  -> National Dex (quando elegível) -> Ruby -> Rainbow Pass
  -> Icefall / Dotted Hole / Rocket Warehouse -> Sapphire -> Celio
  -> Cerulean Cave
```

## 5.2 Flexibilidade obrigatória

- Não obrigar **Misty antes de Bill** se o caminho funcionar no original.
- Não exigir limpar toda a Silph Co. para visitar a parte acessível de Saffron, salvo bloqueios reais de cada prédio.
- A ordem dos ginásios intermediários deve respeitar os mapas e regras do projeto, sem forçar uma fila inexistente.
- **Mewtwo, Deoxys, Lugia e Ho-Oh não são pré-requisitos para finalizar a Liga**.
- **Não confundir possuir HM com poder usá-la fora de batalha**: a insígnia local e a lógica regional precisam permitir.

---

# 6. HMs, insígnias e eventos de campo

Tabela de FireRed (os nomes das HMs e insígnias são os oficiais do remake; não copiar os IDs do GBA para Essentials).

| HM | Origem | Insígnia de Kanto para uso externo | Evento de campo |
|---|---|---|---|
| **HM01 Cut** | Capitão do S.S. Anne | **Cascade** (Misty) | Árvore e grama |
| **HM02 Fly** | Casa na Rota 16 | **Thunder** (Lt. Surge) | Viagem a cidade já visitada |
| **HM03 Surf** | Secret House no Safari Zone | **Soul** (Koga) | Entrar na água |
| **HM04 Strength** | Warden em Fuchsia após Gold Teeth | **Rainbow** (Erika) | Empurrar pedras |
| **HM05 Flash** | Oak's Aide, portaria Rota 2 após registrar 10 espécies capturadas | **Boulder** (Brock) | Iluminar cavernas |
| **HM06 Rock Smash** | Ember Spa, One Island | **Marsh** (Sabrina) | Quebrar rochas |
| **HM07 Waterfall** | Icefall Cave, Four Island | **Volcano** (Blaine) | Subir cachoeira |

`HM08 Dive` não é disponível/necessário em FireRed. Não inventar requisito de Dive.

**Para Dessastre Paradoxal:** manter o requisito de **insígnia de Kanto** no mapa Kanto. Uma insígnia de Johto/Decades não deve desbloquear Cut em Kanto por engano. O projeto já dispõe de uma política regional de HMs; integrar a ela em vez de sobrescrever funções globais de campo. Quaisquer montarias/sistemas novos devem ter uma tabela de equivalência documentada.

### Evento de campo: rotina segura

1. Interagir com obstáculo (ou usar golpe de campo pelo menu).
2. Descobrir região atual; identificar técnica exigida.
3. Checar Pokémon/montaria e regra local.
4. Checar **insígnia da região**, salvo exceção explícita.
5. Executar animação + som + troca de tile/colisão.
6. Persistir apenas se a regra original pedir persistência; obstáculos temporários podem voltar após reentrada.
7. Testar acesso por ambos os lados e não deixar sprite fantasma invisível bloqueando passagem.

---

# 7. Estado, flags e saves — contrato recomendado

## 7.1 Separar três estados

1. **Progresso regional persistente:** insígnias, missões, itens de quest, rival, Liga, pós-jogo e NPCs globais de Kanto.
2. **Estado local persistente:** treinadores derrotados, presentes coletados, blocos resolvidos e encontros únicos.
3. **Estado temporário do mapa:** movimento do NPC, puzzle temporário, som, transição ou câmera.

Não usar uma flag global para algo que precisa distinguir duas instâncias; exemplo Snorlax da Rota 12 e da Rota 16 exigem estados separados.

## 7.2 Namespace de identificadores

Adote:

```text
KANTO_STORY_*
KANTO_BADGE_*
KANTO_NPC_*
KANTO_ITEM_*
KANTO_TRAINER_*
KANTO_PUZZLE_*
KANTO_LEGENDARY_*
KANTO_SEVII_*
KANTO_META_*
```

Modelo de inventário em CSV:

```csv
fire_red_map,fire_red_script,event_type,blue_map_id,blue_event_id,flag_source,flag_dest,status,test
PalletTown,PalletTown_EventScript_OakTriggerLeft,coord,RESOLVER,RESOLVER,VAR_MAP_SCENE_PALLET_TOWN_OAK,KANTO_STORY_OAK,pendente,manual
Route1,Route1_EventScript_MartClerk,npc,RESOLVER,RESOLVER,FLAG_GOT_POTION_ON_ROUTE_1,KANTO_ITEM_R1_POTION,pendente,bag_cheia
Route12,Route12_EventScript_Snorlax,static,RESOLVER,RESOLVER,FLAG_HIDE_ROUTE_12_SNORLAX,KANTO_LEGENDARY_R12_SNORLAX,pendente,captura_derrota_fuga
```

Os valores `RESOLVER` são intencionais. **Nunca inventar IDs RXDATA, eventos ou switches sem checar o projeto instalado.**

## 7.3 Máquina de estados recomendada

Exemplo da quest Ruby/Sapphire:

```text
0 = missão indisponível
1 = Celio pediu Ruby
2 = Ruby adquirida
3 = Ruby entregue, Rainbow Pass recebido
4 = Dotted Hole acessado
5 = Sapphire encontrada e roubada
6 = duas senhas obtidas / Warehouse acessível
7 = Sapphire recuperada
8 = Sapphire entregue, Network Machine ligada
```

Não modelar `SAPPHIRE_COLLECTED=true` na primeira cena de Dotted Hole porque o objeto é roubado antes da entrega final.

## 7.4 IDs, migrações e idempotência

- Criar **registro central de todos os `MapID`** do Kanto adicionado.
- Validar colisões de `event_id`/switches/variáveis com os do Decades e plugins instalados.
- Guardar versão do esquema `KANTO_SAVE_SCHEMA_VERSION` e migração opcional para saves antigos.
- **Nenhuma recompensa permanente pode ser entregue duas vezes** por reload, transferência, derrota, escolha diferente ou viagem entre regiões.
- Checar antes de salvar se o PC possui espaço e se a party ficará válida ao aplicar a regra de especiais.
- Após um reload, reconstruir a aparência dos eventos a partir do estado persistente.

## 7.5 Independência do Decades

Na cópia do seu projeto, **Decades continua campanha principal** e a entrada em Kanto é experimental/opt-in. O estado Kanto deve ser um complemento ao save único, não um overwrite do progresso Decades. Testar Kanto em save de teste separado antes de integrar viagem permanente.

---

# 8. Passo a passo no RPG Maker XP + Pokémon Essentials v21.1

## Passo 1 — Congelar uma versão e fazer backup

1. Copiar a pasta local do jogo (`Game.rxproj`, `Data`, `PBS`, `Graphics`, `Audio`, `Plugins`).
2. Copiar os saves para uma pasta isolada.
3. Registrar hashes, versão do Essentials, versão dos plugins, scripts modificados e data.
4. Se integrar a um repositório, criar branch independente `feature/kanto-eventos-firered`.
5. **Não** modificar a instalação jogável do Decades antes de passar testes no piloto.

**Critério:** abrir a cópia e reproduzir uma partida Decades existente antes de qualquer alteração.

## Passo 2 — Obter a referência decompilada (sem ROM)

No Windows com Git e Python:

```powershell
git clone https://github.com/pret/pokefirered.git
cd pokefirered
git rev-parse HEAD
```

Guardar o commit encontrado no relatório de auditoria. Não é necessário compartilhar uma ROM. A decompilação é fonte de **estrutura e lógica**; o uso de assets e código de terceiros exige conferir autorizações/licenças aplicáveis.

## Passo 3 — Produzir o inventário literal por mapa

Colocar `extrair_eventos_firered.py` em pasta própria e executar:

```powershell
python .\extrair_eventos_firered.py "C:\CAMINHO\pokefirered" --out ".\auditoria-firered"
```

Arquivos gerados:

- `INVENTARIO_COMPLETO_FIRERED.md` — entradas explícitas por mapa, scripts, flags e variáveis.
- `eventos_detalhados.csv` — uma linha por registro (`object`, `warp`, `coord`, `bg`, `connection`).
- `eventos_detalhados.json` — mesmo inventário em JSON.
- `mapas_resumo.json` — contagens e fontes por mapa.

**Limite proposital:** o gerador não converte scripts assembly em Ruby, não revela automaticamente todos os encontros aleatórios e não cria eventos RXDATA; ele serve para impedir que objetos e warps sejam esquecidos.

## Passo 4 — Fazer a correspondência de mapas

Crie uma planilha/tabela como:

```text
MAP_PALLET_TOWN -> MAPID_KANTO_PALLET -> RPG Maker MapXXX.rxdata
MAP_ROUTE1 -> MAPID_KANTO_ROUTE1 -> RPG Maker MapYYY.rxdata
MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB -> MAPID_KANTO_OAK_LAB -> RPG Maker MapZZZ.rxdata
```

`XXX/YYY/ZZZ` devem ser resolvidos **após** a importação real, nunca copiados do GBA. Verificar tamanho, tileset, collision, prioridade, nome, clima, encontros, BGM, portas e posição de chegada.

## Passo 5 — Montar mapas e tilesets primeiro

1. Criar/importar mapas RMXP compatíveis com o Essentials v21.1.
2. Garantir que cada tile tenha passabilidade/priority/terrain tag corretos.
3. Registrar buracos, ledges, portas, água, pedras e árvores.
4. Configurar Map Connections para travessias contínuas sem fade quando adequado.
5. **Só depois** adicionar os NPCs e scripts.

Não é suficiente importar imagem de mapa: uma screenshot não possui eventos, colisões, tiles individuais nem conexão funcional.

## Passo 6 — Identificar eventos da fase piloto

Para cada mapa, ler `map.json` e `scripts.inc`. Criar uma linha no inventário para cada evento, com tipo, coordenada, sprite, flag, condicionais, diálogos, efeito e dependências.

Ordenação eficiente:

1. `warp_events` (entrou/saiu do prédio?)
2. `connections` (atravessou bordas?)
3. `object_events` NPC e treinadores (pode interagir/lutar?)
4. `coord_events` (cena automática dispara uma vez?)
5. `bg_events` (placas/itens ocultos)
6. Scripts de entrada do mapa e rotinas globais
7. Encontros aleatórios/itens/PBS
8. Flags e save/reload

## Passo 7 — Criar o primeiro evento (placa)

No RPG Maker XP:

1. Modo Events (F8); dê duplo clique no tile da placa.
2. Nome: `KANTO_SIGN_PALLET_LAB`.
3. Trigger: **Action Button**; Priority: **Same as Characters** para o objeto sólido ou a prioridade compatível com seu tile.
4. Comando `Show Text`: seu texto localizado, sem copiar assets protegidos.
5. Teste o alcance de interação em quatro direções e se há colisão.

## Passo 8 — Criar warp de porta com retorno

Na porta da casa do jogador em Pallet:

1. Evento invisível no tile da soleira.
2. Trigger: **Player Touch**.
3. Comando `Transfer Player` → mapa `KANTO_HOUSE_1F`, coordenada exata da entrada interna.
4. Adicionar evento recíproco no interior para voltar à Pallet.
5. Configurar direção final do personagem e comportamento de porta/SE/fade.
6. Testar entrar/sair 10 vezes, salvar dentro e reabrir.

**Atenção:** `dest_warp_id` do GBA é índice da lista de warps do mapa de destino, **não** um MapID do RPG Maker.

## Passo 9 — Criar NPC de item único

Exemplo da Rota 1:

- Página 1: `Action Button`, texto do vendedor, checar espaço na Bag, entregar `POTION`, ativar **Self Switch A** somente depois de sucesso.
- Página 2 (Self Switch A ON): texto de NPC que já entregou o item; sem recompensa.
- Para preservar a equivalência FireRed e permitir uso em outros mapas, preferir flag Kanto global `KANTO_ITEM_R1_POTION` quando a mesma entrega puder ser acionada por mais de um NPC.

**Teste:** Bag cheia, Bag com espaço, F5/reentrada, salvar/reabrir, múltiplas interações.

## Passo 10 — Criar treinador que detecta o jogador

1. Adicionar o treinador real em `PBS/trainers.txt` com ID/variante disponível no projeto.
2. Nomear evento com a convenção **`Trainer(3)`** (alcance 3 como exemplo, extraído do mapa real quando possível).
3. Trigger: **Event Touch**.
4. Página 1: introdução, detectar/aproximar, iniciar batalha com `TrainerBattle.start(...)`; somente na vitória ligar `Self Switch A`.
5. Página 2 (A ON): diálogo pós-derrota.
6. Testar visão em linha reta, obstáculos, abordagem com o jogador parado, derrota, retorno e reload.
7. Se seu projeto usar o compilador de eventos por comentários, evitar personalizar a mesma página que será **reescrita** pelo compilador; escolher um dos fluxos.

No Essentials v21.x, o padrão documentado de batalha é `TrainerBattle.start(:CAMPER, "Dave")`; adaptar o tipo, nome e versão ao `trainers.txt` real. A lógica regional de 4 Pokémon no Master e outras variações **não deve ser hard-coded em cada evento**: o evento pede ao gerador de times o preset correto.

## Passo 11 — Criar cena de Oak em Pallet

1. Criar **duas** regiões/tile triggers na saída norte, equivalentes às entradas esquerda/direita do original.
2. Ambas só são válidas antes da escolha do inicial.
3. No disparo, travar controle, tocar música/SE, mostrar Oak, caminhar até o personagem.
4. Levar os dois ao laboratório, setar etapa `KANTO_STORY_OAK=1`, e transferir o jogador.
5. Na lab, permitir escolher exatamente um inicial; batalha rival depende dessa escolha.
6. Ao sair/reentrar, Oak **não** deve capturar novamente o jogador.

Importante: o FireRed possui lógica separada para posicionamento à esquerda e à direita. Não substituir por um único script que falha se o jogador entra pelo segundo tile.

## Passo 12 — Criar eventos de cena e bloqueios

- `Player Touch`/Auto-run executa *uma vez*.
- Primeiro conferir pré-condições.
- Alterar variável/switch **antes** de finalizar transferências que mudam de mapa.
- Em sucesso, atualizar tile/NPC correspondente, som e colisão.
- Quando o jogador não satisfizer a condição, mostrar mensagem adequada e sair sem alterar progresso.
- Ao voltar ao mapa, sincronizar estado do NPC/portão sem criar duplicata.

Exemplos: guardas da passagem de Saffron, entrada do ginásio de Viridian, Ribbon/portão da Liga, entrada Cerulean Cave.

## Passo 13 — Criar puzzles de vários mapas

| Puzzle | Estrutura mínima no RMXP |
|---|---|
| Latas de Lt. Surge | Guardar primeira e segunda lata; resetar se erro; abrir barreira |
| Rocket Hideout spinning tiles | Event Touch direcional, movimento forçado com duração, sem loop infinito |
| Silph Co. teleports | Pares de `Transfer Player`; tabela bidirecional e caminho de saída |
| Safari Zone | Passos/bolas e retorno forçado no fim; impedir salvar em estado inconsistente |
| Pokémon Mansion | Botão da estátua alterna portas e colisão; persistência conforme original |
| Seafoam | Pedras em andares conectados; marcar duas quedas; desativar correnteza |
| Victory Road | Boulder em pressão aciona barreira; revertê-la com mudança de sala conforme regra |
| Icefall Cave | Tiles quebráveis/escorregadios e retorno seguro |
| Dotted Hole | Ordem de quedas/entrada condicional, cena do roubo |

## Passo 14 — Configurar encontros e equipes

1. Mapear espécies do FireRed a IDs simbólicos do Essentials (não assumir slots GBA).
2. Configurar `PBS/encounters.txt` por **MapID do Essentials**, método de encontro, níveis e pesos corretos.
3. Editar/compilar `PBS/trainers.txt` e demais PBS, conforme organização da base Decades.
4. Submeter ao sistema de balanceamento regional Blue (dificuldades, 90%/Master conforme decisões vigentes, escalas e permissões especiais) **sem apagar o time original de referência**.
5. Registrar diferenças intencionais do seu fangame separadas dos dados de FireRed.

**Encontros aleatórios não são 1 `object_event` por Pokémon selvagem.** O catálogo de eventos de mapa, por si só, não revela todas as tabelas de habitat.

## Passo 15 — Compile e rode no Game.exe da cópia piloto

- Para Pokémon Essentials v21.1, usar o fluxo de compilação PBS do próprio Essentials (modo Debug / `Compile data` no jogo, conforme instalação).
- Editar eventos e salvar o projeto no RPG Maker XP.
- Executar testes no Game.exe de uma **cópia isolada**, com perfil de save de teste.
- Rodar novamente após mudança de PBS/Plugins e fechar/reabrir quando houver cache de editor/compilador.
- Evitar tocar diretamente em arquivos internos RXDATA com scripts caseiros sem parser/testes; um mapa corrupto pode inviabilizar o jogo.

## Passo 16 — Integrar gradualmente

1. Só promover o lote quando caminhos e portas funcionarem nos dois sentidos.
2. Executar roteiros de vitória, derrota, reload e ida/volta de região.
3. Comparar lista de eventos extraída com eventos presentes no mapa do RMXP.
4. Documentar o que é obrigatório, opcional, de evento especial e não suportado.
5. Criar changelog e opção de rollback antes de integrar na campanha principal.

---

# 9. Exemplos práticos para eventos RMXP

> Os blocos abaixo são **roteiros/pseudoeventos**, não código assembly, nem arquivos RXDATA importáveis. Substitua IDs por valores existentes no projeto. As chamadas Ruby de batalha seguem os padrões documentados do Essentials, mas devem ser testadas na versão modificada do Decades antes da aplicação.

## 9.1 Exemplo — treinador padrão

```text
Event Name: Trainer(3) KANTO_ROUTE3_BUG_CATCHER_01
Trigger: Event Touch
Priority: Same as Characters
Página 1 (nenhuma condição):
  Script: pbTrainerIntro(:BUGCATCHER)
  Script: pbNoticePlayer(get_self)
  Show Text: "Vamos batalhar!"
  Conditional Branch / Script:
    TrainerBattle.start(:BUGCATCHER, "Nome cadastrado", 0)
      Control Self Switch A = ON
  Script: pbTrainerEnd
Página 2 (Self Switch A ON):
  Show Text: "Você venceu."
```

Verifique que o nome e a versão apontam a uma entrada existente em `trainers.txt`; `pbTrainerEnd` deve encerrar o lock mesmo nos casos de resultado inesperado. Se preferir eventos gerados por comentários, siga a sintaxe do compilador da instalação, sem editar um evento que ele sobrescreverá.

## 9.2 Exemplo — Snorlax da Rota 12 (com resultados separados)

```text
NPC Snorlax visível se KANTO_SNORLAX_R12_RESOLVED = false
Ao interagir:
  se não possui Poke Flute:
    mostrar "Parece que está dormindo."
    encerrar
  se possui Poke Flute:
    perguntar se deseja usar
    se não -> encerrar
    tocar música/animação
    iniciar encontro estático do Snorlax
    registrar resultado conforme API da sua batalha
    se capturado/derrotado: marcar resolvido e remover NPC
    se fugiu/perdeu: aplicar regra FireRed definida no script
  não marcar o NPC como removido *antes* de processar o resultado
```

No original, `Route12/scripts.inc` usa, entre outras, `FLAG_GOT_POKE_FLUTE`, `FLAG_WOKE_UP_ROUTE_12_SNORLAX` e `FLAG_HIDE_ROUTE_12_SNORLAX`. Rota 16 tem sua própria lógica e flags de exibição.

## 9.3 Exemplo — Pokémon lendário no campo

```text
Evento: ZAPDOS_POWER_PLANT
Trigger: Action Button
Página ativa se não KANTO_ZAPDOS_RESOLVED
  exibir sprite
  iniciar WildBattle.start(:ZAPDOS, nível_correspondente)
  após batalha, checar retorno de captura/derrota/fuga
  aplicar as flags de batalha e remoção da decompilação
Página inativa se KANTO_ZAPDOS_RESOLVED
  sem sprite e sem colisão
```

Checar as diferenças entre **enfrentou**, **capturou**, **derrotou** e **fugiu**. `PowerPlant/scripts.inc` contém **dois Electrode estáticos e Zapdos**, com flags separadas.

## 9.4 Exemplo — evento `Player Touch` com requisito

```text
Evento: KANTO_VICTORY_ROAD_GATE
Trigger: Player Touch
Se possui as 8 insígnias de Kanto:
  abrir portão/tile, permitir passagem
Senão:
  mostrar diálogo da insígnia faltante
  impedir avanço, sem teleporte
```

Verificar os oito registros regionais individualmente; não usar somente contagem de insígnias de todos os mundos do fangame.

## 9.5 Exemplo — movimento de Oak com transição

```text
Evento oculto saída Pallet esquerda ou direita
Condição: KANTO_STORY_OAK == 0
Trigger: Player Touch
Set Move Route jogador: parar/virar
Set Move Route Oak: entrar pelo lado correto
Show Text + SE
Set Move Route Oak/Jogador: caminhar até laboratório
Set Switch/Variable: KANTO_STORY_OAK = 1
Transfer Player: laboratório, coordenada definida
No laboratório, próximo evento dispara pela etapa 1
```

Evitar `Autorun` sem desligamento; evitar Oak aparecer atravessando o jogador, e evitar corridas simultâneas de dois eventos caso dois tiles de trigger sejam válidos.

## 9.6 Exemplo — item oculto com controle

```text
Event Name: hiddenitem KANTO_R2_HIDDEN_ITEM_01
Trigger: Action Button
Página 1: sem sprite, condição item ainda não encontrado
  If bag has space:
    dar item
    Self Switch A = ON
  Else:
    informar Bag cheia
Página 2 (A ON): vazia
```

Checar a convenção `hiddenitem` do seu Essentials para permitir que Itemfinder detecte o evento, sem assumir que uma flag do FireRed equivale automaticamente a uma Self Switch.

## 9.7 Exemplo — paredes e tiles dinâmicos

```text
EVENTO_BUTTON_SILPH:
  validar Card Key / flag necessária
  alterar o estado lógico da porta
  mudar a imagem/tile e a colisão do bloqueio
  atualizar o mapa sem resetar a cena
EVENTO_PORTA_SILPH:
  página fechada (bloqueia passagem)
  página aberta (não bloqueia passagem)
```

Um sprite de porta invisível que ainda possui colisão é um bug; uma porta visualmente fechada mas atravessável também.

---

# 10. Adaptação ao seu projeto: Blue Dessastre Paradoxal

Documentação verificada no repositório:

- `README.md`: Essentials v21.1/RPG Maker XP, base Pokémon Decades separada, Blue Studio e estrutura PBS.
- `docs/PROXIMOS_PASSOS.md`: progresso da campanha Kanto e prioridades de validação.
- `docs/KANTO_ETAPAS.md` + `docs/KANTO_FASE_07.md` + `docs/KANTO_FASE_08.md`: divisão em 16 etapas e mapa piloto.
- `docs/KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md`: registro de testes manuais.
- `docs/PLANO_REGIOES_DESSASTRE_V2.md`: fonte de verdade para circuito, restrições, balanceamento e pós-jogo.
- `scripts/battle_polish/Regions.rb` e `RegionalPolicy.rb`: sistemas regionais a integrar, sem sobrescrever.

**Estado do projeto documentado em 12/11/2026:** implementação **08/16 (50%)**; conclusão validada **01/16 (6,25%)**. O piloto declara 40 mapas até Vermilion/S.S. Anne, mas ainda há pendências de teste real de caminhada, portas internas e batalha. Esses números descrevem o documento consultado, **não comprovam que todo o conteúdo dos 40 mapas já foi aceito**.

## 10.1 O que corrigir antes de importar novos eventos

1. **Portas/interiores:** o projeto relata falta de entradas funcionais em casas, Centro Pokémon, Mart e ginásios. Fechar a malha de warps é requisito anterior a mais cutscenes.
2. **Treinadores:** verificar raio de detecção, colisão, aproximação e bloqueio de passagem até a luta exigida.
3. **Insígnias:** mostrar a tela local com oito insígnias e tela geral sem misturar regiões.
4. **Salvar/carregar:** coordenada correta, estado de evento, equipe, item, trainer derrotado, puzzle e retorno.
5. **Testar no .exe real:** o fato de um teste automatizado carregar mapa ou simular vitória não prova que a caminhada e a batalha funcionam pela interface.

## 10.2 Contratos que não podem ser quebrados

- Decades é a campanha principal; Kanto é introduzido no circuito conforme regras existentes.
- Permitir **Testar Kanto** na instância já montada do projeto, sem destruir save Decades.
- Ao viajar para uma região, especiais bloqueados devem ser depositados em Box e impedidos de entrar na party **até obter oito insígnias locais**, com tratamento para falta de vagas.
- HMs sempre dependem de regra/insígnia da região atual.
- Líderes e Elite Four usam as equipes/regras específicas de dificuldade do Blue; o time FireRed original serve de referência de origem, não substitui o balanceamento programado.
- Após zerar as ligas correspondentes, aplicar pós-jogo de times fortalecidos conforme `PLANO_REGIOES_DESSASTRE_V2.md`.
- O NPC de viagem pós-Liga deve apresentar somente destinos efetivamente instalados/liberados; permitir cancelar.
- Repetir a Liga ou concluir uma quest novamente não pode duplicar conquista/recompensa.

## 10.3 Plano de importação incremental no Kanto atual

1. **Lote A — Pallet/Rota 1/Viridian/Rota 2:** todos os warps internos e externos; Oak; encomenda; Potion Rota 1; NPCs, placas e itens.
2. **Lote B — Floresta/Pewter/Rota 3/Mt. Moon:** treinadores realistas, Brock, fósseis, escadas e saídas.
3. **Lote C — Cerulean/Rotas 4,24,25:** rival, Misty, Bill, Ticket, casa Rocket, cave guard.
4. **Lote D — Rotas 5,6,11/Vermilion/S.S. Anne:** guardas/Underground Path, navio, rival, Cut, Lt. Surge.
5. **Lote E — Celadon/Lavender/Saffron:** Rocket Hideout, Silph Scope, Tower, Poké Flute, Silph Co., Sabrina, Erika.
6. **Lote F — Fuchsia/rotas intermediárias:** Snorlax, Cycling Road, Safari, Gold Teeth, Surf/Strength, Koga.
7. **Lote G — Cinnabar/Viridian final:** Seafoam, Mansion, Blaine, primeira Sevii, Giovanni, oito insígnias.
8. **Lote H — Victory Road/Liga/Pós-jogo:** gatechecks, Elite Four, Hall of Fame, National Dex, Sevii 4–7, Cerulean Cave.

**Não marcar cada lote como concluído** apenas porque os arquivos foram gerados. Fechar cada bloco com evidência de caminhada, batalha, flags, recompensas, save/reload e retorno.

---

# 11. Testes e critérios de aceite

## 11.1 Matriz mínima por evento

| Caso | Ação | Resultado exigido |
|---|---|---|
| Inédito | Acionar com estado inicial | Executa exatamente uma vez |
| Repetir | Falar/interagir novamente | Diálogo correto, sem duplicar item ou batalha |
| Reentrar | Sair e voltar ao mapa | Estado lógico e visual preservados |
| Save/reload | Salvar no mapa e carregar | Mesmo estado de NPC/quest/posição |
| Derrota | Perder batalha | Não marcar vitória; respawn correto |
| Fugir | Fugir de selvagem estático | Resposta específica do original, não regra inventada |
| Bag cheia | Receber item | Não consome a oportunidade indevidamente |
| Party cheia | Receber Pokémon | Box/erro tratado sem perda |
| Direção alternativa | Entrar no trigger por outro lado | Cutscene funciona sem atravessar parede |
| Choque com NPC | NPC/treinador bloqueia corredor | Não atravessa nem prende o jogador |
| Dificuldades | Trocar modo de dificuldade | Time correto; evento de história igual |
| Região diferente | Usar HM/insígnia de outra região | Não desbloqueia indevidamente |
| Regresso | Viajar Kanto ↔ Decades | Save único preservado |
| Android | Rodar com JoiPlay após Windows | Sem controles bloqueados, crashes ou tiles corrompidos |

## 11.2 Checklist de caminhos críticos

- [ ] Pallet: dois triggers norte levam Oak ao laboratório; não repetem após inicial.
- [ ] Casa jogador, laboratório, casa rival: cada entrada/saída tem destino e retorno real.
- [ ] Rota 1: Potion uma vez e placas funcionam.
- [ ] Viridian: Parcel, Mart, Centro, Gym bloqueado/aberto no estágio correto.
- [ ] Route 2/Forest/Pewter: portarias, treinadores com visão e Brock.
- [ ] Mt. Moon: andares e escolha de um único fóssil.
- [ ] Cerulean: rival norte, Misty, Bill/Ticket, Rocket, guard da Cave.
- [ ] S.S. Anne: bilhete, rival, capitão, HM e saída de navio.
- [ ] Vermilion Gym: puzzle das latas e Surge.
- [ ] Rocket Hideout: Lift Key, barreiras e Giovanni.
- [ ] Tower: Silph Scope, Marowak, Mr. Fuji, Poké Flute.
- [ ] Rotas 12 e 16: Snorlax independentes; estados de fuga/derrota.
- [ ] Saffron: guardas/Chá, Silph Co., portais, Giovanni, Sabrina.
- [ ] Safari: contador de sessão, Gold Teeth, Surf.
- [ ] Fuchsia: Koga, Warden/Strength.
- [ ] Seafoam: boulders, correnteza, Articuno.
- [ ] Cinnabar: Mansion, Secret Key, Blaine e Bill.
- [ ] Viridian: Giovanni e Earth Badge.
- [ ] Rota 23: oito checagens locais; Victory Road sem softlock.
- [ ] Liga: salas em ordem, batalhas reais, Hall of Fame salvo.
- [ ] Pós-Liga: National Dex e Celio com condições reais.
- [ ] Sevii: Ruby, Icefall, Dotted Hole/Sapphire roubada, Warehouse, Sapphire entregue.
- [ ] Cerulean Cave: guarda desaparece apenas no pós-jogo correto.
- [ ] Event islands: não desbloquear Birth/Navel Rock sem condição explícita.

## 11.3 Problemas comuns e correções

| Falha | Causa provável | Correção |
|---|---|---|
| Porta leva ao mapa errado | `dest_warp_id` tratado como `MapID` | Resolver WarpID → coordenada do mapa de destino |
| NPC atravessa paredes | Move Route com `Through` ligado | Configurar colisão e reset ao terminar cena |
| Treinador não enxerga | Nome errado, trigger incorreto ou raycast/visão bloqueada | `Trainer(n)` + `Event Touch`, conferir tiles |
| Treinador reaparece | Self Switch/flag não persistiu ou mapa mudou ID | Verificar save e remapeamento |
| Item duplica | Flag ligada antes/depois na ordem errada | Verificar `Bag` e marcar coletado após sucesso |
| Evento fica infinito | `Autorun` sem mudança de página | Acionar Self Switch/variável e `Exit Event Processing` |
| Porta some mas ainda bloqueia | Sprite alterado sem colisão | Sincronizar lógica e passabilidade |
| Puzzle trava após salvar | Variáveis temporárias sem reconstrução | Salvar estado necessário ou reset seguro por sala |
| HM funciona com insígnia errada | Usou total global em vez de Kanto | Política regional no ponto único de autorização |
| Save Decades quebra | IDs globais colidiram | Namespace, migração e isolamento do piloto |
| Batalha não abre no .exe | PBS não compilado / trainer inexistente | Validar no debug/compile e conferir IDs simbólicos |
| Perfil Android quebra | Inputs/tiles/plugins incompatíveis | Primeiro Windows, depois Android com logs |

## 11.4 Definição objetiva de "concluído"

Um evento está **implementado** quando existe no RMXP e reproduz o comportamento principal. Está **validado** quando passou pelo menos: ativação inicial, repetição, colisão, salvar/reabrir, vitória/derrota quando aplicável, e compatibilidade com outros mapas/regiões. Estas duas métricas devem ser **duas barras separadas**.

---

# 12. Extração automatizada de **todos os registros explícitos** de mapa

## 12.1 Por que usar o script auxiliar

Apenas resumir Kanto em uma tabela deixaria escapar inúmeros NPCs, warps, placas e itens ocultos. O programa anexo **itera os 425 mapas do `map_groups.json` e lê o conteúdo atual de cada `map.json`**. Para cada mapa, cria linhas de:

- `object_events` — todos os NPCs/objetos explícitos;
- `warp_events` — todas as entradas/saídas definidas;
- `coord_events` — todos os gatilhos de coordenada;
- `bg_events` — todas as placas/itens/pontos de investigação;
- `connections` — todas as conexões entre áreas;
- rótulos encontrados em `scripts.inc`, flags, variáveis e `map_script`s.

Isso produz **o inventário real com quantidade e posição** de acordo com o commit da decompilação obtido pelo usuário, em vez de números estimados.

## 12.2 Limites do levantamento automático

1. O programa não resolve automaticamente todos os comandos internos de scripts (`goto`, `call`, `special`, etc.).
2. Não atribui time/nível ao treinador sem analisar também o banco de treinadores.
3. Não converte encontros de grama/Surf/pesca nem seu peso para PBS.
4. Não gera `MapXXX.rxdata` e não modifica o jogo.
5. Não determina legalidade de usar gráficos/áudio de terceiros.
6. Áreas de protótipo e evento serão enumeradas mesmo quando indisponíveis na história normal.

Para auditoria semântica completa, cada evento extraído deve receber campos adicionais de **pré-condições, resultado, pós-condições e teste**.

## 12.3 Estrutura do pacote entregue

```text
ESTUDO_EVENTOS_MAPA_POKEMON_FIRERED_RPG_MAKER_XP.md
extrair_eventos_firered.py
```

O pacote acompanha o guia em um ZIP opcional. O Markdown principal é legível sem executar o script.

---

# 13. Plano de trabalho e percentuais

Este roteiro é um **plano de auditoria e implementação de eventos**; não substitui as 16 fases existentes do projeto nem modifica suas contagens atuais.

| Fase de auditoria | Trabalho | Critério de fechamento |
|---:|---|---|
| 1/12 | Exportar inventário dos 425 mapas | CSV/MD/JSON gerados sem ausências |
| 2/12 | Mapear IDs de Kanto ↔ RMXP | Todas as correspondências sem colisões |
| 3/12 | Conferir warps/conexões do piloto | Entradas e saídas funcionais |
| 4/12 | Conferir trainers/diálogos/itens | Cada evento com resultado correto |
| 5/12 | Criar flags e migrar save | Save/reload sem regressão Decades |
| 6/12 | Recriar cutscenes/marcos de Pallet a Vermilion | Fases piloto jogáveis, sem softlock |
| 7/12 | Recriar Celadon/Lavender/Saffron | Giovanni, Tower, Silph, três ginásios |
| 8/12 | Recriar Fuchsia/caminhos marítimos | Safari, HM, Snorlax, Surf |
| 9/12 | Recriar Cinnabar/Viridian/Indigo | 8 insígnias e Hall of Fame |
| 10/12 | Recriar Sevii e pós-jogo | Ruby/Sapphire, ligações e Cave |
| 11/12 | Integrar política regional/Blue Studio | Bloqueios/portal/regras respeitados |
| 12/12 | Testar todos os mapas/eventos e rollback | Evidência de runtime real + checklist completo |

**Barras recomendadas na planilha de progresso:**

- **Construção**: número de eventos cujo conteúdo foi implementado / número de eventos exigidos no escopo.
- **Validação**: número de eventos que passaram critérios de aceite / número de eventos exigidos no escopo.

Não calcular percentual sem contar os eventos reais de cada lote e seus testes. Se o escopo excluir salas 2F de troca/Union Room ou eventos especiais desativados, registrar explicitamente essa exclusão.

---

# 14. Referências e links para auditoria
### Fonte primária (decompilação)

- Repositório pret: https://github.com/pret/pokefirered
- Índice de 425 mapas: https://github.com/pret/pokefirered/blob/master/data/maps/map_groups.json
- Estrutura de eventos: https://github.com/pret/pokefirered/blob/master/asm/macros/map.inc
- Tipos de scripts: https://github.com/pret/pokefirered/blob/master/include/constants/map_scripts.h
- Tipos de background events: https://github.com/pret/pokefirered/blob/master/include/constants/event_bg.h
- Pallet JSON: https://github.com/pret/pokefirered/blob/master/data/maps/PalletTown/map.json
- Cena Oak: https://github.com/pret/pokefirered/blob/master/data/maps/PalletTown/scripts.inc
- Laboratório de Oak: https://github.com/pret/pokefirered/blob/master/data/maps/PalletTown_ProfessorOaksLab/scripts.inc
- Rota 1: https://github.com/pret/pokefirered/blob/master/data/maps/Route1/scripts.inc
- Snorlax Rota 12: https://github.com/pret/pokefirered/blob/master/data/maps/Route12/scripts.inc
- Pokémon Tower 6F: https://github.com/pret/pokefirered/blob/master/data/maps/PokemonTower_6F/scripts.inc
- Rocket Hideout B4F: https://github.com/pret/pokefirered/blob/master/data/maps/RocketHideout_B4F/scripts.inc
- Silph Co. 11F: https://github.com/pret/pokefirered/blob/master/data/maps/SilphCo_11F/scripts.inc
- Seafoam B4F: https://github.com/pret/pokefirered/blob/master/data/maps/SeafoamIslands_B4F/scripts.inc
- Victory Road 1F: https://github.com/pret/pokefirered/blob/master/data/maps/VictoryRoad_1F/scripts.inc
- Dotted Hole Sapphire: https://github.com/pret/pokefirered/blob/master/data/maps/SixIsland_DottedHole_SapphireRoom/scripts.inc
- Celio One Island: https://github.com/pret/pokefirered/blob/master/data/maps/OneIsland_PokemonCenter_1F/scripts.inc

### Guias de implementação e mecânicas

- Porymap — editar eventos na decompilação: https://huderlem.github.io/porymap/manual/editing-map-events.html
- Pokémon Essentials — Events: https://essentialsdocs.fandom.com/wiki/Events
- Pokémon Essentials — Trainers: https://essentialsdocs.fandom.com/wiki/Trainers
- Pokémon Essentials — Event encounters: https://essentialsdocs.fandom.com/wiki/Event_encounters
- Pokémon Essentials — Wild Encounters: https://pokemon-essentials.fandom.com/wiki/Wild_Encounters
- Tabela HMs (Pokémon Database): https://pokemondb.net/firered-leafgreen/hms
- Insígnias/HMs: https://bulbapedia.bulbagarden.net/wiki/Appendix:FireRed_and_LeafGreen_walkthrough/Section_5
- Revisão geral FireRed Kanto/Sevii: https://pokedexgenerator.com/walkthroughs/pokemon-firered-leafgreen

### Referências do seu projeto

- Blue Dessastre: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal
- Próximos passos: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/PROXIMOS_PASSOS.md
- 16 etapas: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/KANTO_ETAPAS.md
- Plano de regiões: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/PLANO_REGIOES_DESSASTRE_V2.md
- Feedback manual: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md

---

## Conclusão

A reprodução completa dos eventos de FireRed em um projeto RPG Maker exige **duas entregas diferentes**: (1) o inventário literal de registros dos 425 mapas, obtido da fonte decompilada, e (2) a implementação semântica de cenas, batalhas, estados e desafios no Essentials. O script auxiliar resolve a primeira como base de auditoria; o guia estabelece o passo a passo da segunda.

Para o **Blue: Dessastre Paradoxal**, a implementação deve começar pelas **portas, treinadores e estado persistente do piloto já existente**, antes de adicionar grandes blocos de história. Isso evita crescer a quantidade de eventos em um mapa que ainda não permite ao jogador entrar nos edifícios ou concluir batalhas na campanha real.