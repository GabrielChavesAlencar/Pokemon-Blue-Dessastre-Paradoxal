# Atualizações incrementais Android — Decades e Kanto

Estado: **implementação no código-fonte; lançamento sujeito à compilação e verificação dos respectivos workflows**.

Os dois canais são **independentes**:
- **Decades principal:** `Blue-Android-JoiPlay.zip`, pasta `Pokemon-Blue-Android/`, release `battle-hub-*`.
- **Kanto piloto:** `Blue-Android-Kanto-Piloto.zip`, pasta `Pokemon-Blue-Kanto-Android/`, prerelease `kanto-android-*`.
- Johto **não faz parte** desse mecanismo enquanto não existir um piloto regional autorizado e publicado.

Ambos continuam sendo jogos RPG Maker XP para **JoiPlay + RPG Maker Plugin**, não APKs nativos. As versões atualizadas incluem, na raiz da pasta instalada, `ATUALIZAR-ANDROID.py` e `Data/blue-update.json`. O aplicativo JoiPlay **não aplica patches dentro do jogo**: o menu **Atualizações Android** mostra a revisão e encaminha para o atualizador externo. O Python/Termux realmente consulta a GitHub Release, baixa e aplica as diferenças.

## Primeira instalação / migração obrigatória

A geração anterior dos ZIPs **não contém o atualizador nem o inventário de arquivos**, portanto precisa fazer **uma instalação completa** do próximo ZIP distribuído pelo canal correto. **Não extraia a nova instalação por cima da anterior.** Faça backup dos saves usando a opção `Onde fica meu save?` no Decades; no Kanto, respeite o perfil Kanto Piloto. Mantenha cópias dos arquivos `File A-H.rxdata`, `Auto 1-3.rxdata`, `Game.rxdata` e `.bak` existentes, inclusive se estiverem no diretório de saves configurado no JoiPlay.

Após essa migração, alterações dos próximos builds poderão ser baixadas de forma incremental quando houver patch direto compatível. Se pular uma ou mais versões, ou se ocorrer alteração do executável, configuração mkxp ou outro arquivo crítico, o atualizador pedirá um **ZIP completo** — não fará uma atualização potencialmente perigosa.

## No Android: verificar e instalar

1. Instale o **Termux** por uma fonte oficial/confiável e inicie-o. A instalação de Python é necessária **apenas para atualizar**, não para jogar no JoiPlay.
2. Execute `pkg install python` e `termux-setup-storage`; permita acesso ao armazenamento compartilhado.
3. Extraia o jogo em uma pasta acessível pelo armazenamento compartilhado, por exemplo `Download/Pokemon-Blue-Android` ou `Download/Pokemon-Blue-Kanto-Android`. Pastas privadas de outros aplicativos podem não ser acessíveis ao Termux.
4. Feche o JoiPlay **completamente** antes de qualquer instalação.
5. No Termux, entre na **pasta exata da sua instalação** e execute:

```sh
# Exemplo Decades; para Kanto troque a pasta por Pokemon-Blue-Kanto-Android.
cd ~/storage/shared/Download/Pokemon-Blue-Android
python ATUALIZAR-ANDROID.py
# Se o patch for oferecido:
python ATUALIZAR-ANDROID.py --update
```

O primeiro comando consulta a versão disponível; o segundo baixa o patch e aplica somente se o canal, a revisão de origem e o inventário coincidirem. Abra depois o mesmo `Game.exe` no JoiPlay.

## Como funciona tecnicamente

Cada ZIP completo inclui `Data/blue-update.json` com canal, SHA-40 de revisão, caminhos e SHA-256 dos arquivos rastreados. Arquivos críticos de raiz (como `Game.exe`, `mkxp.json` e o atualizador) ficam em `immutable` e só podem mudar por reinstalação completa. **Exceção importante:** `Kanto pilot.json` é metadado de mapas/eventos, não configuração de saves, e pode ser incluído no patch regional com SHA-256. A etapa de release publica `Blue-Android-{JoiPlay|Kanto-Piloto}.update.json` e, quando a versão anterior dispõe de manifesto e o patch é útil, `Blue-Android-{JoiPlay|Kanto-Piloto}.patch.zip`.

