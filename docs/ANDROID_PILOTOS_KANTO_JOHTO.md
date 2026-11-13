# Android — pilotos Kanto e Johto separados

**13/11/2026 — estado atualizado:** o pacote principal Decades está publicado e o **piloto Android de Kanto foi publicado como prerelease independente**: [Piloto Kanto 638](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/kanto-android-638-d4899b4). **Johto ainda não tem ZIP regional aprovado**. Os próximos ZIPs podem incluir o atualizador incremental por canal, descrito em [ANDROID_ATUALIZACOES_INCREMENTAIS.md](ANDROID_ATUALIZACOES_INCREMENTAIS.md); sua publicação exige workflow aprovado.

## Arquivos esperados
- Modo História / Decades: Blue-Android-JoiPlay.zip (já existe na release).
- Piloto de Kanto: Blue-Android-Kanto-Piloto.zip (**já publicado, prerelease separada**).
- Piloto de Johto: Blue-Android-Johto-Piloto.zip (**pendente**).

Os pilotos são ZIPs completos de RPG Maker XP para JoiPlay + RPG Maker Plugin, não APKs. Não reutilizar ou renomear o pacote geral como se fossem pilotos.

## Histórico de bloqueios anteriores à publicação de Kanto
- O botão Testar Kanto do jogo principal usa o launcher Windows (cmd.exe). Não pode ser executado pelo JoiPlay. É necessária uma instalação já montada como piloto, em que Novo Jogo começa na casa do jogador em Kanto. A montagem isolada de Windows depende de scripts/regions/pilot.py, da fonte FRLG correta e do processo de compilação nativa.
- Johto ainda depende da preparação dos interiores, eventos e arquivos nativos que ficam fora da main. A documentação docs/JOHTO_FASE_04_STAGE_REAL_PRIVADO_77_MAPAS.md afirma que a prévia não está jogável; data/regions/johto-source.json registra distribution_approved: false. Não publicar dados de terceiros sem autorização.
- Cada piloto precisa de seu próprio diretório de save, compilação, trilha de teste e identificação de versão. Não deve modificar game/ nem sobrepor saves da história Decades ou do outro piloto.

## Critérios para liberar cada botão
1. Preparar o piloto em uma cópia isolada e verificar os mapas, warps, PBS, gráficos, plugins, início da campanha e direitos de distribuição dos recursos incluídos.
2. Executar a compilação nativa na cópia regional e comprovar que os dados compilados correspondem à versão dos plugins.
3. Testar início, escolhas, batalhas, movimentação, save/load e controles touchscreen num aparelho Android real com versões identificadas de JoiPlay e RPG Maker Plugin.
4. Empacotar a instalação inteira (Game.exe, Game.ini, configurações, mapas, PBS, gráficos, plugins e dados compilados), excluindo saves, logs e caminhos locais.
5. Publicar o ZIP regional com o nome exato da tabela acima, checksum SHA-256 e notas de experimentalidade na GitHub Release corrente. Não adicionar arquivos enormes diretamente ao Git.
6. Verificar na API releases/latest que o asset está em estado uploaded, tem tamanho positivo e pertence à release correta. O portal detecta o arquivo e converte a opção em link automaticamente.

## Contrato do portal
A página /downloads usa site/src/assets/android-release.js para ler a última release pública e determinar a disponibilidade de cada ZIP por seu **nome exato**. Sem asset confirmado, mostra "Piloto Kanto · indisponível" ou "Piloto Johto · indisponível", sem hyperlink. O pacote geral permanece disponível separadamente.

**Importante:** mostrar as duas opções no site não significa que os pilotos já podem ser instalados no celular. A aprovação e a publicação dependem dos pré-requisitos acima.


## Piloto Kanto — implementação técnica (13/11/2026)

O gerador scripts/android/package_kanto.py cria Blue-Android-Kanto-Piloto.zip com a pasta Pokemon-Blue-Kanto-Android/. Exige uma instalação regional isolada, metadados Kanto pilot.json, 142 mapas remapeados, Pallet como início, perfil próprio de saves, os dois plugins Mobile.rb e KantoPilot.rb compilados e marcador de compilação nativa atual. Não empacota saves, logs ou Main de testes; valida o ZIP e produz checksum SHA-256. O pacote inclui LEIA-ME-ANDROID-KANTO.txt, créditos e a revisão exata.

