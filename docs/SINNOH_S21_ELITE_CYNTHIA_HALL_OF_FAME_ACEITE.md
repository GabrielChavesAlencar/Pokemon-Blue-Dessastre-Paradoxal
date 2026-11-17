# S21 — Liga de Sinnoh, Elite Four, Cynthia e Hall of Fame

**22ª entrega da Barra A — implementação de contratos e testes offline.** A S21 **não instala** os NPCs, mapas, treinadores ou dados PBS de Sinnoh. Também não inicia Game.exe nem JoiPlay.

## O que foi implementado no código

- [`SinnohLeagueContracts.rb`](../scripts/regions/SinnohLeagueContracts.rb) integra, em modo inerte, os **oito checkpoints de fase 9 já definidos no CH14**: Volkner/insígnia Beacon, Barry no portão da Liga, Aaron, Bertha, Flint, Lucian, Cynthia e Hall of Fame. **Não cria um segundo save:** só usa o ledger regional `sinnoh_ch14` do [`BlueSinnohStoryContracts`](../scripts/regions/SinnohStoryContracts.rb).
- **Bloqueios:** o retorno seguro do Mundo Distorcido (S20) precisa estar no prefixo CH14 antes de Volkner; a insígnia local **Beacon** tem que ser concedida separadamente pelo evento do ginásio; Barry exige **as oito insígnias locais de Sinnoh** (Coal, Forest, Cobble, Relic, Fen, Mine, Icicle e Beacon). Insígnias/HMs de outras regiões **não** substituem as de Sinnoh.
- **Vitórias distintas e ordenadas:** Barry → Aaron → Bertha → Flint → Lucian → Cynthia. Apenas o resultado tipado `battle_won` de um futuro callback nativo auditado permite avançar; conversar, se aproximar, perder ou reexecutar uma luta não avança. Não existem níveis fixos impostos aos times: a política dinâmica do Blue (Normal/Master) permanece compartilhada.
- **Hall of Fame independente:** a vitória contra Cynthia **não** conclui a Liga. Uma etapa separada exige `engine_hall_of_fame_confirmed` de um handler instalado e verificado, que só então chama o CH14 com `hall_of_fame_verified: true`. O CH14 atualiza o ledger **`leagues`** da região sem mudar a Liga de Kanto, Johto, Hoenn ou Decades. Isso não cria bandeiras de desbloqueio ou teleportes falsos para Hoenn/Unova (S22 permanece pendente).
- **Instalação bloqueada:** `VERIFIED_NATIVE_SOURCES = {}.freeze`, vazia e imutável. A API pública `record_from_native` recusa registros enquanto não houver MapIDs e callbacks realmente instalados, testados e auditados. O helper de testes é **privado** e não é um atalho nativo para aprovar a Liga.
- O [catálogo S21](../data/regions/sinnoh-league-s21.json) diferencia os oito checkpoints e suas provas exigidas. Referencia as [13 equipes históricas CH15](../data/regions/sinnoh-trainer-teams-ch15.json), das quais Volkner, quatro Elite e Cynthia são apenas **referências**, não dados PBS compilados nem times físicos de Game.exe.

## Validação e preservação do projeto

- [`audit_sinnoh_s21_league.py`](../scripts/regions/audit_sinnoh_s21_league.py) confronta o S21 com o CH14, o inventário de fase 9, o catálogo CH15, as regras de insígnias/HMs CH11 e as referências do detonado **S42–S43**. Falha se houver MapID, PBS/treinador nativo, evento/HoF jogável inventado, mudança na ordem, vitória sem confirmação ou prova de liberação de viagens.
- [`sinnoh_s21_league_runtime.rb`](../tests/sinnoh_s21_league_runtime.rb) executa o **BlueRegions** e **CH14 reais com estados e callbacks sintéticos**, cobrindo S19/S20 como pré-requisito, oito badges, bloqueio de Barry, vitórias de Elite/Cynthia, confirmação adicional de HoF, liga salva/recarregada, proteção de save corrompido, retorno entre regiões e ausência de alteração dos badges nativos.
- [16 testes negativos Python](../tests/test_sinnoh_s21_league.py) verificam falsificação de MapID/PBS, insignias inválidas, fonte nativa indevida, mudança de rosters, ordem da Elite, vitória e HoF equivalentes indevidamente e links de detonado não existentes.
- [CH19](../scripts/regions/sinnoh_ci_ch19.py) executa o auditor Python e o runtime Ruby. A matriz [S30](../scripts/regions/audit_sinnoh_s30_suite.py) exige scripts, contratos e regressões, inclusive todos os casos anteriores.

## Limites e próximos trabalhos físicos

A S21 não adiciona os mapas de Victory Road, salas da Elite Four/Cynthia, Barry pré-Liga, NPCs, batalha nativa, equipes PBS compiladas nem rotina física do Hall of Fame. A referência Platinum não demonstra que esses conteúdos foram copiados/instalados. A confirmação `confirmed: true` de uma fixture **não é prova de Game.exe**.

**Aceite em código após CI e merge:** Barra A **22/32 (68%)**, com **5 parciais e 5 pendentes**; Barra E **20/20 (100%)**, B/C/D **0/13**, e 44 verificações nativas ainda pendentes. Os mapas autorizados, a prova de vitória real, a gravação de save no Windows e o JoiPlay pertencem à implantação e ao QA nativo. **S22 (viagem Hoenn/Unova) permanece pendente.**

## Evidências reais do GitHub Actions

- [Sinnoh S30 — execução 44059296697](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44059296697): **5/5 jobs `success`**. Manifesto (11 testes), Python (incluindo os **16 testes negativos S21**, auditor `sinnoh-s21-league-contract = passed (0)`), Ruby (`sinnoh-s21-league = passed (0)`), portal (**161/161 testes**) e Android estático.
- [Sinnoh CH19 — execução 44059296659](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44059296659): **Python e Ruby `success`**, cada qual incluindo o auditor/runner S21 e emitindo `CH19_SCOPE=sinnoh_only CH19_STATUS=passed NATIVE_QA=false`.
- [Portal Blue — execução 44059296858](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44059296858): build e suíte do portal `success`.
- [Sinnoh CH20 — execução 44059296747](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44059296747): pré-voo **estático** de JoiPlay `success` (18 + 12 verificações); **44 casos de QA nativa continuam não executados**.
- **Limitação da evidência:** nenhum mapa da Liga, PBS compilado, trainer/Champion real, save real Windows, Hall of Fame físico, fonte nativa de batalha, Game.exe ou JoiPlay foi executado. `VERIFIED_NATIVE_SOURCES` segue vazio e as equipes históricas CH15 permanecem **referências**, não conteúdos instalados.
