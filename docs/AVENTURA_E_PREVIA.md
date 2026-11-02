# Aventura, Pokédex e prévia do adversário

## PC e boxes

Na campanha e no Battle Mode do jogo principal, abra o menu de pausa e escolha **PC / Boxes Pokémon**. A tela é o armazenamento nativo: organize a equipe, deposite e retire os Pokémon das boxes. As restrições nativas, como manter um Pokémon utilizável na equipe, continuam valendo. O acesso não depende de comprar o Pokémon Box Link, cujo uso na base também inclui atalhos de treinamento. O PC não abre durante batalhas, Safari ou Concurso de Captura.

O laboratório/Hub mantém seus times separados da campanha e não carrega o save dela.

## Prévia e modificadores em batalha

No menu de comandos ou de golpes, pressione **P** ou clique em **P: Rival**, ao lado do atalho Run no painel superior. A prévia mostra os ícones e nomes das espécies já vistas na Pokédex. As outras vagas mostram **???**, sem nome, forma, nível, golpes, habilidade ou item. Ícones conhecidos usam a forma básica, sem revelar uma forma do adversário que ainda não entrou em campo. Consultar a tela não registra espécies como vistas, não gasta turno e não muda os comandos ou os times.

Enter, Esc, P ou um clique fecham a prévia. Ela também funciona em batalhas em dupla e com mais de um treinador adversário, exibindo as vagas da equipe oposta.

Os modificadores de atributos ficam **abaixo da barra de HP**: por exemplo, **1.5x Def**. Verde indica aumento e vermelho indica redução. O painel acompanha Ataque, Defesa, Ataque Especial, Defesa Especial, Velocidade, Precisão e Evasão. Precisão/Evasão usam o cálculo próprio da engine. Ao zerar os estágios ou trocar de Pokémon, os indicadores acompanham o estado atual. São multiplicadores dos estágios, não uma previsão de todos os efeitos de habilidade, item, clima ou condição de status.

O painel superior também mostra **Suas telas** e **Telas rivais**, com os turnos restantes: **R** = Reflect, **LS** = Light Screen e **AV** = Aurora Veil. A prévia aberta por **P** detalha os nomes e durações dos dois lados. Uma tela expirada desaparece automaticamente.

## Início e separação dos modos

- Um save de **Battle Mode** não pode iniciar **Story Mode**. A opção é retirada dos NPCs/menus e a chamada de configuração também é bloqueada. Para começar a história, use um novo jogo/save próprio; não se apagam Pokémon ou dados de saves existentes.
- Novos jogos pulam a pergunta da trilha sonora e seguem o ramo original **Intended Soundtrack**, preservando o BGM padrão e as listas aleatórias já instaladas.
- No Story Mode, a escolha da Pokédex mantém somente **Metagame Wiki Dex**. A lista de Pokédex acessíveis exibe essa opção, sem apagar as outras listas ou seus registros do save. Battle Mode mantém suas opções.
- A escolha dos iniciais na história oferece **tradicionais** e **monotipo**. Monotipo abre um segundo menu com os **18 tipos** e depois a seleção de **dois Pokémon**, identificada como Inicial 1/2 e Inicial 2/2. Inclui somente Pokémon cujo tipo atual é o selecionado e cujos stats base somam no máximo **350**. Não basta ganhar o tipo ao evoluir. A seleção usa os dados restaurados/atuais da engine, inclui formas regionais elegíveis e exclui espécies pendentes e transformações de batalha. Voltar no menu de tipos não entrega Pokémon. O formato em dupla da história continua valendo.

## Mouse na abertura e nas confirmações

Clique para iniciar na tela de título e para selecionar uma opção do menu inicial. Na entrada de nome, as letras, abas, apagar e OK aceitam cliques; a modalidade de digitação livre tem o botão **Confirmar nome**. As duas janelas de atributos exibidas ao subir de nível podem ser confirmadas com um clique em qualquer parte da tela. Esses cliques ficam limitados às respectivas telas. Setas e Enter continuam disponíveis.

Na seleção dos iniciais, clique nos ícones para mudar de Pokémon e na arte do Pokémon atual para confirmar. As setas laterais também aceitam cliques. A confirmação final usa o diálogo nativo Sim/Não.

## Português e aceleração

A preferência de idioma continua em **Configurações → Language / Idioma**. Foram ampliadas as traduções de aberturas de batalha, mensagens já montadas com nomes/valores, textos com cores, linhas de informação da Pokédex e dados das missões. Habilidades também são traduzidas. Nomes de Pokémon, apelidos, itens e golpes continuam preservados; IDs e condições dos eventos não são traduzidos.

As descrições de missões e nomes de habilidades entram no catálogo offline. Como no restante da localização inicial, a tradução assistida pode precisar de revisão de contexto durante a campanha. A tabela distribuída não requer um serviço de tradução para jogar.

**Delta Speed Up** é o plugin de aceleração da base, e não um emulador. A configuração instalada alterna entre **1x** e **3x**. Ele acelera a linha de tempo das animações; as opções definem se vale sempre ou só nas batalhas. A espera de leitura das mensagens de erro de ataque usa tempo real para continuar legível com o turbo.

O novo jogo pula o questionário sobre emulador/speed-up e seu ramo punitivo. A opção de aceleração é identificada como **Delta Speed Up**, preservando o controle nativo de 1x/3x.

## Comparação no portal

A aba **O que mudou**, em `/o-que-mudou`, compara Pokémon Decades base e Dessastre Paradoxal em duas colunas, com 30 aspectos em ordem de relevância. O histórico por atualização continua automático na aba Atualizações.

`game/Data/blue-readouts-validation.txt` registra a prova nativa dos eventos reais de novo jogo, listas dos 18 tipos, bloqueio de conversão de modo, números da Pokédex, boxes, missões, multiplicadores e prévia por teclado/clique. Todos os testes usam dados novos em memória, com o save da campanha bloqueado pelo laboratório.

`game/Data/blue-touch-validation.txt` registra os cliques nas telas nativas, o ramo real de escolha monotipo e a posição dos modificadores e telas em batalha dupla.
