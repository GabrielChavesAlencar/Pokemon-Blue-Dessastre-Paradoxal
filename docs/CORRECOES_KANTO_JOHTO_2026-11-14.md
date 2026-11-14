# Correções dos testes de Kanto e Johto

- Tela de título: Iron Maeltrom usa 67% da escala anterior e varia suavemente a altura, com o sprite ancorado pela base.
- Menu de pausa: Circuito de regiões usa o ícone de mapa. As entradas de Progressão/Revanches Blue e os atalhos redundantes de cartão saíram do menu. O Trainer Card tradicional continua sendo a entrada para os cartões regionais.
- Kanto: a Rota 2 e as portarias recebem a faixa 13, separada da Viridian Forest (faixa 17). As quatro batalhas da Elite Four usam a trilha de desafio de ginásio e o campeão mantém a faixa própria. O guarda de Pewter condiciona a passagem para a Rota 3 à Boulder Badge.
- Safari Zone: recepção, quatro setores com encontros, casas de descanso, prêmio de Surf e missão dos Dentes de Ouro com Strength. A sessão usa as 30 Safari Balls e o contador de passos do motor. A trilha dos setores reutiliza a faixa 48 do catálogo. O portal mostra os encontros de cada setor.
- Johto QA: menus de viagem rápida só na cópia de teste, placas interativas, nomes de áreas, ajustes de tiles e colisão, música de cura, 17 interiores adicionais, escada do mirante em Cherrygrove e conexões de Violet com as Rotas 32 e 36. Entregue o Ovo Misterioso a Elm para liberar a chegada a Violet; vença Falkner para sair pelos caminhos bloqueados.

A auditoria de Kanto cobriu 142 mapas, com 107 ativos e 35 prévias. Encontrou 348 chaves distintas de NPCs e placas em 246 eventos, todas cadastradas em PT-BR. Os eventos e textos que ainda não foram implementados ficam fora da contagem. A [auditoria de localização](KANTO_AUDITORIA_LOCALIZACAO_PTBR.md) explica como repetir a verificação.

Os testes do Game.exe conferiram o pagamento e as recompensas da Safari, a escolha das trilhas, a escala do sprite e a recarga de save em perfil de QA. Ainda faltam validar a captura e os HMs em uma campanha jogada, ouvir as trilhas no Windows/JoiPlay e revisar as 35 prévias de Kanto. Em Johto, as casas adicionadas usam interiores genéricos e a campanha após Violet continua experimental. O teste dirigido no motor de Johto verificou escada nos dois sentidos, recuperação de HP e disparo do som de cura, nomes de área, bloqueios em Violet e as duas saídas. As barras de aceitação exigem teste interativo.

## Reteste de New Bark, Viridian e Liga

- Em Kanto, a lista abre com a numeração dos 151 Pokémon de Kanto. A tecla **K** e o botão da lista alternam entre Kanto e a Nacional. A preferência usa a região do save atual.
- As setas de Viridian ganham eventos Player Touch a partir do tile direcional original. O personagem gira enquanto se move. A ação para em obstáculos, no piso amarelo ou quando chega ao fim do caminho.
- O retorno da Rota 23 agora chega no lado sul do primeiro guarda, com caminho de volta para a Rota 22. O bloqueio por insígnia continua ativo.
- New Bark mantinha a saída de casa em terra firme, mas o limite de câmera fazia os mapas vizinhos começarem na mesma posição visual. A correção preserva os deslocamentos da câmera nos mapas conectados. Casa, quarto e laboratório reutilizam o tileset instalado para se aproximar do visual de HeartGold e SoulSilver. Os interiores das outras cidades ainda precisam de comparação individual.

Referências visuais para New Bark e seus interiores: [New Bark Town](https://bulbapedia.bulbagarden.net/wiki/New_Bark_Town), [casa do jogador](https://bulbapedia.bulbagarden.net/wiki/Player%27s_house#Johto) e [guia do início de HeartGold e SoulSilver](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pokémon_HeartGold_and_SoulSilver/Part_1).

O [guia do atualizador Android](ANDROID_ATUALIZACOES_INCREMENTAIS.md) usa o canal **Kanto piloto** para este pacote. A validação em aparelho físico continua pendente.
