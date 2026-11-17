# Sinnoh S19 — Team Galactic: contratos de eventos e gates de progressão

**20ª entrega da Barra A: escopo de código e testes, não instalação jogável.** S19 isola os cinco checkpoints da Team Galactic nas fases 5–7 do contrato CH14 já existente. **Não adiciona mapas, sprites, cutscenes, encontros ou treinadores PBS ao Game.exe**.

## Implementação

- [`SinnohGalacticContracts.rb`](../scripts/regions/SinnohGalacticContracts.rb) cria o adaptador de política para cinco eventos: Team Galactic Windworks, batalha da Commander Mars, batalha da Commander Jupiter, encontro de Pastoria e sequência dos lagos. Ordem estrita; Mars e Jupiter exigem `battle_won`, os demais `scene_completed`; Jupiter requer a insígnia regional **Forest**. Cyrus, Spear Pillar e Giratina **não** são concluídos nesta etapa: são S20.
- O adaptador consulta `BlueSinnohStoryContracts.recorded/next_event` e só registra no ledger já existente **`sinnoh_ch14`** via `BlueSinnohStoryContracts.record`. A sequência não pode ser pulada, duplicada ou completada em outra região. Consultas de status e checkpoints não modificam o save.
- A constante `VERIFIED_NATIVE_SOURCES` permanece **vazia e imutável**: `record_from_native` não grava progresso sem callback compilado, associado a MapID real e auditado. `fixture_record` existe **somente para testes sintéticos** e aceita registro artificial fornecido pelo teste, nunca como prova jogável.
- [`sinnoh-galactic-s19.json`](../data/regions/sinnoh-galactic-s19.json) documenta as cinco etapas, seus pré-requisitos, tipos de resultado e referências simbólicas. Cada etapa tem `map_id=null`, `native_event_installed=false`, sem loot, premiação, insignia ou teleporte. Não inventa níveis nem times.
- [`audit_sinnoh_s19_galactic.py`](../scripts/regions/audit_sinnoh_s19_galactic.py) vincula a ordem S19 ao [catálogo CH14](../data/regions/sinnoh-story-ch14-contract.json) e à [cobertura auditável](../data/regions/sinnoh-coverage.json), exigindo fases corretas, badge Forest, callbacks ausentes e bloqueio de instalação fictícia.
- [`sinnoh_s19_galactic_runtime.rb`](../tests/sinnoh_s19_galactic_runtime.rb) usa o **runtime real BlueRegions e CH14** com saves e handlers sintéticos: testa batalha perdida/resultado não comprovado, fonte não registrada, saltos, replays, insígnia Forest, progressão das cinco etapas, serialização, saves corrompidos e separação Decades/Kanto/Johto/Hoenn.
- [12 testes negativos Python](../tests/test_sinnoh_s19_galactic.py) rejeitam MapIDs, times, PBS, recompensas, avanços de checkpoints, alterações de fontes e falsa aprovação de Game.exe. CH19 executa o Ruby e o auditor Python; S30 exige os arquivos.

## O que ainda exige trabalho nativo

As fases **5–7** carecem dos mapas de Valley Windworks/Eterna/Pastoria/lagos efetivamente importados, eventos, NPCs, treinadores Mars/Jupiter, condições visuais, batalhas e callbacks compilados. Somente depois disso é possível preencher fontes nativas verificadas, rodar no Game.exe e JoiPlay, testar save e publicar uma aprovação jogável. O booleano `confirmed=true` de uma fixture não substitui uma batalha real. A S20 — Cyrus, Spear Pillar, Distortion World, Giratina — permanece pendente.

**Critério da entrega de código:** CI CH19 Python/Ruby, S30 (5 jobs), portal e Android estático aprovados e PR integrado à `main`. Nessas condições, S19 pode ser marcada `done` em código, Barra A **20/32 (62%)** (5 parciais, 7 pendentes). Barra E **20/20**, B/C/D **0/13**; 44 verificações nativas ainda não observadas.

## Evidências reais do GitHub Actions

- [Sinnoh S30 — execução 44055558591](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44055558591): **5/5 jobs success**, incluindo manifesto (11 testes), Python com os 12 testes negativos S19 e auditor `sinnoh-s19-galactic-contract = passed (0)`, Ruby `sinnoh-s19-galactic = passed (0)`, Portal (**161/161 testes**) e Android estático.
- [Sinnoh CH19 — execução 44055558291](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44055558291): jobs Python/Ruby `success` com o novo auditor e o runtime S19; `CH19_STATUS=passed NATIVE_QA=false`.
- [Portal Blue — execução 44055558352](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44055558352): build e suíte do site `success`.
- [Sinnoh CH20 — execução 44055558331](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44055558331): pré-voo Android/JoiPlay **estático** aprovado, sem executar aparelho.
- **Limites observados:** nenhuma cópia com mapas nativos da Team Galactic, batalha Mars/Jupiter, gravação de save real, instalação de MapIDs ou execução no Game.exe/JoiPlay foi comprovada. Os 44 casos de QA nativa seguem pendentes. O teste Ruby usa deliberadamente fontes sintéticas para provar o bloqueio e a ordem da máquina de estados.

