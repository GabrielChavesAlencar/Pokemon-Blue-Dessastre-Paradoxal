# Kanto — Fase 6: resultados técnicos da auditoria musical

**Data:** 12/11/2026 · **Fase:** 6 · **Catálogo integral:** 64 MP3 originais, 50 BGM e 14 ME, 135.768.381 bytes (mapeamento versionado). **Não significa 64 músicas já tocando no jogo.**

Este relatório separa **integridade de arquivos**, **codec MP3**, **compilação regional**, **dispatch nativo em Game.exe** e **aceitação de áudio por audição**. Cada dimensão tem uma evidência distinta. Somente faixas com eventos comprovados são instaladas no jogo automaticamente.

## Contagem dos vínculos

| Status de aplicação | Faixas | Evidência |
|---|---:|---|
| **VINCULADA** | **36** (30 BGM + 6 ME) | Regra aprovada do compilador Kanto, com MapID e arquivo verificados |
| **PENDENTE_EVENTO** | **21** | Falta evento/cena/segmento comprovado; não é habilitado preventivamente |
| **MAPA_AUSENTE** | **7** | Tema de área não existente entre os 142 MapIDs importados atuais (ex.: Lavender, Sevii) |
| **TESTADA_NA_ENGINE** | Somente prova amostral de API | A CI Windows exercita BGM ambiente, ME e BGM de cena com `pbBGMPlay` e `pbMEPlay` (sem comprovar reprodução por alto-falante) |
| **BLOQUEADA_AMBIENTE** | **64 (audição)** | A CI não tem ouvinte para comprovar percepção, loop perfeito, fade e retorno audível após ME |

**Artefatos e relatórios reproduzíveis:** `python scripts/music/install_kanto_music.py --audit` valida hashes Git, contagem e tamanhos dos 64 MP3. `python scripts/music/audit_kanto_phase6.py --decoder required` verifica **ffprobe + FFmpeg com decodificação integral dos 64 MP3**, imprimindo a matriz faixa a faixa no log e criando `.blue-work/kanto-music-phase6-audio.json` (ignorado pelo Git). Falha de codec gera erro explícito. A [regressão do Blue Studio](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/regression.yml) é a fonte do resultado do decoder; a [CI nativa de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml) é a fonte do dispatch de BGM/ME no motor.

## Matriz completa das 64 faixas

O status abaixo se refere à **associação funcional**. A coluna de codec é computada a cada execução e publicada nos logs do auditor, e **não** é uma afirmação de que a música foi ouvida.

