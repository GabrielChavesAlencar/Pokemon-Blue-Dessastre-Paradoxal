# Kanto — Fase 2/6: músicas ambientes e transporte

**Data:** 12/11/2026. **Escopo:** BGM somente nos mapas compilados de Kanto, sem editar trilhas globais, mapas antigos de Decades ou saves. **BGM habilitada no código não significa reprodução manual comprovada no Game.exe.**

Referências: [plano geral](KANTO_PLANO_APLICAR_MUSICAS.md), [contratos da Fase 1](KANTO_MUSICAS_FASE_1.md), [regras versionadas](../data/kanto-music-rules.json), [compilador](../scripts/music/compile_kanto_music.py).

## Escopo efetivamente implementado

- **49 associações MAP de ambiente**, aprovadas por chave simbólica em `data/kanto-music-rules.json`. Todos os MapIDs numéricos provêm do `Kanto pilot.json` ou do manifesto `Data/blue-kanto-install.json` da instalação real; **nenhum MapID FRLG é usado na engine**.
- **2 associações TRANSPORT**: bicicleta (`1-37 Cycling`) e Surf (`1-52 Surfing`). Somente quando o respectivo estado de veículo está ativo e a região é KANTO, em MapID Kanto fora das prévias. Na montagem, o plugin toca a faixa via `pbCueBGM` depois do estado nativo; em transição e carregamento usa `pbBGMPlay`. Ao desmontar/sair do Surf, o retorno da engine a `autoplay`/`autoplayAsCue` restaura o tema do mapa. Fora da região o método nativo continua prevalecendo.
- **17 BGM distintas necessárias**, instaladas nas pastas `Audio/BGM/Kanto/`: 15 temas para mapas mais 2 para bicicleta e Surf. O instalador de música de Kanto audita hashes e usa criação exclusiva, sem sobrescrever. O piloto traz essas faixas antes de compilar as regras; a integração transacional leva apenas os arquivos ausentes sem conflito; Kanto já instalado sincroniza pelo fluxo `scripts/music/install.py`.
- **0 músicas de batalha, 0 ME e 0 cenas** habilitadas: permanecem para as Fases 3–5.
- Permanece o mapa original e sua música caso a regra esteja desativada, o arquivo falte, o MapID não pertença a Kanto, o save seja antigo/Decades, o arquivo de regras seja inválido ou haja configuração manual mais prioritária.

## Faixas BGM vinculadas

| Nº | Localização ou estado | Status |
|---|---|---|
| 1-06 | PALLET_TOWN | Habilitada |
| 1-08 | OAK_LAB | Habilitada |
| 1-13 | ROUTE_1 | Habilitada |
| 1-15 | PEWTER_CITY | Habilitada |
| 1-17 | VIRIDIAN_FOREST | Habilitada |
| 1-21 | Todos os 9 `*_CENTER` presentes e fora das prévias | Habilitada |
| 1-25 | Os 8 `*_GYM` presentes e fora das prévias (ambiente, não batalha) | Habilitada |
| 1-34 | MT_MOON_1F / B1F / B2F | Habilitada |
| 1-35 | VERMILION_CITY | Habilitada |
| 1-36 | Os cinco mapas presentes de SS_ANNE_* | Habilitada |
| 1-40 | CELADON_CITY | Habilitada no mapa experimental existente; não promove eventos |
| 1-47 | SILPH_1F até SILPH_11F | Habilitada nos 11 andares não-preview |
| 1-50 | FUCHSIA_CITY | Habilitada |
| 1-55 | CINNABAR_ISLAND | Habilitada |
| 1-56 | MANSION_1F / 2F / 3F / B1F | Habilitada |
| 1-37 | Bicicleta de Kanto (somente montado) | Habilitada |
| 1-52 | Surf de Kanto (somente navegando) | Habilitada |

**Observação:** a ativação em uma área experimental significa apenas que sua geometria/MapID consta do piloto e que a regra de música está vinculada; não certifica interações, NPCs ou campanha finalizados.

### MapIDs compilados comprovados no piloto da CI

Os números abaixo foram observados na **cópia isolada do Blue/Decades usada pela CI** (run [43294567862](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43294567862)). **Não devem ser hardcodados**: cada instalação usa seu próprio arquivo de tradução de IDs, e saves existentes não são renumerados.

