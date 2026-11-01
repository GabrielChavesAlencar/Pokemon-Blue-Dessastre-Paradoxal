# Editor de músicas

Abra `RUN.bat` e escolha **Editor de ROM → Músicas**. A biblioteca usa os arquivos locais de `game/Audio/BGM`; a prévia não precisa abrir o jogo. Selecione uma faixa e clique **Usar esta faixa**, escolha o destino e clique **Aplicar música**.

Os destinos são batalhas selvagens, treinadores, suas músicas de vitória e cada cidade/mapa instalado. Os mapas aparecem com o nome do RPG Maker e seu ID. **Música original do jogo** remove a escolha personalizada; **Sem música** silencia o destino. Faixas personalizadas oferecem volume de 0 a 100% e tom/velocidade de 50 a 150%. Reabra o jogo depois de aplicar. Eventos da história que definem explicitamente a próxima música de batalha ou vitória têm prioridade.

## Importar e substituir

Escolha WAV, OGG, MP3 ou MIDI de até 20 MB e informe um nome para importar. Nenhum áudio é convertido. MIDI funciona no jogo, mas não possui prévia no navegador. Alguns codecs de OGG/MP3 dependem do suporte do navegador e da engine.

Para trocar um arquivo existente, selecione a faixa na biblioteca e marque **Substituir a faixa selecionada**. Isso muda todos os locais que já usam o mesmo arquivo. A gravação exige o hash atual e mantém um backup do arquivo anterior. Se houver alteração concorrente, atualize a biblioteca antes de tentar novamente.

## Armazenamento e reversão

As escolhas ficam em `game/Data/blue-music.json` e em sua versão de leitura pelo jogo, `blue-music.rxdata`. O plugin próprio `scripts/music/BlueMusic.rb` aplica a escolha aos dados do mapa apenas em memória. Os mapas `MapXXX.rxdata`, eventos e PBS originais não são regravados pelo editor de músicas. A instalação do laboratório também instala esse plugin; a primeira abertura após mudança no plugin pode recompilá-lo.

Backups ficam em `.blue-backups/`, incluindo as configurações anteriores e os áudios substituídos. Para restaurar a música de um destino, selecione **Música original do jogo** e aplique. Para desfazer a substituição de um arquivo, reimporte o áudio do backup com a opção de substituição.

As faixas originais, áudios importados, configurações locais e backups ficam fora do GitHub. O repositório publica somente o editor e o plugin que reproduzem o recurso. Não é necessário serviço de streaming, chave de API ou acesso à internet para editar a biblioteca instalada.

## Verificações

`python -m unittest discover -s tests` verifica leitura inerte de Marshal, gravação com reversão, arquivos originais preservados, importação, substituição, proteção contra caminhos externos, conflitos e streaming com Range. `node tests/browser_music_smoke.cjs` verifica o fluxo em Chromium com mapas e WAV sintéticos. O GitHub Actions executa ambos.

`python scripts/battle_lab/launch.py --smoke-test` também valida os hooks de música no motor real. O relatório `game/Data/blue-music-validation.txt` deve terminar em `RESULT=PASS`. O teste usa uma configuração temporária em memória e não muda as escolhas de música da campanha.
