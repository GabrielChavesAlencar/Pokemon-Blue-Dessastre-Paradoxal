# Sinnoh — Fase 03, núcleo Twinleaf / Lake Verity / Sandgem (evento autoral)

**Estado em 13/11/2026:** roteiro, handlers Ruby e compilador de eventos próprios **preparados**; **nenhum mapa Sinnoh real instalado e nenhuma fase jogável aprovada**. Esta página é handoff de integração para Codex após a auditoria real de mapas. Jamais habilitar a opção de Sinnoh ou mudar o início da campanha normal por causa de exemplos de testes.

## 1. Arquivos e responsabilidades

| Arquivo | Responsabilidade | O que ainda não prova |
| --- | --- | --- |
| [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) | Handler Ruby BlueSinnohPilot, estado regional, professor Rowan, Barry, escolha física de Turtwig/Chimchar/Piplup e Pokédex | Engine/Game.exe não executado |
| [sinnoh-twinleaf-events.json](../data/regions/sinnoh-twinleaf-events.json) | 9 mapas **simbólicos**, 5 handlers, 3 Poké Bolas, 16 transições, spawn no quarto do jogador | IDs, tiles, sprites, coordenadas ainda **null/false** |
| [build_sinnoh_twinleaf_events.py](../scripts/regions/build_sinnoh_twinleaf_events.py) | Compilador de overlays em memória sobre **cópia de geometria segura em** `.blue-work/sinnoh-stage/` | Não é instalador de mapas nem de PBS |
| [test_sinnoh_twinleaf_events.py](../tests/test_sinnoh_twinleaf_events.py) | Fixtures sintéticas, whitelist de scripts, hashes de mapas, 3 Poké Bolas/warps e isolamento | QA nativo não feito |
| [sinnoh_pilot_runtime.rb](../tests/sinnoh_pilot_runtime.rb) | Emulação puramente Ruby: save regional, starter, Barry, Pokédex e não regressão | Sem RPG Maker/Essentials instalado |

**Proteção principal:** todos os plugins permanecem próprios de Sinnoh. Os scripts de eventos gerados só podem ser: `BlueSinnohPilot.mother`, `barry_intro`, `rowan_briefcase`, `barry_rival`, `rowan_pokedex` e **três handlers com espécie fixa** `choose_starter_from_ball(:TURTWIG/:CHIMCHAR/:PIPLUP)`. Nada do jogo doador é executado/copied. A engine de batalha é Blue/Decades.

## 2. Fluxo planejado, original para Blue

1. **Quarto do jogador em Twinleaf:** ponto de entrada `SINNOH_PLAYER_BEDROOM`, dentro da casa. Nenhum MapID, spawn ou direção foi presumido, pois a fonte verdadeira ainda não foi mapeada.
2. **Mãe na casa (1F):** apresenta o encontro com Barry e desbloqueia o próximo passo no estado regional `sinnoh_pilot`.
3. **Barry na casa dele:** apresenta o interesse pelo lago. O primeiro diálogo só progride após a conversa com a mãe; não salta o roteiro ao carregar um save.
4. **Rowan próximo à maleta no Lago Verity:** conversa com o jogador e permite três **objetos físicos de Poké Bola**, não uma seleção em menu do professor.
5. **Três Poké Bolas físicas:** apenas um dos iniciais, no nível 5, é recebido através do motor (`pbAddPokemonSilent`). Se a função falhar, a seleção não é salva. Uma segunda Poké Bola não entrega outro Pokémon.
6. **Barry, rival de introdução:** usa o inicial com vantagem de tipo (Turtwig → Chimchar; Chimchar → Piplup; Piplup → Turtwig). Há três **versões planejadas** do treinador `:BLUE_SINNOH_RIVAL` (versões 0/1/2). A batalha não executa sem arquivo `Data/blue-sinnoh-rival-ready.txt` com conteúdo `BLUE_SINNOH_BARRY_V1_READY`, verificado **somente na cópia experimental** depois de configurar as três equipes PBS. Não criar marcador por padrão nem copiar o PBS doador.
7. **Rowan no laboratório de Sandgem:** a Pokédex só é marcada como obtida depois de ter o starter, lutar com Barry e a propriedade real `$player.has_pokedex=` estar disponível. Não altera Decades/Kanto/Johto/Hoenn.
8. **Rota 202 / avanço futuro:** apenas uma conexão de referência. Encontros, treinadores e eventos de tutoriais ainda terão de ser implementados no formato Blue.

Os diálogos acima são redação própria de Blue, não transcrição do roteiro de Pokémon Platinum.

## 3. Condições obrigatórias de um evento compilável

- MapIDs entre 1 e 599, **sem colisão** e coerentes com [plan_sinnoh_remap.py](../scripts/regions/plan_sinnoh_remap.py). **Não pressupor IDs livres sem inventário real de Kanto/Johto/Hoenn**.
- Todos os nove mapas do JSON estão presentes em um stage de geometria de Sinnoh que tenha o `stage-manifest.json` real criado pela transação, com SHA-256 compatível com cada `map_sha256` do JSON.
- Cada `x`, `y`, `arrival_x`, `arrival_y` precisa caber nas dimensões do mapa e ter `verified_position:true` ou `verified_arrival:true` após auditoria **visual/geométrica real**, sem editar esses flags só para satisfazer o teste.
- Cada NPC/Bola precisa de sprite existente na cópia experimental, nome seguro e `verified_sprite:true` após conferir os arquivos efetivos.
- Spawn na casa do jogador: `start.map_id` e coordenadas verdadeiros, `verified_position:true` e `passability_verified:true`, confirmado no motor.
- Os portais em lojas, interiores e routes não comprovados não devem ser inventados. Verificar ida e volta em cena real e não copiar comandos de evento doador.
- Nada é gravado em `game/` ou nos saves; a saída `--stage` é uma pasta nova em `.blue-work/sinnoh-stage/` que precisa ser integrada ao piloto somente depois de QA.
- Não usar `blue_regions.current` de outra região nem alterar flags existentes na save base.

