# Viagem regional livre por NPC — jogo principal (15/11/2026)

**Decisão vigente:** o jogador pode trocar entre quaisquer regiões **efetivamente integradas à mesma instalação** desde o começo do jogo, sem precisar vencer a Liga, obter insígnias, desbloquear vizinhos ou concluir missões de transporte. Para executar uma viagem, é obrigatório **falar com o Agente Regional na cidade inicial da região atual**.

Este documento substitui as antigas regras de **desbloqueio por Liga** do plano v2. Em 15/11/2026, também foi acrescentada a regra **itens-chave e HMs independentes por região**. Insígnias, esmeraldas, progressão dos eventos locais, restrições de Pokémon especiais, vitórias e pós-jogo global continuam independentes.

## Correção do NPC ausente em Cherryhill (15/11/2026)

- **Causa no código anterior:** eventos regionais eram instanciados com `Game_Event.new(map_id,event)`, mas o **Essentials v21.1** exige `Game_Event.new(map_id,event,game_map)`. A simulação anterior aceitava incorretamente dois argumentos.
- **Correção:** os NPCs de Cherryhill, Pallet e New Bark agora recebem seu `Game_Map` proprietário ao serem criados. Para saves que **já estavam na cidade ao carregar**, `Scene_Map#createSpritesets` adiciona os NPCs **antes** de renderizar os sprites, sem precisar sair e entrar na cidade.
- **Mapa correto:** usa Cherryhill City identificada em `MapInfos` quando disponível (Map077 como referência nativa original); evita colocar o NPC em outra cidade quando a instalação reorganiza os IDs.
- **Compatibilidade:** um NPC já criado não é duplicado; os mapas RXDATA e saves originais não são modificados. O agente mantém a viagem livre por conversa, sem menu de teleporte direto, respeitando a separação local de itens-chave/HMs.
- **Teste isolado:** `tests/region_travel_runtime.rb` verifica a assinatura de três argumentos, a presença antes da criação do Spriteset, o reaproveitamento em save já carregado, o mapa alternativo identificado pelo nome, não duplicação, viagem e rollback. Executado em [Decades — regressão de viagem](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/decades-regional-start.yml).
- **Pendente:** validar visualmente o NPC no `Game.exe` do Windows, após atualização pelo `Blue-Story.exe`. Não é necessário começar outro save.

## Cidades iniciais e NPCs

| Origem | Mapa do NPC | Regra |
|---|---|---|
| **Kanto** | Pallet Town, mapa FRLG original 005, remapeado pelo manifesto de instalação | NPC gerado em tempo de execução, perto do ponto de chegada auditado. Não ocupa a casa do jogador e não substitui RXDATA. |
| **Decades** | Cherryhill City, Map077 nativo Decades | NPC gerado em tempo de execução, inclusive em saves Decades antigos sem metadados regionais; não substitui Map077.rxdata. |
| **Johto** | New Bark Town, ponto `npc_point` registrado no manifesto auditado | NPC disponível assim que Johto for integrada e validada, sem exigir a Liga; **piloto separado não serve**. |
| **Hoenn e demais** | Cidade inicial canônica de cada região, com ponto auditado a ser acrescentado quando integrada | **Não inventar coordenadas nem anunciar transporte jogável sem integração e QA.** |

Kanto ↔ Decades é o primeiro trecho efetivo desse circuito; Johto só aparece se um instalador tiver colocado mapas, compilação e prova confiável de NPC/chegada **no Game.exe principal**. Hoenn e Sinnoh têm pilotos independentes, portanto ainda não são destinos deste save; Hisui continua sendo o arco especial em desenvolvimento.

## Regras de deslocamento

