# Sinnoh no Blue-Story compartilhado

O instalador do Windows procura um pacote revisado em `.blue-work/sinnoh-shared/manifest.json` após integrar as demais regiões. Para o Android, o empacotador usa a mesma instalação `game/` e o mesmo canal de atualizações `multiregion`. Com a região instalada e o código compilado, Novo Jogo pode começar em Sinnoh. O agente da cidade de chegada usa o transporte regional do Blue-Story e preserva o mesmo save, a equipe, o PC e as regras de itens-chave e HMs por região.

Para preparar o pacote, a revisão precisa fornecer os 144 mapas, a lista estável de MapIDs, os pontos transitáveis de início, chegada e agente, e `Plugins/ZZZZZ Blue Sinnoh Shared/SinnohSharedEvents.rb`. O módulo `BlueSinnohSharedEvents` deve confirmar em `ready?` que os catálogos e eventos usados pelo conteúdo estão compilados. O manifesto `BLUE_SINNOH_SHARED_V1` registra SHA-256 do pacote e dos índices, tilesets e conexões da base em que foi preparado. Ele só pode registrar aprovação após a revisão de mapas, direitos de distribuição e viagem Windows. A distribuição Android também exige as aprovações `joiplay_travel` e `android_distribution`.

O overlay deve ser montado contra a edição compartilhada já integrada. Ele pode acrescentar mapas, tilesets, conexões internas e arquivos regionais com nomes exclusivos. Arquivos de save, `Game.ini`, `mkxp.json` e `Data/Scripts.rxdata` pertencentes ao piloto ficam fora do pacote. O atualizador Android rejeita uma versão que remova os mapas de Sinnoh de um jogo já integrado.

Os 144 mapas da cópia experimental e os resultados de compilação do PR #338 ainda não formam esse pacote revisado. A viagem compartilhada e a abertura no JoiPlay precisam ser comprovadas no conteúdo integrado antes da distribuição.

## Menu e transporte regional

No menu Novo Jogo, Sinnoh usa o mesmo processo e save das demais regiões. Quando o overlay está pronto, o nome é apenas `Sinnoh`; caso contrário, `Sinnoh (instalação necessária)` informa o bloqueio e retorna à seleção sem abrir o piloto. A opção `Testar Sinnoh` continua sendo exclusivamente de QA.

O ponto de chegada e o agente devem estar no mapa exterior original `Twinleaf Town`, confirmado pelo MapInfos e pela geometria; não se admite um NPC em Sandgem Town ou numa rota como substituto. As viagens usam `BlueRegionTravel`, com a mesma política de Decades, Kanto, Johto e Hoenn, sem exigir a Liga para sair da região. O pacote precisa ser gerado e verificado em uma base compartilhada de teste antes de registrar as aprovações de distribuição. Não confundir aprovação em fixtures com o teste real de ida/volta no Game.exe e JoiPlay.

## Geração do candidato de 144 mapas

Na raiz da instalação gerenciada, com o jogo fechado, o comando `python scripts/regions/prepare_sinnoh_shared.py` usa o gerador regional existente e a base atual de `game/` somente para leitura. Ele prepara `.blue-work/sinnoh-shared-candidate/world/` com os 144 RXDATA, índices, tilesets, conexões e recursos regionais permitidos; os PBS globais de encontros e metadados ficam em `review/`. O arquivo `candidate.json` registra os hashes e as posições calculadas de Twinleaf sem conceder aprovação. O instalador principal não aceita esse candidato como manifesto de lançamento.

O job Windows `sinnoh-shared-world-candidate` prepara uma base descartável e executa o gerador, sem publicar conteúdo privado. Seu marcador confirma apenas a preparação dos arquivos, nunca a viagem nativa. Para instalar e liberar a região ainda é necessário portar os handlers de eventos isolados, compilar o PBS regional sem afetar as outras regiões, testar ida e volta a partir de Twinleaf no Game.exe e no JoiPlay com um save novo de teste, e obter a aprovação de distribuição. O PR #338 permanece uma dependência de conteúdo e suas provas privadas não são intercambiáveis com a validação compartilhada.