**O template original está intencionalmente bloqueado**: todos os MapIDs, posições e nomes de sprite são `null` e todas as verificações são `false`. A tentativa de compilar esse arquivo sem auditar mapas deverá falhar — isso é sucesso da proteção, não um bug.

## 4. Passos para Codex com arquivos verdadeiros

Primeiro seguir o [plano de remapeamento da Fase 01](SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md) e a [prévia de geometria](SINNOH_FASE_01_PREVIA_GEOMETRIA.md), usando somente fonte autorizada. Depois:

1. Conferir quais mapas reais correspondem aos 9 símbolos da template e verificar todos os interiores e links do mapa. Não alterar os IDs de Decades/Kanto/Johto/Hoenn.
2. Produzir um estágio de geometria com `convert_sinnoh_geometry.py`, usar `--stage` **apenas** com o hash real do dry-run. Não misturar arquivos externos com o código autoral.
3. Criar cópia privada do JSON em `.blue-work/sinnoh/twinleaf-events-local.json` e preencher exclusivamente os IDs, hashes, sprites e coordenadas confirmados. Registrar evidências de passabilidade e screenshots no relatório local.
4. Rodar o compilador em modo **somente dry-run**:

```powershell
python scripts/regions/build_sinnoh_twinleaf_events.py --geometry-stage ".blue-work/sinnoh-stage/NOME-DO-STAGE-REAL" --spec ".blue-work/sinnoh/twinleaf-events-local.json" --label sinnoh-story
```

5. Conferir o relatório e só então gerar um **novo overlay isolado** na pasta `.blue-work` com o SHA do dry-run:

```powershell
python scripts/regions/build_sinnoh_twinleaf_events.py --geometry-stage ".blue-work/sinnoh-stage/NOME-DO-STAGE-REAL" --spec ".blue-work/sinnoh/twinleaf-events-local.json" --label sinnoh-story --stage --expected-dry-run SHA256_GERADO_NO_DRY_RUN
```

6. Preparar **três** equipes autorais PBS de Barry com o balanceamento dinâmico Decades/Blue, validar equipe e nomes, habilitar o marcador de rival **somente na cópia** após os testes. Não instalar no `game/` principal.
7. Vincular a cópia de eventos ao piloto isolado **após** verificar todos os vínculos e o início real na casa. Executar no Windows e Android: selecionar Turtwig/Chimchar/Piplup, negar segunda escolha, derrotar/perder do rival, conceder Pokédex, salvar/reabrir, atravessar todos os portais, voltar a Decades e conferir ausência de regressões.
8. Fazer relatório com MapIDs, screenshots/logs, hashes, rollback, testes e direitos; marcar os itens locais no [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md) **só com evidências reais**.

Testes do repositório sem o jogo:

```powershell
python -m unittest discover -s tests -p "test_sinnoh_twinleaf_events.py" -v
ruby -c scripts/regions/SinnohPilot.rb
ruby tests/sinnoh_pilot_runtime.rb scripts/regions/SinnohPilot.rb
```

### Atualização — equipes de Barry já preparadas por código

Consulte [SINNOH_FASE_03_BARRY_PBS.md](SINNOH_FASE_03_BARRY_PBS.md). O gerador [build_sinnoh_barry_pbs.py](../scripts/regions/build_sinnoh_barry_pbs.py) produz as três equipes de Barry a partir dos PBS nativos, e [verify_sinnoh_barry_pbs.py](../scripts/regions/verify_sinnoh_barry_pbs.py) verifica hashes, learnsets e contratos de escala de nível (70%/90%). **Nenhum arquivo de liberação é gerado**, e as três equipes ainda precisam ser compiladas e testadas no Game.exe. Por isso I07 continua **pendente**.

**Conflito a resolver antes de integração:** o piloto anterior [pilot_sinnoh.py](../scripts/regions/pilot_sinnoh.py) usa IDs 800–805, dentro da faixa 600–999 reservada a Johto, e [SinnohPreview.rb](../scripts/regions/SinnohPreview.rb) usa escolha de inicial por diálogo em vez das três Poké Bolas do roteiro novo. Não instalar esses dois modelos simultaneamente sem reconciliar as fontes/IDs/eventos.

## 5. Estado e próximos itens

- **S13** (introdução/Rowan/Barry) e **S14** (três iniciais) passaram a ter código e fixtures, mas devem permanecer **parciais**, não finalizadas.
- **Fase 03/12:** preparação de eventos feita, jogabilidade em Twinleaf/Sandgem **não aprovada**.
- **Barras técnicas/jogáveis/nativas:** **0/13**, sem alterar os saves ou mapa inicial do Blue.
- Próximo passo próprio de código: preparar os contratos das três versões de Barry com PBS e times compatíveis com o level cap do Blue, sem fabricar o conteúdo da fonte.
