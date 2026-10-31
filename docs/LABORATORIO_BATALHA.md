# Laboratório de Batalha local

Na pasta principal do projeto, abra **TESTAR_BATALHA.bat**. É uma sessão limitada do jogo real, com times de **1 a 6 Pokémon por lado** e batalhas **individuais ou em dupla**, usando a engine, os sprites, as animações e os dados compilados da base instalada em `game/`.

## Usar

- A sessão começa com dois times de seis no nível 50. Com a geração autoral instalada, inclui Cave Fang, Archgutor, Iron Crusher e outros Pokémon do projeto. Também há um preset de times oficiais e um teste rápido Pikachu x Eevee.
- Em **Editar meu time** ou **Editar time rival**, selecione um dos seis espaços para editar ou adicionar um integrante. Os times ficam compactos, sem espaços vazios entre os integrantes.
- Cada integrante permite trocar espécie/forma, nível, quatro golpes, habilidade e item; retirar item; mover para a primeira posição; ou remover do time. O último integrante não pode ser removido.
- Os primeiros integrantes entram em campo. Em dupla, os dois primeiros de cada lado são enviados; é necessário ter pelo menos dois Pokémon em cada time. Os reservas participam pelas trocas e substituições normais da engine.
- O catálogo permite escolher **Dessastre Paradoxal** ou o catálogo completo. As sete espécies pendentes não são liberadas para combate.
- As opções de habilidade e item permitem testar Mega Sol e equipar as pedras DP; o Mega Ring é fornecido temporariamente.
- Ajuste o nível individualmente ou use **Nivel de todos**, entre 1 e 100. Ao mudar o nível, os golpes voltam aos quatro últimos aprendidos naquele nível.
- A edição de golpes é livre para experimentos e não valida a legalidade competitiva do moveset.
- Em **Formato**, escolha **Individual** (um Pokémon em campo por lado) ou **Dupla** (dois em campo por lado), depois **Iniciar batalha**. Mesmo a batalha individual pode usar times completos de seis.
- Em **IA**, compare **IA da base**, **Blue estrategica** e **Blue Radical**. A opção Blue Radical é o padrão e usa avaliação de dano, trocas, suporte e duplas inspirada nos princípios públicos do CFRU. [Funcionamento e validação](IA_BLUE_RADICAL.md).
- Ao terminar, você volta ao laboratório. Os times configurados são preservados: a batalha usa cópias, incluindo itens, formas, golpes, PP e ordem dos integrantes.
- Escolha **Sair do laboratorio** para fechar. Para jogar a campanha normalmente, abra **JOGAR.bat**.

A sessão usa IVs 31, EVs 0 e natureza neutra. Não concede experiência ou dinheiro e bloqueia Poké Balls. A interface da batalha mantém o idioma da base do fangame.

## Mouse e HP

- Clique esquerdo seleciona e confirma uma opção visível nos menus, catálogos, comandos de batalha, golpes, alvos e integrantes na tela de troca. Botões visíveis de Mega Evolução e Shift também aceitam clique.
- Clique direito volta/cancela onde a tela permite. Setas e teclas de confirmação continuam disponíveis.
- Os menus do laboratório oferecem **Pagina anterior**, **Proxima pagina** e **Voltar** no rodapé para navegar sem as setas. Nos catálogos originais, PgUp/PgDn continuam disponíveis.
- Cliques fora das opções não confirmam a seleção atual; espaços sem golpe e alvos inválidos são ignorados. Telas auxiliares da engine, como resumo detalhado e mochila, conservam seus controles próprios.
- A duração da animação da barra de HP foi restaurada de zero para **um segundo**, para redução e recuperação. A engine continua controlando números, cores e eventos de HP. Essa correção também vale para a campanha na instalação local; o mouse fica restrito ao laboratório.

## Testar Pokémon e golpes que você criou

Cadastre/edite a espécie no Blue Studio, salve os PBS e abra o laboratório. Ele inicia em modo debug para permitir a compilação necessária. Aguarde a primeira carga e eventuais mensagens do compilador. Uma espécie só entra no catálogo quando a compilação termina com sucesso; o editor salvar o PBS não prova que ela foi compilada. Os sprites e métricas precisam estar instalados na base local. Não é necessário criar uma segunda cópia do jogo.

O laboratório não cria automaticamente Fakémon ou sprites. Ele permite testar as espécies e formas registradas, incluindo as que você cadastrar no editor.

## Isolamento e instalação

O lançador copia apenas o plugin original deste projeto para `game/Plugins/ZZZZ Blue Battle Lab/`. Um pequeno bootstrap optativo é acrescentado ao script `Main` da engine, com backup em `.blue-backups/battle-lab/`. Os outros scripts, mapas e eventos são preservados. O laboratório inicializa um jogador temporário em memória e bloqueia as rotinas de leitura e gravação de save, incluindo autosave; não abre a campanha.

Uma solicitação de abertura vale por 120 segundos e é consumida uma vez. A abertura normal continua sendo a campanha. O atalho precisa ser executado novamente para outra sessão do laboratório. Os arquivos do jogo e os backups continuam ignorados no Git.

Diagnóstico: `game/Data/blue-battle-lab.log`. O teste automatizado usa a mesma cena de batalha, com a IA comandando os dois lados e as confirmações de texto desativadas. Confere batalhas individuais e duplas 6 × 6, preservação dos times, os valores intermediários da animação de HP, geração autoral e bloqueio de saves. Pode ser iniciado com `python scripts/battle_lab/launch.py --smoke-test --timeout 240`. No ambiente isolado de automação, o terminal pode não conseguir abrir uma janela visível; o atalho foi feito para ser usado na sua sessão normal do Windows.

## Portal local

Abra **ABRIR_SITE.bat**, aguarde a mensagem do servidor e visite **http://127.0.0.1:4173**. É necessário Node.js 24. Mantenha a janela aberta enquanto usar o portal; Ctrl+C encerra o servidor. A batalha real abre em uma janela separada pelo atalho do laboratório.
