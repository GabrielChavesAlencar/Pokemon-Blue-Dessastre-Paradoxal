# Kanto — Plano para aplicar as 64 músicas por este chat

> **Plano por fases, não aceite final de jogabilidade.** Estado de 12/11/2026: 64 MP3 publicados (**50 BGM / 14 ME**, 135.768.381 bytes). A [Fase 1](KANTO_MUSICAS_FASE_1.md) isolou região/MapIDs; a [Fase 2](KANTO_MUSICAS_FASE_2.md) habilitou BGM de ambientes em 49 mapas não-preview e bicicleta/Surf; a [Fase 3](KANTO_MUSICAS_FASE_3.md) acrescentou oito temas de batalhas/vitórias por identidade comprovada, totalizando 25 BGM selecionadas. A [Fase 4](KANTO_MUSICAS_FASE_4.md) catalogou as 14 ME e ativou apenas 6 com gatilhos reais de sucesso (8 seguem PENDENTE_EVENTO). A [Fase 5](KANTO_MUSICAS_FASE_5.md) adicionou cinco cenas comprovadas (título do piloto, Oak, rival, evolução e Hall of Fame), e oito cenas permanecem PENDENTE_EVENTO, incluindo abertura cinematográfica e créditos. A [Fase 6](KANTO_MUSICAS_RESULTADOS.md) adicionou auditoria de decodificação integral dos 64 MP3, prova nativa de BGM/ME, correções de cenas e matriz 64/64: 36 VINCULADA, 21 PENDENTE_EVENTO e 7 MAPA_AUSENTE. Kanto continua como `prototype`. Audição real (loop/fade/ME em caixas de som) permanece BLOCKED_ENV, sem aumentar a Barra 2.

## Objetivo e como trabalharemos aqui no ChatGPT

Aplicar progressivamente a trilha de Kanto sem exigir que o usuário configure 64 faixas manualmente. Em cada mensagem, o usuário poderá pedir **“Aplique a Fase N de docs/KANTO_PLANO_APLICAR_MUSICAS.md”**. O assistente deverá **implementar código de verdade**, criar branch/PR, verificar a CI, corrigir falhas e publicar no GitHub quando validado — não simplesmente reescrever o plano.

O jogo completo em `game/` é uma instalação **local ignorada pelo Git**. As mudanças implementadas por este chat precisam ser **scripts e configurações reproduzíveis**, que o projeto aplique quando o usuário sincronizar/reconstruir o jogo. Nenhum teste somente no GitHub comprova que a faixa foi realmente reproduzida no `Game.exe`.

Referências existentes:
- [`data/kanto-music.json`](../data/kanto-music.json): catálogo canônico com número, nome, tipo, tamanho, SHA Git e finalidade de cada faixa.
- [`KANTO_MUSICAS_MAPEAMENTO.md`](KANTO_MUSICAS_MAPEAMENTO.md): análise das 64 músicas.
- [`scripts/music/install_kanto_music.py`](../scripts/music/install_kanto_music.py): já copia os arquivos para `game/Audio/BGM/Kanto` e `game/Audio/ME/Kanto`, sem sobrescrever.
- [`scripts/music/BlueMusic.rb`](../scripts/music/BlueMusic.rb): gerencia BGM de mapa, combate e vitória, mas hoje suas opções de combate estão no escopo **global**.
- [`scripts/music/install.py`](../scripts/music/install.py): grava/adapta configurações do plugin e deve preservar escolhas já existentes.
- [`data/regions/kanto-source.json`](../data/regions/kanto-source.json): os 142 nomes/IDs de origem; [`scripts/regions/pilot_catalog.py`](../scripts/regions/pilot_catalog.py) lê o plano compilado.
- [`scripts/regions/pilot.py`](../scripts/regions/pilot.py), [`install_kanto.py`](../scripts/regions/install_kanto.py): preparação e instalação do piloto.
- [`docs/EDITOR_MUSICAS.md`](EDITOR_MUSICAS.md): edição manual já existente, que **não deve perder as preferências do usuário**.
- [`docs/KANTO_CODEX_TESTES_E2E.md`](KANTO_CODEX_TESTES_E2E.md): requisitos de evidência visual para não confundir testes simulados com jogo real.

