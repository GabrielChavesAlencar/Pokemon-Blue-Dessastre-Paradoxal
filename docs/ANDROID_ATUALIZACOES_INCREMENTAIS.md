# Atualizações incrementais Android — Decades e Kanto

Estado: **implementação no código-fonte; lançamento sujeito à compilação e verificação dos respectivos workflows**.

Os dois canais são **independentes**:
- **Decades principal:** `Blue-Android-JoiPlay.zip`, pasta `Pokemon-Blue-Android/`, release `battle-hub-*`.
- **Kanto piloto:** `Blue-Android-Kanto-Piloto.zip`, pasta `Pokemon-Blue-Kanto-Android/`, prerelease `kanto-android-*`.
- Johto **não faz parte** desse mecanismo enquanto não existir um piloto regional autorizado e publicado.

Ambos continuam sendo jogos RPG Maker XP para **JoiPlay + RPG Maker Plugin**, não APKs nativos. As versões atualizadas incluem, na raiz da pasta instalada, `ATUALIZAR-ANDROID.py` e `Data/blue-update.json`. O aplicativo JoiPlay **não aplica patches dentro do jogo**: o menu **Atualizações Android** mostra a revisão e encaminha para o atualizador externo. O Python/Termux realmente consulta a GitHub Release, baixa e aplica as diferenças.

## Primeira instalação / migração obrigatória

A geração anterior dos ZIPs **não contém o atualizador nem o inventário de arquivos**, portanto precisa fazer **uma instalação completa** do próximo ZIP distribuído pelo canal correto. **Não extraia a nova instalação por cima da anterior.** Faça backup dos saves usando a opção `Onde fica meu save?` no Decades; no Kanto, respeite o perfil Kanto Piloto. Mantenha cópias dos arquivos `File A-H.rxdata`, `Auto 1-3.rxdata`, `Game.rxdata` e `.bak` existentes, inclusive se estiverem no diretório de saves configurado no JoiPlay.

