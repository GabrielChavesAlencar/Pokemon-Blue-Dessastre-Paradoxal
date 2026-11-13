# Hoenn — escolha fundamentada das fontes de mapas e músicas

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Pesquisa e conferência:** 13/11/2026  
**Engine de destino:** RPG Maker XP + Pokémon Essentials v21.1, com os sistemas do Decades/Blue preservados  
**Status:** estudo comparativo e plano inicial. **Nenhum mapa, evento ou áudio de Hoenn foi importado ou testado por este documento.**

> **Resposta curta:** entre os quatro fangames de Hoenn da lista do projeto, **Pokémon Eternal Emerald** é a melhor referência para mapas, ambiente, campanha e escolha musical. **Para conseguir mapas-fonte editáveis**, vale investigar primeiro **The Pokémon World Project** (fora da lista), que já disponibiliza um projeto Hoenn em Essentials v21.1. **Para determinar quais músicas devem tocar**, usar a trilha e as situações originais de **Pokémon Emerald**, com Ruby/Sapphire e ORAS como complementos. Não transplantar músicas nem mapas de terceiros sem confirmar direitos de uso e as dependências técnicas.

## 1. Documentos existentes analisados

- [Estudo de todas as regiões](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md): para Hoenn, cita **Eternal Emerald, Fire Ash, Starwish e Stygian Snakewood**; indica **Emerald** como geografia-base e adverte que a lista não é prova de editabilidade nem de permissão de uso.
- [Plano multirregional v2](PLANO_REGIOES_DESSASTRE_V2.md): exige **Emerald + Ruby + Sapphire**, com conteúdo ORAS opcional; a Liga de **Hoenn libera Johto e Sinnoh**; a região pode ser escolhida como origem quando instalada e validada.
- [Escolha de fontes de Johto](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md): estabelece o padrão de comparar **jogo de referência**, **pacote técnico de mapas** e **catálogo musical** separadamente, com duas barras de aceite.
- [Circuito regional](CIRCUITO_REGIONAL.md) e [implementação definitiva de Johto](JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md): importação isolada, remapeamento, adaptação de eventos ao próprio jogo, backups, migração e evidências de teste.
- [Editor de músicas](EDITOR_MUSICAS.md), [plano musical de Kanto](KANTO_PLANO_APLICAR_MUSICAS.md) e [mapeamento musical de Kanto](KANTO_MUSICAS_MAPEAMENTO.md): usar o sistema BlueMusic, distinguir BGM de ME, associar músicas a eventos reais e auditar prioridade, loop, fade e fallback.
- [README principal](../README.md): o repositório mantém o editor/scripts; a instalação-base do Decades fica localmente em **game/** e não deve ser sobrescrita.

**Regra arquitetural:** Hoenn fornece mundo, NPCs, encontros, treinadores, eventos e música regional. O **combate, IA, escalonamento, saves, PC, Pokédex, BlueMusic e seleção regional** continuam sendo exclusivamente os do Blue/Decades. Não instalar o motor de batalhas ou os plugins completos de um fangame doador.

## 2. Comparação dos quatro fangames que já constam da lista

| Candidato | Evidência pública consultada | Adequação aos mapas de Emerald | Música e problemas | Veredito |
|---|---|---|---|---|
| **Pokémon Eternal Emerald** | Autor declara remake de Emerald em **Essentials v21.1**, campanha e pós-jogo completos; inclui Battle Frontier, gráficos atualizados e música remasterizada. Página marcada como concluída; download principal citado como v2.4.2. | **Muito alta**: mesmo ramo de engine e foco em Hoenn/Emerald, com acréscimos ORAS. | Possui músicas remasterizadas, **mas isso não concede licença**. O autor responde expressamente que a reutilização dos mapas depende do mapa e de pedir autorização. | **1º — melhor fangame da lista para referência; importação depende de autorização e auditoria do pacote.** |
| **Pokémon Fire Ash** | Projeto de RPG Maker XP/Essentials **v19.1**, com diversas regiões, incluindo Hoenn, seguindo a jornada de Ash no anime. | Média: cobre Hoenn, porém mapas, ordem e eventos respondem à narrativa do anime. | Versão de Essentials diferente; trilha e mapas não têm permissão de reaproveitamento confirmada. | **2º — referência secundária de abrangência e viagem multirregional, não fonte principal.** |
| **Pokémon Starwish** | Demo de história ambientada em Hoenn **seis anos depois de Emerald**, com cenário alterado e aproximadamente **2–3 horas**, até a primeira insígnia. | Baixa para reconstrução canônica completa; boa referência criativa de uma Hoenn futura. | Projeto incompleto para fins de campanha Emerald integral; áudios com dublagem não ajudam como catálogo-base. | **3º — referência narrativa e de remodelação de locais, não mapa-base.** |
| **Stygian Snakewood** | Remake alternativo de Snakewood em **Essentials v20.1**, com Hoenn devastada por uma epidemia zumbi; material distribuído como demo/versão em desenvolvimento. | Baixa: releitura deliberadamente não canônica, com alterações profundas do mundo. | Diferenças de engine, terreno, eventos e identidade musical; sem autorização verificada. | **4º — não usar como base geográfica da Hoenn clássica.** |

**Certeza:** os recursos acima foram conferidos em páginas dos próprios projetos ou publicações de seus autores. **Não foram baixados e inspecionados seus arquivos executáveis ou pastas de mapas neste estudo**; a presença real de cada interior, .rxdata e faixa musical dentro de cada download segue não auditada.

Fontes diretas:

- Eternal Emerald: https://eeveeexpo.com/threads/4871/
- Fire Ash: https://www.eeveeexpo.com/threads/9489/
- Starwish: https://zamius.itch.io/pokmon-starwish-demo
- Stygian Snakewood: https://www.pokecommunity.com/threads/stygian-snakewood-a-pok%C3%A9mon-snakewood-remake.527580/

### 2.1. Por que Eternal Emerald vence?

1. **Compatibilidade inicial:** usa Essentials v21.1, versão documentada na base atual do Blue; isso reduz, mas **não elimina**, diferenças de plugins, estrutura e scripts.
2. **Escopo:** o autor indica jornada principal e pós-jogo concluídos, mais adequados que uma demo com uma insígnia ou uma Hoenn alternativa.
3. **Geografia:** é remake direto de Emerald, que já é a campanha canônica escolhida pelo Plano v2.
4. **Recursos adicionais:** Battle Frontier e elementos de ORAS ajudam a definir prioridades futuras; não devem substituir o enredo Emerald sem decisão consciente.
5. **Áudio:** o repertório remasterizado pode servir de **inspiração de arranjo e de associação por cenário**, mas não deve ser copiado para o Git público sem permissão dos titulares.

**Bloqueador incontornável:** o autor de Eternal Emerald informa em sua própria FAQ que é necessário contatá-lo para saber se um determinado mapa pode ser usado no fangame de outra pessoa. Portanto **Eternal Emerald não é tratado como pack livre para cópia**.

## 3. Melhor fonte TÉCNICA de mapas editáveis — fora da lista

**Prioridade para auditoria:** [The Pokémon World Project — repositório de SocomSeal](https://github.com/SocomSeal/The-PMon-World-Project) e [página do recurso na Eevee Expo](https://eeveeexpo.com/resources/1877/).

Por que merece precedência para importação real de mapas:

- Declara **Essentials v21.1** e se apresenta como **recurso para outros criadores**, não apenas jogo distribuído pronto.
- O repositório público possui uma pasta independente **The Pokémon World Project - Hoenn/**, com **Data/MapXXX.rxdata**, **MapInfos.rxdata**, **Tilesets.rxdata**, pastas **Graphics/**, **PBS/** e **Audio/**. Isso comprova a existência de **arquivos-fonte estruturados**, não o funcionamento de todos os mapas.
- A atualização de **23/05/2026** anunciou a maioria dos mapas de Hoenn, com exceções de áreas de pós-jogo como instalações da Battle Frontier.
- O **Roadmap.txt**, datado de **13/10/2026**, ainda prevê concluir Hoenn até o fim de 2026, indica trabalho de eventos até Lilycove e aponta pendências de portas, tilesets e correções. Portanto **não marcar Hoenn como 100% pronta**.
- As porcentagens divulgadas em espelhos/versões diferentes da página do recurso divergem; para aceite, confiar no **inventário do commit efetivamente baixado**, não num único percentual promocional.

**Limitações e direitos:** um repositório público pode conter gráficos, música e recursos de múltiplos autores; sua publicidade não equivale a uma licença geral de redistribuição. O projeto pede créditos a diversos criadores. Auditar termos de uso e licenças de **cada classe de recurso** e solicitar autorização quando necessário. **Não copiar Scripts.rxdata, PluginScripts.rxdata, System.rxdata nem o runtime do World Project para cima do Blue**.

**Fontes complementares para locais faltantes:** Lord Lucario 35 publicou mapas/tilesets individuais de Hoenn na Eevee Expo, incluindo [Mt. Pyre interno](https://eeveeexpo.com/resources/1892/) e [Mirage Tower](https://eeveeexpo.com/resources/1893/). São recursos pontuais: não representam um pack completo. Usar somente conforme as condições do autor; não seguir literalmente tutoriais que mandem substituir arquivos inteiros do banco de um projeto já existente.

### 3.1. Estratégia de fontes recomendada

| Camada de Hoenn | Fonte recomendada | Política |
|---|---|---|
| **Geografia e mapa-base editável** | The Pokémon World Project, após verificação de permissões/arquivos | Importar apenas mapas e dependências aprovados por um pipeline próprio |
| **Conferência visual de mapas, interiores e história** | Eternal Emerald + Pokémon Emerald | Comparar e reconstruir o que faltar, sem copiar conteúdo sem autorização |
| **Regras de enredo e NPCs** | Emerald como linha principal; Ruby/Sapphire como versões alternativas | Recriar/adaptar eventos com as APIs do Blue |
| **Delta Episode e outras adições** | ORAS, em módulo opcional de pós-jogo | Não duplicar ginásios nem substituir a cronologia Emerald |
| **Músicas** | Repertório de Emerald/Ruby/Sapphire; ORAS como referência estética secundária | Catálogo por função; arquivos somente com direito de uso confirmado |
| **Batalhas, recompensas e IA** | Exclusivamente Dessastre Paradoxal/Decades | Nenhuma engine de combate estrangeira |

## 4. Qual a melhor fonte para as músicas?

**Escolha-base: repertório de Pokémon Emerald / Ruby / Sapphire.** A trilha de Emerald é a referência temática mais coerente com a história, o mapa, os ginásios, os eventos climáticos, o Surf/Dive e a Battle Frontier. Os arranjos de **Omega Ruby/Alpha Sapphire** podem orientar uma opção estética moderna, mas nunca substituir automaticamente a identidade regional nem as regras de prioridade do Blue.

**Catálogo de identificação de composições (não é fonte de MP3 para redistribuição):**

- [Pokémon Ruby & Sapphire Super Music Collection — tracklist, Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_RS_music)
- [Pokémon Ruby, Sapphire & Emerald — trabalhos musicais, MusicBrainz](https://musicbrainz.org/work/21810e5b-bd97-4b48-a5dd-8bbdc1da7301)
- [Lista de ambientes em que as músicas são utilizadas, Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/List_of_overworld_music_themes)

**Direitos:** os fonogramas e as composições oficiais não ficam livres só por estarem num jogo, no YouTube ou num pacote de fãs. Mesmo remixes podem exigir autorização do arranjador e de quem controla a composição original. **Para publicação, usar trilhas próprias ou faixas com licenças/permissões comprovadamente adequadas.** Arquivos ainda não licenciados permanecem **pendentes**; não versioná-los no GitHub.

### 4.1. Catálogo funcional inicial para o BlueMusic

A tabela define **chaves de destino e função**, não prova que os arquivos ou MapIDs já existem no Blue. Conferir títulos e ocorrências exatas no catálogo do jogo antes de criar a configuração final. Uma mesma composição pode aparecer em **mais de um local**: não inventar uma música diferente para cada cidade.

| Chave planejada | Referência musical | Destino/condição | Tipo |
|---|---|---|---|
| HOENN_LITTLEROOT | Littleroot Town | Cidade inicial | BGM |
| HOENN_BIRCH_LAB | Birch's Laboratory | Laboratório de Birch | BGM |
| HOENN_ROUTE_101 | Route 101 | Rotas correspondentes (101–103, conforme fonte) | BGM |
| HOENN_OLDALE | Oldale Town | Oldale e locais que compartilham o tema | BGM |
| HOENN_PETALBURG | Petalburg City | Petalburg e locais correspondentes | BGM |
| HOENN_ROUTE_104 | Route 104 | Rotas correspondentes, após auditoria | BGM |
| HOENN_PETALBURG_WOODS | Petalburg Woods | Floresta e cavernas que usam o tema | BGM |
| HOENN_RUSTBORO | Rustboro City | Rustboro e cidades com tema compartilhado | BGM |
| HOENN_DEWFORD | Dewford Town | Dewford Town | BGM |
| HOENN_SLATEPORT | Slateport City | Cidade portuária | BGM |
| HOENN_ROUTE_110 | Route 110 | Rotas realmente associadas | BGM |
| HOENN_VERDANTURF | Verdanturf Town | Verdanturf | BGM |
| HOENN_FALLARBOR | Fallarbor Town | Fallarbor | BGM |
| HOENN_FORTREE | Fortree City | Fortree | BGM |
| HOENN_ROUTE_119 | Route 119 | Rotas associadas, clima conforme eventos | BGM |
| HOENN_LILYCOVE | Lilycove City | Lilycove | BGM |
| HOENN_SOOTOPOLIS | Sootopolis City | Cidade e variações do evento climático | BGM |
| HOENN_EVER_GRANDE | Ever Grande City | Cidade antes da Liga | BGM |
| HOENN_SURF | Surf | Só enquanto o movimento de Surf exigir | BGM campo |
| HOENN_DIVE | Diving | Só após mergulho, restaurando música ao subir | BGM campo |
| HOENN_MT_CHIMNEY | Mt. Chimney | Monte e eventos específicos | BGM |
| HOENN_MT_PYRE | Mt. Pyre | Pisos/áreas correspondentes | BGM |
| HOENN_CAVE_OF_ORIGIN | Cave of Origin | Caverna e eventos adequados | BGM |
| HOENN_SKY_PILLAR | Sky Pillar | Torre de Rayquaza | BGM |
| HOENN_VICTORY_ROAD | Victory Road | Caverna antes da Liga | BGM |
| HOENN_FRONTIER | Battle Frontier | Área do pós-jogo, não ginásios comuns | BGM |
| HOENN_WILD | Battle! Wild Pokémon | Encontro selvagem **em Hoenn** | BGM batalha |
| HOENN_TRAINER | Battle! Trainer | Treinador comum de Hoenn | BGM batalha |
| HOENN_RIVAL | Battle! Brendan/May | Somente rival real e combate correspondente | BGM batalha |
| HOENN_GYM | Battle! Gym Leader | Um dos oito líderes de Hoenn | BGM batalha |
| HOENN_AQUA_MAGMA | Battle! Team Aqua/Magma | Membro da equipe identificado | BGM batalha |
| HOENN_AQUA_MAGMA_LEADER | Battle! Team Aqua/Magma Leaders | Archie/Maxie, conforme campanha | BGM batalha |
| HOENN_ELITE_FOUR | Battle! Elite Four | Elite Four regional | BGM batalha |
| HOENN_CHAMPION | Tema da batalha do campeão | Campeão real da versão canônica escolhida | BGM batalha |
| HOENN_ANCIENT | Battle! Super-Ancient Pokémon | Confronto confirmado com lendário pertinente | BGM batalha |
| HOENN_REGIS | Battle! Regirock/Regice/Registeel | Encontros confirmados com Regis | BGM batalha |
| HOENN_BADGE | Obtained a Gym Badge! | **Depois** da conquista confirmada, uma vez | ME |
| HOENN_ITEM | Obtained an Item! | Depois de receber item, se aplicável | ME |
| HOENN_HALL_OF_FAME | Hall of Fame | Entrada no Hall of Fame confirmada | BGM/ME por evento |
| HOENN_FRONTIER_SYMBOL | Obtained a Battle Symbol! | Recompensa real da Frontier | ME |

**Mapeamento compartilhado relevante:** a documentação musical da geração III associa, por exemplo, a composição **Oldale Town** também a **Lavaridge Town**, e **Rustboro City** também a **Mauville City** e **Mossdeep City**. Em vez de inventar áudios exclusivos para essas cidades, declarar destinos diferentes que reutilizam a composição autorizada correspondente.

**Pendências musicais a catalogar antes de implementar:** abertura, bicicleta, centro Pokémon, Poké Mart, créditos, evolução, captura, vitória selvagem/treinador/líder, tempestades/sol extremo, introdução de Rayquaza, Kyogre/Groudon, cavernas específicas, concurso, transporte de barco, derrota, cura e tema do campeão da versão adotada. Não associar por semelhança de nome; verificar cenas reais e catálogo.

### 4.2. Como integrar sem quebrar as músicas atuais

1. Criar **um manifesto regional por chave e por mapa/evento**, contendo origem, licença, SHA-256, duração, categoria BGM/ME, estado, prioridades e arquivo local.
2. Guardar áudios **autorizados** isoladamente por região, por exemplo **game/Audio/BGM/Hoenn/** e **game/Audio/ME/Hoenn/**. Criar eventualmente **assets/music/hoenn/** somente quando houver autorização explícita para a publicação desse arquivo.
3. Reutilizar o **BlueMusic** e o catálogo já existentes; **não modificar os MapXXX.rxdata** só para trocar música quando o sistema puder configurar em memória.
4. Implementar/validar prioridade: **evento narrativo real** > tema regional específico do mapa/batalha > preferência global configurada pelo jogador, respeitando a semântica atual do Blue; evitar que uma playlist global de combate seja quebrada silenciosamente.
5. Provar que Surf, Dive, montaria/bicicleta e climáticas **restauram a música correta** ao terminar, sem looping sobreposto nem reinício a cada tile.
6. Após uma ME de insígnia/item, restaurar BGM ambiente; não tocar a vinheta duas vezes ao recarregar o save.
7. Sem faixa encontrada, usar **fallback seguro**, registrar diagnóstico, não bloquear mapa, diálogo, batalha ou transição.

## 5. Exigências de Hoenn conforme o Plano Regional v2

### Campanha e integração de história

- **Início em Littleroot:** reproduzir a sequência inicial de Emerald (caminhão de mudança/casa, apresentação de Birch e escolha de Treecko, Torchic ou Mudkip), com origem, destino, direção, portas e transferência testados; **não iniciar no exterior por erro de MapID**.
- Oito ginásios de Hoenn: **Roxanne, Brawly, Wattson, Flannery, Norman, Winona, Tate & Liza e Juan** na campanha-base Emerald. Wallace é Campeão na versão-base Emerald; equipes e eventos alternativos de Ruby/Sapphire/ORAS viram variantes verificadas, **não** uma segunda Liga obrigatória.
- Eventos necessários: Devon, Wally, rival, Team Magma/Aqua, Meteor Falls, Mt. Chimney, Weather Institute, Mt. Pyre, bases das equipes, Seafloor Cavern, Sootopolis, Rayquaza/Sky Pillar e Liga. Integrar rotas de água, correntes, Dive/Surf, cachoeiras, clima e passagem subaquática.
- Acrescentar **exclusivos de Ruby e Sapphire** às tabelas pertinentes sem duplicar uma mesma espécie; cada método de encontro deve manter pesos válidos. Conteúdo ORAS, Delta Episode, Mirage Islands e Frontier são fases opcionais ou pós-jogo com inventário próprio.
- **NPC de viagem regional em Littleroot Town**, após os requisitos de viagem do plano; listar destinos desbloqueados, sem inventar acesso a uma região ainda ausente.
- **Liga de Hoenn concluída → libera Johto + Sinnoh**, mesmo que Johto já estivesse aberta. Desbloqueio somente após evento real da Liga persistido; não disparar ao entrar no Hall.
- Cada insígnia inédita de Hoenn contabiliza **uma única esmeralda global** pelo mecanismo já existente no Blue; **não** criar outro cálculo de níveis. A regra Master (11+ esmeraldas, com percentual definido no sistema nativo) continua a mesma.
- **Insígnias/HMs locais**: consultar requisitos da própria Hoenn, sem converter as oito insígnias globais em desbloqueio de campo universal.
- Lendários, míticos, Ultra Beasts e Paradoxos ficam sujeitos à regra **oito conquistas locais da região atual**; ao mudar para Hoenn sem oito insígnias, depósito/retirada na Box deve seguir o módulo regional e impedir perda de Pokémon ou de itens.
- Sites de treinadores, Pokédex, Habitat Dex, guias e mapas regionais devem exibir **Hoenn** e suas conquistas, sem substituir a visão geral de todas as regiões.
- Revanche superforte de líderes/Elite/Campeão somente após o **pós-jogo global** definido no Plano v2, nunca apenas por concluir Hoenn.

### Critério de mundo completo

Inventariar **todas as cidades, rotas, rotas marítimas, ilhas, cavernas, entradas, interiores, casas, lojas, centros, ginásios, elevadores, NPCs, itens visíveis/ocultos, cutscenes, treinadores, encontros e música**. O fato de a fonte ter mapa exterior não prova que há interiores, scripts, Frontier, encontros ou eventos. Marcar lacunas como pendentes, não preenchê-las com dados inventados.

## 6. Pipeline seguro de importação (sem modificar game/ nesta fase)

### Fase 0 — Evidência, autorização e baseline

- Baixar **somente de fontes oficiais** uma cópia identificada por versão/commit, em **.blue-work/hoenn-source/**; registrar SHA-256 e origem. Separar os candidatos, sem mesclar arquivos por nome.
- Fazer inventário de **Data/MapXXX.rxdata, MapInfos.rxdata, Tilesets.rxdata, Graphics, Audio, PBS, eventos e plugins**, distinguindo mapas reais, vazios e alternativos.
- Criar matriz **recurso / autor / licença / permissão / créditos / pode incorporar? / pode publicar?**. Sem autorização, manter recurso como **referência visual e reconstruir conteúdo próprio**.
- Medir a baseline dos testes e MapIDs usados em **Decades + Kanto + Johto**, incluindo piloto, saves, Battle Hub, site e menus. Registrar commit e hashes antes de qualquer futura aplicação.

**Aceite F0:** uma fonte elegível com autorização identificada, lacunas conhecidas e relatório reproduzível. Sem fonte autorizada, fase de importação fica bloqueada.

### Fase 1 — Manifesto e numeração sem colisões

Propor os seguintes artefatos **a criar somente durante a implementação**:

- data/regions/hoenn-source.json — commit, arquivos, licenças, checksums e créditos.
- data/regions/hoenn-map-plan.json — **chave lógica HOENN_* → sourceMapID → destinationMapID** e estado por mapa.
- data/hoenn-music.json — **chave musical → arquivo permitido → cena/mapa/versão → prioridade**.
- docs/HOENN_ETAPAS.md — dois contadores, evidências e bloqueios.
- scripts/regions/pilot_hoenn.py e scripts/regions/install_hoenn.py — piloto e instalador **ainda não existentes**.

Alocar IDs de destino **consultando os já utilizados**, sem presumir sequência vaga nem reutilizar ID existente. Definir também remapeamento de tilesets, switches, variáveis, self-switches, common events e referências internas. Reservar um namespace de flags para Hoenn.

**Aceite F1:** nenhum ID de destino colide com Decades, Kanto ou Johto, e todas as referências são rastreáveis.

### Fase 2 — Primeira vertical jogável: Littleroot até Petalburg

- Construir uma **cópia isolada** em **.blue-work/hoenn-pilot/**, com save/projeto de testes próprios.
- Importar apenas os mapas aprovados: introdução/caminhão, casa do jogador, Littleroot, laboratório de Birch, Route 101, Oldale, Route 102 e Petalburg; adicionar demais interiores necessários após inventário.
- Remapear transferências bidirecionais, entradas, saídas, tilesets, passabilidade, pontos de cura, clima e MapPosition/town_map da Hoenn.
- Implementar início real, entrega do inicial, primeiro rival, NPCs locais, encontros e treinadores usando **scripts/handlers do Blue**, não scripts de batalha do projeto de origem.
- Aplicar **apenas** as músicas cujos destinos foram confirmados, com arquivos autorizados.

**Aceite F2:** nova partida Hoenn → andar e entrar/sair de casas → batalha selvagem/treinador → salvar → reiniciar → carregar → voltar ao hub/saída segura; Decades/Kanto/Johto continuam intactos.

### Fase 3 — Primeiro ginásio e sistema de progressão

- Route 104, Petalburg Woods, Rustboro, Devon, Roxanne e Stone Badge.
- Testar uma conquista única convertida em **uma** unidade da progressão global original; nenhuma duplicação ao revisitar/revanche ou após crash.
- Validar escala dos níveis e perfis do Blue, menus regionais, encontros no site e identidade da trilha.
- **Não habilitar Hoenn como campanha normal** se o piloto apenas demonstrar o primeiro ginásio.

### Fase 4 — Oito ginásios e jornada Emerald

Expandir por núcleos testáveis: Dewford/Brawly → Slateport/Mauville/Wattson → Mt. Chimney/Lavaridge/Flannery → Petalburg/Norman → Fortree/Winona → Mossdeep/Tate & Liza → Sootopolis/Juan. Incluir todas as rotas terrestres e marítimas, casas, cavernas, itens, NPCs, treinadores e eventos obrigatórios na ordem definida pelo inventário; documentar divergências da versão Emerald.

### Fase 5 — Arco lendário, Liga e pós-jogo

Finalizar clima, Surf/Dive/correntes, equipes Magma/Aqua, Seafloor Cavern, Rayquaza, Victory Road, Elite Four, Wallace, Hall of Fame, desbloqueio **Johto + Sinnoh** e NPC de viagem em Littleroot. Depois, avaliar Battle Frontier, regis, ilhas opcionais, eventos e conteúdo ORAS; não declarar pós-jogo completo antes de conferir áreas realmente existentes.

### Fase 6 — Música, regressões e aceite integral

Associar BGM/ME por **mapa e evento efetivamente instalado**; validar reprodução/loop/fade/volume, prioridades de eventos, Surf/Dive, batalha selvagem/treinador/líder, vitórias e fallback. Testar em **Game.exe nativo no Windows**, com saves antigos, e depois em JoiPlay/Android se suportado. Validar regressões de Decades, Kanto, Johto, menus, BlueMusic, Blue Studio, Battle Hub, site e Pokédex.

## 7. Regra obrigatória: não quebrar o que já existe

1. **Sempre aditivo:** não substituir o jogo-mestre, o banco inteiro de outra região, as músicas atuais ou a engine de batalha.
2. **Somente diff auditado:** leitura de Marshal em modo dados, sem executar scripts de origem; prévia/dry-run antes do apply.
3. **Backup e rollback:** gravar atomicamente e reverter falhas, com logs de arquivo, versão e checksum.
4. **Saves antigos intactos:** map IDs imutáveis; migração versionada caso algo realmente precise mudar; testes reais de save/load em Decades/Kanto/Johto/Hoenn.
5. **Feature flag real:** Hoenn deve permanecer **planned/unavailable** até existir fluxo mínimo funcional aprovado; botão experimental, se criado, não é evidência de campanha pronta.
6. **Separar evidências:** CI, auditoria estrutural, teste de jogo nativo e aprovação manual são diferentes. Nunca declarar uma área inteira jogável com base apenas em mapa importado.
7. **Nenhuma música indevida no Git:** preservar a licença de cada composição/gravação e os áudios anteriores.
8. **Uma só engine:** eventos de origem adaptados à API de batalha e scripts regionais já existentes, sem carregar plugins de outro jogo diretamente.
9. **Conservar políticas globais:** nível e IA Blue, total de esmeraldas, oito insígnias locais, Box de especiais, viagem regional, capturas e pós-jogo mundial.

## 8. Checklist de aceite e duas barras de progresso

**Barra A — Núcleos técnicos verificados em CI (0/7 nesta análise):**

- [ ] F0 — inventário, autorização e baseline reproduzíveis
- [ ] F1 — manifestos e IDs seguros
- [ ] F2 — Littleroot → Petalburg no piloto
- [ ] F3 — primeiro ginásio e esmeralda sem duplicidade
- [ ] F4 — oito ginásios, mapas, NPCs e eventos
- [ ] F5 — arco lendário, Liga, viagem e pós-jogo escopado
- [ ] F6 — música completa, testes de regressão e empacotamento

**Barra B — Núcleos integralmente aceitos no jogo real (0/7 nesta análise):**

- [ ] Validação visual/funcional do mapa e passabilidade
- [ ] Introdução, inicial, rival e NPCs realmente funcionais
- [ ] Primeiro ginásio, derrota, vitória e save/reload reais
- [ ] Todos os oito ginásios e travas de HM conferidos
- [ ] Mar, mergulho, clima, cavernas, transporte e ausência de softlocks
- [ ] Liga, créditos, pós-jogo, viagens e saves antigos
- [ ] Música audível correta, estabilidade PC e Android/JoiPlay quando aplicável

**Os números 0/7 são somente desta implementação de Hoenn**, pois este MD não instala mapas, scripts ou música. Não alteram os contadores atuais de Kanto ou Johto.

## 9. Fontes e data de verificação

**Documentação do próprio Blue, branch main:**

- https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md
- https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/PLANO_REGIOES_DESSASTRE_V2.md
- https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md
- https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/EDITOR_MUSICAS.md

**Fontes externas verificadas em 13/11/2026:**

- Eternal Emerald, declaração de Essentials v21.1 e FAQ sobre pedir autorização dos mapas: https://eeveeexpo.com/threads/4871/
- Fire Ash, Essentials v19.1 e regiões: https://www.eeveeexpo.com/threads/9489/
- Starwish, escopo e limites da demo: https://zamius.itch.io/pokmon-starwish-demo
- Stygian Snakewood, Essentials v20.1 e ambientação: https://www.pokecommunity.com/threads/stygian-snakewood-a-pok%C3%A9mon-snakewood-remake.527580/
- The Pokémon World Project, mapa editável e estrutura: https://github.com/SocomSeal/The-PMon-World-Project
- Atualização do projeto sobre Hoenn: https://eeveeexpo.com/resources/1877/updates
- Roadmap (13/10/2026): https://github.com/SocomSeal/The-PMon-World-Project/blob/main/Roadmap.txt
- Catálogo de músicas: https://musicbrainz.org/work/21810e5b-bd97-4b48-a5dd-8bbdc1da7301

## 10. Decisão final e próxima ação

**Entre os quatro jogos citados na documentação, escolher Pokémon Eternal Emerald como a MELHOR REFERÊNCIA PARA HOENN.** Ele corresponde ao objetivo Emerald, está na mesma versão-base de Essentials e apresenta campanha/pós-jogo anunciados como completos. **Não presumir direito de copiar seus mapas ou músicas.**

**Como ponto de partida efetivamente editável, auditar The Pokémon World Project primeiro**, com autorização, inventário de MapXXX.rxdata, interiores, tilesets e eventos; suprir lacunas com mapas próprios ou recursos pontuais de uso permitido. Para a trilha, escolher **o catálogo de Emerald** e implementar áudios originais/autorizados pela camada regional do BlueMusic.

**Próximo comando de trabalho recomendado:** executar somente a **Fase 0 de Hoenn** — verificar o commit e os recursos disponíveis nas fontes, listar mapa por mapa, lacunas, créditos, permissões e possíveis colisões com Decades/Kanto/Johto. Não importar nada para game/ até a auditoria aprovada.
