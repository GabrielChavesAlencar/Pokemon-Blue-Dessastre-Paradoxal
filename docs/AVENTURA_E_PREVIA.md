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

A preferência de idioma continua em **Configurações → Language / Idioma**. Foram ampliadas as traduções de aberturas de batalha, mensagens já montadas com nomes/valores, textos com cores, linhas de informação da Pokédex e dados das missões. Nomes de habilidades permanecem em inglês. Nomes de Pokémon, apelidos, itens e golpes continuam preservados; IDs e condições dos eventos não são traduzidos.

As descrições de missões e os efeitos das habilidades entram no catálogo offline; os nomes registrados das habilidades ficam preservados. Como no restante da localização inicial, a tradução assistida pode precisar de revisão de contexto durante a campanha. A tabela distribuída não requer um serviço de tradução para jogar.

**Delta Speed Up** é o plugin de aceleração da base, e não um emulador. A configuração instalada alterna entre **1x** e **3x**. Ele acelera a linha de tempo das animações; as opções definem se vale sempre ou só nas batalhas. A espera de leitura das mensagens de erro de ataque usa tempo real para continuar legível com o turbo.

O novo jogo pula o questionário sobre emulador/speed-up e seu ramo punitivo. A opção de aceleração é identificada como **Delta Speed Up**, preservando o controle nativo de 1x/3x.

## Comparação no portal

A aba **O que mudou**, em `/o-que-mudou`, compara Pokémon Decades base e Dessastre Paradoxal em duas colunas, com 33 aspectos em ordem de relevância. O histórico por atualização continua automático na aba Atualizações.

`game/Data/blue-readouts-validation.txt` registra a prova nativa dos eventos reais de novo jogo, listas dos 18 tipos, bloqueio de conversão de modo, números da Pokédex, boxes, missões, multiplicadores e prévia por teclado/clique. Todos os testes usam dados novos em memória, com o save da campanha bloqueado pelo laboratório.

`game/Data/blue-touch-validation.txt` registra os cliques nas telas nativas, o ramo real de escolha monotipo e a posição dos modificadores e telas em batalha dupla.

## Habitat Dex

Abra **Pausa → Pokédex → Habitat Dex**. A opção **Lista de Pokémon** continua abrindo a Pokédex normal. A Habitat Dex se inspira na lista de habitats do Black 2: primeiro escolha uma área visitada e depois o método de encontro, como grama, Surf ou Old Rod.

As áreas mostram contadores de vistos (V) e capturados (C), com estrela quando todas as espécies disponíveis foram capturadas. Espécies vistas mostram nome e ícone; capturadas recebem indicação verde; as desconhecidas mostram somente **?**. Consultar não registra Pokémon como vistos nem libera áreas novas. A lista usa a versão ativa dos encontros, com a mesma tabela base de fallback da engine, e acompanha as substituições por BST da fase da campanha. Espécies repetidas em uma tabela contam uma vez.

Use as setas esquerda/direita ou **Anterior/Próximo** para mudar de página; **Esc/Voltar** retorna ao menu de métodos. As áreas e métodos usam listas com paginação e mouse.

