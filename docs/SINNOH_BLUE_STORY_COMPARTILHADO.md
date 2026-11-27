# Sinnoh no Blue-Story compartilhado

No Windows, o Blue-Story.exe abre o jogo principal diretamente. O instalador procura um pacote revisado em `.blue-work/sinnoh-shared/manifest.json` após integrar as demais regiões. Para instalar Sinnoh para uso local, deixe `Sinnoh Maps.zip` e `Ultimate Gen 4 Overworlds Pack.zip` junto ao Blue-Story.exe. O instalador confere os hashes dos ZIPs e gera os mapas na instalação principal. Com a região instalada e o código compilado, escolha **Novo Jogo → Sinnoh**. O agente de Twinleaf usa o transporte regional do Blue-Story e preserva o mesmo save, a equipe, o PC e as regras de itens-chave e HMs por região.

O empacotador Android usa a instalação `game/` e o canal de atualizações `multiregion`. Para publicar Sinnoh nesse canal, é preciso um pacote aprovado para distribuição e uma validação no JoiPlay.

Para preparar o pacote, a revisão precisa fornecer os 144 mapas, a lista estável de MapIDs, os pontos transitáveis de início, chegada e agente, e `Plugins/ZZZZZ Blue Sinnoh Shared/SinnohSharedEvents.rb`. O módulo `BlueSinnohSharedEvents` deve confirmar em `ready?` que os catálogos e eventos usados pelo conteúdo estão compilados. O manifesto `BLUE_SINNOH_SHARED_V1` registra SHA-256 do pacote e dos índices, tilesets e conexões da base em que foi preparado. Ele só pode registrar aprovação após a revisão de mapas, direitos de distribuição e viagem Windows. A distribuição Android também exige as aprovações `joiplay_travel` e `android_distribution`.

O overlay deve ser montado contra a edição compartilhada já integrada. Ele pode acrescentar mapas, tilesets, conexões internas e arquivos regionais com nomes exclusivos. Arquivos de save, `Game.ini`, `mkxp.json` e `Data/Scripts.rxdata` pertencentes ao piloto ficam fora do pacote. O atualizador Android rejeita uma versão que remova os mapas de Sinnoh de um jogo já integrado.

Os 144 mapas da cópia experimental e os resultados de compilação do PR #338 ainda não formam esse pacote revisado. A viagem compartilhada e a abertura no JoiPlay precisam ser comprovadas no conteúdo integrado antes da distribuição.

## Menu e transporte regional

No menu Novo Jogo, Sinnoh usa o mesmo processo e save das demais regiões. Quando o overlay está pronto, o nome é apenas `Sinnoh`; caso contrário, `Sinnoh (instalação necessária)` informa o bloqueio e retorna à seleção sem abrir o piloto. A opção `Testar Sinnoh` continua sendo exclusivamente de QA.

O ponto de chegada e o agente devem estar no mapa exterior original `Twinleaf Town`, confirmado pelo MapInfos e pela geometria; não se admite um NPC em Sandgem Town ou numa rota como substituto. As viagens usam `BlueRegionTravel`, com a mesma política de Decades, Kanto, Johto e Hoenn, sem exigir a Liga para sair da região. O pacote precisa ser gerado e verificado em uma base compartilhada de teste antes de registrar as aprovações de distribuição. Não confundir aprovação em fixtures com o teste real de ida/volta no Game.exe e JoiPlay.

## Geração do candidato de 144 mapas

Na raiz do projeto, com o jogo fechado, `python scripts/regions/prepare_sinnoh_shared.py` usa a instalação `game/` para leitura. Use `--base-game` para indicar outra instalação Blue-Story. A reserva compartilhada de Sinnoh vai de 452 a 595 para comportar os 152 mapas de Kanto em uma instalação limpa. Gere uma nova cópia de QA se ela tiver sido criada com a reserva anterior. O candidato grava em `.blue-work/sinnoh-shared-candidate/world/` os RXDATA, índices, tilesets, conexões, eventos e recursos regionais. Encontros e metadados entram com validação das seções por MapID. O arquivo `candidate.json` registra hashes, IDs simbólicos e as posições calculadas de Twinleaf.

## Teste em cópia descartável

`python scripts/regions/stage_sinnoh_shared_qa.py --compile` copia a base e compila a camada no Game.exe em `.blue-work/sinnoh-shared-qa/game/`. Use o mesmo `--base-game` da geração quando aplicável. Essa cópia tem um novo perfil de saves. O recibo `stage.json` registra o hash da camada e do cache compilado. A compilação e as viagens têm resultados próprios. Para cobrir as quatro origens da matriz, confira a presença de Kanto, Johto e Hoenn na base antes de gerar o candidato.

Para um ZIP local de JoiPlay use `python scripts/android/package.py --channel multiregion --sinnoh-qa --game-dir .blue-work/sinnoh-shared-qa/game --request-compile`, execute o Game.exe da cópia para compilar e repita o comando sem `--request-compile`. O ZIP de QA fica em `.blue-work/sinnoh-shared-qa/` com seu próprio perfil. O publicador e o atualizador estável rejeitam esse perfil.

Teste Novo Jogo, ida e volta pelo agente para cada região, persistência após fechar e reabrir e regressões com save de teste. Registre separadamente os resultados no Game.exe e no JoiPlay. A promoção exige as provas de viagem, a revisão de escopo de conteúdo da campanha e a aprovação de distribuição.
