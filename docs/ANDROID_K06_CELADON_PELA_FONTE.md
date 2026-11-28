# Android K06: loja e interiores de Celadon pela fonte

Este lote abre a loja de departamentos, suas escadas, elevador e terraço,
além de quatro interiores de Celadon. Saffron continua fechada e este
lote não libera o Game Corner, o esconderijo ou a Silph Scope.

## Antes de atualizar

É preciso ter a [passagem K06 oficial instalada pela fonte](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/android-source-k06-approach-791f8c8).
Se estiver no K05, use primeiro a receita da passagem; se estiver em
edição anterior, siga apenas a cadeia multirregional oficial indicada
na receita anterior. Não reinstale nem troque de canal.

1. Feche o JoiPlay. Tenha Git, Python e `bsdtar` no Termux, com acesso
   à pasta exata do seu jogo. Clone e confira a receita oficial indicada
   na release de Celadon no cache separado
   `$HOME/.cache/pokemon-blue-android/k06-services`. Não substitua os
   caches anteriores de Lavender e da passagem.
2. Confira a instalação sem alterar arquivos:

   ```sh
   python "$HOME/.cache/pokemon-blue-android/k06-services/scripts/android/update_client.py" \
     --game-dir "/caminho/do/jogo" --source --source-stage k06-services
   ```

3. Repita com `--update`. O atualizador busca a fonte original e verifica
   o SHA-256 antes de preparar uma cópia temporária. Abra **só a cópia
   indicada** no JoiPlay para compilar. Não carregue nenhum save nela.
4. Feche o JoiPlay e repita o mesmo comando com `--update`. Depois da
   confirmação, use o atalho original no JoiPlay. Se for interrompido,
   mantenha a pasta temporária e repita o comando com o jogo fechado.

A release não inclui ZIP, patch binário, arquivo de jogo ou save. A
qualificação automatizada valida a compilação e a atualização de uma
instalação descartável, com saves e outras regiões preservados. O teste
físico no Android fica separado.
