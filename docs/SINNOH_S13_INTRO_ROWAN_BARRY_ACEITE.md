# S13 — Introdução, Professor Rowan e Barry (30ª entrega de código)

**Aceite exclusivo de lógica e testes offline, após CI e integração na `main`.** Não confundir `S13 done` no inventário de engenharia com a introdução jogável no Game.exe/JoiPlay.

## Implementado

- [Manifesto S13](../data/regions/sinnoh-intro-s13.json) mapeia a cadeia de **6 checkpoints** em 5 NPC handlers e 3 Poké Bolas autorais do [template CH06](../data/regions/sinnoh-twinleaf-events.json): mãe → Barry (apresentação) → Rowan (maleta) → inicial físico → primeira batalha Barry → Pokédex de Rowan.
- [Runtime endurecido](../scripts/regions/SinnohPilot.rb) rejeita chaves não previstas no save e grava checkpoints apenas em ordem, uma vez por evento confirmado, impedindo a gravação direta de vitória contra Barry e da Pokédex fora dos seus handlers. A derrota válida `canLose` também conclui a batalha; resultado `nil` não conclui.
- [Preflight Ruby read-only](../scripts/regions/SinnohIntroContracts.rb) mostra checkpoint bloqueado, save inválido, outra região e sequência concluída em fixture, sem hooks, itens, saves, NPCs ou arquivos nativos. Sua lista de callbacks confiáveis permanece **vazia**.
- [Auditor S13](../scripts/regions/audit_sinnoh_s13_intro.py) cruza JSON, contrato do CH06 e guardas reais do runtime. [21 testes Python](../tests/test_sinnoh_s13_intro.py) e [teste Ruby](../tests/sinnoh_s13_intro_runtime.rb) verificam resultado de batalha, isolamento, reentrância, dupla recompensa e falsos MapIDs/autorizações.

## Requisitos jogáveis que permanecem pendentes

A trilha de introdução **I01–I05 continua 5/8**; I06, I07 e I08 aguardam auditoria dos nove mapas/sprites/spawn reais, compilação dos três PBS autorais de Barry e testes de fluxo no Game.exe/JoiPlay com saves isolados. Os IDs, posicionamentos e recursos do template continuam `null`/não verificados. A conclusão do contrato S13 **não atesta** esses três marcos.

**Após CI/merge:** Barra A **30/32 (93%)**, 2 parciais (S14, S31), zero pendentes. Barra E **20/20**, B/C/D **0/13** e 44 QA nativos não observados. Os executáveis e a instalação principal permanecem intocados.
