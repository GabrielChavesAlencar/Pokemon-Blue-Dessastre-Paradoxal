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

No Piloto Kanto, abra **Downloads → Pilotos no Android** no site e confira a revisão publicada. Use a pasta **Pokemon-Blue-Kanto-Android** no Termux. As correções de mapas, eventos e Pokédex chegam por esse canal após a publicação do novo ZIP ou patch. Para alternar a Pokédex, use **K** no teclado ou toque no botão da lista quando os toques do JoiPlay estiverem habilitados.

Patches incrementais exigem origem e inventário compatíveis. O atualizador novo faz fallback para baixar o ZIP integral diretamente no Termux, preservando a pasta antiga e os saves; a versão antiga do script requer a migração descrita no fim deste documento. Não há promessa de atualização em segundo plano, APK próprio, autoatualização do JoiPlay ou teste aprovado em aparelho físico.

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

### Notas da compatibilidade incremental

As instruções `LEIA-ME-ANDROID*.txt` e, apenas no canal Kanto, `Kanto pilot.json` são dados **atualizáveis**. Seus hashes devem constar na lista `files`, porque a revisão muda a cada compilação; não são configurações de saves. O atualizador, `mkxp.json`, `Game.exe` e outros binários permanecem protegidos. A primeira migração entre inventários de formatos diferentes poderá exigir ZIP completo; isso deve ser informado ao usuário, nunca mascarado com patch de canal errado.

A verificação do Android Decades compilado teve sucesso na CI; uma tentativa antiga de publicação no GitHub foi recusada com HTTP 403 depois de mudanças posteriores em workflows. A publicação deve seguir a revisão atual da `main`, sem alterar indevidamente os hashes ou apontar `target_commitish` para outra revisão. Disponibilidade dos ZIPs deve ser confirmada na release pública.


## Nova edição compartilhada: Decades + Kanto + Hoenn

**Objetivo:** oferecer, na seção Android do site, um ZIP com as três regiões no **mesmo** `Game.exe` e perfil de saves principal. Não confundir com os pilotos isolados Kanto/Hoenn.

O arquivo da edição conjunta chama-se `Blue-Android-Decades-Kanto-Hoenn.zip`, com pasta interna `Pokemon-Blue-Android/`, e possui **canal próprio** `multiregion`. Ele é publicado em uma release `android-multiregion-*` somente quando o workflow `.github/workflows/android-multiregion.yml` conclui todas as etapas:

1. Instala a base Decades e integra Kanto e Hoenn na `game/` da build principal, sem arquivos de saves dos pilotos.
2. Revalida a prova de todos os mapas de Kanto e de **199 mapas de Hoenn** antes e depois da compilação.
3. Compila PBS e plugins com o `Game.exe` no Windows (incluindo `KantoPilot.rb`, `HoennPilot.rb` e `Mobile.rb`).
4. Inclui os arquivos de prova de instalação da região em `Data/`. O empacotador Decades puro normalmente omite metadados `blue-*.json/txt`; sem esses arquivos, Hoenn apareceria incorretamente como "em preparação" no JoiPlay.
5. Confere ZIP, plugins e inventário SHA-256 de arquivos e somente então publica o asset e o manifesto de atualização. Se faltar qualquer fonte, compilação ou mapa, **não publica** um ZIP falso.
6. A página de downloads consulta as **releases reais** antes de exibir o botão de download da edição multirregional; o arquivo do canal `decades` nunca é usado como substituto.

**Instalação Android:** use JoiPlay + RPG Maker Plugin; extraia o ZIP conjunto em uma **nova pasta**, selecione `Game.exe` e preserve cópias de seus saves antes de testar. A edição compartilhada usa o perfil do Decades, não os perfis isolados. O `ATUALIZAR-ANDROID.py` reconhece `multiregion` e não aplica um patch do Decades puro para apagar mapas ou metadados de Kanto/Hoenn.

**Status de qualidade:** o workflow confirma instalação e compilação em runner Windows, mas não garante jogabilidade no aparelho Android. Testar no JoiPlay em celular real: novo jogo, viagens via NPC Decades ↔ Kanto ↔ Hoenn, salvar/recarregar, Centro Pokémon após derrota, batalhas e cenas com toques. A presença de uma release é prova da geração do ZIP, não prova de todas as histórias e eventos.


## 15/11/2026 — Corrigir erro de New Game no JoiPlay (edição integrada)

**Erro reproduzido no celular:** `[Blue Battle Presentation and Story] RegionStart.rb line 66: NameError uninitialized constant BlueRegionStart::JSON`. O runtime Ruby usado pelo RPG Maker Plugin pode não fornecer a biblioteca `JSON`. O handler de exceção anterior referenciava `JSON::ParserError` diretamente e causava outro `NameError` durante a avaliação do `rescue`.

