# Editor de músicas

Abra `RUN.bat` e escolha **Editor de ROM → Músicas**. A biblioteca usa os arquivos locais de `game/Audio/BGM`; a prévia não precisa abrir o jogo. Selecione uma faixa e clique **Usar esta faixa**, escolha o destino e clique **Aplicar música**.

Os destinos são batalhas selvagens, treinadores, líderes de ginásio/Mestres de Tipo, músicas de vitória e cada cidade/mapa instalado. Os mapas aparecem com o nome do RPG Maker e seu ID. **Música original do jogo** remove a escolha personalizada; **Sem música** silencia o destino. Faixas personalizadas e sorteios oferecem volume de 0 a 100% e tom/velocidade de 50 a 150%. Reabra o jogo depois de aplicar. Eventos da história que definem explicitamente a próxima música têm prioridade sobre os modos de faixa fixa e silêncio.

## Sorteio por batalha

Selvagens, treinadores e líderes possuem listas independentes. Escolha o destino, selecione **Sortear uma faixa por batalha**, marque as músicas da lista (Ctrl/clique permite selecionar várias no computador) e aplique. O jogo escolhe uma faixa antes da batalha e mantém essa escolha durante toda a luta, inclusive em duplas e nas consultas repetidas da introdução. Na próxima batalha há outro sorteio; quando existem duas ou mais faixas disponíveis, a última não se repete imediatamente. O sorteio usa um gerador separado dos cálculos de combate.

Neste modo, a lista escolhida substitui também temas fixos definidos pelos eventos da campanha para essa categoria. As vitórias e cidades continuam com suas próprias configurações. Arquivos ausentes são ignorados; se nenhuma faixa da lista existir, o jogo usa a música original. Selecionar **Música original do jogo** restaura os temas da base para aquela categoria.

A coleção inicial contém **7 músicas de treinador, 6 de encontros selvagens e 6 de líderes**. A classificação reconhece os tipos de treinador dos líderes e os 18 Mestres de Tipo da campanha pelo par classe/nome; outros treinadores da mesma classe continuam na lista comum. Em duplas com um líder, vale a lista de líderes.

Para reproduzir a importação em outra instalação local, organize as músicas em `musicas de pokemon/batalha treinador`, `musicas de pokemon/encontros selvagens` e `musicas de pokemon/gym leader`. Na raiz do projeto, execute:

```powershell
python scripts/music/import_playlists.py --source-dir "C:\Users\cagab\Downloads\musicas de pokemon"
python scripts/music/import_playlists.py --source-dir "C:\Users\cagab\Downloads\musicas de pokemon" --apply
```

A primeira execução apenas mostra o plano. A segunda valida todas as pastas, copia os áudios para `game/Audio/BGM/BlueRandom/`, instala o plugin e ativa as três listas, com backup e reversão em caso de falha. A importação local aceita arquivos de até 128 MB, sem conversão; o limite de envio pelo navegador continua em 20 MB. Reexecutar com os mesmos arquivos não cria cópias extras. Mapas, vitórias e áudios originais são preservados.

## Importar e substituir

Escolha WAV, OGG, MP3 ou MIDI de até 20 MB e informe um nome para importar. Nenhum áudio é convertido. MIDI funciona no jogo, mas não possui prévia no navegador. Alguns codecs de OGG/MP3 dependem do suporte do navegador e da engine.

Para trocar um arquivo existente, selecione a faixa na biblioteca e marque **Substituir a faixa selecionada**. Isso muda todos os locais que já usam o mesmo arquivo. A gravação exige o hash atual e mantém um backup do arquivo anterior. Se houver alteração concorrente, atualize a biblioteca antes de tentar novamente.

## Armazenamento e reversão

As escolhas ficam em `game/Data/blue-music.json` e em sua versão de leitura pelo jogo, `blue-music.rxdata`. O plugin próprio `scripts/music/BlueMusic.rb` aplica a escolha aos dados do mapa apenas em memória. Os mapas `MapXXX.rxdata`, eventos e PBS originais não são regravados pelo editor de músicas. A instalação do laboratório também instala esse plugin; a primeira abertura após mudança no plugin pode recompilá-lo.

Backups ficam em `.blue-backups/`, incluindo as configurações anteriores e os áudios substituídos. Para restaurar a música de um destino, selecione **Música original do jogo** e aplique. Para desfazer a substituição de um arquivo, reimporte o áudio do backup com a opção de substituição.

As faixas originais, áudios importados, configurações locais e backups ficam fora do GitHub. O repositório publica o editor, o plugin, o importador e `data/battle-music-playlists.json`, que registra nomes, categorias e hashes da coleção sem conter áudio. Não é necessário serviço de streaming, chave de API ou acesso à internet para editar a biblioteca instalada.

## Verificações

`python -m unittest discover -s tests` verifica leitura inerte de Marshal, gravação com reversão, arquivos originais preservados, importação, substituição, proteção contra caminhos externos, conflitos e streaming com Range. `node tests/browser_music_smoke.cjs` verifica o fluxo em Chromium com mapas e WAV sintéticos. O GitHub Actions executa ambos.

`python scripts/battle_lab/launch.py --smoke-test` também valida os hooks de música no motor real. O relatório `game/Data/blue-music-validation.txt` deve terminar em `RESULT=PASS`. Se houver coleção importada, verifica classificação, repetição, preparação da batalha e reprodução de todas as faixas pelo decodificador nativo, com volume zero. O teste usa configurações temporárias em memória e não muda as escolhas de música da campanha.