### Regras que todas as fases devem respeitar

1. **Só Kanto.** Não substituir músicas de Decades, outras regiões, arena, saves antigos ou playlists globais. Validar a região ativa, por exemplo via `BlueRegionalPolicy.state`/`BlueRegions`, com fallback seguro quando o estado estiver indisponível.
2. **Não hardcodar MapIDs da fonte.** O mapa original FRLG `5=PALLET_TOWN`, `9=ROUTE_1` ou `25=PEWTER_CITY` não precisa ter esses IDs no jogo instalado. Usar `Kanto pilot.json` para traduzir **source ID → ID real**; preservar o mapeamento histórico de saves.
3. **Não alterar MP3s nem eventos originais do Decades.** A lógica deve usar adaptadores, configurações e cópias isoladas. Implementação idempotente e com rollback/backup quando escrever a configuração local.
4. **Música ambiente BGM ≠ fanfarra ME.** O plugin BlueMusic atual valida arquivos em `Audio/BGM/`; para os 14 ME, implementar playback na API correta da engine e restaurar a BGM quando adequado. Não transformar um ME em BGM com loop.
5. **Eventos e músicas customizadas têm prioridade definida.** Não apagar o sorteio existente de batalha. Não sobrepor uma música explícita de cena por uma música genérica de mapa.
6. **Fallback seguro.** Caso a música específica não exista, o mapa/evento ainda não esteja instalado ou o evento falhe, manter o áudio original e marcar o caso como pendente, sem inventar correspondências.
7. **Qualidade e segurança.** Validar 64 arquivos/hashes, áudio nativo, loop/fade, volumes, retorno de menus, saves e viagem Kanto↔Decades; não alterar a Barra 2 de aceite integral por adicionar música.
8. **Direitos de distribuição.** Os MP3s parecem ser músicas oficiais de Pokémon e o repositório é público; a publicação existente não prova autorização de redistribuição. Não importar novas gravações de terceiros sem revisar os direitos.

## Fase 0 — Auditoria e linha de base (sem trocar músicas do jogo)

**Resultado técnico implementado:** [auditoria e baseline da Fase 0](KANTO_MUSICAS_FASE_0.md), com script `scripts/music/audit_kanto_phase0.py` e verificações da CI. Foram confirmadas **64 faixas (50 BGM/14 ME)**, **142 mapas/45 prévias** e os hooks existentes/pendentes. **Nenhum áudio foi ativado ou testado tocando no Game.exe**; a Fase 1 é o próximo passo.


**Ação:** conferir os 64 MP3 e confirmar que o jogo local ou a cópia piloto tem suporte a BGM/ME. Executar:
```powershell
python scripts/music/install_kanto_music.py --audit
python -m unittest discover -s tests -p "test_kanto_music*.py"
```

**Entregáveis:** inventário `64/64`; hash/tamanho; registro de quais métodos do plugin tocam `BGM`, `ME` e `Victory BGM`; relatório dos destinos que existem atualmente. Confirmar que a instalação do jogo não será sobrescrita.

**Aceite:** auditoria aprovada, nenhum save ou áudio original modificado.

## Fase 1 — Resolver região e MapIDs compilados (PR obrigatório antes das demais)

Criar:
- `data/kanto-music-rules.json` como fonte versionada das associações por **nomes simbólicos** de mapa, cena, classe de batalha, evento e faixa do catálogo.
- `scripts/music/compile_kanto_music.py` (nome sugerido) para validar essas regras, cruzá-las com `data/kanto-music.json` e com `Kanto pilot.json`, resolver os MapIDs reais sem renumerá-los, e gerar somente os registros relativos a Kanto.
- Um adaptador regional no `BlueMusic.rb` (ou plugin próprio) para carregar regras só quando o estado for `KANTO`, sem sobrescrever as chaves `global` como `wild`, `trainer`, `gym`, `wildVictory` e `trainerVictory` de Decades. A preferência manual explícita do usuário deve vencer o padrão regional nos casos documentados.
- Instalação segura no fluxo de `pilot.py`/`install_kanto.py`, aplicada a uma cópia isolada antes de integrar ao `game/` local. **Não apagar `Data/blue-music.json` existente**.

