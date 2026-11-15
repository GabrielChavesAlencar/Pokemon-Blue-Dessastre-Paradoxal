# Hoenn integrado automaticamente ao Blue-Story.exe (build principal Decades)

**Atualizado:** 15/11/2026  
**Código na main:** download e instalação automáticos, validados por testes sintéticos/CI.  
**Windows / Game.exe real:** a instalação e jogabilidade ainda devem ser confirmadas no computador do jogador. Nenhum teste CI substitui essa verificação.

## Comportamento esperado

Ao atualizar e abrir o **Blue-Story.exe** com acesso à internet, o atualizador usa o mesmo fluxo de instalação de Decades/Kanto, depois:

1. Identifica se os 199 mapas de Hoenn já estão instalados e íntegros.
2. Se não estiverem, utiliza um ZIP original já existente, **ou baixa automaticamente** só os recursos necessários da revisão pública fixada de Hoenn, sem pedir ZIP ou BAT ao usuário.
3. Verifica cada arquivo pelo hash SHA-1 do Git e confere os SHA-256 auditados de `MapInfos` e `Tilesets`. Dados baixados ficam apenas na pasta ignorada `.blue-work/hoenn-source/`.
4. Gera os mapas e PBS de Hoenn com MapIDs livres na instalação principal atual, sem substituir saves nem o motor de batalha.
5. Faz backup dos arquivos que precisarem mudar, instala de modo transacional, verifica os 199 mapas e solicita compilação nativa de PBS e plugins.
6. Somente após instalação verificada habilita **Hoenn (viajar)** no Agente de Transporte Regional e a escolha Hoenn no menu de Novo Jogo.

**Não há nenhuma etapa manual obrigatória para obter ou importar o ZIP.** O `INTEGRAR_HOENN_DECADES.bat` anterior permanece como ferramenta de diagnóstico opcional, mas **não é necessário** para a atualização normal.

## Fonte pública fixa e segurança

A fonte é `SocomSeal/The-PMon-World-Project`, commit `c59233bdbaac4fbfeca6aa01c7f05be628da2a92`, diretório `The Pokémon World Project - Hoenn`, tree `c3876ecea7545eb3a91b9c8748d7e2b13f07805d`. Nenhum branch móvel substitui essa revisão sem nova auditoria. São baixados os 199 mapas necessários, as tabelas de mapas/tilesets, PBS de encontros/conexões e os PNG/OGG requeridos para o conteúdo preparado. **Não** são baixados ou executados EXEs, scripts ou saves do doador.

O conteúdo de terceiros é obtido somente no computador do jogador; não é publicado no GitHub deste projeto nem distribuído no arquivo do instalador. As permissões de redistribuição de cada recurso continuam não homologadas.

O integrador não substitui `game/Game.exe`, `Data/System.rxdata`, `Data/Scripts.rxdata`, `Game.ini`, `mkxp.json` nem arquivos de save. O sistema de itens-chave, HMs, insígnias, esmeraldas e times regionais do Blue continua em seu próprio estado. Decades e Kanto não são bloqueados se o download de Hoenn falhar.

## Onde ver o resultado

- `.blue-work/hoenn-main-install-status.json`: estado final `integrated`, `already_integrated`, `integration_blocked` ou `existing_install_needs_review`; identifica causa e origem.
- `.blue-work/hoenn-main-install.log`: passos de download, montagem e validação, incluindo os arquivos e quaisquer erros.
- `game/Data/blue-hoenn-install-status.txt`: código mínimo que o Agente Regional usa para orientar o jogador.
- `game/Data/blue-hoenn-install.json`: manifesto com 199 mapas, remapeamentos, origem e hashes.
- `.blue-backups/hoenn-<data>/`: backup criado quando a integração escreve arquivos do jogo.

Se o resultado for `integration_blocked`, confirme conexão de internet e o motivo exato no log. O download é retomável: arquivos já corretos são reutilizados sem serem baixados de novo. Se detectar cache alterado ou instalação parcial, não faz sobrescrita forçada nem cria IDs fictícios.

## O que continua disponível

**Hoenn integrada:** mesmo `Game.exe`, mesmo perfil de save da campanha principal, Novo Jogo na casa de Littleroot, chegadas via Agente Regional na cidade inicial, viagens Decades ↔ Kanto ↔ Hoenn após verificação do conteúdo. O sistema regional ainda aplica requisitos de desbloqueio das regiões de acordo com o progresso.

**Testar Hoenn:** continua sendo o piloto QA isolado, com seu próprio perfil de save; essa opção não comprova instalação na build principal.

**Importante:** 199 mapas representam o recorte autoral do piloto e não garantem 100% do Emerald. A documentação `HOENN_PENDENCIAS_IMPLEMENTACAO.md` registra eventos, NPCs, puzzles, músicas e QA ainda pendentes.

## QA real obrigatória, ainda pendente

1. Verificar que o Blue-Story.exe realmente baixou e integrou os mapas em `game/` sem ZIP manual; confirmar logs e hash da revisão.
2. Reiniciar o `Game.exe` principal após recompilação, acessar o Agente Regional e confirmar **Hoenn (viajar)**, não **Hoenn (em preparação)**.
3. Viagem Decades → Hoenn → Kanto → Hoenn, sem duplicar NPC ou reiniciar abertura da região; preservar inventário, party, PC, badges, HMs e flags.
4. Novo Jogo Hoenn → casa de Littleroot → mãe, Birch, inicial, Rota 101, Oldale → salvar e recarregar.
5. Derrota em Hoenn após ter curado em Kanto/Decades → retornar ao Centro regional de Oldale ou ao último Centro visitado em Hoenn.
6. Testes de ginásios, Surf/Dive/Waterfall, Aqua/Magma, Liga/Wallace, Hall da Fama, gráficos, música, localização PT-BR e Windows/Android/JoiPlay.

A integração **não é declarada jogável** somente porque os testes Python/Ruby/GitHub Actions passaram.
