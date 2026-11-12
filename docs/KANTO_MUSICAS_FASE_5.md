# Kanto — Fase 5/6: temas de cenas, título contextual e Hall of Fame

**Estado de 12/11/2026:** integração reproduzível de cinco contextos confirmados. **Não é aceite auditivo interativo, nem indica que todas as cenas da campanha foram concluídas.**

Referências: [plano das 64 músicas](KANTO_PLANO_APLICAR_MUSICAS.md), [Fase 4](KANTO_MUSICAS_FASE_4.md), [manifesto](../data/kanto-music-rules.json), [adaptador Ruby](../scripts/music/BlueMusic.rb), [cenas de Kanto](../scripts/regions/KantoPilot.rb) e [título de Decades](../scripts/battle_polish/Title.rb).

## As 13 faixas de cena — cinco efetivamente vinculadas

| Nº | Cena | Status e condição |
|---|---|---|
| 1-02 | Opening Movie | **PENDENTE**: não existe cinematográfica de Kanto comprovada |
| 1-03 | Title Screen | **ATIVA:** exclusivamente no Game.exe do piloto **separado**, identificado por `Kanto pilot.json`, manifesto de 142 MapIDs e ausência do marcador de integração na campanha principal |
| 1-04 | Game Tutorial | **PENDENTE:** não há tutorial de Kanto específico confirmado |
| 1-05 | Welcome to the World of Pokémon | **PENDENTE:** não há cena introdutória ao mundo Pokémon; a conversa no laboratório não deve fingir que é esse filme |
| 1-07 | Professor Oak | **ATIVA:** na entrega efetiva do pacote de Viridian a Oak, uma única vez, com desbloqueio de Pokédex |
| 1-10 | Rival Appears | **ATIVA:** antes da primeira batalha com Blue, da batalha de Silph Co. e da luta final de Blue como Campeão; exige condições reais que já dão início a cada duelo |
| 1-16 | Teachy TV Menu | **PENDENTE:** não há menu real e auditado |
| 1-24 | Guide | **PENDENTE:** falta uma sequência de orientação com início e término verificados |
| 1-30 | Evolution | **ATIVA:** apenas quando o Essentials toca a BGM nativa `Evolution` dentro da animação de evolução; a vinheta ME `Evolution success` da Fase 4 permanece independente |
| 1-60 | Pokémon Jump | **PENDENTE:** não foi encontrado minijogo funcional |
| 1-71 | Epilogue | **PENDENTE:** mensagem pós-Liga não é um epílogo completo, nem um segundo evento com música própria |
| 1-72 | Hall of Fame | **ATIVA:** somente após a Liga de Kanto ser completada com a sequência Lorelei → Bruno → Agatha → Lance → Blue, `BlueRegions.complete_league` verdadeiro, e antes do retorno a Pallet |
| 1-73 | Staff Credits | **PENDENTE:** não existe uma cena de créditos exclusiva de Kanto; não substituir os créditos nem a introdução de Decades |

As oito cenas pendentes possuem `pending_reason` explícito nas regras, mas não produzem nenhuma linha `SCENE` no manifesto do jogo e não têm MP3 instalado automaticamente nesta fase.

## Áudio e retorno ao mapa

As músicas de diálogo usam `BlueMusic.with_kanto_scene`. O adaptador:

1. Confirma `BlueRegionalPolicy` em Kanto, MapID compilado realmente existente e não-preview e MP3 acessível;
2. Captura a **BGM original** (nome, volume e pitch) do sistema nativo antes de iniciar a cena;
3. Toca apenas a faixa autorizada durante o diálogo;
4. Restaura **exatamente aquela BGM**, somente quando o mesmo mapa e a mesma região continuam ativos e nenhuma outra trilha de evento ou batalha substituiu a cena.

Se o mapa mudou, houve viagem entre regiões, um evento assumiu a música ou não havia BGM anterior, o código não tenta reconstruir a trilha por palpite. A animação de evolução usa um hook mais simples: substitui o **único** `pbBGMPlay("Evolution")` nativo, sem chamar outra música em paralelo, e deixa a própria rotina de evolução restaurar o som.

### Título principal de Decades preservado

O título musical de Kanto é usado **somente no piloto isolado**, detectado pelo arquivo `Kanto pilot.json` e pelo manifesto compilado de 142 MapIDs. Em `game/Game.exe` principal, mesmo com os mapas Kanto integrados, continua valendo `BlueParadoxTitle::Music` e sua preferência musical original. O menu de três opções `Continuar / Novo jogo / Testar Kanto` não é alterado.

## Por que o Hall of Fame não toca duas vezes

O evento `league_finalize` já recusa a conclusão se faltar alguma vitória na sequência ou se Kanto já tiver sido concluída. A música começa **após** `BlueRegions.complete_league(progress, "KANTO")` confirmar a transação, sem inventar uma sequência de créditos. Em derrota ou tentativa repetida, não existe chamada da faixa do Hall of Fame.

## Auditoria esperada

| Item | Valor |
|---|---:|
| Mapas na tradução SCOPE | 142 |
| MAP (ambiente) | 49 |
| TRANSPORT | 2 |
| BATTLE | 8 |
| BASEPOOL de Decades | 3 |
| ME comprovadas | 6 |
| SCENE comprovadas | **5** |
| SCENE pendentes | **8** |
| MP3 BGM distintos aprovados | **30** |
| MP3 ME distintos aprovados | **6** |
| Catálogo original | 64 (50 BGM / 14 ME) |

## Testes e comandos

~~~powershell
python -m unittest discover -s tests -v
python scripts/music/install_kanto_music.py --audit
python scripts/music/install_kanto_music.py --game .blue-work/kanto-pilot --phase5
python scripts/music/install_kanto_music.py --game .blue-work/kanto-pilot --approved
python scripts/music/compile_kanto_music.py --game .blue-work/kanto-pilot
ruby -c scripts/music/BlueMusic.rb
ruby tests/kanto_music_runtime.rb
ruby tests/kanto_music_battles.rb
ruby tests/kanto_music_me.rb
ruby tests/kanto_music_scenes.rb
~~~

Na [CI de regressão](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/regression.yml) os testes de Python e Ruby são sintéticos, incluindo cancelamento por região/mapa, fallback se o arquivo faltar e retorno à BGM anterior. Na [CI nativa de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml) o Game.exe e o integrador são exercitados com 30 BGM e seis ME instalados e suas associações conferidas.

**Limitação:** teste nativo do projeto e contratos sintéticos não provam por audição a reprodução, loop, fade nem o áudio real durante uma sessão jogável. A Barra 2 de aceite integral da campanha não é alterada.

**Próximo passo:** Fase 6 — aceitação de áudio, codecs, fades, retorno da BGM após eventos, batalha e viagem; inspeção dos cenários ainda pendentes. Implementar créditos, filme de abertura, epílogo ou minijogos **somente quando as respectivas cenas existirem**, sem antecipar gatilhos.
