# Android multirregional: atualização de Kanto pela fonte

A compilação desta atualização usa a instalação multirregional existente e
baixa somente a fonte de Kanto necessária à etapa do endereço do autor original,
com SHA-256 conferido. A receita não publica ou baixa um ZIP multirregional,
não redistribui a fonte nem os arquivos de Hoenn e não reinstala o jogo.

## Etapa K05, Lavender

A edição de partida verificada no GitHub Actions é a multirregional 247.
Esta receita não se aplica ao Decades isolado, ao piloto Kanto ou a pastas
modificadas. A revisão funcional é
`0eaf9401b2d9e828e8549f7c7fea28c5de748157`, a mesma da versão Windows 1634;
o marcador também registra a revisão da receita e o hash do inventário local.
O teste automatizado do compilador é em Windows. Não equivale a teste no JoiPlay
de um dispositivo Android.

### Usar o atualizador no Termux

Use a revisão exata da receita indicada no lançamento de K05 pela fonte.
A pasta da receita fica no armazenamento privado do Termux; a cópia de
compilação precisa ficar no armazenamento compartilhado para o JoiPlay abri-la.
O Termux precisa ter acesso ao diretório do jogo.

1. No Termux, com Python, Git e `bsdtar` disponíveis, obtenha o código da
   receita publicado no repositório oficial do projeto. Use o destino
   `$HOME/.cache/pokemon-blue-android/k05` para que o atualizador instalado
   encontre a receita. A receita confere a ancestralidade e os arquivos
   rastreados; não aponte para a versão flutuante de `main`.
2. Feche o JoiPlay. No comando a seguir, troque `/caminho/do/jogo` pela
   pasta multirregional já instalada. O comando sem `--update` somente
   confere a instalação, sem baixar ou copiar arquivos:

   ```sh
   python "$HOME/.cache/pokemon-blue-android/k05/scripts/android/update_client.py" \
     --game-dir "/caminho/do/jogo" --source
   ```

3. Repita com `--source --update`. A primeira execução monta uma cópia
   separada, em uma pasta `-Compilar-K05` ao lado do jogo. Não substitua o
   jogo principal pelo atalho temporário. Adicione no JoiPlay a cópia
   impressa pelo atualizador como um jogo separado e inicie apenas para
   compilar, sem abrir nenhum save.
4. Quando a compilação terminar, feche o JoiPlay e execute o mesmo comando
   com `--source --update` novamente. O atualizador só aplica a cópia
   compilada, verifica os arquivos e mapas de Hoenn e atualiza a revisão
   por último. Se falhar, não use `--full` ou um patch binário para
   contornar a verificação. A atualização final aceita apenas o conjunto
   de arquivos necessário a Kanto.

Se o Termux fechar durante a instalação, mantenha o JoiPlay fechado e rode
o mesmo comando de atualização novamente, com a mesma pasta de compilação.
O atualizador confere o registro da instalação interrompida e retoma a partir
dos arquivos verificados. Não apague a pasta temporária se houver erro.

Após o êxito, abra o atalho original do jogo. O novo `ATUALIZAR-ANDROID.py`
da pasta instalada reconhece `--source` e a receita no cache acima. Uma
receita de etapa posterior deve validar o inventário local produzido pela
receita anterior; o atualizador não assume que um patch binário comum
corresponda a essa instalação.
