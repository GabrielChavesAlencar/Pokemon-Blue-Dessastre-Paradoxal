# Blue — Hub de Batalha

**[⬇ Baixar somente o Hub de Batalha para Windows](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/latest/download/Blue-Battle-Hub.zip)** · [Releases e SHA-256](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases)

Um minijogo local contra a IA, com montador inteiro dentro da janela do jogo, inspirado na facilidade do teambuilder do Pokémon Showdown. A batalha usa a engine real do Blue, incluindo a geração Dessastre Paradoxal. Você configura seu time e o adversário, joga em individual ou dupla e volta ao montador após a luta. O Hub não carrega nem salva a campanha.

## Instalar o pacote separado

1. Instale [Python 3.10+](https://www.python.org/downloads/windows/) e [Git para Windows](https://git-scm.com/downloads/win).
2. Baixe o ZIP pelo botão acima e escolha **Extrair tudo**. Não execute de dentro do arquivo ZIP.
3. Abra **`INSTALAR_HUB.bat`** na pasta extraída. Mantenha o CMD aberto até aparecer **Hub instalado**. A primeira instalação baixa a base do jogo e as referências; pode demorar.
4. Abra **`HUB_DE_BATALHA.bat`**. Aguarde a compilação na primeira abertura. O atalho antigo **`TESTAR_BATALHA.bat`** também abre o Hub.

O pacote separado contém somente os módulos do Hub, instaladores, dados e sprites/cries autorais necessários. Não inclui o Blue Studio nem o portal. Os arquivos originais do Decades são obtidos separadamente pelo instalador; por isso o ZIP pequeno não representa o tamanho total da instalação. Não precisa de navegador, Node ou RPG Maker XP para jogar. A conexão é necessária para instalar e para buscar links PokéPaste; a montagem e as batalhas funcionam localmente.

Enquanto o repositório for privado, o download exige acesso autorizado no GitHub. O mesmo link fica público quando o autor tornar o projeto público. A versão inicial do Hub oferece batalhas contra IA; não há salas, contas ou multiplayer online nesta etapa.

## Montar os times

Use **MEU TIME** e **ADVERSÁRIO** para alternar os lados. Cada um tem até seis integrantes; os primeiros entram em campo. Clique em um slot vazio para adicionar, ou em um integrante para editar.

- **Pokémon:** busca por nome, identificador, tipo ou habilidade; formas, atributos base e BST aparecem na tabela. O filtro **Dessastre Paradoxal** mostra a geração especial. Megas são preparadas com a forma base e a pedra exigida pela engine, para transformar durante a batalha.
- **Item e habilidade:** clique no campo e escolha na lista. As habilidades são as disponíveis para a espécie. É possível retirar o item.
- **Golpes:** clique em um dos quatro campos. A lista começa pelo learnset da espécie, com tipo, categoria, poder, precisão, PP e descrição. **Todos (livre)** permite combinações para testes, mesmo fora do learnset. Golpes duplicados são recusados.
- **Atributos:** edite Nature, EVs e IVs e veja os atributos finais calculados pelo próprio jogo. Os EVs têm controle por clique/arraste ou número, máximo de 252 por atributo e 510 no total; IVs vão de 0 a 31. Nível, sexo, shiny e Tera Type têm controles próprios. Alterar o nível preserva os golpes escolhidos.
- **Formato, IA e mecânicas:** escolha individual ou dupla, perfil da IA e controles de Terastal, Dynamax, Mega e Z-Moves. Duplas precisam de pelo menos dois integrantes por time. A qualidade dos sprites continua disponível nas opções.

**BATALHAR** abre a luta no tamanho normal da engine. Ao terminar, você volta ao montador com os times preservados. A tela do montador usa uma resolução própria; a campanha e as batalhas conservam sua resolução normal.

## Importar PokéPaste ou texto do Showdown

Escolha primeiro **MEU TIME** ou **ADVERSÁRIO** e clique **Importar**:

- **Colar time ou link:** copie o texto exportado do Showdown ou um link como `https://pokepast.es/bf2e74c7e8b615a6`, depois escolha essa opção no Hub.
- **Digitar link Pokepaste:** digite o endereço ou use Ctrl+V no campo. Enter confirma e Esc cancela.

O download acontece com uma tela de progresso. A importação mostra a prévia antes de substituir o time. Se algum Pokémon, golpe, item ou habilidade não existir na instalação, a prévia explica o problema. Você pode cancelar ou confirmar explicitamente apenas os integrantes compatíveis; não há substituições silenciosas de espécies.

As **45 novas Megas de Z-A/Mega Dimension** usam suas próprias pedras, incluindo **Floettite**, **Dragoninite** e as pedras X/Y/Z. Megaite e suas variantes continuam funcionando para os treinadores e itens já existentes na campanha. As Megas antigas que ainda usam Megaite na base continuam sendo adaptadas explicitamente na prévia (por exemplo, Charizardite Y). O exportador preserva o nome da pedra do paste nessas adaptações.

Também são aceitos links do PokéPaste traduzidos pelo Google: o Hub baixa o texto original em inglês, preservando os nomes do Showdown. O download roda em um processo auxiliar Python, enquanto o menu continua ativo. Esc cancela, há limite de tempo e de 64 KB, e as falhas ou a área de transferência vazia mostram uma mensagem antes de voltar ao montador. Nenhum time é substituído sem a confirmação na prévia.

## Novas Mega Evoluções

O catálogo em `data/za-megas.json` aplica os seis atributos, tipos, pedras e habilidades às **45 novas Megas**, com 48 entradas visuais e 50 registros da engine ao incluir sexos de Meowstic e origens de Zygarde. O mesmo instalador atualiza a campanha e o Hub. As demais formas e os Pokémon autorais são preservados.

Os atributos seguem a tabela principal de Z-A do documento fornecido; **Mega Starmie tem Ataque 140/BST 660**, e não a variante de Champions com Ataque 100/BST 620. As habilidades confirmadas seguem o catálogo Champions. Dragonize, Piercing Drill, Eelevate, Fire Mane, Aura Guard e Spicy Spray têm efeitos próprios; Mega Sol reutiliza a implementação de sol pessoal já presente no projeto.

Conforme a escolha do autor, **Zygarde, Heatran, Darkrai, Magearna, Zeraora e Tatsugiri** mantêm as habilidades existentes da base enquanto o catálogo não as confirma. Essas formas aparecem com **[habilidade provisoria]** no Hub. Isso não representa confirmação da habilidade oficial. Os sprites de Pokémon são reutilizados da base instalada. As novas pedras têm IDs individuais; quando não existe arte individual na base, usam temporariamente o ícone local da Megaite.

Os efeitos foram consultados na [implementação primária do Pokémon Showdown](https://github.com/smogon/pokemon-showdown/blob/master/data/abilities.ts). Os dados fornecidos pelo autor e a decisão sobre habilidades provisórias estão registrados no catálogo.

O exemplo fornecido importa os seis integrantes, incluindo Mega Floette. **EVs são preservados literalmente**: um valor `32 Spe` continua sendo 32 EVs; o Hub não o transforma em 252. Nível ausente usa 100. Também são lidos IVs, Nature, habilidade, item, apelido, sexo, shiny, felicidade, Tera Type e os quatro golpes. As listas refletem os dados da engine instalada, que podem diferir do formato competitivo em que o paste foi criado.

## Biblioteca e exportação

A sessão mantém os dois times e as opções ao fechar e reabrir o Hub, em arquivos próprios da instalação. **Salvar** guarda uma cópia do time selecionado na biblioteca; **Biblioteca** carrega uma cópia para qualquer lado. Os arquivos ficam em `game/BlueHub/`, separados do save da campanha. Guarde essa pasta ao atualizar a instalação.

**Exportar** copia o time selecionado em texto Showdown para a área de transferência. Você pode colá-lo em um arquivo, no PokéPaste ou em outro Hub compatível. O Hub só lê a área de transferência quando você escolhe colar ou usa Ctrl+V; exportar modifica a área de transferência de forma explícita.

## Atualizações e validação

A rotina **Hub de Batalha — download separado** cria uma Release com `Blue-Battle-Hub.zip` e seu SHA-256 quando os módulos do Hub são atualizados na `main`. Cada pacote inclui `hub-manifest.json`, com a revisão e os hashes dos arquivos. Para atualizar, feche o jogo, extraia o ZIP novo sobre a pasta do Hub preservando `game/` e `.blue-work/`, e execute `INSTALAR_HUB.bat` novamente.

O pacote não distribui saves, backups, MP3s pessoais, executáveis ou assets originais do fangame. A base usada pelo instalador continua fixada na referência do projeto.

O smoke nativo grava `game/Data/blue-hub-validation.txt`, que deve terminar em **RESULT=PASS**. Ele verifica importação/exportação, pedras Mega, EVs/IVs, erros de dados, todos os painéis e a renderização nativa. O smoke completo também executa batalhas reais individuais/duplas e confirma a proteção do save da campanha. Testes Python verificam o pacote separado, seus hashes, a ausência dos arquivos do jogo e a instalação sem abrir a campanha.