Referência de funcionamento: [Habitat List de Black 2 e White 2](https://bulbapedia.bulbagarden.net/wiki/Habitat_List).

## Ajuda, personagem e pesca

A tela inicial de explicação das teclas aceita um clique para continuar. Na escolha de personagem, clique no personagem ou no retrato e confirme no diálogo Sim/Não; teclado e cancelamento do diálogo continuam disponíveis.

A Old Rod usa a tabela OldRod quando ela existe. Nos mapas da base que só cadastram SuperRod, as varas sem tabela herdam a tabela de pesca local em memória, preservando espécies e pesos. Tabelas próprias já existentes têm prioridade e os dados originais não são regravados. A base tinha um caminho de fisgada manual que repetia a espera mesmo após uma reação correta; o adaptador agora retorna sucesso e permite ao handler nativo iniciar o encontro. A mesma correção atende Good Rod e Super Rod. Clique ou use o comando de confirmação quando aparecer a mordida. Se o mapa não tem nenhuma tabela de pesca, não aparece Pokémon; encontros de Surf ou de grama não são convertidos em pesca.

`game/Data/blue-exploration-validation.txt` registra a prova das telas nativas, handler da Old Rod, Habitat Dex e fronteiras das quatro faixas de campanha. Os testes usam memória temporária do laboratório.

## Pausa e atalho do resumo

Os ícones e as setas do carrossel de pausa aceitam cliques. Clicar em um ícone seleciona e executa a ação nativa correspondente, incluindo Pokémon, Pokédex e Salvar. O fechamento após salvar continua usando a proteção contra atualizar componentes já descartados.

No resumo de um Pokémon da equipe, clique em **Pokédex [P]** ou pressione **P** para abrir a ficha daquela espécie e forma. Voltar retorna ao resumo e ao mesmo integrante. A opção **View Pokédex** também fica disponível no menu de opções das páginas. O atalho respeita a obtenção da Pokédex, não aparece para ovos e fica desativado durante a batalha.

## Habitat atual e localização no mapa

Ao abrir a Habitat Dex, ela entra diretamente na rota/cidade atual quando existe um habitat disponível. Interiores usam a posição regional cadastrada ou a de um mapa pai para encontrar a área correspondente. **Outros habitats** abre a lista de áreas visitadas. Se o local atual não tem encontros cadastrados, o título da lista informa onde você está.

Escolha **Ver no mapa**, ou clique em **Mapa [M]** na página de espécies. O mapa regional usa o desenho instalado e as coordenadas nativas: dourado indica o habitat, azul indica o jogador quando está na mesma região. Os marcadores podem coincidir. Locais sem coordenadas cadastradas mostram uma mensagem, sem receber uma posição inventada.

O mapa abre com **zoom de 3×**, centralizado no habitat. Use **+ / −** ou **I / O** para ampliar/reduzir, setas ou arraste com o mouse para mover, **Centralizar** para retornar ao habitat e **Região** para ver o mapa inteiro. Os limites do recorte acompanham as bordas da imagem.

A entrada da Pokédex usa dois cartões grandes com imagens: **Lista de Pokémon** e **Habitat Dex**. Os métodos de encontro de cada habitat também usam cartões quadrados, com ícones de mapa, grama, pedras, varas e outros métodos. Há até seis cartões por página, botões de página e Voltar. As setas e a confirmação pelo teclado continuam funcionando. Os ícones dos métodos não revelam Pokémon desconhecidos.

## Aprender golpes e sprites de costas

Na tela de escolher um golpe para esquecer, clique na linha do golpe desejado ou em **Cancelar / Voltar**. O clique percorre a seleção nativa e mantém as confirmações e restrições originais. Espaços vazios não são selecionáveis. A tela de esquecer um golpe sem aprender outro também recebe o mesmo controle. No relembrador de golpes, as linhas visíveis, setas de rolagem e botão de voltar também aceitam cliques.

Foram revisados visualmente os 70 sprites de costas disponíveis dos Pokémon autorais, incluindo as 12 Megas. Somente **Ammnoid** tinha direção claramente invertida: sua imagem de costas agora é espelhada durante a renderização, inclusive nos dois espaços aliados em duplas, shiny e opções de qualidade. A arte original permanece preservada; imagens da frente e substituições por outras espécies mantêm sua orientação.

`game/Data/blue-dex-cards-validation.txt` registra os testes nativos dos cartões, seleção de golpes, zoom e orientação das formas autorais prontas para batalha. Os testes usam memória temporária do laboratório e não carregam a campanha.

## Pesquisa e filtros da Pokédex

Na lista da Pokédex, clique em **Pesquisa / Filtros [F]**, pressione **F** ou use o comando de pesquisa nativo. É possível buscar parte do nome, filtrar tipo, mostrar todas as entradas, somente vistos ou somente capturados, e ordenar por número, nome, altura ou peso. Nomes e tipos usam os dados atuais do jogo. Pesquisa por nome/tipo e ordens descritivas não revelam espécies desconhecidas.

**Aplicar filtros** atualiza a lista; **Limpar filtros** restaura a lista e numeração nativas. Sem resultados, a consulta informa isso e permite ajustar os critérios. **Busca avançada** mantém a pesquisa original, incluindo suas outras categorias. Pesquisar não registra Pokémon como vistos ou capturados.

## Comparações de altura e peso

Na ficha de um Pokémon da Pokédex há duas abas novas: **Altura** e **Peso**, acessíveis pelas setas ou clicando nos cabeçalhos. Altura coloca a figura do Pokémon e a silhueta do jogador lado a lado, na mesma escala física e com as duas medidas. Peso usa uma balança que inclina para o lado mais pesado e mostra os dois valores.

A referência do jogador começa em **1,70 m e 60 kg**, escolhidos pelo autor. Use **Referência jogador**, na parte inferior dessas abas, ou confirme com Enter para ajustar altura em centímetros e peso em quilos. A preferência acompanha os metadados do save quando a campanha for salva normalmente. As medidas do Pokémon vêm da espécie/forma atual; dados ausentes são indicados com `?`.

## Impacto de entrada por peso

A apresentação de entrada inclui um impacto cosmético inspirado no [efeito de entrada de Black/White](https://www.dragonflycave.com/unova/bw-changes/#weight-based-sendout). No Blue, as faixas são: abaixo de 50 kg sem impacto pesado; 50–149,9 kg com toque leve; 150–299,9 kg com poeira e impacto médio; 300 kg ou mais com estrondo e mais poeira. A poeira é desenhada pelo código e os sons vêm da instalação existente.

O efeito começa após a materialização ou ao terminar o deslizamento de um selvagem. Pokémon Flying, com Levitate ou com altitude visual cadastrada não levantam poeira do chão. São usados o peso e a forma da espécie, sem alterar stats ou o cálculo de golpes. Os sprites e o fundo retornam à posição original, e as partículas são descartadas ao terminar a animação.

`game/Data/blue-dex-features-validation.txt` registra a prova nativa dessas telas, da escala, dos filtros e da entrada pesada.

## Treino, pesca e consulta dos líderes

A loja mostra **número da TM/TR + nome do golpe em inglês**, também nas confirmações. Habilidades preservam seus nomes registrados em inglês nas mensagens e menus, mesmo usando Português.

Há seis itens consumíveis novos na aba **Treino**, por **$750 cada**: EV Cleaner HP, Attack, Defense, Sp. Atk, Sp. Def e Speed. Cada um zera somente o atributo correspondente, recalcula os stats e mantém os outros EVs. Cancelar, escolher um ovo ou usar no atributo já zerado não gasta o item. O EV Cleaner completo continua disponível por $2.000.

No menu de contexto de um Pokémon da equipe, **Relembrar golpes** abre o relembrador nativo sem cobrar item. Mostra golpes do learnset por nível até o nível atual, incluindo os anteriores ao nível de captura, e os primeiros golpes registrados pelo jogo; exclui os que já são conhecidos. Não libera golpes de níveis futuros nem o catálogo geral de tutor/TMs. Usa as confirmações e a troca de um dos quatro golpes da engine. Ovos, Pokémon Shadow e o menu durante uma batalha não recebem essa opção.

O Trainer Card mostra a dificuldade atual e o total de cristais: Iniciante (0–1), Intermediário (2–4), Avançado (5–10) ou Master (11+).

### Varas e Habitat Dex

As três varas deixam de copiar a mesma tabela. A classificação usa a menor categoria de vara encontrada nas tabelas de [FireRed/LeafGreen](https://github.com/pret/pokefirered/blob/master/src/data/wild_encounters.json) e [Emerald](https://github.com/pret/pokeemerald/blob/master/src/data/wild_encounters.json). Feebas recebe tratamento raro no Blue. Para espécies sem referência nesses arquivos, a adaptação do Blue usa taxa de captura, BST e estágio evolutivo: taxa menor que 90 ou BST maior que 450 são raros; base com taxa de pelo menos 190 e BST de até 350 é comum; os demais são intermediários. Isso é um balanceamento do Blue para o catálogo ampliado, não uma reprodução de chances oficiais de todas as gerações.

Old Rod acessa comuns; Good Rod acessa comuns e intermediários; Super Rod acessa todas as espécies locais de pesca, incluindo as raras. Quando as três categorias estão presentes, as massas de chance são 100% comuns na Old, 30% comuns/70% intermediários na Good e 10% comuns/75% intermediários/15% raros na Super. Dentro de cada grupo, a proporção dos slots locais é preservada. Grupos ausentes são redistribuídos entre os disponíveis; uma vara sem espécies elegíveis não tem encontro. Áreas com uma única espécie ou categoria podem repetir encontros entre varas.

Nenhuma espécie de fora da tabela local é introduzida. Surf, encontros de terra, fases, versões da campanha e os arquivos PBS permanecem preservados. A Habitat Dex reúne as três varas em um único cartão **Pesca**. Cada Pokémon identificado aparece uma vez e indica Old, Good e/ou Super conforme a tabela efetiva; desconhecidos continuam ocultos.

### Chefes no portal

As fichas dos 18 líderes mostram somente **Full Doubles**, com seis Pokémon e quatro dificuldades. Os dados são exportados da engine instalada usando as mesmas substituições de espécie e filtros de golpes da campanha. As séries de golpes cobrem os níveis 1–100; o site permite informar o maior nível do jogador e usa 70% nas primeiras três faixas e 90% no Master, com arredondamento para baixo e mínimo 1. Itens, habilidades e EVs acompanham a forma adaptada. Os demais chefes mantêm suas referências específicas.

Para atualizar esses perfis após alterar treinadores ou regras, com o jogo fechado: `python scripts/battle_lab/launch.py --prepare-only --smoke-test --export-campaign-reference`, abra o Game.exe preparado e aguarde a conclusão dos testes, depois execute `python scripts/export_story_teams.py`. A exportação usa memória temporária e não carrega a campanha. O sincronizador só aceita dados nativos com o mesmo CRC do PBS e das regras de campanha; perfis antigos são removidos se a fonte ou as regras mudarem sem uma nova exportação.

A correção de direção do Ammnoid normaliza cada quadro de costas em memória antes de a engine aplicar as animações, incluindo Rollout e efeitos recebidos. A orientação e o ângulo de repouso são restaurados ao terminar os players. Veja também [Álbum e mapas](ALBUM_E_MAPAS.md) para a grade de 12 Pokémon, prêmio por área e capturas do site.

`game/Data/blue-next-validation.txt` registra a prova dos seis itens, relembrador com aprendizado real, todas as tabelas de pesca, nomes de TMs/habilidades, agrupamento de varas e quatro dificuldades do Trainer Card. O teste de Rollout está em `blue-dex-cards-validation.txt`.
