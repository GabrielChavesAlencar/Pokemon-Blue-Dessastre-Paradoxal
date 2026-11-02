# Português, comandos e indicadores de batalha

Em **Configurações → Language / Idioma**, escolha **Português** (tradução para o português brasileiro). A preferência é salva com as configurações normais e pode voltar para English. A tela de configurações muda imediatamente. A localização inclui diálogos da história, menus, mensagens, descrições e textos extraídos dos eventos comuns/mapas. As escolhas continuam usando seus índices e condições originais, mesmo quando o rótulo exibido está traduzido.

Os nomes registrados de Pokémon, itens e golpes, e os apelidos dos Pokémon do jogador, permanecem iguais. Isso inclui palavras ambíguas como **Psychic**, que continua sendo Psychic quando é o nome do golpe. O painel de terreno usa um contexto separado para indicar Psíquico. Não se alteram os IDs dos treinadores, espécies, golpes, quests, itens ou eventos.

Os botões principais da batalha recebem rótulos de texto em português sobre os mesmos alvos de clique. A imagem original dos botões é preservada para English. Arquivos de imagens/áudio passados por `_INTL` mantêm o caminho original, e interpolações são tratadas como valores opacos, sem executar código Ruby da tabela.

A tradução inicial foi assistida por um modelo local e recebe ajustes manuais para mensagens e menus importantes. A cobertura automática do catálogo não equivale a uma revisão literária de cada diálogo; termos e contexto podem precisar de revisão durante a campanha. Nenhum serviço de tradução é necessário para jogar: o instalador compila a tabela própria em um recurso Marshal lido pela engine.

## Batalhas

- Mensagens de erro de precisão permanecem na tela por pelo menos **1,6 segundo real após aparecerem por completo**. O turbo e pressionar confirmação repetidamente não encurtam esse intervalo.
- **R** escolhe o comando **Run**. Funciona no menu principal e no seletor de golpes. Continua respeitando a engine: confirmação de desistência, tentativas de fuga, armadilhas e batalhas em que fugir é proibido.
- O painel compacto no canto superior direito mostra clima, terreno, Trick Room e Tailwind, com a duração restante quando aplicável. Tailwind distingue **Seu lado** de **Rival**. Efeitos expirados somem do painel. Sem efeitos ativos, Campo: normal / Field: clear e o atalho Run ficam em uma faixa de 22 pixels no topo, liberando a área dos sprites. O seletor F6 de mecânicas acompanha a altura do painel. Mega Sol não é exibido como um sol global, pois seu efeito é pessoal.
- No modo História, as perguntas de formato oferecem somente **Double Battle / Batalha em dupla**, além de cancelar. Isso abrange também perguntas fora dos ginásios; os formatos livres do Hub/Battle Mode continuam disponíveis.
- Líderes dos 18 ginásios recebem multiplicador **2× no dinheiro**, comparados a um treinador normal de mesma classe, nível e fase. O multiplicador acumula com as regras nativas de prêmio e os multiplicadores por fase já existentes.

## EV Cleaner

Na loja, aba **Treino**, **EV Cleaner** custa **2.000**. É um consumível usado pela mochila em um Pokémon: confirme para zerar os seis EVs e recalcular os atributos. Preserva IVs, Nature, nível, golpes e item equipado. Cancelar ou escolher um Pokémon sem EVs não consome o item; ovos não podem recebê-lo. Seu nome permanece EV Cleaner em ambos os idiomas.

## Verificação e manutenção da localização

`game/Data/blue-ui-validation.txt` registra a verificação na engine: atalhos nos dois menus, mensagem de erro com turbo, painel de campo, consumo do item, preço, nomes preservados, opção de idioma, persistência em memória e índices das escolhas. O laboratório mantém a campanha isolada durante os testes.

`scripts/localization/catalog.py` extrai texto de `messages_core.dat`, `messages_game.dat`, mapas e eventos comuns sem regravá-los. `translate.py` é uma ferramenta opcional de autoria; seus modelos e dependências não entram no download do jogo. `data/pt-br.json` é a tabela própria distribuída. O compilador `scripts/localization/install.py` a converte para `game/Data/blue-pt-br.dat` dentro da transação de instalação com backup e rollback.

O trabalho de tradução usa [OPUS-MT, Helsinki-NLP](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-pt), modelo com licença [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), e sua [conversão CTranslate2 int8 por Playto](https://huggingface.co/playto-mt/opus-mt-tc-big-en-pt-ct2), revisão `86bd3fee2b37851b8eb86747c1078b885f5808fd`. Referência do projeto: Jörg Tiedemann e Santhosh Thottingal, *OPUS-MT – Building open translation services for the World* (EAMT 2020). As mensagens fundamentais da interface recebem revisão manual no módulo `BlueLocale::MANUAL`.

Parte do catálogo utiliza também [Helsinki-NLP/opus-mt-en-ROMANCE](https://huggingface.co/Helsinki-NLP/opus-mt-en-ROMANCE), com alvo `pt_br` e licença Apache 2.0, pela [conversão CTranslate2 de Michael Feil](https://huggingface.co/michaelfeil/ct2fast-opus-mt-en-ROMANCE), revisão `d62d0b4a730ec5f0275877c6df91698c0b7627f3`. Os pesos dos dois modelos ficam apenas no ambiente de autoria e não são redistribuídos no pacote do jogo.
