# JOHTO — GUIA DEFINITIVO DE IMPLEMENTAÇÃO INTEGRAL
## Mapas, eventos, NPCs, itens, encontros, músicas e campanha usando o motor de batalha do Blue/Decades

**Projeto:** [Pokémon Blue — Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Data-base:** 13/11/2026  
**Natureza:** especificação técnica EXECUTÁVEL POR FASES; **não** é certificação de Johto instalada.  
**Fonte narrativa de referência:** Pokémon HeartGold/SoulSilver (HGSS), com conteúdo complementar de Crystal identificado como variante.  
**Motor:** Game.exe/Essentials e **sistema de combate, Pokédex, evolução, itens, progresso regional, balanceamento e saves já existentes no Blue/Decades**. Nenhuma engine de batalha externa será importada.

> **REGRA 0 — sem falsa conclusão:** ter um arquivo Ruby, JSON, MD, teste simulado ou botão `Testar Johto` não significa que um mapa ou evento esteja funcionando no jogo. Cada recurso só passa a `VERIFIED_PLAYABLE` após existir na instalação isolada e passar por testes reais. Este documento **não executa** os passos; ele define exatamente como implementá-los.

---

## 1. Objetivo, escopo completo e critérios de fidelidade

**Resultado esperado:** começar **dentro da casa do jogador em New Bark**, sair, falar com todos os NPCs presentes, entrar em interiores, obter itens e Pokémon, lutar e capturar Pokémon usando a batalha nativa do projeto, concluir **8 ginásios + Liga de Johto**, visitar todas as rotas/dungeons, realizar missões Rocket, lendários, conteúdo secundário e pós-jogo, usar música adequada em cada evento, salvar/recarregar e viajar por portais regionais já existentes sem perder Pokémon.

**Cobertura obrigatória:**
1. **Geografia:** cada cidade, rota, andar de dungeon, casa e loja, entrada/saída/porta/warp, acesso via Surf/Cut/Strength/Rock Smash/Whirlpool/Waterfall e colisões.
2. **Eventos:** cada NPC visível, evento oculto/automático, diálogos e escolhas, switches, ações especiais, puzzles, cenas e progressão; diálogos novos em português e reescritos/adaptados, sem presumir autorização para redistribuir texto oficial literal.
3. **Batalhas:** treinadores comuns, rival, Rockets, líderes, Elite, campeão, Pokémon selvagens, lendários e rematches — **chamando exclusivamente o motor atual**.
4. **Itens:** todos os itens visíveis/ocultos, presentes únicos, recompensas de batalha e missão, TMs/HMs, Key Items, Apricorns, berries, compras/estoques, trocas e itens condicionados.
5. **Encontros:** espécies, níveis, percentuais e condições por área (grama, água, pesca, Headbutt, surf, dia/noite, swarm, lendário, roamer etc.) definidos e verificados na integração.
6. **Áudio:** BGM de cidade/rota/interior/dungeon, batalha, vitória, recebimento de item/insígnia, cenas, ME, transições/loop/fade e fallback, com fontes e direitos aprovados.
7. **Sistemas HGSS:** Pokégear/telefone/rematches, Day Care, Radio Tower, Game Corner (somente se implementado e adequado), apricorn/Kurt, Bug-Catching Contest, Pokéathlon, Safari Zone, S.S. Aqua, Battle Frontier e demais atividades relevantes. Toda adaptação ou ausência deve ser **explicitamente identificada**, nunca escondida.
8. **Integração regional:** cartões de treinador **local e global**, esmeraldas (soma das insígnias válidas entre regiões), HMs locais, transferência/Box, especiais bloqueados até oito insígnias e pós-jogo forte; preservar regras particulares de Decades.

**Fidelidade:** HGSS como fluxo principal, Crystal como variante explicitamente configurada onde diverge (ex.: Suicune/Eusine). Não fundir eventos incompatíveis das duas versões no mesmo save de maneira que a história quebre. Recursos de plataforma DS que não podem ser reproduzidos no motor devem ter um **equivalente projetado e testado** ou ficar como `BLOCKED_FEATURE`, impedindo alegar `100% HGSS`.

### 1.1. Documentos de referência que NÃO devem ser substituídos

- [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md) — as **duas barras** de progresso e os 16 núcleos existentes.
- [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) — fases e políticas base.
- [JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) — seleção de fonte, créditos, direitos, limitações.
- [JOHTO_TESTES_E2E.md](JOHTO_TESTES_E2E.md) e [JOHTO_FASE_16_INTEGRACAO_E_ACEITE.md](JOHTO_FASE_16_INTEGRACAO_E_ACEITE.md) — release, 13 provas, rollback.
- [PLANO_REGIOES_DESSASTRE_V2.md](PLANO_REGIOES_DESSASTRE_V2.md), [CIRCUITO_REGIONAL.md](CIRCUITO_REGIONAL.md), [KANTO_BALANCEAMENTO_PALLET_CARTOES_REGIONAIS.md](KANTO_BALANCEAMENTO_PALLET_CARTOES_REGIONAIS.md).
- [JOHTO_FASE_04_EVENTOS_NEW_BARK.md](JOHTO_FASE_04_EVENTOS_NEW_BARK.md) até [JOHTO_FASE_15_MUSICAS_TREINADORES_PORTAL.md](JOHTO_FASE_15_MUSICAS_TREINADORES_PORTAL.md) — funções parciais a aproveitar, não provas de gameplay.

### 1.2. Fontes e limites reais

- **Mapas:** [Remastered Kanto and Johto Overworld and Caves Map Pack — AenaonDogsky](https://www.eeveeexpo.com/resources/828/), v.3. Serve de *base de terreno/tiles*: exterior de Johto e cavernas, **exceto Mt. Silver**; contém também Kanto e áreas beta que NÃO devem ser confundidas com a campanha principal. A fonte recomenda refazer conexões ao importar em projeto existente e **não copiar MapInfos.rxdata**.
- **Narrativa, eventos, itens e sequência:** [walkthrough HGSS](https://bulbapedia.bulbagarden.net/wiki/Walkthrough%3APok%C3%A9mon_HeartGold_and_SoulSilver) e as páginas de cada local do [índice de Johto](https://bulbapedia.bulbagarden.net/wiki/Template%3AJohto). Esses são **referenciais de inventário e verificação**, não arquivos de script prontos para colar.
- **Música:** referências de nomes/uso HGSS em [documento de seleção](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md). Catálogo do projeto: [data/johto-music.json](../data/johto-music.json) e [data/johto-music-rules.json](../data/johto-music-rules.json); atualmente **42 BGM + 11 ME planejados e todos desativados**.
- **Direitos:** registrar separadamente autor/licença/permissão de cada tileset, sprite, mapa, faixa, fonte e texto; **crédito não equivale a licença**. Se os direitos não permitirem redistribuição, substituir por assets originais/autorizados. O projeto tem de continuar montável sem baixar material protegido automaticamente.

---

## 2. ESTADO REAL E ORDEM DE PRECEDÊNCIA

Em 13/11/2026, `data/regions/johto-source.json` mantém `archive_sha256: null`, `mapping_verified: false`, `import_enabled: false` e `maps: {}`. `stage_johto.py` gera apenas **prévia geométrica sem eventos/áudio**, e `install_johto.py --apply` **recusa instalação**. O menu `Testar Johto` existe, mas não há piloto nativo instalado. As 16 etapas continuam **PARCIAIS**, com **0/16 integralmente aprovadas em cada barra**.

**Dependências críticas em ordem:** pacote real → inventário/IDs → tilesets/passabilidade → todos os mapas, interiores e warps → NPCs/eventos/itens → PBS/encounters e motor atual → saves/flags → áudio → campanha completa → QA Windows/JoiPlay → instalação transacional.

Não marcar uma etapa como finalizada só por ter criado a classe Ruby ou os dados de teste.

---

## 3. ESTRUTURA DOS ARQUIVOS: EXISTENTES vs. A CRIAR

### 3.1. Reaproveitar (EXISTEM)

- `scripts/regions/prepare_johto_source.py`: extração **ZIP** segura (somente dados RMXP e PNGs permitidos).
- `scripts/regions/audit_johto.py`: auditoria inert/read-only dos Map*.rxdata, eventos e warps; não executar comandos de scripts externos.
- `scripts/regions/plan_johto.py`: planeja IDs livres **600–999**, mapeamento estável.
- `scripts/regions/stage_johto.py`: **prévia sem eventos** e com tiles remapeados; não usá-la como campanha.
- `scripts/regions/verify_johto.py`: integridade da prévia geométrica.
- `scripts/regions/JohtoPilot.rb`, `JohtoViolet.rb`, `JohtoAzalea.rb`, `JohtoGoldenrod.rb`, `JohtoEcruteak.rb`, `JohtoOlivineCianwood.rb`, `JohtoJasmine.rb`, `JohtoMahogany.rb`, `JohtoBlackthorn.rb`, `JohtoLeague.rb`, `JohtoLegendaries.rb`: **lógica Ruby parcial** dos eventos centrais, que deverá ser vinculada aos mapas.
- `scripts/battle_polish/Regions.rb`, `RegionalPolicy.rb`, `RegionalCards.rb`, `RegionStart.rb`, `RegionTravel.rb`, `TitleKanto.rb`: regras de regiões, viagem/Box, cartões e botão.
- `scripts/music/BlueMusic.rb`: áudio do motor, já adaptado para outros contextos; estender **regionalizadamente**, sem perder preferências atuais.
- `scripts/regions/install_johto.py`: diagnóstico e bloqueio da publicação; o `--apply` atual **não instala**.
- `site/public/data/johto-preview.json`: **148 locais simbólicos e 36 tipos planejados de treinadores**, não mapas ou equipes jogáveis.

### 3.2. Artefatos propostos (AINDA NÃO IMPLEMENTADOS)

Não assumir que esses scripts existem. Criar e testar progressivamente:

`data/regions/johto-map-registry.json` — cada mapa físico, nome simbólico, ID origem→destino, hash, tileset, bioma, tamanho, status.  
`data/regions/johto-warps.json` — conexões/portas bidirecionais e requisitos.  
`data/regions/johto-event-registry.json` — **todos** os eventos de todos os mapas, inclusive invisíveis.  
`data/regions/johto-npcs.json` — **todos** os NPCs, aparências, coordenadas, diálogos, interações e estado.  
`data/regions/johto-items.json` — **todos** os itens, quantidade, condição, recorrência e recibo.  
`data/regions/johto-trainers.json` — referência de cada treinador ao PBS existente, versão e perfil de dificuldade.  
`data/regions/johto-encounters.json` — encontros realmente auditados, por mapa/horário/método.  
`data/regions/johto-story-gates.json` — grafo de pré/pós-condições, missões, versões HG/SS/Crystal.  
`data/regions/johto-coverage.json` — relatório gerado de cobertura e evidências (não manualmente forjado).  
`scripts/regions/build_johto_events.py` — compila **eventos próprios** e dados dos registries para o RMXP compatível com Blue.  
`scripts/regions/compile_johto_content.py` — valida e gera PBS/encounters/itens, com saída isolada.  
`scripts/regions/pilot_johto.py` e `JOHTO_JOGAR_EXPERIMENTAL.bat` — piloto jogável isolado.  
`scripts/regions/install_johto_transactional.py` ou evolução auditada de `install_johto.py` — aplicação com plano, backups, verificação e rollback; **não** liberar o `--apply` antes de aprovação.  
`tests/test_johto_content_coverage.py`, `tests/test_johto_event_compiler.py`, `tests/test_johto_warps.py`, `tests/test_johto_npc_item_integrity.py`, `tests/test_johto_battle_bridge.py`, `tests/test_johto_music_runtime.py`, `tests/test_johto_pilot_e2e.py` — novos contratos e smoke tests.  
`docs/JOHTO_EVIDENCIAS_WINDOWS.md` e `docs/JOHTO_EVIDENCIAS_JOIPLAY.md` — logs, vídeos/prints e IDs dos saves de teste.

**Regra de layout:** artefatos fonte e registries aprovados sob `data/regions/`; build local e bytes de terceiros somente em `.blue-work/` (ignorado); backups em `.blue-backups/`; nunca colocar ROMs, mídia sem direitos, Game.exe, save ou a instalação completa no GitHub.

---

## 4. MODELO DE INVENTÁRIO OBRIGATÓRIO: TODOS OS MAPAS/NPCS/ITENS

Cada mapa **físico** (inclusive cada andar, casa, escada, corredor, porão, sala secreta) tem registro estável. Exemplo de **formato alvo**, sem alegar que MapID 600 é New Bark:

```json
{
  "map_key": "JOHTO_NEW_BARK_PLAYER_HOME_1F",
  "source_map_id": null,
  "target_map_id": null,
  "source_sha256": null,
  "status": "PENDING_SOURCE",
  "variant": "HGSS",
  "tileset_key": "JOHTO_INTERIOR_HOUSE",
  "warps": ["JH_WARP_HOME_1F_TO_NEW_BARK", "JH_WARP_HOME_1F_TO_2F"],
  "npcs": ["JH_NPC_MOTHER"],
  "events": ["JH_EV_HOME_FIRST_VISIT"],
  "items": [],
  "encounter_key": null,
  "bgm_cue": "town_new_bark",
  "evidence": []
}
```

**Contrato de evento individual** (usar esquema de versão e validação reais, campos abaixo são orientação de design):
- `event_key` único e imutável; `map_key`, coordenadas, sprite, direção e prioridade.
- `trigger`: ação, toque, contato, autorun ou paralelo **com condição de parada**; sem loop infinito.
- `pages[]`: condições de switch/variável/self-switch/progresso; predicados do estado regional; versão HG/SS; ordem de prioridade definida.
- `action`: diálogo PT-BR próprio, movimentação, cutscene, item, troca, batalha via bridge, telefone, loja, teleport/warp, puzzle, insígnia.
- `preconditions`, `postconditions`, `on_cancel`, `on_defeat`, `on_retry`, `on_save_reload`.
- `consumes` e `grants` com inventário verificado. Itens únicos e vitórias **idempotentes**.
- `evidence`: log/teste real, estados antes/depois e se há foto/vídeo.

**Contrato de NPC individual:**
- `npc_key`, `map_key`, `event_key`, nome/identificador, classe (`story`, `trainer`, `merchant`, `healer`, `gift`, `phone`, `trade`, `flavor`, `roamer`), coordenada/sprite/página, textos e condições.
- Para todos os NPCs sem batalha: testar interação **antes e depois da mudança de estado**; NPC neutro não pode desaparecer porque o jogador recebeu insígnia.
- Para treinador: `trainer_type` + `trainer_name` + `trainer_version` + `pbs_key` + `battle_profile` + `rematch_state`; distinguir treinador opcional de obrigatório. NPC treinador que perdeu NÃO pode dar prêmio de vitória se batalha cancelou ou falhou.

**Contrato de item individual:**
- `item_key`, `map_key`, coordenada ou NPC de origem, `item_id` nativo existente, quantidade, categoria, visível/oculto/loja/presente/recompensa; condições HGSS e flags regionais.
- `repeatability`: `once`, `daily`, `weekly`, `shop`, `renewable`, `conditional`; registrar claramente regra por save.
- **Só gravar flag de recebido após `pbReceiveItem`/API nativa confirmar**. Inventário cheio/cancelamento não consome o item; save/reload não duplica.
- Validação cruzada contra a lista da localização de HGSS e, quando disponível, evento real de fonte com permissão de uso. **Não inventar quantidade, item ou posição.**

### 4.1. A regra de COMPLETUDE (não negociável)

- Gerar inventário de **todos os Map*.rxdata** existentes na fonte e da campanha reconstituída, com nomes reais, andares, eventos, posições e parâmetros (como dados inertes).
- O Map Pack é principalmente terreno e pode ter **zero NPCs/eventos**. Por isso, `source_event_count == 0` **não** significa `100% dos NPCs de Johto feitos`.
- Para cada `map_key` da matriz na Seção 5, confrontar: (A) mapa RMXP; (B) walkthrough HGSS daquela área; (C) lista de NPCs, itens, TMs/HMs, lojas, treinadores, encounters e puzzles; (D) conteúdo realmente compilado no piloto.
- Criar uma **checklist de cobertura por sala, evento e item**, com `expected_count` e `implemented_count`. Se o total esperado não foi auditado, `expected_count = null` e **status = BLOCKED_INVENTORY** — não transformar valor desconhecido em zero.
- Totais separados: mapas físicos, conexões, NPCs, treinadores, eventos automáticos, itens visíveis/ocultos, casas/interiores, lojas, métodos de encontro, cues de música, variantes HGSS e testes. Exigir **100% dos elementos obrigatórios auditados** para `VERIFIED_PLAYABLE` local.
- Todas as entradas `PENDING_SOURCE`, `PENDING_PBS`, `PENDING_RIGHTS`, `BLOCKED_FEATURE` ou `PENDING_GAMEPLAY` impedem afirmar que Johto inteira está pronta.

---

## 5. MATRIZ GEOGRÁFICA MESTRE — INCLUIR TODA JOHTO

A tabela identifica os **núcleos mínimos obrigatórios e os eventos marcantes** de cada área. **Não é uma lista exaustiva de cada NPC/item do jogo:** a exaustividade será obtida pelo inventário verificável da Seção 4, área por área; detalhes variam entre Gold/Silver/Crystal e HGSS. Os números de MapID só serão definidos **depois da auditoria real**. Cada casa, andar, salinha, telhado acessível e seção de caverna terá linha própria no registry.

| Áreas (desdobrar em mapas físicos) | NPCs, eventos, itens e marcos que DEVEM ser conferidos |
|---|---|
| **New Bark Town**, casa 1F/2F, laboratório Elm, casa do rival, vizinhança | Spawn no quarto; mãe/menus/contato; Elm e assistente; escolha única Chikorita/Cyndaquil/Totodile; telefone/Pokégear; rival, item de entrega, retorno e primeiro save |
| **Route 29**, acessos à Route 46 | Tutoriais/primeiros NPCs, itens no solo e ocultos, Apricorns, bloqueios iniciais, encontros dia/noite |
| **Cherrygrove City**, interiores/lojas/Centro | Guia da cidade/mapa, cura, lojas, pescadores/casas e diálogos; passagem inicial |
| **Route 30**, casa do Mr. Pokémon, início da Route 31 | Mr. Pokémon/Oak, ovo e encomenda, árvores de Apricorn, treinadores, bifurcações, itens/encounters |
| **Route 31**, **Dark Cave** (todas entradas/andares) | Entrega/assuntos secundários, Cut/Flash/Rock Smash quando aplicável, itens, treinadores, encontros |
| **Violet City**, escola, casas, Centro/Mart, **Sprout Tower** (todos andares), Gym | Sages e Elder Li, rival, Falkner/Zephyr, entregas/quests, HM/itens, transições e diálogos por insígnia |
| **Ruins of Alph** (ruínas, salões, câmaras, salas/puzzles) | Puzzles Unown e letras, acesso por ferramentas, itens ocultos, encontros condicionados, pesquisas/NPCs |
| **Route 32**, Centro e acessos | Treinadores, compra/entrega conforme versão, Old Rod quando aplicável, Apricorns, Union Cave, água e itens |
| **Union Cave** (todos andares/seções), **Route 33** | Quedas/escadas, partes acessíveis com Surf/Strength, treinadores, itens, encontros especiais por dia/condição |
| **Azalea Town**, **Slowpoke Well** (todos pisos), Gym, casa Kurt | Slowpoke, Kurt/Apricorn Balls, Rocket/Proton, Bugsy/Hive, rival e fuga após evento, itens/entradas |
| **Ilex Forest** (entradas/saídas e shrine) | 2 Farfetch'd e puzzle completo, lenhador/Cut, shrine/Celebi onde aplicável e permitido, Headbutt, treinadores/itens |
| **Route 34**, Day Care e acessos | Day Care, ovo/criação/troca, treinadores, Gift/Phone/itens, conexão Goldenrod |
| **Goldenrod City**: Centro, Mart e pisos, Department Store, Radio Tower, Tunnel/Underground, Gym, Flower Shop, Bike Shop, Game Corner, Name Rater, Magnet Train Station, casas | Whitney/Plain, quiz rádio, loja por andar, Bike, SquirtBottle, Bill, NPCs de serviços, acesso a porões, itens, cenas Rocket, loteria/telefone/minijogos implementáveis |
| **Route 35**, portões e **National Park** | Treinadores, portões, itens, eventos de calendário, Bug-Catching Contest com premiação/encounters |
| **Pokéathlon Dome** e acesso | Recepção, NPCs, inscrições, provas/minijogos e prêmios; desenvolver equivalente compatível com PC ou manter pendência declarada |
| **Route 36**, **Route 37** | Sudowoodo obstáculo e batalha/remoção única, Flower Shop, encontros/treinadores, Apricorns e warps |
| **Ecruteak City**, Dance Theater, Burned Tower, Bellchime Trail, Bell Tower (todos pisos), Gym, casas | Rival, trio de bestas, Eusine/Suicune por variante, Kimono Girls, Rocket do teatro, Morty/Fog, Surf e gating das torres |
| **Route 38**, **Route 39**, **Moomoo Farm** | Treinadores, itens, leite/Miltank e quests, acesso Olivine |
| **Olivine City**, Gym, harbor, Lighthouse (todos andares), casas, Centro/Mart | Jasmine, Ampharos/Amphy, missão SecretPotion, pescadores, HM/itens, viagem, interiores |
| **Route 40**, **Route 41** oceânicas, **Whirl Islands** (4 entradas e pisos) | Surf, nadadores, Whirlpool, ilhas e saídas verificadas, Lugia e eventos condicionados, itens especiais |
| **Cianwood City**, Pharmacy, Gym, casas, norte/cliff | SecretPotion, Chuck/Storm, Fly, Eusine/Suicune quando aplicável, presente/troca, itens, caminhos Safari |
| **Cliff Edge Gate**, **Routes 47–48**, **Cliff Cave**, **Embedded Tower**, **Safari Zone Gate**, **Safari Zone** | Entrada e portões, Surf/Waterfall/Strength, rotas e zonas, Baoba/NPCs, mecânicas Safari e habitats/itens, lendário do Embedded Tower sob condições |
| **Route 42**, **Mt. Mortar** (todas entradas/andares) | Surf, três entradas, Karate King/Tyrogue quando aplicável, Waterfall/itens especiais, treinadores |
| **Mahogany Town**, **Route 43**, **Lake of Rage**, **Team Rocket HQ** (todos andares), Gym | Red Gyarados, Lance, Rocket, alarmes/portas/painéis, Electrode, Pryce/Glacier, desbloqueio da Radio Tower e itens |
| **Goldenrod Radio Tower** (invasão) e **Underground** (porão/switch puzzle) | Rival, diretor real/falso, Rockets/executivos, Card Key, Basement Key, libertação, retorno às atividades normais |
| **Route 44**, **Ice Path** (pavimentos e puzzles) | Strength, pedras, piso escorregadio, HMs e itens, entradas para Blackthorn |
| **Blackthorn City**, Gym, **Dragon's Den**, Route 45, Route 46 | Clair, quiz do Dragon Master, Rising após prova, Waterfall, rotas de volta, itens/encounters/treinadores |
| **Route 27**, **Tohjo Falls**, **Route 26**, **Victory Road**, portões | Oito insígnias Johto verificadas, cascata, rivais, checkpoints, HMs, treinadores, cura e itens |
| **Indigo Plateau / Liga de Johto** (salas individualizadas) | Will, Koga, Bruno, Karen, Lance, Hall of Fame real, créditos/retorno, retry após derrota, desbloqueio regional |
| **Pós-jogo Johto**: Bell Tower/Whirl/Lake/ruínas, roamers, **Mt. Silver** + Route 28, Red e casa de descanso quando aprovados | Ho-Oh, Lugia, Raikou, Entei, Suicune/Eusine, Unown, Kimono, Red, rematches e recompensas; **Mt. Silver deve ser criado/adquirido separadamente** |
| **Frontier Access**, **Battle Frontier**, **S.S. Aqua**, áreas opcionais/acessos de conexão | NPCs, serviços, recompensas, transporte e atividade equivalente no motor atual; não reimplementar Kanto ao usar S.S. Aqua |
| **Interiores compartilhados de todo o percurso** | Centro Pokémon, Mart, casas, ginásios, portões, elevadores, escadas, PC, curandeiros, oficiais, recepcionistas, comerciais e NPCs sem combate; cada porta tem retorno válido |

**Atenção geográfica:** Route 26, Route 27, Route 28 e Indigo Plateau são áreas de fronteira/associadas a Kanto no cânone; **a lógica de campanha/insígnias da Liga de Johto deve ficar separada** mesmo que parte da geografia ou da engine seja compartilhada. A viagem entre regiões no Blue respeita o NPC da cidade inicial e os desbloqueios, não cria teleport arbitrário.

### 5.1. Inventário de interações que não podem ser esquecidas

Cobrir **em cada área**, quando existir na referência HGSS: 
- NPCs que apenas conversam; diálogos alternativos por turno/progresso; NPCs que seguem/andam/bloqueiam portas; treinadores com campo de visão e rematches; guildas/serviços;
- NPCs que curam, dão Pokémon, ovos, itens, telefone, TMs/HMs, dicas, trocas; lojas com estoque e preço; elevadores; PC/Box; NPC de viagem (sempre cidade inicial e somente após Liga);
- Itens visíveis, invisíveis/Itemfinder, sob pedra ou árvore, Poké Balls de chão, itens de Surf/pesca, berries/Apricorns, premios de minijogo, gifts de personagens, loot de encontros, entradas de caverna e lendários;
- Interações com Cut, Surf, Fly, Flash, Strength, Rock Smash, Whirlpool, Waterfall, bike, Rock Climb (se aplicável) e pontos condicionados;
- Eventos por relógio/dia da semana, estação quando reproduzida, horário, rádio/telefone, encontros itinerantes, swarm, dia/noite, Headbutt e pesca;
- Portas e rotas bloqueadas, revisita pós-insígnia/Liga, eventos com interrupção/derrota, cutscenes com recuperação de save;
- Cartazes/placas, mapas, limites do cenário, sprite/pivot, colisões, som de interação, posição após warp e autoswitch;
- Diferenciar recursos **canon HGSS**, **variante Crystal** e **conteúdo custom Blue** no registry.

---

## 6. PASSO A PASSO DE IMPLEMENTAÇÃO — EXECUTAR NESTA ORDEM

### PASSO 00 — Baseline e segurança antes de qualquer escrita

1. Fazer snapshot/hash da instalação `game/` local (incluindo Game.exe, `Data/MapInfos.rxdata`, `Tilesets.rxdata`, `Scripts.rxdata`, PBS, plugins, áudio e saves de TESTE); comparar com `main` e registrar versões.
2. Rodar a CI atual de Decades/Kanto/Blue Studio e guardar falhas **pré-existentes**. Não mascarar uma falha de Kanto para liberar Johto.
3. Criar workspace ignorado `.blue-work/johto-source`, `.blue-work/johto-pilot`, backups `.blue-backups`. Não sincronizar cópia do jogo, mapas proprietários ou saves no Git.
4. Definir modo `JOHTO` sem alterar `DECADES`/`KANTO`; reservar MapIDs em `600–999` **só depois de comprovar livres**. Conflito → replanejar, jamais sobrescrever.

**Aceite:** baseline reprodutível e sem alteração nos hashes originais.

### PASSO 01 — Obter, validar e inventariar fonte real de terreno

1. Obter **legitimamente** a versão exata do Map Pack escolhida; preservar arquivo original e SHA-256, autor, versão, data, permissões de uso/distribuição (inclusive contribuições dos artistas).
2. Se ZIP, usar o extrator atual; se RAR, extrair manualmente em workspace e auditar antes de usá-lo. Scripts de terceiros (Ruby/RGSS) e executáveis não devem ser executados/importados automaticamente.
3. Conferir mapa por mapa em `MapInfos.rxdata`, dimensões, tileset, lista de eventos, warps, coordenadas, colisões, regiões, imagens/tilesets, nomes e créditos.
4. Separar mapas Johto, Kanto, variantes beta, placeholders, interiores e mapas repetidos. Não copiar beta/placeholder como se fosse local canônico.
5. Atualizar `johto-source.json` apenas com fatos conferidos; não liberar `import_enabled` até fechar direitos, nomes e mapeamento.

**Comandos existentes, em PowerShell desde a raiz do repositório** (pasta de saída nova, o extrator não sobrescreve):
```powershell
python scripts/regions/prepare_johto_source.py --archive ".blue-work/johto-source/original.zip" --output ".blue-work/johto-source/project"
python scripts/regions/audit_johto.py --source ".blue-work/johto-source" --archive ".blue-work/johto-source/original.zip" --game "game" --output ".blue-work/johto-audit.json"
```
O comando não baixa a fonte por conta própria. Se o arquivo estiver em estrutura diferente ou `game/` não existir, corrigir as pré-condições e documentar; não fingir auditoria concluída.

### PASSO 02 — Reconstruir catálogo total de mapas e slots

1. Criar `johto-map-registry.json` com *todos* os nomes reais do audit, inclusive cada andar/interior; relacionar à matriz da Seção 5.
2. Criar `source_map_id → target_map_id` estável, inclusive em saves futuros; congelar IDs já publicados; o plano não pode alterar mapa da Kanto/Decades.
3. Remapear tilesets, autotiles, ID de tileset, passabilidade, prioridades, autotile animation, sombras, panorama/fog/battleback e dimensões. Verificar renderização.
4. Atualizar `MapInfos` por merge **controlado e testado**, nunca por cópia do pacote; idem Tilesets. Escrever somente na área de staging isolada.
5. Para a prévia, usar os scripts `plan_johto.py`, `stage_johto.py` e `verify_johto.py`, observando as flags/entradas esperadas em `--help`.
6. Separar `GEOMETRY_PREVIEW` (sem eventos/áudio) de `PLAYABLE_CONTENT`, nunca elevar a barra de gameplay com a prévia.

**Aceite:** mapa origem→destino congelado, sem colisões e com todas as localidades auditadas; faltantes listadas com plano de construção.

### PASSO 03 — Criar mapas ausentes e validar arquitetura física

1. Construir com arte original/autorizada os locais ausentes do pacote (prioridade: **casa/quarto do protagonista, interiores faltantes, Mt. Silver/Red**, demais estruturas descobertas).
2. Inserir todas as casas/lojas/ginásios/salas/cavernas citados no walkthrough, inclusive cada piso e setor de puzzle.
3. Definir `warps` direcionais e **retorno bidirecional** por chave estável, com `x/y` válidos e mapa de chegada física não bloqueada. Entradas de cavernas multiporta devem retornar pela entrada correta.
4. Definir conexões de overworld sem emendas visíveis, passagem por portões e limites de câmera; validar respawn, cutscene, Fly e Surf.
5. Usar testes automáticos de grafo: todo mapa acessível deve ter saída válida, exceto salas explicitamente terminais; toda porta normal deve ter contrapartida. Detectar órfãos, loops de transferência, spawns em parede e MapIDs inexistentes.
6. Inspecionar visualmente colisão/passabilidade de todos os tiles críticos e pisos de puzzle em Game.exe, não só dimensões do RXDATA.

**Aceite:** percorrer a geografia em cópia isolada, abrir e fechar portas, andar por todos os interiores e sair de todas as cavernas, antes de popular eventos.

### PASSO 04 — Definir o catálogo COMPLETO de NPCs, eventos e itens

1. Para CADA mapa, abrir página HGSS correspondente; inventariar 100% de NPCs, treinadores, páginas de diálogo, visitas condicionais, itens (visíveis/ocultos), objetos de cenário interativos e mudanças após missões.
2. Usar comandos de eventos encontrados na fonte RMXP **como dados inertes** somente após auditoria; nunca importar seus scripts terceiros por execução. Se fonte de terreno não contiver NPCs, reconstruir manualmente pelo roteiro de referência.
3. Inserir `johto-npcs.json`, `johto-event-registry.json`, `johto-items.json`, `johto-story-gates.json`; para cada chave registrar estado de implementação e origem confirmada.
4. Validar todos os símbolos nativos (`GameData::Item`, espécie, trainer/PBS, skills); nunca deixar ID fictício ou classe sem registro no executável.
5. Gerar um relatório `expected vs actual` por mapa e por tipo de objeto, inclusive NPCs que só aparecem de noite, depois da Liga ou em eventos especiais.

**Aceite:** nenhum NPC/item/evento obrigatório está sem chave/posição/estado conhecido. Inventário desconhecido continua `BLOCKED_INVENTORY`.

### PASSO 05 — Compilar eventos próprios no RMXP, sem engine estrangeira

1. Implementar `build_johto_events.py`, com schema versionado e testes, para materializar `RPG::Event`, páginas, conditions, movement route e comandos de diálogos/gatilhos **compatíveis com a versão real do jogo**. Usar `server.ruby_marshal`/serializador já existente onde suportado.
2. **Não chamar scripts importados** do pack. Somente invocar funções da camada `BlueJohto*` ou API do Blue, após verificar assinaturas e testes.
3. Adaptar módulos `JohtoPilot` até `JohtoLegendaries` a eventos físicos: recepção de quest, luta, derrota, tentativa novamente, insígnia/item, cenas e persistência.
4. Criar novos handlers por evento faltante com namespace `BlueJohto*`, sem editar sistema inteiro de combate/saves. Não reutilizar switches globais antigos de Kanto/Decades.
5. Criar páginas para NPCs fixos e móveis, movimentação, visibilidade, recompensa única, desbloqueios, scripts autorun com desarme, batalhas de treinador e retorno de warp.
6. **Testar em uma sala mínima** antes de compilar centenas de eventos; validar eventos/código serializados no motor real, não apenas no parser Python.

**Aceite:** NPCs falam, portas abrem, cenas terminam, flags persistem, game não trava em autorun/parallel.

### PASSO 06 — Adaptador para o MOTOR DE BATALHA EXISTENTE (obrigatório)

**Johto NÃO terá sistema de combate próprio.** Só fornece *dados* e *gatilhos* para as APIs já existentes.

- Treinadores: tipos/nomes/versões PBS **compilados para o Essentials exato instalado**; evento chama bridge testada que, por sua vez, usa o fluxo de `TrainerBattle.start` (ou API existente efetivamente verificada), preservando transições, IA, itens, experiência, dinheiro, desmaio, efeitos, save e música do Blue.
- Selvagens: cadastrar `encounters` por MapID e método; delegar seleção do encontro, combate/captura/fuga, drops, habilidades e tempo ao motor atual; não usar um clone de battle scene ou import de scripts de HGSS.
- Lendários/estáticos: só gravar `captured`/`defeated` após resultado real da batalha/captura e persistência.
- Rival: três variantes de equipe pelo inicial e revisitas, usando `BlueJohtoPilot` e flags; conferir PBS/marker antes de permitir início.
- Lideranças/Elite: reaproveitar `BlueJohtoViolet`, `...Azalea`, `...Goldenrod`, `...Ecruteak`, `...OlivineCianwood`, `...Jasmine`, `...Mahogany`, `...Blackthorn`, `...League`. Insígnias vêm de `BlueRegions.award` e verificações reais, não de um evento que simplesmente marca vitória.
- Master Mode: respeitar regra atual de **quatro Pokémon nos treinadores que começariam com três, nível ajustado pelo perfil de 90%, cobertura de fraquezas** e demais particularidades já implementadas; sem alteração global de dificuldade. Os níveis dos líderes obedecem ao cálculo de esmeraldas e balanceamento já existente, com travas de mínimo/máximo e testes.
- Pós-mundo completo: perfis fortes de líderes/Elite/campeão via `world_champion_rematch` somente após conclusão verificável de todas as regiões.
- Testar derrota, fuga, cancelamento, batalha impossível, equipe cheia, falta de Pokémon, recompensas únicas, rematch, música e retorno ao campo.

**Aceite:** batalha Johto passa pela **mesma cena, IA, base de dados, controles, músicas configuráveis e persistência de Decades/Blue**. Testar que não existe `PokemonBattle_Johto` ou `Scene_Johto` introduzida como substituta.

### PASSO 07 — Itens e serviços: distribuição exaustiva, transações seguras

1. Para cada área, registrar itens visíveis, ocultos, gift, pós-batalha, apricorn, TM/HM, key item, shop, quest, telefone e evento diário/semanal; conferência com walkthrough e itemdex de HGSS.
2. Criar evento de pickup único que usa API nativa para conceder, **não** modifica o bag por conta própria; item só desaparece após sucesso. Testar mochila cheia.
3. Para itens consumidos (`SecretPotion`, chaves Rocket etc.), checar posse, usar/remover uma vez, mudar cena somente após sucesso; rollback em falha.
4. Lojas: ID nativo, quantidade/estoque conforme projeto, preço, desbloqueios e opção de compra/venda. Serviços: Center (cura real), Mart, PC, trade, move tutor, Move Deleter/Relearner quando existirem, Name Rater, Day Care, Berry/Apricorn.
5. Puzzles de item: SquirtBottle/Sudowoodo, Cut, Medicine/Ampharos, Basement Key/Card Key, HM/insígnias, Legendary items e rematches; nunca passar pelos bloqueios sem requisitos.
6. Testar coleta → save → reload → revisita, incluindo duplicidade/cancelamento/dia seguinte. Cada categoria tem script de verificação.

### PASSO 08 — Encontros selvagens e habitats

1. Mapear todos os métodos de encontro por MapID/bioma/horário e fonte escolhida; versionar dados para reprodução.
2. Integrar **tabelas de encontros já existentes** do Blue, sem sobrescrever encontros de Kanto/Decades.
3. Respeitar Pokémon de Johto e variantes adicionais do Dessastre onde fizer sentido, com regras do projeto; taxas como 5% ou 20% **somente onde a configuração efetiva determinar**, nunca copiar percentuais sem prova.
4. Conferir espécie, forma, habilidade, nível, tipo e método; séries de teste determinísticas amostram 1.000+ encontros em simulação e fazem smoke test real de grass/water/rod/headbutt/day-night (simulação estatística NÃO substitui Game.exe).
5. Atualizar localizações/Dex/site somente após as tabelas entrarem no jogo e serem lidas de sua fonte compilada.

### PASSO 09 — Trilha sonora regional e cenas (sem substituir Kanto)

1. Inspecionar `data/johto-music.json` (53 cues PLANNED), `data/johto-music-rules.json` (tudo `enabled:false`) e o fluxo `BlueMusic.rb`; catalogar todas as faixas realmente exigidas após a matriz final de áreas/eventos. **53 é ponto de partida, não promessa de cobertura absoluta.**
2. Obter/produzir áudio com **direito explícito de distribuição**, metadados, SHA-256, formato suportado, loudness, pontos de loop, fade e créditos; não instalar trilhas comerciais sem autorização.
3. Destinos separados: `Audio/BGM/Johto/` e `Audio/ME/Johto/`. Não copiar MP3/OGG de Kanto como se fossem de Johto, não tocar onde MapID não esteja aprovado.
4. Compilar BGM por `map_key→target_map_id`, incluindo cidades, rotas, interiors, casas especiais, cavernas, torres, nave, bike/Surf, ginásios, Liga, regiões opcionais.
5. Categorizar pelo **oponente/evento real**: wild, trainer, rival, Rocket, gym, beast, Ho-Oh, Lugia, Elite, Lance; vinhetas de vitória/insígnia/recebimento/curar/evolução; cenas Elm, Kimono, Radio Tower, Hall of Fame e créditos.
6. Garantir prioridade de override, volume do editor do usuário, loop e retorno à BGM anterior após ME, derrota, captura, entrada/saída de caverna e troca de região; teste com arquivo ausente mantém fallback seguro.
7. Adicionar hooks apenas quando a integração com a batalha nativa demonstrar contexto JOHTO e áudio validado; evitar hooks globais que vazem para Kanto/Decades.
8. Testar todas as cues por playback real Windows/JoiPlay e registros de eventos, não apenas `File.exist?`.

**Aceite:** nenhum disparo incorreto/duplicado, loops/fades audíveis, nenhum mapa errado tocando música de outra região.

### PASSO 10 — Estados, saves, duas páginas de treinador, viagens e pós-jogo

1. Registrar todas as flags dentro de `$PokemonGlobal.blue_regions` no escopo Johto ou esquema regional versionado; save nativo permanece fonte única. Não recriar slot de save na troca de região.
2. Conquista local de `ZEPHYR`, `HIVE`, `PLAIN`, `FOG`, `STORM`, `MINERAL`, `GLACIER`, `RISING`; total global de esmeraldas calculado de conquistas reais entre regiões usando `BlueRegions.crystal_total`.
3. **Duas páginas de treinador** dentro do jogo: (A) insígnias da região atual e (B) insígnias/esmeraldas do conjunto de regiões. Conferir total após mudança de região e load.
4. HMs: requisito de insígnia de **Johto** conforme política/configuração regional do projeto e item/ação real disponíveis; não deixar posse de insígnia Kanto desbloquear HM Johto indevidamente.
5. NPC de viagem sempre **cidade inicial** (New Bark em Johto), disponível nas condições já definidas após Liga; Kanto↔Johto apenas se o destino físico estiver comprovado; Hoenn continua indisponível enquanto não instalada.
6. Ao viajar, conservar mesmo save, movimentar Pokémon especiais para Box se ainda bloqueados no destino, validar espaço e equipe utilizável, impedir retirada antes das oito insígnias do destino, rollback se falhar.
7. Hall of Fame deve ser gravado pela **batalha e fluxo real**, e não somente por `complete_league` chamado numa simulação. Após todas as ligas, habilitar time forte de rematch.
8. Na fase de primeiro lançamento, permitir piloto isolado `Testar Johto` mesmo que campanha completa não esteja concluída, **rotulando a extensão testável** (ex.: New Bark → Violet) e usando saves de piloto separados. Não usar o piloto para alterar save principal.

---

## 7. ORDEM DE ENTREGA JOGÁVEL — 16 MARCOS, SEM PULAR PARA A FASE 17

| Marco | Entrega jogável obrigatória | Código/MD que já auxilia | Teste de aceite no Game.exe |
|---|---|---|---|
| **01–03** | Pacote auditado, IDs/tiles/warps reais e prévia física segura | `prepare_johto_source.py`, `audit_johto.py`, `plan_johto.py`, `stage_johto.py` | Percorrer geografia do primeiro recorte em cópia; zero regressões |
| **04** | New Bark completa: quarto/casa, mãe, Elm, inicial, rival, Route 29 inicial | `JohtoPilot.rb` | Abrir `Testar Johto`, sair de casa, escolher inicial, batalhar, salvar/reabrir |
| **05** | Route 29–31, Cherrygrove, Violet, Sprout Tower, Falkner | `JohtoViolet.rb` | Percurso sem teleport, treinadores/itens, Zephyr real |
| **06** | Route 32/33, Union Cave, Azalea, Slowpoke Well, Bugsy | `JohtoAzalea.rb` | Rocket/Kurt, Hive, itens/Cut, viagem de ida/volta |
| **07** | Ilex, Route 34, Goldenrod e todos interiores/Whitney | `JohtoGoldenrod.rb` | 2 Farfetch'd, loja/radio/Day Care, Plain |
| **08** | Routes 35–39, Park, Ecruteak, Burned Tower/Morty | `JohtoEcruteak.rb` | Sudowoodo, rival, teatro, Fog/Surf |
| **09** | Olivine/Lighthouse, Routes 40/41, Cianwood/Chuck | `JohtoOlivineCianwood.rb` | Ampharos pede medicação, Storm/Fly, Surf |
| **10** | Retorno Olivine/Jasmine e mar/Whirl acessível conforme HMs | `JohtoJasmine.rb` | SecretPotion consumida, cura real, Mineral |
| **11** | Mahogany/Lake of Rage, HQ, Pryce e Radio Tower | `JohtoMahogany.rb` | Gyarados, Rockets, puzzles, Glacier, Rocket vencida |
| **12** | Route 44, Ice Path, Blackthorn, Clair/Dragon's Den | `JohtoBlackthorn.rb` | Strength/Waterfall, Rising e oito insígnias |
| **13** | Routes 26–27, Tohjo, Victory Road, Elite/Lance | `JohtoLeague.rb` | Hall of Fame verdadeiro, derrotas/retry, save e desbloqueios |
| **14** | Lendários, roamers, Unown, Mt. Silver/Red e conteúdos especiais | `JohtoLegendaries.rb` | Capturas/fugas, versões, post-game, rematches |
| **15** | Todas cues aprovadas, treinadores/encounters/site sincronizados | `johto-music*.json`, `johto-preview.json` | Música real, equipe normal/Master, dados locais verdadeiros |
| **16** | Installer transacional, viagens, regressão e aceite final | `install_johto.py`, `RegionTravel.rb`, `JOHTO_TESTES_E2E.md` | Windows/JoiPlay, backup/rollback e 13 checks reais |

**Regra de prioridade:** fases 01–04 devem chegar a gameplay físico **antes de ampliar mais lógica sintética**. Depois repetir o ciclo completo `mapa → NPCs → itens → treinadores → encontros → música → game test` por região, até o fim. Marcar avanço apenas para marcos que cumprirem **seus** critérios sem quebrar os demais.

---

## 8. CONTRATOS DE TESTE AUTOMÁTICO + E2E REAIS

### 8.1. Testes automatizados já existentes

Rodar a partir da raiz, com Python/Ruby e dependências presentes:

```powershell
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
python -m unittest discover -s tests -p "test_kanto*.py" -v
python scripts/regions/install_johto.py --dry-run
python scripts/music/audit_johto_phase15.py
```

Rodar também as suítes de Blue Studio/batalha/música compartilhadas conforme CI. **Um dry-run que roda sem exceção pode continuar relatando bloqueios**. O verificador `--strict` retorna erro enquanto a fonte/aceite estiverem faltando; **não** mudar exit code para esconder pendências.

### 8.2. Testes NOVOS a implementar (não afirmar existentes)

1. `test_johto_content_coverage`: para cada mapa e interior, inventário HGSS definido, nenhuma chave órfã, nenhum `expected_count=null` classificado como completo.
2. `test_johto_event_compiler`: páginas, condições, coordenadas, triggers; sem loops de autorun/parallel; rollback e scripts de eventos nunca executados da origem.
3. `test_johto_warps`: portais bidirecionais, geometria, spawn no piso correto, nenhuma conexão com mapa Kanto acidental.
4. `test_johto_npc_item_integrity`: todos NPCs interagíveis, itens únicos, bag cheia e persistência; nenhuma duplicação.
5. `test_johto_battle_bridge`: treinador/selvagem/gym/Elite/lendário invocam engine atual, sem engine paralela; vitória, derrota e rematch.
6. `test_johto_encounters`: percentuais, métodos, horário, MapID correto e flags; ausência de espécie fantasma.
7. `test_johto_music_runtime`: IDs, categorização, direitos, fallback, fade, restauração e não-vazamento regional.
8. `test_johto_save_travel`: save/reload, Box cheia, equipe especial, títulos/cenas, troca de região/rollback.

### 8.3. Matriz E2E manual/instrumentada no Game.exe e JoiPlay

Para **cada marco/área**, executar:
- Spawn correto dentro da casa (primeiro dia) ou na posição de save; sair/entrar em **todas** as portas e interagir com **todos** os NPCs/placas.
- Coletar 100% dos itens visíveis/ocultos e recompensas condicionais auditadas; bag cheia, item não obtido, save e retorno.
- Travar/destravar missões na ordem certa; repetir diálogo, cancelar, perder batalha, sair e entrar no mapa, reiniciar o Game.exe.
- Batalhar com todos os treinadores e encontros; conferir modo normal e Master, insígnias, HM, dinheiro/exp, Hall of Fame, capturas e rematches.
- Testar cutscenes/autoplay: nenhum freeze, softlock, loop nem evento inacessível. Checar overworld e cave em zoom/resolução real.
- Testar BGM/ME e alteração de preferências do usuário; fade/loop após batalha, porta, viagem, reload e silêncio.
- Abrir save antigo Decades/Kanto e passar regressão; nunca quebrar conquistas/registros preexistentes.
- Nos portais Kanto↔Johto, testar ida/volta, NPC na cidade inicial, Box/especiais, salvamento e falhas intencionais de warp.
- Registrar versão do Game.exe, hashes, OS/plataforma, save de teste, mapa, NPC/item, evidências e resultado. **Só um teste efetivamente executado no motor conta como `GAMEPLAY_VERIFIED`**.

### 8.4. A condição de release final (13 gates existentes)

Observar `data/regions/johto-release-proof.schema.json` e exigir todos:
1. `source_rights`; 2. `maps_and_warps`; 3. `sprites_and_tilesets`; 4. `story_events`; 5. `trainers_pbs`; 6. `battles_and_encounters`; 7. `native_save_reload`; 8. `hms_and_badges`; 9. `region_travel_and_box`; 10. `audio_rights_and_playback`; 11. `kanto_decades_regression`; 12. `windows_gameplay`; 13. `joiplay_gameplay`.

Somente com prova **real** pode emitir, **na instalação isolada já validada**, `Data/blue-johto-install.json` com status `VERIFIED_PLAYABLE` e `Data/blue-johto-start.txt`, com SHA-256 de origem e arquivos da instalação, `start` (dentro da casa), `travel_point` (rua de New Bark) e `npc_point` (NPC sem sobrepor o jogador), sem violar MapID 600–999. Arquivo vazio `{}`, boolean inventado, teste Ruby sintético ou mapa sem eventos não certifica release.

---

## 9. INSTALADOR TRANSACIONAL, REPRODUTIBILIDADE E ROLLBACK

Implementar somente depois dos blocos físicos:
1. Gerar **manifesto de alterações exato**: arquivos novos/alterados, hashes antes/depois, espaço, versões, status de licença, índices, MapIDs e lista de testes.
2. Preparar **cópia separada do jogo** em `.blue-work/johto-pilot` e preservar originais. Nenhuma escrita em `game/` durante a auditoria.
3. Construir atomicamente os arquivos novos/mesclados, nunca substituir `Game.exe`, `System.rxdata`, `Scripts.rxdata` de terceiros ou saves. Mesclar somente estruturas auditadas e suportadas; scripts próprios entram pelos mecanismos de plugins/compilação do Blue.
4. Rechecar hash dos originais antes de cada commit. Backups com nomes imutáveis, manifesto e prova de restauração; rollback total em erro/interrupção; testar falha induzida.
5. Instalar PBS/encounters/áudio do piloto com namespace Johto; compilar e iniciar Game.exe isolado com save separado. Gerar `JOHTO_JOGAR_EXPERIMENTAL.bat` e `scripts/regions/pilot_johto.py`, verificados pelo `TitleKanto.rb`.
6. Somente depois de CI e QA E2E real habilitar `--apply` transacional para instalação principal. **Não desativar controles de `install_johto.py` para acelerar o processo**.
7. Publicar scripts, documentação, manifestos e testes no GitHub. Mídia autorizada deve seguir política de distribuição; fonte original, executáveis e saves locais não vão para `main`.

---

## 10. CHECKLIST DE ENTREGA POR MAPA (copiar para cada mapa físico)

- [ ] Identificação canônica/variante e inclusão no registry; MapID origem→destino congelado.
- [ ] Arte/tileset/autotile/passabilidade/colisão/dimensões e direitos conferidos.
- [ ] Todas as portas, escadas, conexões, passagens especiais e retornos têm testes.
- [ ] **Todos** NPCs visíveis e condicionais listados, posicionados, com sprite/diálogo PT-BR/flags.
- [ ] Todos os treinadores identificados por PBS válido e conectados à batalha do Blue, incluindo Master/rematches.
- [ ] **Todos** itens visíveis/ocultos, TMs/HMs, recompensas, lojas e interações têm registro/condição/recebimento testado.
- [ ] Eventos de missão, puzzles, versões HGSS, cutscenes e mudanças pós-história funcionando.
- [ ] Encontros, taxas, Pokémon/formas, horários, HM/ferramenta e acesso ao ambiente validados.
- [ ] BGM/ME, cena, volume, loop, fade, fallback e preferência pessoal testados.
- [ ] Vitória/derrota/cancelamento, PC/Box/Party, save/reload e reentrada testados.
- [ ] Nenhum `PENDING_*`, `BLOCKED_*` ou `expected_count=null` para obrigações do escopo declarado.
- [ ] Log, screenshot/vídeo no Game.exe e, na fase de release, JoiPlay; regressões Kanto/Decades verdes.
- [ ] Relatório assinado pelo processo de QA: `map_key`, testes, hashes, diferenças para HGSS e ID do commit.

**Definição de pronto por área:** 100% da checklist E o inventário conferido. **Definição de Johto inteira pronta:** todas áreas do escopo (incluindo interiores/opcionais previstos e Mt. Silver), história, eventos, itens, músicas, formas/versões compatíveis, saves e 13 gates reais concluídos.

---

## 11. PROMPTS OPERACIONAIS PARA CONTINUAR POR ESTE CHAT/CODEX

**Primeira implementação prioritária:**

> Execute o PASSO 00 e o PASSO 01 de `docs/JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md`, analisando o `game/` local e a fonte original do Map Pack (se presente). Produza hashes, inventário dos mapas, fonte/arte/direitos pendentes e relatório de bloqueios. Não sobrescreva Decades/Kanto e não declare Johto jogável sem execução no Game.exe. Publique somente código, testes e documentação, após CI.

**Primeiro piloto físico:**

> Execute PASSOS 02–06 somente para New Bark Town, Route 29 e os interiores indispensáveis. Importe terreno em cópia isolada, crie portas, casa, laboratório, mãe, Elm, três iniciais e rival; compile PBS válido e vincule às funções BlueJohto existentes, usando unicamente o motor de batalha atual. Crie o `Testar Johto` funcional com saves isolados, teste no Game.exe, registre pendências e não toque na campanha Decades/Kanto.

**Expansão por região:**

> Conclua o Marco N da Seção 7 do MD mestre. Para cada mapa físico dessa área, inventarie **todos** NPCs, eventos e itens, crie os eventos próprios, compile treinadores/encontros para a battle engine Blue e música regional autorizada, execute os contratos e E2E reais, publique alterações auditadas sem regressão. Só marque o marco como aprovado com 100% dos elementos desse escopo comprovados.

**Release final:**

> Quando todos os marcos estiverem realmente jogáveis, execute PASSOS 08–10, auditoria de cobertura, testes Windows/JoiPlay e os 13 gates; implemente e valide instalação transacional com backups e rollback. Nunca habilite `--apply` nem `VERIFIED_PLAYABLE` por sucesso de testes sintéticos.

---

## 12. RESUMO DA DECISÃO TÉCNICA

**Não importar um fangame HGSS pronto para dentro do Blue.** Importar **somente a geografia e artes cuja utilização tenha sido autorizada**, reconstruir **todos os NPCs, eventos, itens, encontros e música** de forma auditável para o runtime atual e chamar **somente a battle engine já existente**. O plano é incremental, mas a meta de cobertura é a **Johto inteira**. O primeiro sucesso real será `Testar Johto → casa de New Bark → Elm → inicial → rival → save/reload`, e não a produção de mais um documento de lógica simulada.

**Situação deste MD:** especificação publicada; mapas/eventos reais/áudios/PBS e aceitação continuam sujeitos à implementação e às evidências necessárias.