**Testar:** carregamento Kanto, retorno Decades, saves sem região inicializada, mapas prévia, config antiga, modo personalizado/sorteio e duplicação sem efeitos. Só avançar após CI verde.

## Fase 2 — BGM de cidades, rotas, interiores e transporte (25 faixas)

**Fase 2 implementada:** ver [resultado e limitações](KANTO_MUSICAS_FASE_2.md). Foram aprovadas 49 associações de ambiente por MapID compilado, mais duas trilhas condicionais de bicicleta/Surf (17 MP3 distintos). `SILPH_LOBBY` continua em prévia; `ROUTE_4` aguarda comprovação do trecho após Mt. Moon. Faixas de localidades ausentes continuam pendentes. Este vínculo não comprova som audível nem modifica a Barra 2 de aceite.

Aplicar BGM por **chaves de mapas**. Onde houver vários andares, conferir quais estão realmente instalados/ativos; o status de 45 mapas como prévias não deve ser falsamente promovido.

| Grupo/ação | Faixa(s) | Onde usar |
|---|---|---|
| `PALLET_TOWN` e `OAK_LAB` | `1-06` / `1-08` | Exterior de Pallet; laboratório separado |
| `ROUTE_1` | `1-13` | Caminho para Viridian |
| `VIRIDIAN_FOREST` | `1-17` | Floresta |
| `PEWTER_CITY` | `1-15` | Cidade |
| `MT_MOON_1F/B1F/B2F` | `1-34` | Andares ativos |
| `ROUTE_4` | `1-32` | Priorizar trecho de saída de Mt. Moon após conferir transição |
| `*_CENTER` | `1-21` | Pokémon Centers, não Poké Marts |
| `*_GYM` | `1-25` | Ambiente do ginásio, não a música de batalha |
| `VERMILION_CITY` e `SS_ANNE_*` | `1-35` / `1-36` | Cidade e navio; entrada/saída sem vazamento |
| `CELADON_CITY` | `1-40` | Cidade |
| Rocket Game Corner / Rocket Hideout | `1-41` / `1-45` | Só quando o interior/evento existir |
| `SILPH_LOBBY` e `SILPH_1F`–`11F` | `1-47` | Andares de Silph Co. efetivamente utilizáveis |
| `FUCHSIA_CITY` | `1-50` | Cidade |
| `CINNABAR_ISLAND`, `MANSION_*` | `1-55` / `1-56` | Ilha e andares de Mansion |
| Bicicleta / Surf | `1-37` / `1-52` | Somente durante o estado; restaurar ao parar |
| Lavender, Pokémon Tower, estrada para Fuchsia, Net Center, Sevii | `1-38`, `1-39`, `1-48`, `1-57`, `1-59` | **Só se o mapa existir.** Não inventar Lavender/Sevii em Kanto atual |

**Importante:** o pacote não apresenta uma faixa intitulada “Cerulean City”, “Saffron City”, “Viridian City”, “Safari Zone”, “Victory Road” ou “Indigo Plateau”. Deixar o **tema original** onde não houver correspondência aprovada, em vez de atribuir música por suposição.

**Verificações:** mudança entre exterior/interior, reentrada, interrupção por combate, bicicleta, Surf, troca de região, mapa de prévia e fallback por arquivo ausente. Publicar commit/PR com lista de MapIDs realmente associados.

## Fase 3 — Batalhas, adversários especiais e vitórias (12 faixas)

