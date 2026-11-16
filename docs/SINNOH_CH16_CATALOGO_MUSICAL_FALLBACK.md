# Sinnoh — CH16: catálogo musical e fallback seguro via BlueMusic

**Data:** 16/11/2026 · **Resultado:** CH16 concluída como **contrato estático e testes isolados**. Nenhum áudio instalado, licenciado ou reproduzido no Game.exe/JoiPlay.

Arquivos: [catálogo CH16](../data/regions/sinnoh-music-ch16.json), [auditor Python](../scripts/music/audit_sinnoh_music_ch16.py), [resolvedor Ruby inerte](../scripts/music/SinnohMusicContracts.rb) e [tabela musical de referência](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md).

## Inventário: 46 entradas simbólicas, sem músicas

O [planejamento já existente](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) descreve **45 chaves musicais originais** de Platinum (tema de região, cidade, rota, batalha, cena, Surf e vinheta). A CH16 registra **46 cues separadas** porque a referência única `SINNOH_HALL_OF_FAME` foi desdobrada em `SINNOH_HALL_OF_FAME_BGM` e `SINNOH_HALL_OF_FAME_ME`, preservando `source_key` para rastreabilidade.

| Grupo simbólico | Quantidade |
|---|---:|
| city | 14 |
| route | 6 |
| cave | 7 |
| scene | 4 |
| battle | 10 |
| transport | 1 |
| post_game | 1 |
| me | 3 |
| **Total** | **46** |

São **43 BGM e 3 ME**. As referências incluem Twinleaf e Route 201 dia/noite, Sandgem, Jubilife, Oreburgh, Eterna, Hearthome, Canalave, Snowpoint, Sunyshore, Mt. Coronet, Oreburgh Mine, Galactic HQ, Distortion World, Barry, líderes, Galactic, Cyrus, Giratina, Elite Four, Cynthia e Hall of Fame.

Cada registro mantém `track_path`, `track_sha256`, `physical_map_id`, `physical_event_id`, `loop_start_ms`, `loop_end_ms`, `fade_seconds`, `volume` e `pitch` **nulos**. `source_verified=false`, `license_verified=false`, `compiled_binding_verified=false` e `enabled=false` permanecem obrigatórios. Não atribuir nomes de arquivo, MapIDs, durações, loops ou licenças por suposição.

## Prioridade e propriedade do áudio

A prioridade documentada, protegida pelo auditor e pelo resolvedor de planejamento, é:

1. **Áudio explicitamente definido pelo evento da engine**, incluindo `nextBattleBGM`, sempre preservado; não atropelar música específica do jogador.
2. **Cena nativa verificada**, como Giratina, Distortion World, pré-Cynthia ou Hall of Fame, apenas futuramente quando houver handler e arquivo aprovado.
3. **Configuração existente no BlueMusic**, inclusive manual, aleatória ou `mute`, prevalece sobre qualquer tentativa de fallback regional.
4. **Batalha regional verificada**, com treinador/espécie nativos para distinguir selvagem, líder, Elite Four, Cyrus e Cynthia.
5. **Transporte regional válido**, por exemplo Surf, com estado real da engine.
6. **Mapa/ambiente regional validado**, preservando dia/noite e temas que já existam no Blue.
7. **Fallback nativo**, preservando áudio atual e configuração de Decades, Kanto, Johto ou Hoenn.

Essa ordem é um **contrato para integração futura**, e não um hook já instalado. `BlueSinnohMusicContracts.resolve` consulta `BlueMusic.entry` de forma somente leitura e **nunca retorna um objeto de áudio tocável**; todas as cues de Sinnoh estão desabilitadas até haver direitos, arquivos reais, mapa/evento identificado e testes nativos.

## Fallback, fades e loops

- **Arquivo ausente, licença/sha não validados ou cue fora de escopo:** manter o áudio que o motor já escolheu. Não forçar silêncio ou renomear uma trilha nativa.
- **Após batalha:** delegar ao motor o retorno à BGM do mapa/horário atual.
- **ME de insígnia, item e Hall of Fame:** apenas depois de confirmação do evento; após a vinheta, delegar ao motor a retomada da trilha anterior.
- **Cena com BGM temporária:** restaurar trilha anterior apenas se continuar no mesmo mapa e o evento ainda possuir o áudio. Nunca ressuscitar BGM após mudança de mapa/região ou novo evento de áudio.
- **Cue idêntica/reload:** não reiniciar a mesma trilha nem criar loop duplicado.
- **Fade, volume, tom e loop:** desconhecidos, portanto não inserir valores 0, 100 ou 0,4 s como se refletissem os arquivos reais. Usar os defaults da engine até análise posterior de áudio permitido.

Uma marcação Ruby como evento confirmado é **dado sintético para testar a máquina de decisões**, não prova de que o usuário chegou ao evento na partida. Sem `Audio/BGM/Sinnoh` ou `Audio/ME/Sinnoh` licenciado, a CH16 não habilita nenhuma música.

## Direitos e preservação das demais regiões

Não foi criado, copiado, exportado ou publicado **nenhum MP3, OGG, WAV, MIDI ou arranjo protegido**. Os arquivos `BlueMusic.rb`, `data/kanto-music*.json`, `data/johto-music*.json`, dados compartilhados de áudio, mapas, PBS e saves foram **preservados**, sem alteração. O módulo de Sinnoh **não é chamado por `BlueMusic.install`** e não executa `pbBGMPlay`, `pbMEPlay` ou `pbCueBGM`.

## Testes de auditoria e CI

```bash
python scripts/music/audit_sinnoh_music_ch16.py
python -m unittest discover -s tests -p 'test_sinnoh_music_ch16.py' -v
ruby -c scripts/music/SinnohMusicContracts.rb
ruby tests/sinnoh_music_ch16_runtime.rb scripts/music/BlueMusic.rb scripts/music/SinnohMusicContracts.rb data/regions/sinnoh-music-ch16.json
```

[**CI 43977207679 — Sinnoh isolada aprovada**](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43977207679): **23/23 testes CH16**, integração Ruby com `BlueMusic.rb` real e **347/347 testes Python isolados de Sinnoh**. Verificações negativas rejeitam direitos fictícios, arquivos inventados, hooks, MapIDs, musicas fora da região, alteração de prioridade, fade/loop falsos, replay e falsa aprovação jogável.

**Ainda não executado:** audição e loop/fade reais, testes de playback, autorização/distribuição de arquivos, integração com mapas e eventos da engine, Game.exe Windows e JoiPlay Android. **Barras oficiais preservadas:** A 8/32 (25%), B/C/D 0/13; Barra E 16/20 (80%) contabiliza somente código, contratos e testes.