O atualizador consulta `releases/latest` (Decades) ou a prerelease `kanto-android-*` mais recente dentre as 100 releases (Kanto), sem confundir os downloads. Confere SHA-256, tamanhos, nomes dos arquivos, origem/destino, inventário local e possíveis modificações do usuário. Nunca aplica caminhos fora das pastas permitidas e proíbe arquivos de save, logs e backup. Mantém os arquivos substituídos em `.blue-android-update-backups/<revisão-antiga>-to-<nova>/` e tenta restaurá-los se ocorrer falha durante a aplicação. Antes da atualização, **também faça uma cópia manual do seu save**: backups de arquivos do jogo não substituem backup de progresso.

O patch atual é **de uma revisão publicada para a próxima**, não um sincronizador arbitrário de qualquer versão antiga. Se não houver patch adequado, o programa oferece o link do ZIP completo e não altera a instalação. Não há promessa de atualização em segundo plano, APK próprio, autoatualização do JoiPlay ou teste aprovado em aparelho físico.

## Publicação e testes

- `scripts/android/build_manifest.py`: inventário por canal e compatibilidade imutável.
- `scripts/android/package.py`: instalação completa do Decades.
- `scripts/android/package_kanto.py`: instalação completa isolada do Kanto.
- `scripts/android/publish_updates.py`: manifesto público + ZIP incremental verificado.
- `scripts/android/update_client.py`: cliente Termux/Python, incorporado como `ATUALIZAR-ANDROID.py`.
- `tests/test_android_updates.py`: testes de atualizações, segurança e isolamento.
- `.github/workflows/battle-hub-release.yml`: publica Decades e os ativos do canal.
- `.github/workflows/kanto-pilot-check.yml`: publica Kanto como prerelease separada, após testes nativos e compilação; requer `[android-kanto-release]` no commit.

Nenhuma publicação deve ser considerada pronta antes de o workflow correspondente terminar com sucesso e os assets aparecerem na release. Os testes automatizados de ZIP **não substituem** um teste real no Android, especialmente a concessão de acesso ao armazenamento pelo Termux e a retomada dos saves no JoiPlay.

## Publicação inicial dos novos canais

A primeira release com inventário é a **linha de base** de atualizações. Os ZIPs Android antigos não possuem `Data/blue-update.json` e exigem instalação completa separada. A geração de patch começa a partir da **segunda** release compatível do mesmo canal. O código nunca promove ZIP antigo do Kanto como se fosse Decades ou vice-versa.

Checklist de release: testes Python e Ruby aprovados, compilação nativa e revisão `Revision` validadas, checksum do ZIP conferido, manifesto `.update.json` publicado na release certa, teste em aparelho Android real e verificação de reabertura do save (o último item é manual e pode permanecer pendente). A presença dos arquivos no GitHub não significa que houve teste manual em dispositivo.

## Primeira release verificada com atualizador

O **Kanto piloto** foi publicado na prerelease [kanto-android-670-20089a5](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/kanto-android-670-20089a5), com `Blue-Android-Kanto-Piloto.zip` e `Blue-Android-Kanto-Piloto.update.json`. Trata-se da primeira base do canal, por isso **ainda não há patch incremental desta versão antiga para ela**. A próxima publicação compatível poderá usar essa revisão como origem.

O workflow da versão principal Decades deve publicar `Blue-Android-JoiPlay.zip` e o manifesto `Blue-Android-JoiPlay.update.json` juntos. Se o token GitHub recusar a publicação de uma execução antiga por divergência nos arquivos do workflow, rode uma build da `main` atual. **Nunca ajuste `target_commitish` para outra versão do código só para contornar o bloqueio:** a revisão publicada deve corresponder ao ZIP gerado.