**Fase 3 implementada:** ver [código, prioridades e evidências](KANTO_MUSICAS_FASE_3.md). Oito BGM de combate/vitória foram ativadas com guardas de classe real de adversário e espécie Legendary, distinção de Blue Campeão, assinatura dos sorteios padrão de Decades e respeito a músicas de eventos e personalizadas. As introduções 1-20/1-33/1-46 e a cena 1-26 aguardam gatilho auditado; não são tocadas automaticamente. Nenhum ME foi ativado.

| Contexto (somente Kanto) | Introdução ou batalha | Vitória |
|---|---|---|
| Selvagem comum | `1-18 Battle! (Wild Pokémon)` | `1-19 Victory! (Wild Pokémon)` |
| Treinador comum | `1-11 Battle! (Trainer)` | `1-12 Victory! (Trainer)` |
| Líder de ginásio | `1-27 Battle! (Gym Leader)` | `1-28 Victory! (Gym Leader)` |
| Lendário | `1-53 Battle! (Legendary Pokémon)` | Seguir regra comprovada do evento |
| Blue como **Campeão** no final da Liga | `1-70 Final Battle! (Rival)` | Fluxo de pós-Liga; não é tema de qualquer rival |
| Introdução de treinador homem/mulher/vilão | `1-20`, `1-33`, `1-46` | São entradas, não BGM de batalha |
| Cena tensa de duelo | `1-26` | Somente evento que pedir explicitamente |

**Pendência técnica conhecida:** o plugin atual implementa `wildVictory` e `trainerVictory`, não vitória específica de ginásio. Criar essa distinção para Kanto, com testes por oponente real, sem afetar a configuração global. Em batalhas duplas, Master e revanche, evitar trocar o tema no meio da luta; respeitar escolha de eventos especiais e restauração ao derrotar/fugir.

## Fase 4 — As 14 vinhetas ME disparadas por eventos

**Fase 4 implementada parcialmente por disponibilidade real de eventos:** o [relatório auditável](KANTO_MUSICAS_FASE_4.md) confirma seis vinhetas ativas (Pokémon, item, cura na casa da mãe, insígnia, evolução e captura), com oito vinhetas catalogadas mas explicitamente pendentes de um evento real. O instalador importa apenas seis MP3 ME, sem tocar em Decades. **Não interpretar 14 faixas catalogadas como 14 eventos já implementados.**

| Número | Quando usar — nunca tocar antes da condição |
|---|---|
| `1-01` | Game Freak Logo, caso exista uma cena de logotipo pertinente |
| `1-09` | Pokémon efetivamente recebido |
| `1-14` | Item efetivamente recebido |
| `1-22` | Evento do canto de Jigglypuff |
| `1-23` | Cura efetivamente finalizada no Centro Pokémon |
| `1-29` | Insígnia concedida **após vitória**, sem duplicação |
| `1-31` | Pokémon evoluiu com sucesso |
| `1-42` | Vitória de minijogo, se implementado |
| `1-43` | Jackpot, se implementado |
| `1-44` | Pokémon Printer, se implementado |
| `1-49` | Poké Flute realmente usada em evento (por exemplo Snorlax) |
| `1-51` | Golpe apagado após confirmação |
| `1-54` | Captura bem-sucedida, não tentativa que falhou |
| `1-58` | Avaliação da Pokédex feita por Oak |

Implementar hook ME com `Audio/ME/Kanto/` na engine e respeitar prioridade, volume, fade/reentrada da música ambiente e controles cancelados. Não tocar na abertura da tela ou na simples visita ao NPC sem completar a ação.

## Fase 5 — Abertura, cenas especiais e pós-jogo (13 faixas)

**Fase 5 implementada, com escopo auditado:** [relatório e eventos comprovados](KANTO_MUSICAS_FASE_5.md). Cinco faixas foram ativadas: 1-03 (título exclusivo do piloto), 1-07 (Oak após entrega de pacote), 1-10 (rival antes de três lutas reais), 1-30 (animação de evolução) e 1-72 (Hall de Kanto após Liga completa). **Oito continuam PENDENTE_EVENTO**: 1-02, 1-04, 1-05, 1-16, 1-24, 1-60, 1-71 e 1-73; em especial NÃO tocar créditos sem sequência de créditos real. Sem mudança no título de Decades.

