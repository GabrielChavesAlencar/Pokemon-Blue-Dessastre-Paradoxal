# Johto diretamente no Decades — Blue-Story.exe

**Atualizado:** 16/11/2026  
**Estado:** existe agora uma **integração experimental privada** de Johto ao Game.exe principal, preparada pelo Blue-Story.exe. **Não foi testada como jogável no Game.exe nem no JoiPlay**, e não é o lançamento definitivo de Johto.

## Quarto antigo aparecendo mesmo após atualizar (diagnóstico real)

**Se ainda aparece a escada no canto inferior direito**, confirmar primeiro se o
`Game.exe` iniciado é da **mesma pasta atualizada**. O Blue-Story procura o
projeto ao lado do executável; se não encontrar, utiliza por padrão
`%LOCALAPPDATA%\\PokemonBlueDessastreParadoxal\\game\\Game.exe`.
Cópias independentes de `Game.exe` **não recebem automaticamente** a atualização.

Passos sem apagar save:

1. Fechar `Game.exe` por completo.
2. Executar o **Blue-Story.exe** atual (ele baixa o código da `main`).
3. Abrir a pasta do projeto gerenciada e clicar duas vezes em
   `VERIFICAR_QUARTO_JOHTO.bat`. Se a instalação tiver sido criada automaticamente,
   a pasta geralmente fica em `%LOCALAPPDATA%\\PokemonBlueDessastreParadoxal`.
4. O BAT lê `game/Data/Map674.rxdata` e `game/Data/Map675.rxdata`, confere
   posição do warp real (antigo 9,8; novo 4,4), tile da escada esquerda e o
   retorno do térreo, e aplica a correção com backup **apenas se** os hashes
   da prévia Johto estiverem íntegros. A confirmação é
   `LAYOUT_HGSS_APPLIED`; não basta o instalador dizer `ready=true`.
5. O diagnóstico completo é salvo em
   `.blue-work/johto-bedroom-diagnostic.json`. Se indicar
   `FAILED`, `OLD_OR_DIFFERENT_BEDROOM` ou `MAP_READ_ERROR`, conferir o
   `game_dir`, o campo `preview_integrity_error` e o log
   `.blue-work/johto-main-install-status.json`. **Não apagar arquivos de
   Map674/Map675, nem os saves ou o manifesto para forçar a reinstalação.**
6. Abrir o `Game.exe` da pasta reportada em `game_exe`; sair e entrar no
   quarto novamente para confirmar que o mapa renderizado é o instalado.

**Importante:** a correção do mapa desloca a escada e os móveis com os tiles
**já existentes**, não incorpora as imagens do HGSS. Para o design realmente
parecido com HeartGold/SoulSilver, enviar/preparar o PNG original dos tilesets
Akizakura16 (casas) e DonLawride (Centro/Market), além do manifesto privado de
posicionamentos, seguindo
[`JOHTO_HGSS_INTERIORES_PRIVADOS.md`](JOHTO_HGSS_INTERIORES_PRIVADOS.md).
Sem esses PNGs, o resultado continuará com os móveis/piso do Decades,
mesmo com o layout corrigido. Os créditos e permissões dos autores devem ser
respeitados antes de distribuir os gráficos num ZIP público.

## Como atualizar no Windows

## Atualização do Blue-Story (16/11): escolher o pacote na própria janela

A janela do **Blue-Story.exe geral** agora confere o status de Johto **antes de iniciar Game.exe**. Se a região não estiver montada, oferece **SIM: selecionar o ZIP original e instalar no mesmo jogo**, **NÃO: abrir apenas as regiões existentes** e **CANCELAR: sair**. Ao selecionar o ZIP, ele valida SHA-256, copia o arquivo para `.blue-work`, monta os 100 mapas com backup/rollback e solicita compilação nativa de PBS e plugins. Não cria um perfil separado de saves.

No menu **Novo Jogo**, **Johto** só aparece com o nome sem sufixo se o pacote principal tiver sido reconhecido. Caso contrário, exibe **Johto (instalação necessária)** e nunca inicia o piloto isolado silenciosamente. A opção separada **Testar Johto** permanece apenas para QA.

Os navegadores podem renomear o ZIP como `... (1).zip`; o instalador passou a procurar cópias numeradas, e ignora cache inválido quando houver uma cópia íntegra em Downloads. Nenhum arquivo privado de Johto é embutido no código público do site ou no EXE: o usuário precisa possuir o ZIP original, disponível nesta conversa.