O workflow .github/workflows/kanto-pilot-check.yml agora prepara a compilação regional, guarda um GitHub Actions Artifact e só cria uma prerelease separada quando tudo for aprovado. A marca no commit [android-kanto-release] ativa essa publicação. A prerelease segue o padrão kanto-android-N-SHA e não altera a release principal. O site consulta releases/latest para a História e releases?per_page=30 para os pilotos.

### Bloqueio nativo detectado

Em 13/11/2026 a CI Windows conseguiu preparar a fonte e montar o piloto, porém Game.exe excedeu 150 segundos na verificação nativa (execução 43489379211). A compilação Android geral também excedeu 300 segundos no mesmo ambiente. Não ignorar essas falhas nem publicar um ZIP renomeado do Decades. O workflow passou a gerar diagnósticos de stdout/stderr e scripts de teste em caso de timeout.

### Caminho de compilação local, se a CI continuar bloqueada

Com a fonte FRLG e a base já instaladas em um Windows funcional, na raiz do projeto:

~~~powershell
python scripts/regions/pilot.py
python scripts/android/package_kanto.py --game-dir .blue-work/kanto-pilot --request-compile
# Abrir o Game.exe da pasta .blue-work/kanto-pilot para compilar os plugins.
python scripts/android/package_kanto.py --game-dir .blue-work/kanto-pilot --revision <sha-completo-de-40-caracteres>
python scripts/android/package_kanto.py --verify --revision <sha-completo-de-40-caracteres>
~~~

O Android usa JoiPlay + RPG Maker Plugin e precisa ser validado em aparelho real. Não publicar recursos de terceiros sem os créditos e direitos necessários.


## Diagnóstico de Kanto Android — tentativa de 13/11/2026

A execução nativa do piloto em GitHub Actions (run 43493750021) montou a fonte FRLG e os mapas, mas não concluiu o teste do Game.exe. O log registrou LoadError de json em RegionStart.rb, além de LoadError de set em Illusion_Perception.rb do plugin Advanced AI importado da base, e terminou em timeout. Portanto, nenhum ZIP regional foi liberado nessa execução.

A integração Blue foi corrigida em scripts/battle_polish/RegionStart.rb: json e digest deixam de ser requisitos para iniciar Decades/Kanto e só são carregados na validação da prova de Johto. Caso essas bibliotecas Ruby não estejam disponíveis, a prova de Johto continua bloqueada. Isso não ignora validação de Johto nem altera saves.

Este commit dispara uma nova tentativa da CI Kanto. O ZIP Blue-Android-Kanto-Piloto.zip só poderá ser criado como prerelease separada depois de o teste nativo e o compilador JoiPlay finalizarem com êxito. Em caso de erro, a CI publica diagnósticos e mantém o botão do site indisponível.

## Segunda rodada de diagnóstico do Kanto

A execução 43495139107 avançou após corrigir o carregamento da biblioteca JSON. Em vez de timeout, o teste nativo revelou `NoMethodError` no verificador `KantoNativeCheck.rb`: alguns eventos do mapa não têm página ativa e `event.list` pode ser `nil`. O teste foi alterado para percorrer `Array(event.list)`, mantendo a verificação dos teletransportes sem tocar nos eventos originais. A próxima compilação continua bloqueada se qualquer teste nativo ou verificação de JoiPlay falhar.

## Ajuste do configurador mkxp-z para o pacote Android Kanto

Na execução 43495547842, toda a verificação nativa Kanto, inclusive a integração segura no Decades, concluiu com êxito. A etapa de empacotamento Android falhou antes da compilação porque o validador usava json.loads sobre mkxp.json. Esse arquivo no Pokémon Decades usa comentários // aceitos pelo mkxp-z. O empacotador agora extrai e valida estritamente somente as propriedades ativas dataPathApp e dataPathOrg, exige um único valor correto para cada uma e rejeita configurações sobrepostas, sem alterar o mkxp.json. Testes unitários adicionais cobrem comentários e duplicidade. Este commit dispara uma nova tentativa experimental.

## Terceira rodada de empacotamento

Na execução 43496189183, os testes nativos Kanto e a regressão de integração no Decades passaram, mas o validador do pacote recusou os saves. A causa foi o formato real do mkxp.json gerado por scripts/regions/pilot.py: dataPathApp e dataPathOrg aparecem na mesma linha, apesar dos comentários do JSONC original. Agora a validação remove linhas inteiramente comentadas, aceita as duas propriedades na mesma linha, exige ocorrência única e compara os dois perfis de save exatos. Testes reproduzem a configuração escrita pelo gerador. O ZIP continua bloqueado se falhar qualquer verificação.