| Número | Cena/uso |
|---|---|
| `1-02` | Opening Movie de Kanto, se disponível |
| `1-03` | Tela de título **contextual** de Kanto, sem substituir menu de Decades |
| `1-04` | Tutorial de Kanto |
| `1-05` | Introdução de Professor Oak ao mundo Pokémon |
| `1-07` | Encontro/conversa importante com Oak |
| `1-10` | Rival aparece antes de uma batalha |
| `1-16` | Teachy TV, se existir |
| `1-24` | Guia/ajuda em evento ativo |
| `1-30` | Animação de evolução |
| `1-60` | Minijogo Pokémon Jump, se existir |
| `1-71` | Epílogo após conclusão efetiva da campanha |
| `1-72` | Hall of Fame **apenas após a vitória real** |
| `1-73` | Créditos após conclusão da Liga, respeitando Decades |

Conferir Liga Lorelei → Bruno → Agatha → Lance → Blue, derrota não libera Hall, repetições não concedem prêmio duas vezes, e voltar a Decades restaura sua trilha. Se não houver evento real, registrar **PENDENTE_EVENTO** no relatório, não ativar antecipadamente.

## Fase 6 — Regressões e instalação segura

**Implementação técnica:** ver [resultados 64/64 e plano de audição](KANTO_MUSICAS_RESULTADOS.md). A auditoria FFmpeg/FFprobe é obrigatória na CI e decodifica cada MP3 inteiro; as provas de API BGM/ME na engine são distintas de áudio perceptível. Corrigido o retorno ao silêncio após uma cena em mapas sem música anterior. **As 28 faixas sem vínculo não foram ativadas artificialmente.**

1. Validar as **64 entradas** do catálogo contra arquivos reais e verificar soma 50 BGM + 14 ME, ausência de duplicação, faixas com destino e integridade SHA.
2. Simular o plano de instalação na cópia isolada antes de aplicar; não reescrever `MapXXX.rxdata` do Decades ou um arquivo `Data/blue-music.json` personalizado.
3. Testar prioridades: evento explícito > fallback ambiental (conforme regra), preferências manuais existentes, Kanto/Decades, save legado, líder/selvagem/rival/lendário, versão Master, vitória/derrota.
4. Rodar `python -m unittest discover -s tests`, `python scripts/music/install_kanto_music.py --audit`, teste de editor, workflows de Blue Studio/portal e CI nativa de Kanto. Adicionar novos testes sempre que uma fase criar novos hooks.
5. No Windows com `Game.exe` de cópia descartável, verificar se o codec MP3 toca realmente: **loop, fade, retorno após ME, sem cortes, volume e ausência de travamentos**. Sem esse ambiente, registrar `BLOCKED_ENV` em vez de afirmar áudio testado.
6. Criar `docs/KANTO_MUSICAS_RESULTADOS.md` com cada faixa marcada `VINCULADA`, `TESTADA_NA_ENGINE`, `PENDENTE_EVENTO`, `MAPA_AUSENTE` ou `BLOQUEADA_AMBIENTE`; PR/commit por fase. Não incrementar a Barra 2 de jogabilidade apenas por concluir áudio.

## Matriz das 64 músicas (cobertura completa)

O estágio previsto abaixo não quer dizer que a faixa já esteja aplicada. As finalidades são baseadas nos nomes e catálogo existentes, **não em reprodução auditada**.

