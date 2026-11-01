# Progressão Story, entradas de batalha e mouse

As regras novas de níveis, inventário inicial e lojas estão em [Economia e jornada](ECONOMIA_E_JORNADA.md). Treinadores comuns agora usam 70% do maior nível do time; bosses e líderes mantêm o escalonamento anterior. As regras de BST descritas abaixo continuam valendo depois do ajuste de nível.

## Traditional Starters

Escolha **Story Mode → Traditional Starters**, primeira opção na seleção de iniciais. A campanha passa a usar o número real de esmeraldas/insígnias do treinador:

| Esmeraldas | Modo | Limite de BST dos adversários |
|---|---|---|
| 0 e 1 | Inicial | 350 |
| 2 e 3 | Intermediário | 450 |
| 4 ou mais | Avançado | Sem limite; equipe original da base |

BST é a soma dos atributos base, não os atributos calculados no nível atual. Pokémon que já cabem no limite permanecem; os que ultrapassam são substituídos. A escolha prioriza pré-evoluções da mesma família, depois tipagem igual, tipo principal e tipos compartilhados. Não tenta preencher todo slot com o máximo permitido. Por exemplo, Charizard vira Charmander no Inicial e Charmeleon no Intermediário; Gyarados pode virar Magikarp nos dois estágios.

O nível escalonado pela base, tamanho/formato do time, natureza e treinamento são mantidos. A substituição ajusta habilidade e golpes à espécie válida e remove pedras Mega incompatíveis. Formas e Megas do adversário que excederiam o teto são bloqueadas enquanto houver limite. Os Pokémon do jogador, parceiros e encontros selvagens não são substituídos. Battle Mode e laboratório usam seus times normais.

As equipes são preparadas em memória, depois do escalonamento de nível. Os PBS de treinadores e os eventos não são regravados. Com quatro esmeraldas, as equipes normais voltam automaticamente. As esmeraldas são lidas quando a próxima luta começa; a segunda e a quarta não alteram uma batalha que já estava em andamento.

Em um save anterior à atualização, abra **Pausa → Progressão / Revanches Blue** no Story Mode e confirme a ativação da progressão. A origem dos iniciais não era registrada pela base; por isso saves antigos não são classificados automaticamente como Traditional Starters.

## Revanches entre estágios

O Decades já permite enfrentar novamente os treinadores pelos eventos normais. Além disso, o menu **Pausa → Progressão / Revanches Blue** registra as vitórias realizadas com a progressão ativa e libera uma revanche quando o modo passa de Inicial para Intermediário ou Avançado. Cada confronto pode ser vencido uma vez por estágio por esse menu. Perder não consome a oportunidade; o histórico é salvo com a campanha e distingue nomes, versões e batalhas contra dois treinadores.

A revanche Blue chama a batalha diretamente, sem executar novamente o evento da história. Ela dá **somente o dinheiro da vitória**, sem EXP, drops de Pickup/Honey Gather, esmeraldas ou recompensas de missão. Não apaga flags de treinadores, quests ou conquistas. Vitórias anteriores à instalação continuam acessíveis pelos treinadores normais, mas não são inventadas no histórico novo.

## Entradas inspiradas no FireRed

- Selvagem: o sprite frontal desliza da esquerda para a posição adversária em aproximadamente dois segundos, sem Poké Ball. O motor mantém cry e brilho shiny.
- Treinador adversário: o treinador sai da tela; a Poké Ball aparece perto da posição de entrada, espera, abre e libera o Pokémon com expansão.
- Jogador: o protagonista faz o arremesso quando seus quadros estão disponíveis; a bola percorre um arco antes de abrir. O sprite de costas permanece escondido até a liberação. Isso também vale para o Pokémon que segue o jogador, cujo caminho anterior pulava a bola.
- Trocas: reutilizam a bola/liberação, sem repetir a apresentação completa do treinador. Duplas possuem atraso entre as liberações. A bola real do Pokémon, a espécie, forma, sprites, métricas e cries da instalação são preservados.

Esta é uma adaptação para Essentials/DBK usando os assets instalados, não a execução do código de GBA. Tempos usam as unidades do `PictureEx` (20 por segundo). Fluxos especiais de introdução DBK e Safari continuam com seu tratamento próprio.

A EXP usa a interpolação nativa, com duração nominal de 1,75 s para encher a barra e mínimo de 0,3 s para um ganho pequeno. Mudanças de nível continuam passando pela animação de barra cheia e pelo fluxo normal de atributos/golpes. Velocidade acelerada configurada no motor pode reduzir o tempo percebido.

## Mouse na campanha

Os controles compartilhados agora funcionam na campanha e no laboratório: listas de comandos/diálogos, botões de batalha, golpes, alvos de duplas e seleção da equipe. Botão direito equivale a voltar. As teclas continuam funcionando. Não é um sistema de caminhar clicando no mapa.

O adaptador aceita tanto menus que atualizam a janela antes de `Input.update` quanto menus que fazem o contrário. Cada clique é consumido uma vez, evitando confirmação acidental no próximo menu.

## Instalação e testes

Abra `ABRIR_JOGO.bat` para preparar os plugins da campanha ou `TESTAR_BATALHA.bat` para o laboratório. Feche o jogo antes de atualizar. Fontes próprias ficam em `scripts/battle_polish/` e `scripts/battle_lab/Interface.rb`; a instalação mantém backup em `.blue-backups/`.

`python -m unittest discover -s tests` valida os instaladores e a preservação de arquivos com dados sintéticos. O smoke do laboratório executa a validação do motor em `game/Data/blue-polish-validation.txt`, que deve terminar em `RESULT=PASS`: limites para todas as espécies/formas com atributos, fronteiras das esmeraldas, golpes das substituições, histórico, regras de recompensa, eventos de escolha, interpolação de EXP e agendas reais de animação.

Referência conceitual: estudo `Animacoes_Entrada_Pokemon_FireRed.md` fornecido pelo autor e rotinas públicas de [pret/pokefirered](https://github.com/pret/pokefirered). Não são publicados assets gráficos, código de engine ou dados de campanha do Decades.