| Nº | Canal | Faixa | Status | Regra/motivo |
|---:|---|---|---|---|
| 01 | ME | 1-01. Game Freak Logo | PENDENTE_EVENTO | PENDENTE_EVENTO_LOGO |
| 02 | BGM | 1-02. Opening Movie | PENDENTE_EVENTO | PENDENTE_CINEMATIC_OPENING |
| 03 | BGM | 1-03. Title Screen | VINCULADA | scenes:pilot_title |
| 04 | BGM | 1-04. Game Tutorial | PENDENTE_EVENTO | PENDENTE_REAL_TUTORIAL |
| 05 | BGM | 1-05. Welcome to the World of Pokémon! | PENDENTE_EVENTO | PENDENTE_WORLD_INTRO_CUTSCENE |
| 06 | BGM | 1-06. Pallet Town | VINCULADA | maps:PALLET_TOWN |
| 07 | BGM | 1-07. Professor Oak | VINCULADA | scenes:oak_talk |
| 08 | BGM | 1-08. Professor Oak's Laboratory | VINCULADA | maps:OAK_LAB |
| 09 | ME | 1-09. Obtained a Pokémon! | VINCULADA | events:obtained_pokemon |
| 10 | BGM | 1-10. Rival Appears | VINCULADA | scenes:rival_appears |
| 11 | BGM | 1-11. Battle! (Trainer) | VINCULADA | battles:trainer |
| 12 | BGM | 1-12. Victory! (Trainer) | VINCULADA | battles:trainerVictory |
| 13 | BGM | 1-13. Road to Viridian City - Leaving Pallet Town | VINCULADA | maps:ROUTE_1 |
| 14 | ME | 1-14. Obtained an Item! (Version 1) | VINCULADA | events:obtained_item |
| 15 | BGM | 1-15. Pewter City | VINCULADA | maps:PEWTER_CITY |
| 16 | BGM | 1-16. Teachy TV Menu | PENDENTE_EVENTO | PENDENTE_TEACHY_TV |
| 17 | BGM | 1-17. Viridian Forest | VINCULADA | maps:VIRIDIAN_FOREST |
| 18 | BGM | 1-18. Battle! (Wild Pokémon) | VINCULADA | battles:wild |
| 19 | BGM | 1-19. Victory! (Wild Pokémon) | VINCULADA | battles:wildVictory |
| 20 | BGM | 1-20. Trainer Appears (Boy) | PENDENTE_EVENTO | Sem vinculo auditado |
| 21 | BGM | 1-21. Pokémon Center | VINCULADA | maps:CELADON_CENTER, maps:CERULEAN_CENTER |
| 22 | ME | 1-22. Jigglypuff's Song | PENDENTE_EVENTO | PENDENTE_EVENTO_JIGGLYPUFF |
| 23 | ME | 1-23. Pokémon Healed | VINCULADA | events:healed |
| 24 | BGM | 1-24. Guide | PENDENTE_EVENTO | PENDENTE_TIMED_GUIDE_EVENT |
| 25 | BGM | 1-25. Pokémon Gym | VINCULADA | maps:CELADON_GYM, maps:CERULEAN_GYM |
| 26 | BGM | 1-26. Tense Battle! | PENDENTE_EVENTO | Sem vinculo auditado |
| 27 | BGM | 1-27. Battle! (Gym Leader) | VINCULADA | battles:gym |
| 28 | BGM | 1-28. Victory! (Gym Leader) | VINCULADA | battles:gymVictory |
| 29 | ME | 1-29. Obtained a Gym Badge! | VINCULADA | events:badge_awarded |
| 30 | BGM | 1-30. Evolution | VINCULADA | scenes:evolution |
| 31 | ME | 1-31. Congratulations, Your Pokémon Evolved! | VINCULADA | events:evolved |
| 32 | BGM | 1-32. Road to Cerulean City - Leaving Mt. Moon | PENDENTE_EVENTO | ROUTE_4_SEGMENT_UNVERIFIED |
| 33 | BGM | 1-33. Trainer Appears (Girl) | PENDENTE_EVENTO | Sem vinculo auditado |
| 34 | BGM | 1-34. Mt. Moon | VINCULADA | maps:MT_MOON_1F, maps:MT_MOON_B1F |
| 35 | BGM | 1-35. Vermilion City | VINCULADA | maps:VERMILION_CITY |
| 36 | BGM | 1-36. S.S. Anne | VINCULADA | maps:SS_ANNE_1F, maps:SS_ANNE_2F |
| 37 | BGM | 1-37. Cycling | VINCULADA | transport:bicycle |
| 38 | BGM | 1-38. Lavender Town | MAPA_AUSENTE | Sem vinculo auditado |
| 39 | BGM | 1-39. Pokémon Tower | MAPA_AUSENTE | Sem vinculo auditado |
| 40 | BGM | 1-40. Celadon City | VINCULADA | maps:CELADON_CITY |
| 41 | BGM | 1-41. Rocket Game Corner | MAPA_AUSENTE | Sem vinculo auditado |
| 42 | ME | 1-42. Winning! | PENDENTE_EVENTO | PENDENTE_MINIGAME |
| 43 | ME | 1-43. Jackpot! | PENDENTE_EVENTO | PENDENTE_JACKPOT |
| 44 | ME | 1-44. Pokémon Printer | PENDENTE_EVENTO | PENDENTE_PRINTER |
| 45 | BGM | 1-45. Rocket Hideout | MAPA_AUSENTE | Sem vinculo auditado |
| 46 | BGM | 1-46. Trainer Appears (Bad Guy) | PENDENTE_EVENTO | Sem vinculo auditado |
| 47 | BGM | 1-47. Silph Co. | VINCULADA | maps:SILPH_10F, maps:SILPH_11F |
| 48 | BGM | 1-48. Road to Fuchsia City - Leaving Lavender Town | MAPA_AUSENTE | Sem vinculo auditado |
| 49 | ME | 1-49. The Poké Flute | PENDENTE_EVENTO | PENDENTE_POKE_FLUTE |
| 50 | BGM | 1-50. Fuchsia City | VINCULADA | maps:FUCHSIA_CITY |
| 51 | ME | 1-51. Move Deleted | PENDENTE_EVENTO | PENDENTE_CONFIRMED_DELETE_HOOK |
| 52 | BGM | 1-52. Surfing | VINCULADA | transport:surf |
| 53 | BGM | 1-53. Battle! (Legendary Pokémon) | VINCULADA | battles:legendary |
| 54 | ME | 1-54. Caught a Pokémon! | VINCULADA | events:caught |
| 55 | BGM | 1-55. Cinnabar Island | VINCULADA | maps:CINNABAR_ISLAND |
| 56 | BGM | 1-56. Pokémon Mansion | VINCULADA | maps:MANSION_1F, maps:MANSION_2F |
| 57 | BGM | 1-57. Pokémon Net Center | MAPA_AUSENTE | Sem vinculo auditado |
| 58 | ME | 1-58. Professor Oak's Evaluation | PENDENTE_EVENTO | PENDENTE_OAK_EVALUATION |
| 59 | BGM | 1-59. Sevii Islands - Four Island - Five Island | MAPA_AUSENTE | Sem vinculo auditado |
| 60 | BGM | 1-60. Pokémon Jump | PENDENTE_EVENTO | PENDENTE_POKEMON_JUMP |
| 70 | BGM | 1-70. Final Battle! (Rival) | VINCULADA | battles:champion |
| 71 | BGM | 1-71. Epilogue | PENDENTE_EVENTO | PENDENTE_DISTINCT_EPILOGUE_SCENE |
| 72 | BGM | 1-72. Hall of Fame | VINCULADA | scenes:hall_of_fame |
| 73 | BGM | 1-73. Staff Credits | PENDENTE_EVENTO | PENDENTE_KANTO_CREDITS_SEQUENCE |

