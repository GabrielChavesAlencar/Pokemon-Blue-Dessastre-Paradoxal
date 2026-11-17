# S22 — viagem pós-Liga: Sinnoh → Hoenn / Unova (pré-verificação segura)

**23ª entrega da Barra A de Sinnoh — código, auditoria e testes offline.** Esta entrega NÃO instala transportes físicos, mapas, NPCs, MapIDs nem desbloqueia viagens nativas no Game.exe/JoiPlay.

## O que foi preparado de verdade

O [adaptador `BlueSinnohTravelContracts`](../scripts/regions/SinnohTravelContracts.rb) é **somente leitura** e representa o itinerário **pós-Hall of Fame** descrito pelo [CH14](../scripts/regions/SinnohStoryContracts.rb). Ele exige a confirmação independente do Hall of Fame no ledger `sinnoh_ch14`, a Liga regional registrada uma única vez, um destino realmente instalado, **origem física Sinnoh instalada**, contexto de Agente Regional e fonte do próprio NPC auditada.

Os retornos do pré-voo distinguem `story_incomplete`, `destination_not_installed`, `source_not_installed`, `npc_context_required`, `npc_context_unavailable` e `departure_handler_not_verified`. O registro imutável `VERIFIED_NATIVE_DEPARTURES = {}.freeze` permanece **vazio**: nenhum booleano de um teste nem o próprio Hall of Fame transforma o pré-voo em autorização de teleporte. O adaptador não expõe método de viagem, não usa `BlueRegionTravel.perform` nem grava save.

### Situação atual dos destinos

| Destino lógico após Liga de Sinnoh | Chegada física | Saída física de Sinnoh | Estado |
|---|---|---|---|
| Hoenn | Pode estar instalada em builds Blue já auditadas; verificar `BlueRegionTravel.hoenn_installed?`/ponto real | **Não existe origem Sinnoh aprovada** | Bloqueado mesmo com chegada verificada |
| Unova | **Nenhum ponto de chegada nativo instalado/verificado** | **Não existe origem Sinnoh aprovada** | Bloqueado; jamais reutilizar mapa de Hoenn |

A referência de **Hoenn/Unova após a Liga** é parte da rota narrativa de Sinnoh, não uma alteração do **circuito global Blue**, cujo `BlueRegions.unlocked` continua permitindo *viagem lógica livre* entre regiões. Um destino lógico listado no menu não equivale a um mapa instalado. **Não introduzimos uma exigência de Hall of Fame para Kanto, Johto, Hoenn ou Decades já funcionais**.

### Proteção dos itens e Pokémon

A lógica de viagens reais segue pertencendo a [`BlueRegionTravel`](../scripts/battle_polish/RegionTravel.rb). Ao executar **a prévia de uma viagem**, seu `stage_local_bag` monta uma cópia isolada: guarda **Key Items e HMs da origem** no registro regional, troca apenas por itens do destino, guarda os itens do **PC de itens** da mesma forma e mantém itens comuns. O destino é separado por nome da região; **um HM de Sinnoh não vale como HM adquirido em Hoenn**, e o retorno restaura os itens de Sinnoh. A mesma API de viagem também preserva o time/Box, regras de Pokémon especiais e rollback em caso de falha. A S22 testa essas invariantes **com bolsas e PCs sintéticos**, sem chamar `perform`, `move_to` ou `travel`, alterar itens reais ou modificar o comportamento global.

## Provas e CI

- [`sinnoh-travel-s22.json`](../data/regions/sinnoh-travel-s22.json): contratos de destino e inventário. MapIDs, partida física, ponto de chegada de Unova e fontes de NPC continuam `null` ou vazios; Game.exe, JoiPlay e QA nativo são `false`.
- [`audit_sinnoh_s22_travel.py`](../scripts/regions/audit_sinnoh_s22_travel.py): verifica a política compartilhada de Regions/RegionTravel, CH14, fonte de Sinnoh ainda não importada e circuitos registrados. Falha se houver viagem habilitada falsamente, mudança de política global ou transferência indevida de itens.
- [`sinnoh_s22_travel_runtime.rb`](../tests/sinnoh_s22_travel_runtime.rb): executa os módulos Ruby **reais** sobre regiões, bags e itens sintéticos; inclui antes/depois de Hall, Hoenn simulado, bloqueio de Unova, origem inexistente, contexto NPC falso, saves Kanto/Johto/Hoenn/Decades, inventário de ida/volta e rollback pré-escrita de dados inválidos.
- [16 testes negativos Python](../tests/test_sinnoh_s22_travel.py): rejeitam MapIDs, fontes nativas, chegada Unova inventada, falso Hall, NPC não verificado, isolamento da Bag/PC ausente, alteração das regras compartilhadas e certificado de Game.exe.
- [CH19](../scripts/regions/sinnoh_ci_ch19.py) roda o auditor Python e o teste Ruby. A [matriz S30](../scripts/regions/audit_sinnoh_s30_suite.py) exige os arquivos e evita regressões.

## Pendências para a viagem física

Faltam mapa e NPC de partida realmente instalados em Sinnoh, mapa de chegada de Unova, verificação de chegada de Hoenn na **build específica** do jogador, prova de passabilidade e disponibilidade dos agentes, MapID/teleporte seguro, recompensas e itens regionais na engine, save real e casos Game.exe/JoiPlay. **Não foi aplicado patch de teleportes ou materiais do jogo principal.**

**Aceite em código após CI e merge:** Barra A **23/32 (71%)**, 5 parciais, 4 pendentes; Barra E 20/20; B/C/D 0/13, 44 verificações nativas pendentes. A S23 — pós-jogo/revanches — continua pendente. **O projeto Sinnoh ainda não é jogável.**

## Evidências reais do GitHub Actions

- [Sinnoh S30 — execução 44061544618](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44061544618): **5/5 jobs `success`** (manifesto, Python com **16 testes negativos S22** e auditor `sinnoh-s22-travel-contract = passed (0)`, Ruby `sinnoh-s22-travel = passed (0)`, portal **161/161 testes** e Android estático).
- [Sinnoh CH19 — execução 44061544763](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44061544763): **Python/Ruby `success`**, executando o auditor e o runtime S22 explicitamente; `CH19_SCOPE=sinnoh_only CH19_STATUS=passed NATIVE_QA=false`.
- [Portal Blue — execução 44061544641](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44061544641): build e suíte do portal `success`.
- [Sinnoh CH20 — execução 44061544598](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44061544598): pré-voo JoiPlay **estático** aprovado (18 + 12 verificações). **44 casos nativos continuam sem execução.**
- **O que não foi testado:** Game.exe, partida real Windows/JoiPlay, mapas de Unova, NPC ou partida física em Sinnoh, passagem de Pokémon entre regiões com dados reais, arquivos de Bag/PC do usuário e retorno de teleporte. A fixture Hoenn usa um **ponto fictício somente para testar o bloqueio de fonte Sinnoh**, e nunca se converte em prova ou mapeamento nativo.