**Atenção:** a existência do código no GitHub não prova que um novo EXE foi compilado e publicado. É obrigatório verificar o workflow de release, baixar o EXE atualizado e executar o instalador no Windows com o ZIP privado original. O teste automatizado não comprova gameplay no Game.exe nem no JoiPlay.

1. Baixar **Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip** (SHA-256 `74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49`) e deixá-lo **sem extrair** na pasta `Downloads` do mesmo usuário Windows, ou na raiz do projeto ou em `.blue-work`.
2. Fechar `Game.exe` e abrir **o mesmo Blue-Story.exe geral**. Ele baixa a nova revisão, prepara Decades/Kanto/Hoenn e só depois monta Johto.
3. Conferir `.blue-work/johto-main-install-status.json`. O sucesso **experimental** é `"status": "experimental_installed_not_native_tested"`. Qualquer outro status deixa Johto bloqueada e informa `reason`; não criar marcadores manualmente.
4. Na primeira abertura do jogo, permitir a compilação nativa de scripts/PBS solicitada pelo launcher. Em Novo Jogo, uma instalação experimental montada corretamente deve mostrar **Johto (prévia integrada)** e iniciar no quarto de New Bark, dentro da **mesma pasta game/** e do mesmo perfil de saves.
5. Reportar o resultado do teste com screenshot e o arquivo `.blue-work/johto-main-install-status.json`; nenhuma aprovação de gameplay foi feita nesta sessão.

**Aviso:** o ZIP original indica `can_install=false` como **prévia bruta**. Ele só é admitido como *entrada privada* do novo montador `scripts/regions/johto_main_preview.py`, nunca é extraído diretamente em `game/` nem publicado na distribuição. A origem dos assets/músicas ainda carece de aprovação para redistribuição pública.

## O que foi implementado

- `scripts/install_game.py` e `scripts/regions/auto_integrate_johto.py`: integração Johto automática depois de Kanto/Hoenn, busca em Downloads e diagnóstico claro.
- `scripts/regions/johto_main_preview.py`: valida ZIP privado pelo hash exato, prepara **82 mapas originais + 18 interiores adaptados = 100 mapas (Map600–Map699)**, preserva **Hoenn Map700+**, mantém os mapas antigos de Kanto/Decades, reindexa tilesets, mescla `MapInfos.rxdata` e conexões PBS e instala os eventos/sprites e scripts Ruby adaptados de Johto.
- O construtor **não** altera `System.rxdata`, `Scripts.rxdata`, `Game.ini`, `mkxp.json`, `Game.exe`, saves, perfis de usuário nem os MapIDs existentes. Faz backup em `.blue-backups/johto-preview-...`, aborta se houver colisão e reverte todas as suas alterações em caso de erro.
- `RegionStart.rb` / `TitleKanto.rb`: Novo Jogo → Johto tenta a região integrada primeiro; o piloto separado é só fallback caso exista. O marcador de **prévia experimental** é diferente do lançamento com 13 comprovantes `VERIFIED_PLAYABLE`. A seleção não exige a biblioteca JSON/Digest no JoiPlay.
- `JohtoMainCompile.rb`: os marcadores de prontidão das batalhas de Silver, treinadores de rota e Falkner/Sprout só são escritos após a compilação real do PBS, com verificação de tipos, equipes e encontros; nunca apenas por presença dos arquivos.
- `tests/test_johto_main_preview.py`: testes de backup, escrita do marcador por último, rollback, fonte inválida, não sobrescrita de MapIDs e ausência de alterações no dry-run.

## Correção confirmada com ZIP original — 16/11, 02h

**Causa real identificada:** a versão anterior de `johto_main_preview.py` recusava qualquer evento na posição inicial `Map674 (6,7)`. O próprio preparador original de Johto (`repair_new_bark`) coloca nesse ponto o evento invisível autorun `JH_NEW_GAME_PROFILE`. Assim o `build_overlay` sempre interrompia com `Spawn do jogador ocupado por evento`; o Blue-Story continuava com `Johto (instalação necessária)`.

**Corrigido em `scripts/regions/johto_main_preview.py`:** aceitar exclusivamente o evento invisível autorun `JH_NEW_GAME_PROFILE` na posição inicial, com nome, trigger e ausência de sprite conferidos. NPCs, tiles bloqueantes por evento, outros triggers ou eventos extras sobre o spawn continuam rejeitados. Um teste de regressão agora reproduz este caso.

**Validação efetivamente executada neste atendimento:** o ZIP privado ORIGINAL com SHA-256 `74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49` foi processado contra os arquivos-base reais presentes no arquivo privado `johto-pilot-inputs.zip`, com `Game.exe` substituído por placeholder de teste (não executado). O `dry-run` passou com `maps: 100, files: 135`; `--apply` gravou a integração experimental e `preview_proof` validou os 100 mapas e 133 hashes. Em uma segunda cópia foram adicionados registros e MapIDs sintéticos representando Kanto (410) e Hoenn (702); os dois mapas e respectivos registros e tilesets foram preservados após a integração.

**Limite desta evidência:** o pacote principal **real do usuário** (MapInfos/Tilesets após todas as atualizações), a compilação de PBS pelo Essentials, o jogo executado no Windows e o JoiPlay não foram testados aqui. A montagem validada não equivale a afirmar que a campanha completa de Johto está funcional.

**Entrega privada:** foi criado no chat um ZIP de 1,7 MB com `Blue-Story.exe` compilado e o ZIP de Johto juntos. O Blue-Story procura o ZIP ao lado do EXE e o prepara automaticamente na mesma instalação antes do `Game.exe`, sem criar outro save. Esse pacote privado **não** é anexado à release pública do GitHub.

## Hotfix do crash na abertura de Johto — 16/11/2026

**Sintoma real do Windows:** janela preta, `Script 'Blue Johto Main Preview|Boot.rb' line 774: SystemStackError: stack level too deep`.

**Causa reproduzida em Ruby:** `JohtoMainCompile.rb` usava `Compiler.singleton_class.prepend(CompilerHook)` e `super` para interceptar `Compiler.main`. Outros plugins Blue (Options, ZA Megas, Music) fazem `alias ... main`; quando um desses aliases é definido após o prepend, cria-se um ciclo `super -> alias -> hook -> super`.

**Correção instalada na main:** retirado todo hook de `Compiler.main` do `JohtoMainCompile.rb`. A leitura dos registros `GameData::Trainer` e `GameData::Encounter` agora acontece em `EventHandlers.add(:on_enter_map)`, após a compilação nativa, e só grava marcadores de batalha quando os registros realmente existem. Falhas de compilação não liberam batalhas nem devem derrubar o resto do jogo.

**Como aplicar a quem JÁ instalou Johto:** **feche o Game.exe e execute o mesmo Blue-Story.exe geral novamente com internet**. Ele baixa o novo código e detecta o manifesto existente. `auto_integrate_johto.py` chama `refresh_installed_runtime()`, que compara o SHA do `Boot.rb` atual com `Data/blue-johto-main-preview.json`, faz backup da versão antiga e substitui **somente** `Plugins/ZZZZZ Blue Johto Main/Boot.rb` e o manifesto atualizado. O próprio instalador em seguida solicita a recompilação do plugin/PBS antes de abrir o Game.exe. **Não é necessário reinstalar os 100 mapas, copiar o ZIP original, apagar dados ou trocar saves.**

**Verificação:** em `.blue-work/johto-main-install-status.json` procurar `"status": "experimental_installed_not_native_tested"`, `"ready": true` e na primeira correção `"runtime_hotfix": "compiler-no-prepend-v2"`. A prova persistente fica em `game/Data/blue-johto-main-preview.json` com `"runtime_hotfix": "johto-compiler-no-prepend-v2"`. O backup da correção fica em `.blue-backups/johto-boot-hotfix-...`.

**Testes efetivamente executados:** workflow dedicado de Ruby com aliases de Compiler carregados depois de Johto (sem recursão), teste Python de correção e rollback com manifesto de 100 mapas, além de aplicação real da atualização de Boot em uma **cópia de teste com os 100 mapas instalados**. O manifest/hash foi revalidado e uma segunda execução não alterou arquivos. Comparação de SHA antes/depois mostrou mapas Johto, `MapInfos.rxdata`, `Tilesets.rxdata`, `PBS/map_connections.txt` e o save de teste preservados. **A execução de Game.exe no Windows do usuário não foi realizada**; nenhum teste de gameplay completo é alegado.

## Redesign do quarto do jogador — referência HeartGold/SoulSilver

O quarto **Map674** no jogo principal foi reorganizado usando os sprites e tiles nativos do pacote Johto já instalado; **não** é uma imagem gerada. Em comparação ao desenho anterior, a escada visual passou do canto inferior direito para o lado esquerdo, acompanhada por um pequeno tapete; a cama ficou embaixo à esquerda, o tapete azul no centro, escrivaninha/computador e TV na parede superior e planta no lado direito.

O redesign está em `scripts/regions/johto_visual.py:style_bedroom_hgss` e é aplicado automaticamente a novas instalações experimentais de Johto pelo `johto_main_preview.py`. O MapID permanece **674**, as dimensões **14×11** e o spawn **(6,7)**. O evento original `JH_NEW_GAME_PROFILE` não é removido. A escada real `JH_HOME2F_TO_1F` passa para **(4,4)**; o evento inverso do térreo `JH_HOME1F_TO_2F` preserva o mesmo ID e volta a **(4,5)**. Os outros eventos do mapa são preservados.

**Para quem já instalou Johto:** fechar o `Game.exe` e executar o mesmo `Blue-Story.exe` com internet. O instalador detecta o manifesto de Johto, atualiza apenas `game/Data/Map674.rxdata`, `game/Data/Map675.rxdata` e `game/Data/blue-johto-main-preview.json`, após revalidar os hashes anteriores. O backup é criado em `.blue-backups/johto-bedroom-hgss-...`. Na segunda atualização o procedimento é idempotente e não precisa do ZIP privado novamente. Não alterar o `Data/MapInfos.rxdata`, `Data/Tilesets.rxdata`, mapas de Kanto/Hoenn, salvamentos ou arquivos executáveis. Se mapas tiverem sido editados por outro editor fora do manifesto, o instalador não deve sobrescrevê-los silenciosamente.

**Teste realizado:** no workflow `johto-local-integration-fixture.yml`, os testes Python confirmam os tiles, os dois sentidos de transferência, a manutenção do spawn/evento de perfil, os hashes, o comportamento idempotente e o rollback. **Teste visual e de colisões dentro do Game.exe ainda é necessário**: abrir Johto, conferir escada à esquerda, descer/subir, salvar/recarregar e observar a passagem em tiles de entrada. Não marcar a campanha completa como jogável com base apenas nesses testes.

## Limites conhecidos e testes pendentes

Esta implementação é **prévia de desenvolvimento**, não um Johto completo e certificado: o OFFLINE12 ainda tinha mapas e eventos sem validação nativa, e a adaptação das casas adicionais foi reduzida ao intervalo 682–699 para não invadir os IDs 700–999 de Hoenn. Outras cidades, interiores, missões, Liga, sprites, passabilidade e viagens exigem testes reais. Áudio HGSS opcional não é publicado nem exigido pela instalação.

**Os testes automatizados de lógica e proteção passaram para os casos sintéticos disponíveis.** Falta validar a montagem com o ZIP original **contra a instalação atual** de Decades+Kanto+Hoenn e lançar `Game.exe`; não se deve chamar uma compilação automática de prova de gameplay. O canal Android multirregional continua Decades+Kanto+Hoenn, **sem Johto** até haver compilação e testes JoiPlay verificados.

`scripts/regions/install_johto.py --apply` continua bloqueado para o **lançamento final** enquanto não existirem os 13 critérios de aceitação: direitos dos assets, mapas/warps, sprites/tilesets, story, PBS, batalhas/encontros, save/load, HMs/insígnias, viagem/Box, música, regressão Kanto/Decades, teste Windows e teste JoiPlay.

## Critério para concluir a integração

- Confirmar o status experimental no Blue-Story; confirmar início real em New Bark e eventos Elm/Silver, saída para Rota 29/Cherrygrove e batalha com Falkner.
- Salvar/recarregar, abrir save antigo, visitar Decades/Kanto/Hoenn sem quebrar o jogo, testar itens-chave/HMs, PC, insígnias, level cap, respawn e viagem.
- Auditar conteúdo que ainda falta e corrigir qualquer bloqueio com base nos logs, sem declarar sucesso jogável antes dos testes.
- Só depois considerar release público, download automático Android/Termux e aceitação dos 13 critérios.

**Referências:** `docs/JOHTO_OFFLINE_FASE_12_AUDITORIA_INTEGRACAO.md`, `docs/JOHTO_PENDENCIAS_APOS_OFFLINE_12_DE_12.md`, `docs/JOHTO_FASE_16_INTEGRACAO_E_ACEITE.md`, `docs/HOENN_INTEGRACAO_DECADES_MAIN.md`.