Após essa migração, alterações dos próximos builds poderão ser baixadas de forma incremental quando houver patch direto compatível. Se pular versões ou mudar arquivos críticos, o cliente novo instalará pelo Termux o **ZIP completo validado**, com backup da instalação antiga. Clientes antigos ainda precisam da migração descrita no fim do guia.

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
# Para instalar patch ou ZIP completo pelo cliente novo:
python ATUALIZAR-ANDROID.py --update
```

O primeiro comando consulta a versão disponível. O segundo baixa o patch compatível ou, sem ele, baixa e aplica o ZIP completo validado, preservando a pasta anterior e os saves locais. Abra depois o mesmo `Game.exe` no JoiPlay.

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
5. Reabra o mesmo jogo no JoiPlay e teste **New Game → Decades / Kanto / Hoenn**. Se não houver patch direto, use o cliente novo do Termux para aplicar o ZIP completo. O jogo antigo permanecerá numa pasta de backup. No atualizador antigo, siga antes a migração indicada no fim deste documento.

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


## 15/11/2026 — Kanto mostra "instalação necessária" na edição integrada Android

**Sintoma real no JoiPlay:** em `New Game`, Hoenn está habilitada, mas Kanto aparece como `Kanto (instalação necessária)`, mesmo na edição Decades + Kanto + Hoenn publicada com 142 mapas de Kanto validados pela etapa de build.

**Correção de código:** `scripts/battle_polish/RegionStart.rb` agora verifica Kanto sem depender de `JSON.parse`, mesmo quando o JoiPlay expõe uma constante `JSON` incompleta. Valida `blue-kanto-start.txt`, `blue-kanto-ready.txt`, o manifesto original `blue-kanto-install.json`, os 142 mapas referenciados por IDs exclusivos, PBS e plugin Kanto. Sem provas válidas, não libera o menu. Hoenn mantém seu verificador independente dos 199 mapas.

**Regressão:** `tests/region_start_android_no_json_runtime.rb` agora cobre seleção de Kanto, Hoenn e Decades sem JSON, com constante JSON sem método parse e com parse falhando; verifica rejeição ao remover um mapa de Kanto ou adulterar o marcador. O pacote Android deve compilar a nova versão de `RegionStart.rb` em `Data/PluginScripts.rxdata`, além de incluir a fonte. O workflow multirregional exige compatibilidade entre ambos.

**Atualizar no celular:** depois de uma nova release multirregional **concluída e publicada com essa correção**, feche o JoiPlay, faça backup dos saves e entre na pasta do jogo no Termux. Execute `python ATUALIZAR-ANDROID.py --update`. O cliente novo utilizará patch quando compatível ou instalará o ZIP completo sem precisar extrair manualmente, preservando a instalação anterior. Não use as releases `decades` ou o piloto isolado de Kanto na edição integrada. Se a release ainda tiver o mesmo commit anterior à correção, ela não contém a solução.

**Aceite físico pendente:** abrir New Game e confirmar que Kanto está selecionável, iniciar Pallet Town, carregar/salvar, viajar a Hoenn e verificar que ambos continuam funcionando no JoiPlay real.


## 15/11/2026 — Correção urgente: atualizador selecionava uma release ANTIGA

**Reprodução confirmada em captura do Termux do usuário:** a instalação era o commit `125155eaf256fcc3e5bfa9880585e9d07ce22618` (`android-multiregion-15`), mas o atualizador escolheu `af0c4947cb006b26cc680b0ea33bea19d98c459c` (`android-multiregion-9`) e começou a baixar novamente o ZIP completo de 1,4 GB. A API `/releases?per_page=100` retornou os itens na ordem 9, 3, 15, que **não é cronológica**; o cliente antigo retornava o primeiro item correspondente ao canal. Esse downgrade também explica por que a correção mais recente da seleção de Kanto não aparece no aparelho.

**Correção do cliente:** `scripts/android/update_client.py` consulta as páginas disponíveis, filtra releases publicadas do canal correto que tenham ZIP e manifesto, e seleciona a data `published_at` mais recente, sem depender da ordem da API nem do número da tag. Antes de baixar ou aplicar qualquer patch/ZIP completo, consulta `GET /repos/.../compare/<instalada>...<disponível>` e exige `status=ahead`. Respostas `behind`, `diverged`, `identical` para revisões diferentes, ou comparações inconclusivas **bloqueiam sem alterar arquivos**. Reinstalação forçada da mesma revisão continua permitida.

Os testes `tests/test_android_updates.py` reproduzem a ordem real 9, 3, 15; conferem rascunhos/manifests incompletos; verificam a proteção por ancestralidade; e confirmam que uma tentativa de downgrade não inicia downloads. O workflow multirregional executa os testes antes de gerar/publicar o pacote.

**Recuperação no celular:** não executar repetidamente o cliente antigo. Primeiro esperar o Termux concluir; 100% do download não significa conclusão da instalação. Com o JoiPlay fechado e saves copiados, verificar a versão em `Pokemon-Blue-Android/Data/blue-update.json`. Se a atualização terminou substituindo por `af0c494...`, procurar ao lado da pasta do jogo o backup `Pokemon-Blue-Android.blue-backup-125155eaf256`; restaurá-lo com o jogo fechado, mantendo também a pasta antiga como salvaguarda. Não excluir backups sem antes inspecionar saves. Se não houver backup, não inventar a restauração: usar o cliente corrigido para consultar uma release realmente nova.

O arquivo `ATUALIZAR-ANDROID.py` já instalado não se corrige sozinho. Para consultar/usar a nova versão do script sem reinstalar manualmente, executar a partir da pasta do jogo:

    python -c 'import urllib.request; urllib.request.urlretrieve("https://raw.githubusercontent.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/main/scripts/android/update_client.py", "ATUALIZAR-ANDROID-CORRIGIDO.py")'
    python ATUALIZAR-ANDROID-CORRIGIDO.py --game-dir .

Somente após aparecer uma nova release integrada publicada que contenha o código corrigido de Kanto, aplicar `python ATUALIZAR-ANDROID-CORRIGIDO.py --game-dir . --update`. Caso a revisão publicada ainda seja `125155e...`, o cliente deve informar que a instalação está atualizada; ela **ainda não contém a correção de Kanto**. Não baixar o ZIP `af0c494...` para tentar corrigir esse bug.

**Aceite:** publicar o ZIP multirregional após compilar e conferir `RegionStart.rb` no cache `Data/PluginScripts.rxdata`; validar `New Game → Kanto`, Hoenn e saves no JoiPlay real. Código corrigido/CI não equivalem a teste concluído no celular.

## 17/11/2026 — Atualizador rápido sem backup (substitui o comportamento anterior)

A partir deste código, o comando padrão `python ATUALIZAR-ANDROID.py --update` **não faz backup**, **não reinstala o jogo** e **não baixa automaticamente o ZIP completo**. Se existir um patch publicado para a revisão exata registrada em `Data/blue-update.json`, ele baixa apenas os arquivos alterados, valida canal, revisão, SHA-256 e tamanho, grava cada arquivo individualmente por substituição atômica e atualiza o marcador de versão por último. Arquivos inalterados e saves permanecem no lugar; não é criada `.blue-android-update-backups/`.

O empacotador publica deltas para diferentes revisões anteriores de cada canal (priorizando recentes e a mais antiga, conforme a esteira) em `patches[]`, mantendo `patch` para compatibilidade. Também pode atualizar o próprio `ATUALIZAR-ANDROID.py` por patch, migrando o arquivo das listas antigas de `immutable` para `files`, **sem** permitir alterações em `Game.exe`, `mkxp.json`, `Game.ini` ou saves por meio do patch.

Sem patch direto compatível, `--update` informa a indisponibilidade e termina sem baixar os cerca de 1,4 GB do ZIP completo nem alterar o jogo. Apenas quem executar **explicitamente** `python ATUALIZAR-ANDROID.py --full --update` autoriza baixar o ZIP integral verificado. Mesmo nesse modo, o cliente deixa a instalação no mesmo diretório, modifica somente arquivos com conteúdo diferente, preserva saves e arquivos extras, e **não** faz backup.

**Trade-off escolhido:** sem backup, não há rollback automático entre múltiplos arquivos. O cliente valida os hashes antes de escrever, usa arquivos temporários por arquivo e, se for interrompido, aceita arquivos já atualizados e consegue retomar o mesmo patch. Isso reduz espaço ocupado e cópias, mas não elimina riscos de queda de energia/armazenamento defeituoso; mantenha uma cópia pessoal do save importante fora da pasta do jogo.

**Ativar em instalações antigas:** versões já extraídas não substituem sozinhas seu atualizador Python antes de executar o código novo. Na pasta do jogo (Termux com permissão de armazenamento), execute uma vez:

```sh
python -c 'import urllib.request; urllib.request.urlretrieve("https://raw.githubusercontent.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/main/scripts/android/update_client.py", "ATUALIZAR-ANDROID-RAPIDO.py")'
python ATUALIZAR-ANDROID-RAPIDO.py --game-dir . --update
```

Depois de instalada uma release que incorpore o novo atualizador, use normalmente `python ATUALIZAR-ANDROID.py --update`. Feche o JoiPlay antes de executar. Não confunda código publicado na main com patch/ZIP já aprovado e distribuído em release.