| Nº | Faixa original | Canal | Etapa | Utilização prevista |
|---:|---|---|---:|---|
| 01 | Game Freak Logo | ME | F4 | Vinheta breve do logotipo na abertura |
| 02 | Opening Movie | BGM | F5 | Trilha da animação/cena inicial |
| 03 | Title Screen | BGM | F5 | Tela de título e menu principal |
| 04 | Game Tutorial | BGM | F5 | Tutorial e explicação de comandos |
| 05 | Welcome to the World of Pokémon! | BGM | F5 | Introdução do Professor Oak ao mundo Pokémon |
| 06 | Pallet Town | BGM | F2 | Tema ambiente de Pallet Town |
| 07 | Professor Oak | BGM | F5 | Diálogo e aparições do Professor Oak |
| 08 | Professor Oak's Laboratory | BGM | F2 | Interior do laboratório do Professor Oak |
| 09 | Obtained a Pokémon! | ME | F4 | Vinheta ao receber um Pokémon |
| 10 | Rival Appears | BGM | F5 | Aparição do rival antes da cena ou duelo |
| 11 | Battle! (Trainer) | BGM | F3 | Batalhas normais contra treinadores |
| 12 | Victory! (Trainer) | BGM | F3 | Música de vitória contra treinador; manter no canal BGM para compatibilidade com BlueMusic |
| 13 | Road to Viridian City - Leaving Pallet Town | BGM | F2 | Rota 1, saída de Pallet em direção a Viridian |
| 14 | Obtained an Item! (Version 1) | ME | F4 | Vinheta ao obter um item comum |
| 15 | Pewter City | BGM | F2 | Tema ambiente da cidade de Pewter |
| 16 | Teachy TV Menu | BGM | F5 | Tela/menu da Teachy TV |
| 17 | Viridian Forest | BGM | F2 | Tema da Viridian Forest |
| 18 | Battle! (Wild Pokémon) | BGM | F3 | Combates contra Pokémon selvagens |
| 19 | Victory! (Wild Pokémon) | BGM | F3 | Música de vitória em encontro selvagem; usar canal BGM |
| 20 | Trainer Appears (Boy) | BGM | F3 | Tema de introdução de treinador masculino |
| 21 | Pokémon Center | BGM | F2 | Ambiente interno de Pokémon Center |
| 22 | Jigglypuff's Song | ME | F4 | Canto musical de Jigglypuff em evento |
| 23 | Pokémon Healed | ME | F4 | Vinheta de Pokémon restaurados no Centro Pokémon |
| 24 | Guide | BGM | F5 | Cena ou orientação de guia/tutorial |
| 25 | Pokémon Gym | BGM | F2 | Ambiente interno de ginásios Pokémon |
| 26 | Tense Battle! | BGM | F3 | Clima de tensão antes ou durante um confronto importante |
| 27 | Battle! (Gym Leader) | BGM | F3 | Batalhas contra líderes de ginásio |
| 28 | Victory! (Gym Leader) | BGM | F3 | Música de vitória contra líder; manter no canal BGM |
| 29 | Obtained a Gym Badge! | ME | F4 | Vinheta de recebimento de insígnia do ginásio |
| 30 | Evolution | BGM | F5 | Trilha de animação de evolução |
| 31 | Congratulations, Your Pokémon Evolved! | ME | F4 | Vinheta de conclusão da evolução |
| 32 | Road to Cerulean City - Leaving Mt. Moon | BGM | F2 | Rota 4, saída do Mt. Moon para Cerulean |
| 33 | Trainer Appears (Girl) | BGM | F3 | Tema de introdução de treinadora feminina |
| 34 | Mt. Moon | BGM | F2 | Tema de exploração do Mt. Moon |
| 35 | Vermilion City | BGM | F2 | Tema ambiente de Vermilion City |
| 36 | S.S. Anne | BGM | F2 | Tema de exploração do navio S.S. Anne |
| 37 | Cycling | BGM | F2 | Tema de deslocamento de bicicleta |
| 38 | Lavender Town | BGM | F2 | Tema ambiente de Lavender Town |
| 39 | Pokémon Tower | BGM | F2 | Tema de exploração da Pokémon Tower |
| 40 | Celadon City | BGM | F2 | Tema ambiente de Celadon City |
| 41 | Rocket Game Corner | BGM | F2 | Tema ambiente do Rocket Game Corner |
| 42 | Winning! | ME | F4 | Vinheta ao ganhar em minijogo |
| 43 | Jackpot! | ME | F4 | Vinheta de jackpot em minijogo |
| 44 | Pokémon Printer | ME | F4 | Vinheta musical da impressora Pokémon |
| 45 | Rocket Hideout | BGM | F2 | Tema de exploração do Rocket Hideout |
| 46 | Trainer Appears (Bad Guy) | BGM | F3 | Tema de entrada/aparição de antagonista |
| 47 | Silph Co. | BGM | F2 | Tema de exploração do prédio Silph Co. |
| 48 | Road to Fuchsia City - Leaving Lavender Town | BGM | F2 | Rota desde Lavender em direção a Fuchsia |
| 49 | The Poké Flute | ME | F4 | Execução musical da Poké Flute, usada em evento como Snorlax |
| 50 | Fuchsia City | BGM | F2 | Tema ambiente de Fuchsia City |
| 51 | Move Deleted | ME | F4 | Vinheta ao apagar um movimento |
| 52 | Surfing | BGM | F2 | Tema de navegação com Surf |
| 53 | Battle! (Legendary Pokémon) | BGM | F3 | Batalha contra Pokémon lendário |
| 54 | Caught a Pokémon! | ME | F4 | Vinheta ao capturar um Pokémon |
| 55 | Cinnabar Island | BGM | F2 | Tema ambiente de Cinnabar Island |
| 56 | Pokémon Mansion | BGM | F2 | Tema de exploração da Pokémon Mansion |
| 57 | Pokémon Net Center | BGM | F2 | Ambiente do Pokémon Net Center |
| 58 | Professor Oak's Evaluation | ME | F4 | Vinheta de avaliação da Pokédex pelo Professor Oak |
| 59 | Sevii Islands - Four Island - Five Island | BGM | F2 | Tema das Sevii Islands, Four Island e Five Island |
| 60 | Pokémon Jump | BGM | F5 | Trilha do minijogo Pokémon Jump |
| 70 | Final Battle! (Rival) | BGM | F3 | Confronto final contra o rival/Campeão |
| 71 | Epilogue | BGM | F5 | Trilha de epílogo após concluir a história |
| 72 | Hall of Fame | BGM | F5 | Tema do registro no Hall of Fame; BGM enquanto a tela estiver ativa |
| 73 | Staff Credits | BGM | F5 | Trilha de créditos finais |