**Correção:** `RegionStart.rb` verifica a presença de `::JSON.parse` antes de usá-lo e, quando indisponível, consulta o manifesto compacto dos 199 mapas, o registro do instalador e os marcadores finais já verificados de Hoenn. Removidas referências a `JSON::ParserError` em handlers de Hoenn/Johto. Johto permanece fechado se a auditoria não puder ser feita. Os saves, Game.exe e os dados de combate não foram alterados. O teste `tests/region_start_android_no_json_runtime.rb` executa `New Game` sem nenhuma biblioteca JSON/Digest no Ruby simulado.

**Atualização simplificada no celular (sem reinstalação, quando existir patch):**

1. Feche o JoiPlay completamente e copie seus saves para um diretório seguro.
2. Abra o Termux já configurado com Python e armazenamento. Se ainda não instalou, execute `pkg install python` e `termux-setup-storage` e conceda permissão.
3. Entre na pasta em que o ZIP **multirregional** foi extraído (o caminho abaixo é apenas um exemplo):

```sh
cd ~/storage/shared/Download/Pokemon-Blue-Android
python ATUALIZAR-ANDROID.py --update
```

4. O atualizador valida o canal `multiregion`, hash, tamanho, versão de origem, arquivos protegidos e faz backups antes de aplicar. Se houver patch direto compatível, baixa apenas as diferenças. **Não** use o atualizador ou pacote `decades` puro nesta pasta.
5. Reabra o mesmo jogo no JoiPlay e teste **New Game → Decades / Kanto / Hoenn**. Se não existir patch direto, baixe o ZIP da edição integrada mais recente e extraia em pasta nova após copiar os saves. **Nunca** sobrescreva a instalação antiga sem backup.

O workflow `android-multiregion.yml` consulta a última release integrada válida antes de gerar nova versão, tenta produzir um `Blue-Android-Decades-Kanto-Hoenn.patch.zip` e o publica se a atualização for segura e menor que o ZIP completo. O site mostra a release completa; o Termux escolhe o patch compatível automaticamente.


## 15/11/2026 — Atualização pelo próprio Termux, mesmo sem patch

O atualizador agora tem **dois caminhos** nos canais Decades, Kanto e multiregion:

- **Patch incremental**, quando existe uma diferença compatível. Baixa apenas os arquivos alterados.
- **Instalação completa assistida**, quando a release não tem patch, há alterações em arquivos imutáveis ou a instalação pulou revisões. O Termux baixa o ZIP inteiro, valida SHA-256 e tamanho pelo manifesto da release, valida também cada arquivo extraído, prepara a nova versão em pasta temporária e troca a instalação mantendo o **mesmo caminho do Game.exe**. A pasta anterior fica como backup no mesmo diretório pai.

O caminho completo preserva automaticamente saves locais conhecidos (File A–H.rxdata, Auto 1–3.rxdata, Game.rxdata e backups .bak). Perfis externos do JoiPlay não são modificados. Arquivos personalizados não reconhecidos ficam na cópia integral da pasta antiga, não sendo transportados para a nova versão. Faça backup dos saves antes, feche o JoiPlay, confira espaço suficiente para download e extração e teste o save após a atualização.

Comandos da versão nova:

    cd ~/storage/shared/Download/Pokemon-Blue-Android
    python ATUALIZAR-ANDROID.py                 # consultar
    python ATUALIZAR-ANDROID.py --update        # instalar patch ou ZIP integral
    python ATUALIZAR-ANDROID.py --full --update # forçar ZIP integral

**Instalações antigas:** o arquivo ATUALIZAR-ANDROID.py dentro dos ZIPs anteriores não ganha o fallback sozinho. Para ativar esta função **uma vez**, use o Termux na pasta instalada, sem substituir o script antigo:

    cd ~/storage/shared/Download/Pokemon-Blue-Android
    python -c 'import urllib.request; urllib.request.urlretrieve("https://raw.githubusercontent.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/main/scripts/android/update_client.py", "ATUALIZAR-ANDROID-NOVO.py")'
    python ATUALIZAR-ANDROID-NOVO.py --game-dir . --update

Depois de atualizar para um ZIP que já inclui o cliente novo, retome o comando padrão ATUALIZAR-ANDROID.py. Se faltar Data/blue-update.json, a primeira instalação segue exigindo um ZIP completo em pasta nova e cópia segura dos saves.

**Limites:** a atualização depende de release íntegra disponível, internet, espaço suficiente, permissão de armazenamento e JoiPlay fechado. Falhas de download ou verificação deixam a pasta original intacta. A troca de diretórios tenta rollback se falhar; não apague o backup antes de testar. Mudança entre canais (Decades puro e Decades + Kanto + Hoenn, por exemplo) continua exigindo migração explícita, nunca automática.