## Escopo efetivamente instalado

O piloto e o integrador montam as mesmas 36 faixas aprovadas, com 142 registros `SCOPE`, 49 `MAP`, 2 `TRANSPORT`, 8 `BATTLE`, 3 `BASEPOOL` de Decades, 6 `ME` e 5 `SCENE`. **Mapas preview-only, créditos de Kanto, abertura sem cena, leituras de menus, Battle! de classes incorretas e vinhetas sem conclusão permanecem desativados.**

Para evitar sobrescrita, o instalador compara hash do catálogo em cada origem e destino e utiliza abertura exclusiva. Reexecução é idempotente; arquivos divergentes interrompem a instalação. As preferências `Data/blue-music.json`/`.rxdata`, os saves e a posição inicial de Decades não são atualizados por essas regras.

## Correção da Fase 6 — Cena em mapa silencioso

Foi identificado um problema real no adaptador `BlueMusic.with_kanto_scene`: antes, se não houvesse BGM anterior, a cena seria **ignorada**. O adaptador passou a permitir a reprodução e, no mesmo mapa/região, chamar `pbBGMStop` ao terminar, recuperando o silêncio original. O teste cobre saída normal, exceção, cenas aninhadas, mudança de mapa, troca de região e caso em que um evento substitui a música durante a cena.

## Testes automatizados e limites