| MapID na CI | Mapa Kanto | Faixa BGM |
|---:|---|---:|
| 300 | `PALLET_TOWN` | 1-06 |
| 301 | `OAK_LAB` | 1-08 |
| 303 | `ROUTE_1` | 1-13 |
| 305 | `VIRIDIAN_CENTER` | 1-21 |
| 310 | `VIRIDIAN_FOREST` | 1-17 |
| 311 | `PEWTER_CITY` | 1-15 |
| 312 | `PEWTER_GYM` | 1-25 |
| 313 | `PEWTER_CENTER` | 1-21 |
| 317 | `MT_MOON_CENTER` | 1-21 |
| 318 | `MT_MOON_1F` | 1-34 |
| 319 | `MT_MOON_B1F` | 1-34 |
| 320 | `MT_MOON_B2F` | 1-34 |
| 322 | `CERULEAN_CENTER` | 1-21 |
| 324 | `CERULEAN_GYM` | 1-25 |
| 330 | `VERMILION_CITY` | 1-35 |
| 331 | `VERMILION_CENTER` | 1-21 |
| 333 | `VERMILION_GYM` | 1-25 |
| 335 | `SS_ANNE_1F` | 1-36 |
| 336 | `SS_ANNE_2F` | 1-36 |
| 337 | `SS_ANNE_CAPTAIN` | 1-36 |
| 338 | `SS_ANNE_B1F` | 1-36 |
| 339 | `SS_ANNE_DECK` | 1-36 |
| 341 | `CELADON_CITY` | 1-40 |
| 342 | `CELADON_CENTER` | 1-21 |
| 350 | `CELADON_GYM` | 1-25 |
| 354 | `FUCHSIA_CITY` | 1-50 |
| 355 | `FUCHSIA_CENTER` | 1-21 |
| 357 | `FUCHSIA_GYM` | 1-25 |
| 380 | `SAFFRON_CENTER` | 1-21 |
| 382 | `SAFFRON_GYM` | 1-25 |
| 388 | `SILPH_1F` | 1-47 |
| 389 | `SILPH_2F` | 1-47 |
| 390 | `SILPH_3F` | 1-47 |
| 391 | `SILPH_4F` | 1-47 |
| 392 | `SILPH_5F` | 1-47 |
| 393 | `SILPH_6F` | 1-47 |
| 394 | `SILPH_7F` | 1-47 |
| 395 | `SILPH_8F` | 1-47 |
| 396 | `SILPH_9F` | 1-47 |
| 397 | `SILPH_10F` | 1-47 |
| 398 | `SILPH_11F` | 1-47 |
| 417 | `CINNABAR_ISLAND` | 1-55 |
| 418 | `CINNABAR_CENTER` | 1-21 |
| 420 | `CINNABAR_GYM` | 1-25 |
| 422 | `MANSION_1F` | 1-56 |
| 423 | `MANSION_2F` | 1-56 |
| 424 | `MANSION_3F` | 1-56 |
| 425 | `MANSION_B1F` | 1-56 |
| 426 | `VIRIDIAN_GYM` | 1-25 |

Mapas não ativados: `ROUTE_4` → MapID **316** (trecho não verificado); `SILPH_LOBBY` → MapID **387** (prévia).

## Pendências explícitas, sem inventar mapas

- `ROUTE_4` / `1-32`: a fonte confirma a rota, mas a música é específica da saída de Mt. Moon para Cerulean; associar ao MapID inteiro sem validar o trecho poderia tocar no segmento errado. **PENDENTE_TRANSICAO**, sem ativação.
- `SILPH_LOBBY` / `1-47`: está na lista dos 45 mapas em prévia. **PREVIEW_ONLY**, sem BGM; Silph 1F–11F permanecem vinculados.
- Não constam do manifesto atual: Lavender / Pokémon Tower (`1-38`, `1-39`), Rocket Game Corner/Hideout (`1-41`, `1-45`), Pokémon Net Center (`1-57`), Sevii (`1-59`). A estrada `1-48` não tem correspondência segura para Kanto atual.
- Não foram atribuídos temas por suposição para Viridian City, Cerulean City, Saffron City, Safari Zone, Victory Road ou Indigo Plateau.

## Instalação e testes reproduzíveis

Para preparação automática do piloto, o fluxo `scripts/regions/pilot.py` copia os 17 MP3s antes de compilar os mapas. Para importação inicial, `scripts/regions/install_kanto.py --apply` inclui esses MP3s na transação. Para Kanto já instalado, `scripts/music/install.py` sincroniza as faixas e recompila o escopo, mantendo a música manual de Decades.

Comandos de auditoria (a partir da raiz):

~~~powershell
python scripts/music/install_kanto_music.py --audit
python -m unittest discover -s tests -p "test_kanto_music*.py" -v
ruby -c scripts/music/BlueMusic.rb
ruby tests/kanto_music_runtime.rb
python scripts/music/compile_kanto_music.py --game .blue-work/kanto-pilot
python scripts/music/install_kanto_music.py --game .blue-work/kanto-pilot --phase2
~~~

A [CI de regressão](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/regression.yml) testa Python/Ruby/Chromium e hashes dos 64 MP3, e a [CI nativa de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml) exige **142 linhas SCOPE, 49 MAP, 2 TRANSPORT, 0 BATTLE, 17 MP3s instalados** tanto no piloto quanto no jogo descartável integrado.

## Limites de comprovação

A CI comprova mapa compilado, presença de arquivo, integridade, montagem dos plugins e verificações nativas existentes. **Não comprova áudio ouvido** em uma partida real e interativa (loop MP3, fade audível, troca de região durante música, interrupção/restauração de batalha e salvamento completo do usuário). Esses pontos exigem observação manual no Windows ou prova nativa específica e seguem marcados **BLOQUEADA_AMBIENTE / TESTE_NATIVO_PENDENTE**.

**Barra 2 — Aceite integral:** sem mudança; associar músicas não equivale a aprovar jogabilidade.

**Próximo passo:** Fase 3 — associar BGM de batalhas de Kanto por classe real de adversário, vitória do líder, rival Campeão e temas especiais, preservando o sorteio global de Decades.