1. O menu **Circuito de regiões** é apenas informativo. **Nenhum botão de teleporte no menu de pausa**. `BlueRegionTravel.agent(true)` é chamado exclusivamente pelo evento do NPC; `travel` e `perform` exigem esse contexto e verificam que o jogador continua na cidade inicial correta.
2. O agente mostra todas as regiões do catálogo e indica **atual**, **viajar** ou **em preparação**, conforme mapas verdadeiros e ponto de chegada validado. Não criar mapa, progresso ou save fictício.
3. O jogador confirma o destino. Equipe, dinheiro, itens comuns, TMs/TRs, itens equipados, Boxes de Pokémon, Pokédex e histórico regional permanecem no **mesmo save**. **Itens-chave e HMs não atravessam regiões:** são guardados no inventário da origem e restaurados ao retornar. O mesmo vale para itens-chave/HMs depositados no **PC de itens**, sem afetar as Boxes de Pokémon.
4. A regra de **oito conquistas locais para Pokémon especiais** continua valendo na região de destino. Quando necessário, o sistema pré-reserva vagas das Boxes e deposita os especiais antes de transferir; não pode deixar a party sem Pokémon apto, nem viajar com Box cheia. Falha de transferência faz rollback de região, equipe, PC de itens, Bolsa, atalhos, opções de batalha e posição.
5. Cada região mantém seus próprios eventos, HMs, badges e elite; viajar cedo **não** concede automaticamente iniciais, insígnias ou vitórias em Ligas. O jogador pode voltar à região anterior para continuar seu progresso local.
6. A Liga é mantida no estado `leagues` apenas para conquistas, pós-jogo e rematches Full Power; não desbloqueia transporte. O nome `unlocked` no código passa a significar destinos do circuito disponíveis conceitualmente; **disponibilidade física** exige instalador e prova local.
7. Saves Decades antigos sem `blue_regions` podem encontrar o NPC, e o primeiro deslocamento cria o estado regional sem migrar ou apagar sua campanha original. Em saves antigos iniciados em Kanto, o destino capturado de `System.rxdata` podia apontar à **introdução** de Decades e reabrir o seletor de personagem. Agora essa coordenada antiga **não é usada para viajar**: a entrada ocorre em um ponto passável da **Cherryhill City (Map077)**, próximo ao Agente Regional, sem repetir a introdução.

## Itens-chave e HMs por região (regra vigente)

**Exemplo:** ao sair de **Kanto** com a Poké Flauta e HM01 Cut, esses itens desaparecem temporariamente da Bolsa e do PC de itens durante a visita a **Decades**. Para usá-los em Decades, o jogador precisa **obter novamente as versões locais**. Ao voltar a Kanto, seus itens originais são restaurados automaticamente, sem duplicação. É possível possuir uma cópia de HM01 em **cada região**, independentemente, e voltar a elas várias vezes.

- **Guardados por região:** todo item com `GameData::Item.is_key_item?` ou `is_HM?` (não apenas HM01–HM07). Inclui atalhos registrados desses itens e também os exemplares que estiverem no PC de itens.
- **Continuam compartilhados:** Poké Bolas, remédios, itens comuns, TMs/TRs, itens equipados nos Pokémon, dinheiro, Pokémon e Boxes. Um Pokémon pode manter um golpe HM aprendido, mas **não pode executá-lo fora de batalha** em outra região até ter o HM local e cumprir os requisitos de insígnia/evento da região atual.
- **Respeito às mecânicas originais:** em **Kanto**, continuam obrigatórios o HM local e as regras de insígnias + Pokémon elegível. Em **Decades** e demais regiões integradas, o acesso ao HM exige também a cópia regional; depois disso prevalecem as verificações nativas de insígnia/eventos. Um save legado de Decades que nunca viajou continua usando os requisitos nativos até sua primeira troca.
- **Persistência:** os registros ficam em `$PokemonGlobal.blue_regions["region_key_items"][REGIAO]`, campos `items`, `registered` e `pc_items`. Não é criado save separado. Quando um save antigo for atualizado, **o jogo atribui os itens atualmente presentes à região atual na primeira viagem**, pois não há histórico suficiente para identificar onde foram obtidos antes desta mudança.
- **Segurança:** o destino é simulado em cópias temporárias da Bolsa e do PC de itens. Sem espaço para restaurar os itens locais ou com dado inválido, a viagem é **cancelada antes de mover o jogador**. Se a transferência falhar, a operação restaura o inventário, atalhos, PC de itens, party, Boxes e progresso. Nunca excluir os itens guardados em uma região só porque ela não está ativa.

