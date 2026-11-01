# Jornada, economia e vendedores Blue

Ao escolher **Story Mode** em uma jornada nova, o jogo pergunta quais mecânicas estarão habilitadas: Mega Evolução, Z-Moves, Terastal e Dynamax. Finalize em **Começar jornada**. A escolha fica no save da campanha, vale para os dois lados e não muda a configuração independente do Hub. Habilitar uma mecânica não entrega equipamento nem pedras: eles precisam ser obtidos ou comprados.

A jornada começa **sem itens na mochila**. O preenchimento gratuito da base e o kit de ferramentas da introdução são bloqueados; ao sair da introdução, a mochila é limpa uma única vez. O dinheiro inicial da base é mantido para as primeiras compras. Saves existentes não têm sua mochila apagada. Itens obtidos normalmente depois da introdução são preservados.

Na campanha, os geradores de Pokémon, Auto Grind e reposição gratuita de itens são retirados dos mapas carregados. Os antigos vendedores passam a abrir a loja paga. A preparação livre de equipes e inventários do Battle Mode e do Hub continua disponível fora da campanha.

A configuração inicial da campanha também deixa de preencher o PC com todas as espécies e formas da base. O fluxo de escolha dos iniciais continua funcionando; depois disso, a equipe cresce por encontros, capturas e presentes legítimos da história.

Ferramentas de gerar dinheiro/itens, atravessar paredes e o telefone de teleporte irrestrito também ficam bloqueados na campanha quando já estavam em um save antigo. Os itens permanecem na mochila desse save; seus usos de sandbox continuam disponíveis fora da campanha. O telefone da base permitia pular diretamente para áreas e quests ainda não alcançadas, por isso não faz parte dos equipamentos vendidos.

## Treinadores

Cada Pokémon de um treinador comum usa `max(1, floor(maior nível do time × 0,70))`. O cálculo considera o time inteiro e ignora ovos: nível máximo 10 → adversários no 7; 50 → 35; 100 → 70. É calculado no início da luta, depois do escalonamento da base, sem regravar PBS nem modificar o Pokémon original do treinador.

Líderes, mestres, bosses e rivais continuam no caminho anterior. A identificação usa os nomes dos 18 mestres e Danny, além das classes identificadas como Leader, Master, Boss, Elite, Champion, Rival ou Admin. A progressão anterior de BST por esmeraldas continua valendo no Traditional Starters. Cada vitória contra treinador na campanha dá o prêmio nativo: nível máximo do adversário × dinheiro-base da classe, com os multiplicadores nativos. Classes com valor zero usam 30 por nível. O Hub continua sem recompensar a campanha.

## Loja por abas

Há um vendedor acessível ao lado de cada enfermeira Joy visível. As inserções são feitas em memória e não alteram os arquivos de mapas. Converse com ele para abrir a loja. Clique nas abas ou use esquerda/direita para trocar de categoria; use o mouse ou cima/baixo para escolher um item, confirme, escolha a quantidade e confirme o valor. Esc/botão direito sai.

As abas são **Cura, Poké Balls, Mega Stones, Cristais Z, Treino, TMs/TRs, Equipamentos e Outros**. O painel mostra dinheiro, preço, descrição e quantidade na mochila. Uma compra só desconta dinheiro após validar saldo e espaço; equipamentos importantes são vendidos uma única vez.

Todos os itens utilizáveis do catálogo estão à venda, incluindo pedras autorais e Z-A. **Itens de missão, chaves de progressão e ferramentas de gerar dinheiro/itens ou atravessar paredes não são vendidos**, para preservar a história. Os equipamentos de mecânicas e utilidades básicas têm uma lista explícita de exceções. Ter uma mecânica desativada não impede comprar sua pedra; a restrição continua sendo aplicada na batalha.

Remédios, vitaminas, mints e Rare Candy que a base tinha transformado em itens-chave infinitos voltam a ser **consumíveis** na campanha: cada uso bem-sucedido gasta a quantidade usada. Eles podem ser comprados em quantidades normais. Ferramentas legítimas de treino e formas, varas de pesca, bicicleta e charms também podem ser comprados; equipamentos reutilizáveis custam 10.000 e charms de raridade custam 50.000. Ferramentas que definem insígnias, vitória automática, nível arbitrário ou golpes sem restrição ficam fora da campanha.

## Critério de preços

Preços de referência de Emerald vêm da tabela pública de [pret/pokeemerald](https://github.com/pret/pokeemerald/blob/master/src/data/items.h): Poké Ball 200, Great Ball 600, Ultra Ball 1.200, Potion 300, Super Potion 700, Hyper Potion 1.200, Full Restore 3.000, Revive 1.500, além dos remédios de status e repelentes.

Os preços seguintes são **balanceamento próprio do Blue**, não preços oficiais: Mega Stone 30.000; cristal Z 20.000; equipamentos de mecânicas 10.000; Master Ball 100.000; TMs/TRs 5.000; mints, Ability itens e Bottle Caps 10.000 (Ability Patch/Gold Bottle Cap 20.000); berries 100. Outros itens mantêm o preço positivo da instalação, com mínimo 100. Itens que eram gratuitos recebem um preço pela categoria, entre 1.000 e 5.000. A revenda nas lojas nativas não supera metade do preço de compra, evitando lucro infinito entre lojas.

Para os outros itens competitivos que têm preço em Battle Points, a raridade é convertida em dinheiro usando **1 BP = 500**, adotando o maior valor entre essa conversão e o preço monetário da base. As faixas explícitas acima têm prioridade. É uma regra de balanceamento do Blue; não existe uma taxa oficial de conversão BP/dinheiro nos jogos originais.

## Sprites de costas autorais

As espécies Dessastre Paradoxal que usam escala traseira 1 passam para 1,5: os quadros de 128 px são renderizados em 192 px. Sprites frontais, arquivos de arte, sprites oficiais e métricas já personalizadas continuam com suas escalas. O mesmo ajuste vale para shiny e para os perfis de qualidade.

## Verificação

O smoke nativo grava os resultados em `game/Data/blue-polish-validation.txt`. Ele verifica níveis, preservação dos bosses, escolhas da campanha, preços positivos, compras sem saldo, descontos exatos, limite de revenda, um vendedor acessível por Joy, remoção dos geradores, inserção sem duplicação, inventário inicial e renderização da loja. Os instaladores mantêm backups em `.blue-backups/`.
