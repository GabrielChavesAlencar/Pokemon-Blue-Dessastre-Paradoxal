# Sinnoh — S15: oito ginásios e insígnias (27ª entrega)

**Aceite de código, apenas offline; sujeito a CI e merge.** Não representa ginásios abertos no Game.exe, mapas, NPCs, PBS compilado ou insígnias nativas reais.

## Entregáveis

- [Contrato S15](../data/regions/sinnoh-gyms-s15.json): oito ginásios históricos do Pokémon Platinum na **ordem da história**: Roark/Coal, Gardenia/Forest, Fantina/Relic, Maylene/Cobble, Crasher Wake/Fen, Byron/Mine, Candice/Icicle, Volkner/Beacon.
- Cada entrada referencia a cidade, a equipe histórica sem níveis fixos de runtime, insígnia local, pré-requisitos de sequência e respectiva permissão HM do **contrato CH11**, sem alterar sua ordem técnica (no CH11, Cobble precede Relic; na história Platinum, Fantina vem antes de Maylene).
- [Adaptador Ruby](../scripts/regions/SinnohGymContracts.rb) consulta `BlueRegions.local_achievements`, permite pré-visualização de sequência e impede repetir insígnias. **Nenhum callback nativo está registrado** (`VERIFIED_NATIVE_SOURCES = {}`); `record_from_native` permanece fail-closed mesmo quando se fornece uma vitória forjada.
- [Auditor](../scripts/regions/audit_sinnoh_s15_gyms.py) combina contratos CH11, CH15, registro público, Campaign (Normal 70% / Master 90%) e as proteções de `BlueRegions`. [22 testes Python](../tests/test_sinnoh_s15_gyms.py) rejeitam MapIDs, NPC, PBS, insígnia, licença ou batalha inventada.
- [Teste Ruby](../tests/sinnoh_s15_gyms_runtime.rb) exercita os oito ginásios contra **estado simulado do BlueRegions real**, sem saves ou Game.exe, e exige que nenhuma vitória/evento sem vínculo nativo conceda insígnias.
- O runner CH19 e o manifesto S30 passam a cobrir S15; Kanto/Johto/Hoenn/Decades, `BlueMusic`, a Pokédex, saves, HM já implantados e ferramentas de instalação permanecem intactos.

## Pendências para a S15 jogável

Fonte RMXP autorizada, oito mapas/ginásios com eventos compilados, NPCs de líderes, PBS verificados, callback real de vitória, efeitos e itens pós-batalha, regressão de derrotas/reforços, insígnias e HM locais, save/load e 44 verificações Windows/Android. Nada disso foi simulado como instalação bem-sucedida.

**Após CI/merge:** Barra A **27/32 (84%)** (4 parciais, 1 pendente), Barra E **20/20**, B/C/D **0/13**. S15 `done` significa apenas **contrato e integração preparatória**, nunca jogabilidade comprovada.
