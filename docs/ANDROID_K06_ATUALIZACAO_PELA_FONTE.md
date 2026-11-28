# Android K06: passagem de Lavender a Celadon

O primeiro lote K06 conecta Lavender à Rota 8, Passagem Subterrânea,
Rota 7 e Celadon. As duas portarias de Saffron continuam fechadas.
Não libera Game Corner, o esconderijo da Rocket ou a conclusão da Torre
Pokémon. São sete mapas antes em prévia, com os mesmos IDs e a mesma
instalação e perfil de saves.

## Pré-requisito

Esta receita suporta a instalação **multirregional K05 já atualizada pela
fonte**, a partir da edição 247 testada. Caso tenha a 247 sem K05, use
[primeiro a receita publicada de Lavender](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/android-source-k05-0eaf940).
Em uma edição multirregional mais antiga, use primeiro apenas o caminho de
atualização oficial para a [edição 247](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/android-multiregion-247-02732ea).
A receita K06 não tenta migrar diretamente uma edição mais antiga,
Decades isolado ou Kanto piloto. Não use um ZIP ou patch de outro canal.

## Rodar no Termux

1. Feche o JoiPlay. Com Python, Git e `bsdtar` no Termux, obtenha a
   receita exata indicada na release oficial de K06. Use o cache separado
   `$HOME/.cache/pokemon-blue-android/k06`, sem substituir a pasta `k05`.
2. Pela primeira vez, use o atualizador que vem na receita nova, não
   o script antigo da pasta do jogo:

   ```sh
   python "$HOME/.cache/pokemon-blue-android/k06/scripts/android/update_client.py" \
     --game-dir "/caminho/do/jogo" --source --source-stage k06 --update
   ```

   Sem `--update` o comando apenas confere o estado. O Termux precisa
   ter acesso à pasta original do jogo no armazenamento compartilhado.
3. Adicione **apenas a cópia temporária** indicada pelo comando ao JoiPlay
   como outro jogo, só para compilar. Não carregue saves nessa cópia.
4. Feche o JoiPlay e repita o comando anterior. O atualizador só altera
   os arquivos necessários depois de validar a compilação. Se o Termux
   for fechado durante a instalação, mantenha a pasta de compilação e
   execute o mesmo comando novamente com o JoiPlay fechado.
5. Quando terminar, use o atalho original no JoiPlay. O atualizador
   instalado reconhece a receita K06 nesse cache.

O projeto publica só a receita e as instruções. O arquivo original de
Kanto é baixado do autor com SHA-256 verificado, não de um novo ZIP do
jogo. A compilação automática é verificada em Windows; não substitui o
teste no aparelho Android.
