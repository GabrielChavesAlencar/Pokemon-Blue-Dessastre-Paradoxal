# S20 — Cyrus, Spear Pillar, Mundo Distorcido e Giratina

**21ª entrega da Barra A de Sinnoh.** Esta entrega implementa e testa **contratos de progressão offline**, não instala mapas, puzzles, cutscenes, Pokémon lendários ou batalhas em Game.exe.

## Implementação real em código

- O [adaptador Ruby `SinnohDistortionContracts.rb`](../scripts/regions/SinnohDistortionContracts.rb) usa **apenas o ledger existente `sinnoh_ch14`**, vinculado ao [runtime CH14](../scripts/regions/SinnohStoryContracts.rb). O CH14 já define o prefixo ordenado das 22 etapas da história e exige insígnias **Mine e Icicle** antes de Cyrus. A S20 isola exatamente **nove checkpoints da fase 8**, sem avançar etapas da Liga.
- O [contrato auditável S20](../data/regions/sinnoh-distortion-s20.json) distingue cinco provas de vitória (`battle_won`: Cyrus, Saturn, Mars, Jupiter, Cyrus final), a cena de Dialga/Palkia (`scene_completed`), conclusão explícita dos puzzles (`puzzles_solved`), resolução do encontro com Giratina (`encounter_resolved`) **sem obrigar captura** e prova distinta de retorno (`safe_return_confirmed`). Essas assinaturas são políticas **propostas de callback**, não eventos mapeados, compilados nem auditados no Game.exe.
- Antes de S20, as cinco etapas da S19 têm que estar completas pelo CH14. Pular o primeiro Cyrus, Saturn, Mars, Jupiter, a cena do Spear Pillar, os puzzles, a batalha final, Giratina ou o retorno é recusado. Repetir um checkpoint não produz nova gravação; saves falsos, regiões divergentes e insígnias faltantes são recusados sem reparo automático.
- **`VERIFIED_NATIVE_SOURCES = {}.freeze`**: o registro de callbacks nativos permanece vazio e congelado. O método público `record_from_native` **não pode gravar** checkpoint por evento fictício, texto de NPC ou botão; a rotina interna de teste não é um callback público. A S20 **não** cria flags paralelas, recompensa Giratina, concede badge/HM, modifica Bag/Party, cria MapIDs ou teleporta o jogador.
- Depois de confirmar *sinteticamente* o último checkpoint, o CH14 indica `P09_VOLKNER_BEACON_BADGE` como a próxima etapa; isso **não executa** o teleporte ou libera o evento de Volkner. O próximo acesso físico depende do fluxo nativo e de pontos de destino auditados.

## Auditoria e testes

- O [auditor `audit_sinnoh_s20_distortion.py`](../scripts/regions/audit_sinnoh_s20_distortion.py) cruza os nove checkpoints com o catálogo CH14, as referências de fase 8, a seção S39 do detonado e o runtime Ruby. Falha se houver ordem ou resultado diferente, fonte nativa/mapa/teleporte/PBS não comprovado, provas de Game.exe/Android inventadas, equipe concedida ou alteração do ledger.
- [`tests/sinnoh_s20_distortion_runtime.rb`](../tests/sinnoh_s20_distortion_runtime.rb) exercita o **BlueRegions e CH14 reais** usando *apenas* estados e fontes sintéticas; verifica Forest, Mine, Icicle, resultado correto de cada etapa, fonte suspeita, replays, atalhos, prefixos CH14, serialização, saves corrompidos, região atual, ausência de premiação e a distinção entre encontrar Giratina e retornar ao mundo normal.
- [16 testes negativos Python](../tests/test_sinnoh_s20_distortion.py) rejeitam MapIDs, PBS, callbacks ou teleporte inventados; tipo de prova errado; recompensas e Giratina concedida; falso `can_install`; guarda de fonte enfraquecida; ausência de S39; save CH14 paralelo; e CI/runtime ausentes.
- Os runners estão adicionados a [CH19](../scripts/regions/sinnoh_ci_ch19.py) e são obrigatórios no [manifesto S30](../scripts/regions/audit_sinnoh_s30_suite.py).

## Pendências nativas explícitas

Não temos mapas autorizados e remapeados de Galactic HQ, Mt. Coronet/Spear Pillar e Mundo Distorcido, destino seguro do retorno, scripts/eventos compilados, treinadores Cyrus/Saturn/Mars/Jupiter, puzzles navegáveis, batalha/captura real de Giratina nem validação Game.exe/JoiPlay. A sequência offline **não produz nem instala esses recursos**. Por isso **S20 fica `done` apenas no escopo de implementação de contratos/testes**, sem prometer gameplay. S07/R07–R09 e S31 continuam bloqueando implantação/aceite técnico.

**Critério de conclusão no código:** PR na `main` após CH19 Python/Ruby, S30 (5 jobs), portal e CH20 estático aprovados, com evidência neste documento. Nesse escopo, **Barra A 21/32 (65%)** (5 parciais, 6 pendentes); **Barra E 20/20**, **B/C/D 0/13**, 44 casos nativos não executados.

## Evidências de CI

Registrar somente as execuções de GitHub Actions realmente concluídas. Não contar a suíte sintética como prova de jogo nativo.
