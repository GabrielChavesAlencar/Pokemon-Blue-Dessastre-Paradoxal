# Sinnoh — CH14: Galactic, Cyrus, Elite Four, Cynthia e viagens pós-Liga

**Data:** 16/11/2026 · **Status:** contratos e testes isolados concluídos; **0 eventos nativos instalados** nesta fase.  
**Manifesto:** [`data/regions/sinnoh-story-ch14-contract.json`](../data/regions/sinnoh-story-ch14-contract.json)  
**Runtime:** [`scripts/regions/SinnohStoryContracts.rb`](../scripts/regions/SinnohStoryContracts.rb)  
**Auditor:** [`scripts/regions/audit_sinnoh_story_ch14.py`](../scripts/regions/audit_sinnoh_story_ch14.py).

## Escopo validado

São **22 checkpoints de história ordenados**, com identificadores provenientes de [`sinnoh-coverage.json`](../data/regions/sinnoh-coverage.json), mais dois identificadores *simbólicos* documentados no [detonado organizado](SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md) (Cyrus final no Distortion World — **S39** — e Barry no portão da Liga — **S42**). Não foram deduzidos números de mapa, NPC, eventos Essentials, itens ou equipes.

| Trecho | Requisito de progressão |
|---|---|
| Windworks, Mars e Jupiter | Ordem dos incidentes; Jupiter exige Forest Badge local |
| Pastoria e incidentes dos lagos | Os checkpoints anteriores devem estar registrados |
| HQ Galactic: Cyrus, Saturn e libertação; Spear Pillar: Mars/Jupiter | HQ Cyrus exige Mine e Icicle locais; cada etapa possui confirmação separada |
| Distortion World, Cyrus final, Giratina e retorno | Puzzles antes do confronto final; retorno seguro é um checkpoint próprio |
| Volkner e Barry pré-Liga | Beacon Badge verificado antes do checkpoint correspondente; **8 badges locais** antes do portão da Elite Four |
| Aaron → Bertha → Flint → Lucian → Cynthia | Sem pular batalhas nem concluir a Liga ao derrotar Cynthia |
| Hall of Fame | Exige **duas confirmações separadas**: conclusão do evento e Hall of Fame confirmado pelo motor; então e somente então utiliza `BlueRegions.complete_league(state, "SINNOH")` |

O guard Ruby usa a chave regional `state["sinnoh_ch14"]` como **prefixo estrito** da lista. No caso de estado ausente, a consulta devolve progresso vazio **sem escrever nada**; em save desconhecido, versão incompatível, flags fora da sequência, insígnias inválidas ou Liga contraditória, a leitura **recusa e não repara silenciosamente**. A gravação rejeita duplicatas, resultados não confirmados e tentativa de vitória de outra região. Todos os métodos aceitam estados de jogadores que iniciaram em outra região **quando a região atual é SINNOH**; a viagem de volta não pode recriar a campanha.

## Hoenn, Unova e circuito compartilhado

O Blue já possui circuito de viagem **logicamente livre** em `BlueRegions.unlocked`: isso não indica que todos os destinos tenham mapas. A CH14 **não altera** a política de viagem principal e **não grava** flags `hoenn_unlocked`/`unova_unlocked` artificiais.

A função read-only `BlueSinnohStoryContracts.post_cynthia_destination(state, destination)` informa por que **Hoenn ou Unova** permanecem bloqueadas:

1. História incompleta ou Hall of Fame ainda não confirmado → `:story_incomplete`.
2. Serviço regional ou ponto de chegada físico não validado → `:travel_service_missing` ou `:destination_not_installed`.
3. Destino existente mas origem Sinnoh ainda sem instalação válida → `:source_not_installed`.
4. Origem/destino existentes, porém fora do contexto do NPC → `:npc_context_unavailable`.
5. Apenas quando todas as validações físicas do serviço regional passarem → `:eligible_only_via_verified_npc`. A função **não teleporta**.

Na build atual, `RegionTravel.rb` **não aceita Sinnoh como origem física**, e Unova não possui destino implementado. Mesmo simulando uma chegada Hoenn válida no teste, viajar desde Sinnoh ainda é bloqueado. A vitória da Liga sozinha não instala mapas.

## Como chamar no futuro — apenas de um handler nativo auditado

Um evento real da engine deverá completar sua batalha/animação/resultado, verificar sucesso e somente depois chamar `BlueSinnohStoryContracts.record(state, chave, confirmed: true)`. Para `P09_HALL_OF_FAME`, acrescentar `hall_of_fame_verified: true` **somente** após confirmação independente da engine. Valores booleanos em testes são *simulações*, não atestados de autenticidade. O plugin não foi conectado aos mapas nem aos instaladores, portanto nenhuma flag pode progredir jogando a versão atual.

A rotina não cria Pokémon, Master Ball, HMs, insígnias, script global, mapa ou teleport. As premiações deverão ser implementadas mais adiante como eventos nativos independentes com validação e teste visual. O registro de Ligas continua centralizado no sistema regional, sem duplicar o contador mundial.

## Testes e resultados

```bash
python scripts/regions/audit_sinnoh_story_ch14.py
python -m unittest discover -s tests -p 'test_sinnoh_story_ch14.py' -v
ruby -c scripts/regions/SinnohStoryContracts.rb
ruby tests/sinnoh_story_ch14_runtime.rb tests/regions_data_fixture.rb scripts/battle_polish/Regions.rb scripts/battle_polish/RegionTravel.rb scripts/regions/SinnohStoryContracts.rb data/regions/sinnoh-story-ch14-contract.json
```

[**CI 43973023734 — job isolado Sinnoh aprovado**](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43973023734): **15/15 testes Python CH14**, teste Ruby de transição e save (22 checkpoints, duplicações, resultados de batalhas, Hall of Fame, reload e viagens negativas), **301/301 testes Python Sinnoh**. Os arquivos originais de Decades, Kanto, Johto, Hoenn, Unova e seus saves não foram modificados.

**Limitação da evidência:** são contratos e fixtures headless. **Game.exe/JoiPlay, 22 eventos físicos, flags nativas, compilação PBS e instalação real de destinos não foram executados.**

**Barra E:** 14/20 (70%). **Barra A:** 8/32 (25%). **B/C/D:** 0/13.
