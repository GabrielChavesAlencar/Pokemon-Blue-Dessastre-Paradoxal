# Jornada, economia e vendedores Blue

## Atualização de balanceamento

- Rare Candy e todas as Exp. Candies saíram do catálogo. Itens de aumento direto de atributos usados manualmente em batalha, como X Attack/Defense/Speed/Special/Accuracy (inclusive variantes 2–6), Dire Hit e Max Mushrooms, também não são vendidos e ficam bloqueados na batalha da campanha. Não se removem itens já guardados no save nem itens equipados normais, como Choice Band.
- TMs usam o golpe, não o número da TM: até 40 de poder = 500; até 60 = 1.500; até 80 = 3.000; até 100 = 4.500; até 120 = 5.500; acima disso = 7.500. Golpes de dano variável recebem 7.500; status comuns custam 2.500, cura/proteção/setup forte/campo relevante custam 5.000. TRs consumíveis custam 70% da faixa, arredondada para centenas. Ember seria 500 e Fire Blast custa 5.500; as TMs efetivamente disponíveis continuam sendo as cadastradas pela base. Não é criada uma TM de Ember se ela não existir.
- A referência pesquisada é a [tabela de itens de Emerald](https://github.com/pret/pokeemerald/blob/master/src/data/items.h): Fire Blast/TM38 custa 5.500, Reflect/TM33 e Flamethrower/TM35 custam 3.000, Sludge Bomb/TM36 custa 1.000. As faixas do Blue são uma adaptação por força/utilidade, e não uma cópia literal de todos os preços oficiais.
- Equipamentos agora têm preços individuais. Exemplos: guia/mapa 500; música/Old Rod 1.000; bicicleta/Good Rod 5.000; Box Link 12.000; Mega Ring/Z-Ring 15.000; Tera Orb/Dynamax Band 20.000; Ability Vial 25.000; Tera Jewel 30.000; Shiny Charm 80.000. Ferramentas de formas têm a faixa padrão de 10.000 quando não possuem preço específico.
- A taxa de prêmio por nível da classe do treinador recebe multiplicador **1× no iniciante, 2× no intermediário e 3× no avançado**. O prêmio continua usando o maior nível real do adversário e os multiplicadores nativos de batalha. Assim, mantendo a classe e a fase, um oponente de nível maior paga mais; mantendo a classe e o nível, a fase mais avançada paga mais.

### Seis seletores de IV

Na aba **Treino**, há um seletor para cada atributo: HP, Ataque, Defesa, Ataque Especial, Defesa Especial e Velocidade. Cada um custa **50.000**. Use-o fora da batalha pela mochila, escolha um Pokémon e um valor de **0 a 31**. Só o IV escolhido muda; os atributos são recalculados. O item é consumido apenas se o valor mudar. Cancelar, selecionar o valor atual ou tentar usar em um ovo não gasta o item. Os atalhos gratuitos de IV da tela de equipe/resumo ficam ocultos na campanha; a edição livre do Hub continua disponível.

### Golpes de treinadores por fase

No iniciante (0–1 esmeralda), o poder base máximo é **60**; no intermediário (2–3), **90**. Isso vale também para líderes e bosses, que seguem o escalonamento de 70% descrito abaixo. No avançado (4+), seus golpes permanecem como antes.

São retirados boosts/drops de dois ou mais estágios, alterações de vários atributos, resets/copias/inversões de estágios e golpes de dano extremo/variável ou chamadas de golpes que escapariam ao limite. Swords Dance, por exemplo, não passa. A troca procura golpes do mesmo papel, categoria e tipo, entre os aprendidos por nível até o nível atual ou por tutor; não usa egg moves como atalho. Não repete golpes. Se uma espécie não possui nenhum candidato permitido, fica sem golpes selecionáveis e a engine usa seu Struggle nativo, sem ensinar um golpe ilegal.

As equipes são copiadas em memória: os Pokémon do jogador, o montador do Hub, os PBS e os saves originais não são regravados. O seletor também remove o Hyper Training apenas do atributo alterado quando necessário, para que escolher IV 0 resulte realmente em IV 0 na batalha.

Ao escolher **Story Mode** em uma jornada nova, o jogo pergunta quais mecânicas estarão habilitadas: Mega Evolução, Z-Moves, Terastal e Dynamax. Finalize em **Começar jornada**. A escolha fica no save da campanha, vale para os dois lados e não muda a configuração independente do Hub. Habilitar uma mecânica não entrega equipamento nem pedras: eles precisam ser obtidos ou comprados.

A jornada começa **sem itens na mochila**. O preenchimento gratuito da base e o kit de ferramentas da introdução são bloqueados; ao sair da introdução, a mochila é limpa uma única vez. O dinheiro inicial da base é mantido para as primeiras compras. Saves existentes não têm sua mochila apagada. Itens obtidos normalmente depois da introdução são preservados.

Na campanha, os geradores de Pokémon, Auto Grind e reposição gratuita de itens são retirados dos mapas carregados. Os antigos vendedores passam a abrir a loja paga. A preparação livre de equipes e inventários do Battle Mode e do Hub continua disponível fora da campanha.

A configuração inicial da campanha também deixa de preencher o PC com todas as espécies e formas da base. O fluxo de escolha dos iniciais continua funcionando; depois disso, a equipe cresce por encontros, capturas e presentes legítimos da história.

Ferramentas de gerar dinheiro/itens, atravessar paredes e o telefone de teleporte irrestrito também ficam bloqueados na campanha quando já estavam em um save antigo. Os itens permanecem na mochila desse save; seus usos de sandbox continuam disponíveis fora da campanha. O telefone da base permitia pular diretamente para áreas e quests ainda não alcançadas, por isso não faz parte dos equipamentos vendidos.

## Treinadores

Cada Pokémon de qualquer treinador da campanha, inclusive líderes, mestres, bosses e rivais, usa `max(1, floor(maior nível do time × 0,70))`. O cálculo considera o time inteiro e ignora ovos: nível máximo 10 → adversários no 7; 50 → 35; 100 → 70. É calculado no início da luta, depois do escalonamento da base, sem regravar PBS nem modificar o Pokémon original do treinador.

A progressão de BST por esmeraldas continua valendo no Traditional Starters. Cada vitória contra treinador na campanha dá o prêmio nativo: nível máximo do adversário × dinheiro-base da classe, com os multiplicadores nativos. Classes com valor zero usam 30 por nível. O Hub continua sem recompensar a campanha.

## Loja por abas

Há um vendedor acessível ao lado de cada enfermeira Joy visível. As inserções são feitas em memória e não alteram os arquivos de mapas. Converse com ele para abrir a loja. Clique nas abas ou use esquerda/direita para trocar de categoria; use o mouse ou cima/baixo para escolher um item, confirme, escolha a quantidade e confirme o valor. Esc/botão direito sai.

As abas são **Cura, Poké Balls, Mega Stones, Cristais Z, Treino, TMs/TRs, Equipamentos e Outros**. O painel mostra dinheiro, preço, descrição e quantidade na mochila. Uma compra só desconta dinheiro após validar saldo e espaço; equipamentos importantes são vendidos uma única vez.

Todos os itens utilizáveis do catálogo estão à venda, incluindo pedras autorais e Z-A. **Itens de missão, chaves de progressão e ferramentas de gerar dinheiro/itens ou atravessar paredes não são vendidos**, para preservar a história. Os equipamentos de mecânicas e utilidades básicas têm uma lista explícita de exceções. Ter uma mecânica desativada não impede comprar sua pedra; a restrição continua sendo aplicada na batalha.

Remédios, vitaminas e mints que a base tinha transformado em itens-chave infinitos voltam a ser **consumíveis** na campanha: cada uso bem-sucedido gasta a quantidade usada. Eles podem ser comprados em quantidades normais. Ferramentas legítimas de treino e formas, varas de pesca, bicicleta e charms também podem ser comprados, pelos preços individuais descritos no balanceamento. Ferramentas que definem insígnias, vitória automática, nível arbitrário ou golpes sem restrição ficam fora da campanha. Rare Candy e Exp. Candies não são vendidos.

## Critério de preços

Preços de referência de Emerald vêm da tabela pública de [pret/pokeemerald](https://github.com/pret/pokeemerald/blob/master/src/data/items.h): Poké Ball 200, Great Ball 600, Ultra Ball 1.200, Potion 300, Super Potion 700, Hyper Potion 1.200, Full Restore 3.000, Revive 1.500, além dos remédios de status e repelentes.

Os preços seguintes são **balanceamento próprio do Blue**, não preços oficiais: Mega Stone 30.000; cristal Z 20.000; Master Ball 100.000; mints, Ability Capsule e Bottle Caps 10.000 (Ability Patch/Gold Bottle Cap 20.000); berries 100; seletores de IV 50.000. TMs/TRs e equipamentos usam as faixas e valores individuais da atualização acima. Outros itens mantêm o preço positivo da instalação, com mínimo 100. Itens que eram gratuitos recebem um preço pela categoria. A revenda nas lojas nativas não supera metade do preço de compra, evitando lucro infinito entre lojas.

Para os outros itens competitivos que têm preço em Battle Points, a raridade é convertida em dinheiro usando **1 BP = 500**, adotando o maior valor entre essa conversão e o preço monetário da base. As faixas explícitas acima têm prioridade. É uma regra de balanceamento do Blue; não existe uma taxa oficial de conversão BP/dinheiro nos jogos originais.

## Sprites de costas autorais

As espécies Dessastre Paradoxal que usam escala traseira 1 passam para 1,5: os quadros de 128 px são renderizados em 192 px. Sprites frontais, arquivos de arte, sprites oficiais e métricas já personalizadas continuam com suas escalas. O mesmo ajuste vale para shiny e para os perfis de qualidade.

## Verificação

O smoke nativo grava os resultados em `game/Data/blue-polish-validation.txt`. Ele verifica níveis de todos os treinadores, preservação dos times de origem, escolhas da campanha, preços positivos, compras sem saldo, descontos exatos, limite de revenda, um vendedor acessível por Joy, remoção dos geradores, inserção sem duplicação, inventário inicial e renderização da loja. Os instaladores mantêm backups em `.blue-backups/`.

## Encontros selvagens e opções de batalha

Selvagens usam `max(1, floor(maior nível do time × 0,45))`, ignorando ovos, depois dos handlers de escalonamento da base. Maior nível 50 → selvagem 22; maior nível 100 → selvagem 45. A entrada direta de batalhas selvagens também recebe a regra. Os encontros gerados usam os golpes de nível da espécie no nível calculado.

Na progressão Traditional Starters, selvagens seguem a mesma seleção por família/tipos usada nos treinadores: BST máximo 350 no inicial (0–1 esmeralda), 450 no intermediário (2–3), sem teto no avançado (4+). A restrição a mudanças de forma também vale para o adversário selvagem. O limite não altera Pokémon que o jogador já capturou.

Os diálogos de treinadores da campanha oferecem **Start Battle (Exp Gain)** e saída. A cura gratuita por treinador e a alternativa Forfeit Option foram retiradas; as enfermeiras continuam funcionando. Ginásios oferecem apenas **Full Power Team → Double Battle → Start Battle (Exp Gain)**, além de cancelar. O adaptador de início também garante o time 2v2 Full Power em eventos antigos. Revanches Blue agora habilitam EXP e dinheiro, preservando o bloqueio de drops e a frequência por estágio. O Hub e o Battle Mode mantêm seus próprios formatos e não dão EXP à campanha.

## Status e efeitos de fim de turno

Sono usa a distribuição de contadores **2, 3, 3**, que bloqueia respectivamente uma, duas e duas ações antes de acordar. Paralisia impede agir com probabilidade exata de **1/8 (12,5%)**; a redução normal de Speed é preservada. Rest continua com duração explícita e Early Bird mantém sua interação. Esses dois ajustes seguem o [mod Champions do Pokémon Showdown](https://github.com/smogon/pokemon-showdown/blob/master/data/mods/champions/conditions.ts); Freeze e outros golpes não recebem alterações não solicitadas.

Leech Seed mantém seu efeito clássico: drena 1/8 do HP máximo do alvo a cada fim de turno e recupera o HP do Pokémon na posição beneficiária. O modo que ocultava mensagens/animações de fim de turno foi desativado. Imunidade de Grass, Magic Guard, Big Root e Liquid Ooze continuam usando a lógica da engine.

## Correção do menu ao salvar

Salvar com sucesso encerra o menu e descarta seus sprites. O loop de pausa agora encerra imediatamente após esse callback, antes de atualizar o HUD de novas quests. Isso corrige `undefined method 'y' for nil:NilClass` após salvar, inclusive ao sair para a rota e retornar ao Centro Pokémon. Não há migração nem limpeza do save existente.

A validação adicional fica em `game/Data/blue-journey-validation.txt`: inclui eventos reais dos mapas, os dois percentuais, os tetos de BST, ganho nativo de EXP, três turnos consecutivos de Leech Seed, probabilidades dos status, retorno ao Centro e fechamento do HUD. O teste de save serializa/recarrega apenas objetos temporários em memória; o laboratório mantém as proteções contra gravação da campanha.