- **Python:** suíte completa do projeto; catálogo 64/50/14, 36 vínculos, 21 eventos pendentes, 7 áreas ausentes, manifestos e MapIDs; testes de decoder de sucesso e arquivo corrompido; ausência de arquivos; região/save antigo.
- **Ruby sintético:** Fases 1 a 5, tema de campo, classes de treinador/lendário/Campeão, vitória/derrota, custom/random, prioridade de `nextBattleBGM`, veículos, ME depois do commit, cenas silenciosas, cenas aninhadas e retorno do áudio.
- **FFmpeg real:** `ffprobe` identifica codec, canais, taxa amostral e duração, enquanto `ffmpeg -xerror` decodifica o MP3 **inteiro** para saída nula, sem tocar música em alto-falantes.
- **Game.exe descartável:** o script `KantoMusicNativeProbe.rb` executa na engine mkxp-z real, resolve BGM/mapa, ME e cena, testa dispatch do áudio com APIs nativas, verifica ausência de créditos fictícios e retorno à proteção de Decades. Não modifica a campanha do usuário.
- **Limite inegociável:** checks de código, decodificação em FFmpeg e BGM selecionada na engine **não provam** áudio perceptível, loop perfeito, fades naturais, corte na vitória, pausas do ME ou ausência de estalos/latência numa partida Windows real.

## Aceitação auditiva no Game.exe (pendente)

A prova auditiva ainda requer uma sessão no Windows com dispositivo de áudio ativo, preferencialmente usando `Testar Kanto`, em saves de teste. Critérios objetivos:

1. Na tela principal de Decades, ouvir apenas a música de título de Decades; no piloto isolado de Kanto, ouvir 1-03. Verificar que `Continuar` e `Novo jogo` não mudam os slots.
2. Na casa do jogador/Pallet/Oak, confirmar que 1-06/1-08 iniciam sem cortes, fazem loop corretamente e 1-07 aparece só ao entregar o pacote, retornando ao BGM anterior.
3. Antes do duelo com Blue em Pallet/Silph/Liga, confirmar 1-10 e depois o tema próprio de batalha 1-11/1-70; vitória deve selecionar a faixa de vitória sem duplicar o BGM anterior.
4. No ginásio, ouvir 1-25 no mapa, 1-27 no líder, 1-28 na vitória e a ME 1-29 **uma vez** após a insígnia. Perder não pode tocar ME de insígnia.
5. Em encontro selvagem, ouvir 1-18; lendário 1-53. Captura real deve tocar 1-54 após armazenar; uma tentativa falha não.
6. Em evolução, ouvir 1-30 e, ao concluir, ME 1-31. Cancelar não pode tocar a ME de sucesso; retorno ao BGM original sem interrupção.
7. Bicicleta 1-37 e Surf 1-52: conferir loops e restauração do tema de mapa ao desmontar, atravessar mapas e recarregar save.
8. Na sequência Lorelei → Bruno → Agatha → Lance → Blue, validar 1-72 **somente** após registrar a Liga; derrota e tentativa repetida não tocam Hall of Fame. Créditos 1-73 não podem começar sem cena correspondente.
9. Trocar Kanto → Decades → Kanto e carregar saves anteriores: músicas personalizadas e aleatórias de Decades, volume, pitch, inventário, boxes e progresso não podem ser alterados.
10. Para todas as amostras, registrar se codec/volume, **loop, fade-in/fade-out, pausa e retomada de BGM após ME**, latência e final da música foram perceptivelmente corretos.

**Estado de audição:** `BLOCKED_ENV` até haver evidência sonora de teste local. **Barra 2 — Aceite integral da campanha: inalterada.**

## Execução local/CI

~~~powershell
python -m unittest discover -s tests -v
python scripts/music/install_kanto_music.py --audit
python scripts/music/audit_kanto_phase6.py --decoder required
ruby -c scripts/music/BlueMusic.rb
ruby tests/kanto_music_runtime.rb
ruby tests/kanto_music_battles.rb
ruby tests/kanto_music_me.rb
ruby tests/kanto_music_scenes.rb
~~~

Na ausência de FFmpeg/FFprobe, use `--decoder auto`: o relatório marca `BLOCKED_ENV` em vez de afirmar que os MP3 foram testados. A CI obrigatória usa `--decoder required` e não aceita decoder ausente.

**Próxima etapa:** realizar a aceitação auditiva em um Windows com áudio e desbloquear somente os eventos de mapa/cena efetivamente implementados. Concluir esta fase de testes técnicos **não** equivale a declarar todas as 64 faixas vinculadas ou a campanha integralmente aprovada.
