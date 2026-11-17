# Sinnoh S14 — três iniciais e Poké Bolas físicas (entrega 31/32)

**Aceite de implementação em código e testes offline, sujeito a CI e merge.** Nenhum sprite, posição nativa, mapa original ou evento físico instalado no Game.exe/JoiPlay é aprovado nesta entrega.

## Entrega

- [Manifesto das três Poké Bolas](../data/regions/sinnoh-starters-s14.json): Turtwig (`SN_BALL_TURTWIG`), Chimchar (`SN_BALL_CHIMCHAR`) e Piplup (`SN_BALL_PIPLUP`) ficam **exclusivamente no Lago Verity**, em eventos de ação física `action` após Rowan explicar a maleta; os MapIDs, coordenadas, sprites, IDs de evento e callbacks nativos continuam **null / não verificados**.
- [Compilador de eventos](../scripts/regions/build_sinnoh_twinleaf_events.py) agora cruza **chave, espécie, mapa e handler** com o auditor CH06, rejeitando atalhos que troquem o conteúdo de uma Poké Bola e gatilhos `touch` que entregariam Pokémon ao caminhar. Mantém os eventos autorais e remove scripts/áudio da origem no stage isolado.
- [Pré-visualizador Ruby](../scripts/regions/SinnohStarterContracts.rb) distingue maleta bloqueada antes de Rowan, inicial escolhido, outras Poké Bolas indisponíveis, estado forjado e região errada, **sem distribuir Pokémon** e sem ativar eventos. `VERIFIED_NATIVE_SOURCES={}` permanece vazio até prova real.
- [Auditor S14](../scripts/regions/audit_sinnoh_s14_starters.py) cruza CH06, S13, escolha única em `SinnohPilot.rb`, ligação correta entre os três rivais do Barry e integridade do compilador; [24 testes Python](../tests/test_sinnoh_s14_starters.py) cobrem eventos errados, gatilhos falsos, mapas inventados e compilação sintética. [Teste Ruby](../tests/sinnoh_s14_starter_runtime.rb) executa as três escolhas separadamente, simulando entrega falha, reentrância, save/load, mudança de região e recusa de duplicidade.

Os eventos de Lago Verity ainda precisam ser auditados e posicionados em mapas autorizados, com sprites e eventos realmente compilados em cópia isolada. O requisito de três equipes PBS do Barry permanece sem aceite físico.

**Após CI/merge:** Barra A **31/32 (96%) de engenharia**, uma parcial **S31**. Barra E **20/20**. B/C/D **0/13**, **44 casos nativos pendentes**. Trilha I01–I08 ainda **5/8**, com I06–I08 pendentes. **Nenhum acesso nativo a Sinnoh é liberado.**
