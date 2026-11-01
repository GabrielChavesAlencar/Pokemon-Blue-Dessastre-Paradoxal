# Battle Mode, mecânicas e sprites

## Poké Bola Dessastre Paradoxal

No jogo normal (`JOGAR.bat`), visite Testing Paradise ou Battle Paradise 130, 230, 330 ou 430. A Poké Bola nova fica próxima do gerador da geração 9, preferindo **32,24**, à direita. O plugin verifica o terreno e usa uma posição livre em até quatro tiles de distância nos dois eixos se necessário. Abre o menu **BLUE / Battle Mode**, também disponível no menu de pausa em **Opcoes de batalha Blue**.

O acesso considera que a Poké Bola pode ficar sobre uma mesa: o jogador precisa alcançar o piso ao lado para interagir, sem precisar pisar sobre ela. O teste também confere que o acesso ao gerador original da geração 9 continua livre.

O gerador oferece 52 espécies prontas e 12 opções de Mega, com nível entre 1 e 100, IVs 31 e EVs 0. Uma escolha de Mega gera a espécie-base com sua pedra DP equipada, para testar a ativação. Os sete cadastros sem atributos não aparecem. Se a equipe estiver cheia, é possível confirmar o envio ao PC ou cancelar, sem apagar integrantes.

Os eventos são acrescentados apenas aos mapas em memória; os arquivos `MapXXX.rxdata` originais não são regravados. Feche o jogo ao instalar o plugin e reentre na área ao reabrir.

## Mecânicas independentes

Escolha **Mecanicas de batalha** no menu Blue, ou **Mecanicas: Terastal / Dynamax / Mega / Z** no laboratório. Cada mecânica pode ser ativada ou desativada separadamente. As regras valem para ambos os lados na próxima batalha; o menu também permite ativar ou desativar todas.

Desativar bloqueia elegibilidade, registro e as chamadas de transformação por scripts. Ativar mantém os requisitos normais de espécie, item e mapa. Não altera os switches numerados do fangame. As preferências de Battle Mode ficam nas configurações do jogo e só se aplicam às cinco áreas listadas; as escolhas do laboratório são independentes e temporárias.

O laboratório fornece Mega Ring, Dynamax Band, Z-Ring e Tera Orb para os testes dos dois lados. Pedras/cristais ainda devem ser equipados nos Pokémon. O Tera Orb é recarregado entre testes e Dynamax pode ser testado fora de Power Spots. Se Mega estiver desativada, uma forma Mega selecionada diretamente é revertida apenas na cópia usada pela batalha, preservando o time editado.

## Qualidade dos sprites

Disponível no menu Blue, no laboratório e nas opções normais em **Sprites Blue**.

| Modo | Resolução dos quadros em memória | Animação |
|---|---|---|
| Original | Original, com suas métricas | Todos os quadros |
| Leve | Até 128 px no maior lado | Até 24 quadros distribuídos pelo ciclo |
| Econômico | Até 96 px no maior lado | Primeiro quadro estático |

O tamanho na tela e as posições são mantidos; quadros menores são ampliados ao exibir. Vale para novos carregamentos: reabra a batalha/ficha para atualizar sprites já carregados. Escolher Original restaura a qualidade completa. Se as animações estiverem desligadas nas opções da base, os modos reduzidos mantêm somente o primeiro quadro.

Os PNG/GIF originais não mudam. Formas que pintam pixels específicos, como Spinda, mantêm seu pipeline nativo. O decoder ainda lê a origem; a economia se concentra nas cópias de quadros mantidas pelo sistema animado. No teste com Great Tusk, quadros e bitmap de exibição usaram **23.817.920 bytes** no original, **1.726.528** no leve e **190.528** no econômico. Esses valores não representam toda a memória do jogo nem uma medição de FPS.

## Instalação e diagnóstico

Abrir `TESTAR_BATALHA.bat` instala os plugins próprios. Para instalar sem abrir o laboratório: `python scripts/battle_lab/launch.py --install-only`; depois abra `JOGAR.bat`.

O atalho procura Python 3.10+ no PATH e nas instalações locais do Windows. O launcher aguarda um novo `MENU_READY` antes de declarar sucesso e permanece ativo até você fechar o jogo. **Mantenha o CMD aberto enquanto joga; pode minimizá-lo.** Isso evita que lançadores que agrupam os processos encerrem o jogo quando o processo pai termina. Erros de inicialização ficam em `game/Data/blue-battle-launcher.log`; o laboratório registra seu estado em `game/Data/blue-battle-lab.log`.

O atalho usa o caminho real do interpretador, validado por uma saída de identificação; não depende apenas do código de saída de um alias. Seu diagnóstico inicial fica em `.blue-work/battle-launcher-cmd.log`, mesmo antes de iniciar Python. O executável abre sem o argumento nativo `debug`, evitando o console separado; a solicitação do laboratório ativa o compilador Ruby no bootstrap do jogo.

Na abertura normal do `.bat`, Python apenas instala/prepara os plugins. O CMD usa `start /WAIT` para abrir o executável diretamente no diretório do jogo, pelo mesmo mecanismo de `JOGAR.bat`. O log do CMD registra o código de saída nativo. A execução por argumentos de diagnóstico continua disponível pelo launcher Python.

O smoke test verifica menus, regras independentes, bloqueio/reativação nos dois lados, gerador, eventos nos cinco mapas, integridade dos arquivos originais, redução de memória, Spinda e retorno à qualidade original. O relatório `game/Data/blue-battle-options-validation.txt` deve terminar em `RESULT=PASS`; as batalhas completas devem terminar em `SMOKE=PASS` no log do laboratório.
