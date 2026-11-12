# Kanto — Fase 4/6: 14 vinhetas ME e reprodução somente em eventos concluídos

**Data:** 12/11/2026 · Estado: integração de eventos comprovados + catálogo completo. **Não equivale a aceite integral do jogo nem a teste auditivo interativo.**

Referências: [plano musical](KANTO_PLANO_APLICAR_MUSICAS.md), [Fase 3](KANTO_MUSICAS_FASE_3.md), [regras](../data/kanto-music-rules.json), [compilador](../scripts/music/compile_kanto_music.py), [runtime](../scripts/music/BlueMusic.rb), [eventos de Kanto](../scripts/regions/KantoPilot.rb).

## Escopo entregue

As **14 faixas ME** estão catalogadas e têm um status explícito. Apenas **6** têm gatilho de sucesso comprovado no Kanto preparado, e são ativadas nesta fase. As outras **8** estão documentadas como PENDENTE_EVENTO e **não são instaladas/acionadas automaticamente**. Ativar músicas sem evento real geraria vinhetas falsas e interferiria na campanha.

| Número | Vinheta | Situação e gatilho |
|---|---|---|
| 1-01 | Game Freak Logo | PENDENTE_EVENTO — sem logotipo de Kanto próprio validado |
| 1-09 | Pokémon recebido | **ATIVA** — Oak entrega inicial e Fighting Dojo, após `pbAddPokemonSilent` retornar sucesso |
| 1-14 | Item recebido | **ATIVA** — item coletado, HM Cut, Master Ball ou S.S. Ticket físico, somente após `$bag.add` verdadeiro |
| 1-22 | Canção de Jigglypuff | PENDENTE_EVENTO — sem NPC/ação auditada |
| 1-23 | Pokémon curados | **ATIVA** — serviço da mãe de Pallet após `$player.heal_party`; Centros Pokémon aguardam confirmação do script nativo específico |
| 1-29 | Insígnia conquistada | **ATIVA** — uma de oito insígnias de Kanto, somente se venceu e `BlueRegions.award` retornou verdadeiro |
| 1-31 | Evolução concluída | **ATIVA** — intercepta somente `pbMEPlay("Evolution success")` do Essentials v21.1 (não `Evolution start`) |
| 1-42 | Vitória de minijogo | PENDENTE_EVENTO — sem minijogo validado |
| 1-43 | Jackpot | PENDENTE_EVENTO — sem jackpot validado |
| 1-44 | Pokémon Printer | PENDENTE_EVENTO — sem impressora validada |
| 1-49 | Poké Flute | PENDENTE_EVENTO — sem uso comprovado de flauta em Snorlax |
| 1-51 | Golpe apagado | PENDENTE_EVENTO — confirmação e mudança real ainda não auditadas |
| 1-54 | Pokémon capturado | **ATIVA** — após `Battle::CatchAndStoreMixin#pbRecordAndStoreCaughtPokemon` consumir a lista de capturados com sucesso em uma batalha selvagem |
| 1-58 | Avaliação de Oak | PENDENTE_EVENTO — conversa com Oak não é avaliação completa da Pokédex |

## Sem disparos duplicados e sem mudar Decades

- **Mapa e região:** somente `BlueRegionalPolicy.state["current"] == "KANTO"` ou o estado real do piloto isolado, em um MapID compilado e não-preview, habilitam as faixas. Decades, saves anteriores, mapas antigos e as outras regiões continuam com suas músicas.
- **Uma conclusão, uma vinheta:** os eventos KantoPilot já impedem repetir presente, item e insígnia. A música só é chamada dentro do ramo efetivo de sucesso. Conversas, menus, derrotas, falhas de armazenamento e cancelamentos permanecem silenciosos.
- **Motor nativo:** `pbMEPlay(RPG::AudioFile)` reproduz de `Audio/ME/Kanto/`. É o próprio motor do Essentials que pausa e retoma a BGM (ambiente, bicicleta, Surf ou música anterior); o plugin **não** chama `pbBGMStop`, `pbBGMPlay` ou troca de mapa ao tocar uma ME.
- **Evolução:** `Evolution success` já é uma vinheta nativa pós-sucesso; o adaptador substitui **uma** chamada no mesmo lugar, em vez de tocar outra música. `Evolution start` e animação (Fase 5) continuam inalteradas. Um `Pkmn get` genérico emitido *antes* do armazenamento continua nativo para não tocar ME antes da entrega; os presentes silenciosos de Kanto são disparados somente após confirmação.
- **Captura:** a lista real `@caughtPokemon` está não vazia antes do registro/armazenamento, é consumida com sucesso pelo método nativo e só então a vinheta regional é emitida. Captura falha, batalha não selvagem ou retorno com erro não geram ME.
- **Falta de arquivo:** se a ME estiver ausente ou a configuração inválida, o compilador não emite o vínculo e o runtime mantém o áudio original. A cópia de MP3 exige hash do catálogo e nunca sobrescreve arquivo divergente.
- **Controle da campanha:** nenhum save, configuração global de BGM, inventário ou estado de vitória é modificado pela camada musical. Oito ME pendentes não têm linha `ME` gerada em `Data/blue-kanto-music.txt`.

## Resultados de compilação esperados

| Medida | Expectativa |
|---|---:|
| SCOPE — MapIDs reais de Kanto | 142, incluindo 45 previews |
| MAP — ambientes, Fase 2 | 49 |
| TRANSPORT — Surf/bicicleta, Fase 2 | 2 |
| BATTLE — temas/vitórias, Fase 3 | 8 |
| BASEPOOL — presets de Decades | 3 |
| ME — ações comprovadas, Fase 4 | **6** |
| ME — catalogadas | **14** |
| ME — sem evento comprovado | **8** |
| MP3 BGM distintos copiados | 25 |
| MP3 ME distintos copiados | **6** |
| MP3 preservados no catálogo original | **64 (50 BGM/14 ME)** |

## Reprodução e testes

O [workflow de regressão](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/regression.yml) testa o compilador e o adaptador Ruby sem tocar áudio real. O [workflow nativo de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml) instala as seis ME reais e comprova a montagem dos 142 IDs e das seis regras tanto na cópia piloto quanto no jogo integrado descartável. Os comandos, na raiz do projeto:

~~~powershell
python scripts/music/install_kanto_music.py --audit
python -m unittest discover -s tests -p "test_kanto_music*.py" -v
ruby -c scripts/music/BlueMusic.rb
ruby tests/kanto_music_runtime.rb
ruby tests/kanto_music_battles.rb
ruby tests/kanto_music_me.rb
python scripts/music/install_kanto_music.py --game .blue-work/kanto-pilot --phase4
python scripts/music/install_kanto_music.py --game .blue-work/kanto-pilot --approved
python scripts/music/compile_kanto_music.py --game .blue-work/kanto-pilot
~~~

**Limite de comprovação:** os contratos e a compilação são automatizados; escuta real, codec/volume ME, fade, retomada exata da música ambiente durante batalha e transição entre regiões precisam de uma sessão real no Game.exe. Nenhuma fase técnica equivale a subir a Barra 2 de aceite integral de jogabilidade.

## Próxima fase

**Fase 5 — abertura, cenas e pós-Liga.** Associar somente cenas reais (Oak, rival, Hall of Fame, créditos) a seus BGMs; evitar música de créditos sem vitória, repetição de recompensa e mudanças na tela de título de Decades. Os oito ME pendentes somente poderão ser habilitados em etapa posterior se existir código/ação comprovada e teste específico.