**QA automatizada:** `tests/region_travel_runtime.rb` e `tests/region_policy_runtime.rb`, executados em [Decades — entrada e transporte](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/decades-regional-start.yml). Cobrem várias viagens, duas cópias do mesmo HM, TM compartilhada, PC de itens, mochila sem espaço, bloqueio de Surf em Decades e rollback. **Jogo real Game.exe no Windows ainda precisa ser verificado.**

## Decades sem menus duplicados e mecânicas padrão

- **Troca Kanto → Decades:** preserva o avatar e equipe da partida. O transporte entra diretamente em Cherryhill City e não reexecuta seleção de personagem, modo História, iniciais ou preferências de batalha.
- **Novo Jogo → Decades:** preserva apenas o menu necessário de **escolha de região na tela inicial**. A introdução nativa prossegue pelos seus eventos, mas as opções de modo História, perfil padrão e iniciais tradicionais são escolhidas automaticamente sem menus adicionais. O perfil padrão é 0; quando o evento solicitar iniciais tradicionais, os dois primeiros padrões automáticos são Bulbasaur e Charmander.
- **Mecânicas da campanha Decades:** `mega=true`, `zmove=true`, `tera=true`, `dynamax=false`. O padrão é aplicado na criação da campanha e na primeira viagem para Decades. As preferências alteradas depois são guardadas separadamente para cada região.
- **Segurança:** antigas coordenadas de chegada gravadas com mapa da introdução são ignoradas. O destino novo é calculado a partir de tiles passáveis de Map077, sem editar o RXDATA nem supor um ponto que possa estar ocupado pelo NPC. A transação mantém rollback de equipe, PC, posição e opções regionais.
- O sistema não distribui Mega Rings, Z-Rings ou Tera Orbs automaticamente: as permissões ficam habilitadas, mas Pokémon e equipamentos continuam sujeitos às regras do jogo.

**QA automatizada:** [Decades - entrada sem menus e transporte](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/decades-regional-start.yml). A campanha completa no `Game.exe` ainda precisa de verificação jogável, sobretudo a atribuição dos iniciais e a continuidade dos eventos nativos da introdução de Decades.

## Arquivos de implementação

- `scripts/battle_polish/Regions.rb`: catálogo de viagem livre, menu somente informativo, conquistas inalteradas.
- `scripts/battle_polish/RegionTravel.rb`: validação dos destinos instalados, agentes em Pallet/Cherryhill/New Bark e gate obrigatório do evento do NPC.
- `scripts/battle_polish/RegionStart.rb`: início regional nativo e prova do pacote integrado; sem alterações de ponto inicial.
- `tests/region_travel_runtime.rb`: testes isolados de NPCs físicos, viagem antes da Liga, mapa correto, PC, rollback, não duplicação e proteção de RXDATA.
- `tests/hoenn_qa_phase10_runtime.rb`: QA da Liga mantendo concessão de vitórias separada da liberdade de transporte.

## Validar no Game.exe Windows (pendente de teste real)

- Atualizar pelo **Blue-Story.exe**, mantendo o save de teste salvo em backup; começar **Kanto** com zero badges e encontrar o agente em **Pallet Town**.
- Abrir o agente, viajar para **Decades**, confirmar a chegada nativa e encontrar o agente em **Cherryhill City**, sem vencer a Liga. Retornar para **Pallet Town**.
- Fazer o caminho inverso começando **Decades**, inclusive num **save antigo** anterior à integração regional, sem apagar progressos.
- Verificar que o menu de pausa **não transporta**; falar com NPC em rota aleatória não pode liberar uma viagem.
- Confirmar que **Johto, Hoenn e Sinnoh** não oferecem teleporte para pilotos isolados; se uma Johto integrada for certificada, testar New Bark sem concluir a Liga.
- Validar o depósito de especiais no PC, rejeição de viagem com Box cheia ou equipe inutilizável, save/reload e rollback em falha de transfer.
- Verificar que HMs e itens-chave obtidos **não são transportados**, mas retornam ao acessar a região de origem; TMs, itens comuns e Pokémon permanecem, e nenhum HM pode ser usado fora da região sem sua cópia local. Insígnias, escalonamento, encontros, rival e campanha de Decades **não são avançados por uma viagem**.

**Status:** alterações no código e testes publicadas; **sem aprovação jogável até executar QA no Game.exe**.