**Contagem:** F2 = 25 BGM de ambiente/transporte; F3 = 12 BGM de batalhas/introduções; F4 = 14 ME; F5 = 13 BGM de cenas. **Total = 64/64.**

## Mensagens prontas para continuar neste chat

As frases abaixo são suficientes para iniciar cada implementação. Em qualquer fase, o assistente precisa ler este plano e o estado atual do código; não deve depender apenas de resumos de conversa.

| O que enviar aqui no chat | Entrega esperada |
|---|---|
| **Aplique a Fase 0 do plano musical de Kanto no GitHub.** | Auditoria dos 64 MP3s, estado e teste inicial. |
| **Aplique a Fase 1 do plano musical de Kanto no GitHub.** | Adaptação do plugin para Kanto, MapIDs reais, regras versionadas e regressões. |
| **Aplique a Fase 2 do plano musical de Kanto no GitHub.** | Temas de mapas e transporte, fallbacks e provas. |
| **Aplique a Fase 3 do plano musical de Kanto no GitHub.** | Batalhas, líder, campeão, vitórias e proteção de Decades. |
| **Aplique a Fase 4 do plano musical de Kanto no GitHub.** | As 14 vinhetas ME disparadas no momento correto. |
| **Aplique a Fase 5 do plano musical de Kanto no GitHub.** | Menus, Oak, rival, evolução, epílogo, Hall e créditos. |
| **Aplique a Fase 6 do plano musical de Kanto no GitHub.** | Testes de áudio, integração, relatórios e ajustes finais. |

**Formato da resposta ao final de cada fase:** PR/commit e links da CI; quantas faixas vinculadas, quantas efetivamente testadas, quantas pendentes e por quê; arquivos alterados; próxima fase. **Não pedir para o usuário ligar cada faixa à mão** quando o próprio projeto permitir geração automática da configuração.
