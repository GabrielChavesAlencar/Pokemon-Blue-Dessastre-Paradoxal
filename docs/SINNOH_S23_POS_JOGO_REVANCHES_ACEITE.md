# S23 — Pós-jogo e revanches de Sinnoh: Battle Zone, lendários e Full Power

**24ª entrega da Barra A: políticas e testes offline.** Nenhum mapa de Sinnoh foi instalado no Blue/Decades nesta entrega; nem Game.exe nem JoiPlay foram executados. Os contratos nunca devem converter uma referência do detonado Platinum em encontro jogável, time PBS compilado ou disponibilidade de item de evento.

## Entregas reais de código

- [`SinnohPostgameContracts.rb`](../scripts/regions/SinnohPostgameContracts.rb) é um adaptador **não carregado pelo jogo principal**. A partir do único CH14 `sinnoh_ch14` e do Hall of Fame confirmado separadamente (S21), ele prepara um ledger opcional **`sinnoh_s23`** para seis marcos não lineares e idempotentes: Battle Zone, Heatran, Cresselia, Darkrai, Shaymin e primeiro marco de revanche Full Power.
- O adaptador **não concede itens, Pokémon, portais nem recompensas**. A rotina de gravação acessível a possíveis eventos futuros (`record_from_native`) está bloqueada porque `VERIFIED_NATIVE_SOURCES = {}.freeze`. O método de fixture é privado e não pode comprovar jogabilidade.
- **Battle Zone**: requer Hall of Fame Sinnoh para o roteiro local; a chegada ao Fight Area e a entrada pela balsa exigirão eventos e MapIDs nativos auditados. **Heatran**: o marco da Battle Zone deve estar previamente registrado e a quest real de Stark Mountain deve ser comprovada. **Cresselia**: referência opcional de Fullmoon Island após a Liga, sem captura automática.
- **Darkrai e Shaymin**: exigem comprovação específica dos requisitos/itens de evento em *callbacks nativos futuros*. Os itens não são gerados, e a prova usada em teste é sintética; nenhuma espécie é inserida automaticamente na party, PC ou Pokédex.
- **Revanches Platinum locais:** as referências históricas de **Aaron, Bertha, Flint, Lucian e Cynthia (5)** podem ser consultadas depois da Liga de Sinnoh, mas não são partidas jogáveis nem times Blue Full Power. O CH15 possui **0 times históricos de revanche de líderes de ginásio confirmados**; não inventar esses times.
- **Revanches oficiais Blue Full Power:** exigem o estado de **campeão das dez Ligas** (`BlueRegions.world_champion?`) **e uma equipe nativa de revanche independentemente verificada**. O status `first_clear` não vira Full Power apenas por concluir Sinnoh; a política `BlueRegions.profile` existente permanece intacta. O primeiro marco é idempotente; **repetição efetiva de batalhas** não foi implementada sem treinador NPC e callback nativo.
- **Pokémon especiais** (lendários/míticos/UB/paradoxos) permanecem sujeitos à regra já existente de **oito insígnias locais** para entrar na party; isso é distinto da condição global de dez Ligas das revanches mais fortes. Nada altera o balanceamento dinâmico Normal 70% / Master 90% ou as exceções de líderes e Campeões.

## Inventário e testes

- [`sinnoh-postgame-s23.json`](../data/regions/sinnoh-postgame-s23.json) cruza **14 áreas planejadas da fase 10** com **6 marcos opcionais**, sem MapIDs, eventos compilados, pesos de encontros, recompensas, músicas ou QA nativo.
- [`audit_sinnoh_s23_postgame.py`](../scripts/regions/audit_sinnoh_s23_postgame.py) exige 14 áreas/6 marcos CH01, Hall CH14, 13 times históricos CH15 e **5 referências de rematch da Elite/Cynthia**. Recusa Time/PBS/MapID/quest/Full Power certificados ficticiamente.
- [`sinnoh_s23_postgame_runtime.rb`](../tests/sinnoh_s23_postgame_runtime.rb) exerce o **BlueRegions e CH14 reais** com saves e callbacks **sintéticos**: HoF, Battle Zone → Heatran, três encontros opcionais, itens de evento, World Champion 10/10, replay idempotente, save/load, dados corrompidos, região atual e 7 vs 8 badges para espécies especiais.
- [16 testes Python negativos](../tests/test_sinnoh_s23_postgame.py) preservam ausência de fonte nativa, evento de item/captura fictício, proteção dos oito badges, equipe Full Power não verificada e níveis históricos não aplicados como níveis fixos.
- A matriz [CH19](../scripts/regions/sinnoh_ci_ch19.py) executa o auditor Python e o runner Ruby; a [matriz S30](../scripts/regions/audit_sinnoh_s30_suite.py) exige os arquivos.

## Pendências para uma região jogável

É necessário importar legalmente os mapas da Fight Area, Survival Area, Resort Area, Route 225–230, Stark Mountain, Battle Frontier, Fullmoon Island, Newmoon Island e Flower Paradise; criar NPCs/eventos reais, validar balsa/portais, capturas e quests; compilar os PBS de revanches com variantes Normal/Master e versões; testar acessos, save/reload, vitórias/derrotas, Hall e itens reais no Windows e JoiPlay. As **14 áreas CH01 são apenas referências**, e os seis eventos não estão instalados.

**Aceite apenas em código após CI e merge:** Barra A **24/32 (75%)**, 5 parciais e 3 pendentes; E **20/20**, B/C/D **0/13**, **44 testes nativos não executados**. O código não torna a campanha, a Battle Zone ou as revanches jogáveis.

## Evidências reais do GitHub Actions

- [Sinnoh S30 — execução 44076081364](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44076081364): **5/5 jobs `success`**. Manifesto (11 testes), Python (incluindo **16 testes negativos S23** e `sinnoh-s23-postgame-contract = passed (0)`), Ruby (`sinnoh-s23-postgame = passed (0)`), Portal (**161/161 testes**) e Android estático.
- [Sinnoh CH19 — execução 44076081101](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44076081101): **Python e Ruby `success`**, ambos com auditor/runner S23 explicitamente verificados; `CH19_SCOPE=sinnoh_only CH19_STATUS=passed NATIVE_QA=false`.
- [Portal Blue — execução 44076081026](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44076081026): build e testes do portal `success`.
- [Sinnoh CH20 — execução 44076081118](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44076081118): pré-voo JoiPlay **estático aprovado**, sem execução do jogo Android. **44 verificações nativas pendentes**.
- A primeira rodada do [PR #83](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/83) encontrou um **erro de sintaxe numa condição redundante do teste Ruby S23**; a condição foi removida sem alterar qualquer script de jogo. A segunda rodada acima aprovou Python/Ruby, manifesto, portal e Android estático.
- **Limite do CI:** nenhuma área Battle Zone, evento lendário, batalha de revanche, time PBS, item ou save de Game.exe/JoiPlay foi compilado, instalado ou testado nativamente. Os cenários de Hall of Fame, eventos e 10 Ligas foram simulados com dados e callbacks **sintéticos**.
