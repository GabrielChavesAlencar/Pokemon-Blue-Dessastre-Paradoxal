# Sinnoh no Blue-Story compartilhado

O instalador do Windows procura um pacote revisado em `.blue-work/sinnoh-shared/manifest.json` após integrar as demais regiões. Para o Android, o empacotador usa a mesma instalação `game/` e o mesmo canal de atualizações `multiregion`. Com a região instalada e o código compilado, Novo Jogo pode começar em Sinnoh. O agente da cidade de chegada usa o transporte regional do Blue-Story e preserva o mesmo save, a equipe, o PC e as regras de itens-chave e HMs por região.

Para preparar o pacote, a revisão precisa fornecer os 144 mapas, a lista estável de MapIDs, os pontos transitáveis de início, chegada e agente, e `Plugins/ZZZZZ Blue Sinnoh Shared/SinnohSharedEvents.rb`. O módulo `BlueSinnohSharedEvents` deve confirmar em `ready?` que os catálogos e eventos usados pelo conteúdo estão compilados. O manifesto `BLUE_SINNOH_SHARED_V1` registra SHA-256 do pacote e dos índices, tilesets e conexões da base em que foi preparado. Ele só pode registrar aprovação após a revisão de mapas, direitos de distribuição e viagem Windows. A distribuição Android também exige as aprovações `joiplay_travel` e `android_distribution`.

O overlay deve ser montado contra a edição compartilhada já integrada. Ele pode acrescentar mapas, tilesets, conexões internas e arquivos regionais com nomes exclusivos. Arquivos de save, `Game.ini`, `mkxp.json` e `Data/Scripts.rxdata` pertencentes ao piloto ficam fora do pacote. O atualizador Android rejeita uma versão que remova os mapas de Sinnoh de um jogo já integrado.

Os 144 mapas da cópia experimental e os resultados de compilação do PR #338 ainda não formam esse pacote revisado. A viagem compartilhada e a abertura no JoiPlay precisam ser comprovadas no conteúdo integrado antes da distribuição.
