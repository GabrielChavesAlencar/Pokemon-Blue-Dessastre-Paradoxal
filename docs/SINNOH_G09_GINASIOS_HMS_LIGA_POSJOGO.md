# Sinnoh G09 — auditoria de progressão (ginásios, HMs, Liga e pós-jogo)

**17/11/2026 · GitHub-only.** Esta entrega reconcilia contratos *já existentes*, sem criar novos mapas, NPCs, PBS, insígnias, recompensas ou teletransporte no jogo. **Não executa Game.exe/JoiPlay e não acessa saves reais.** O resultado da auditoria é um checklist com todos os vínculos nativos ainda pendentes.

## 1. Ordem dos oito ginásios e correspondência de HMs

A [matriz G09](../scripts/regions/audit_sinnoh_g09_progression.py) cruza **S15, S16 e CH11** pela **insígnia**, nunca por índice de array. A ordem narrativa dos ginásios preservada por S15 difere, no terceiro e quarto elementos, da ordem histórica/administrativa dos marcos de HMs CH11.

| Ordem dos ginásios | Líder | Insígnia | HM necessário para uso em campo | Item HM |
| --- | --- | --- | --- | --- |
| 1 | Roark | COAL | ROCK_SMASH | HM06 |
| 2 | Gardenia | FOREST | CUT | HM01 |
| 3 | **Fantina** | **RELIC** | **DEFOG** | HM05 |
| 4 | **Maylene** | **COBBLE** | **FLY** | HM02 |
| 5 | Crasher Wake | FEN | SURF | HM03 |
| 6 | Byron | MINE | STRENGTH | HM04 |
| 7 | Candice | ICICLE | ROCK_CLIMB | HM08 |
| 8 | Volkner | BEACON | WATERFALL | HM07 |

O catálogo regional CH11 continua listando `COAL, FOREST, COBBLE, RELIC, FEN, MINE, ICICLE, BEACON` **sem ser reordenado**. Reordenar diretamente esse catálogo poderia romper o armazenamento regional existente. Os testes G09 asseguram o vínculo Fantina → RELIC → DEFOG e Maylene → COBBLE → FLY.

**Ter a insígnia não equivale a receber o HM.** Para autorizar uma ação de campo serão exigidos comprovante de coleta **dentro de Sinnoh**, item correto e badge local. Um item trazido de Kanto, Johto, Hoenn ou Decades não satisfaz a condição. Os adaptadores `SinnohGymContracts.rb` e `SinnohHMContracts.rb` continuam com registros de fontes nativas vazios; portanto não concedem badges nem HMs na instalação real.

## 2. Distortion World, Elite Four, Cynthia e Hall of Fame

O contrato [S21](../data/regions/sinnoh-league-s21.json), ligado ao livro de eventos [CH14](../data/regions/sinnoh-story-ch14-contract.json), prevê **oito checkpoints**:

| Etapa | Checkpoint | Evidência prévia necessária |
| --- | --- | --- |
| 1 | Volkner / BEACON | Retorno seguro de Distortion World (S20) e insígnia separada |
| 2 | Barry antes da Liga | Oito insígnias de Sinnoh |
| 3 | Aaron | Vitória confirmada sobre Barry |
| 4 | Bertha | Vitória confirmada sobre Aaron |
| 5 | Flint | Vitória confirmada sobre Bertha |
| 6 | Lucian | Vitória confirmada sobre Flint |
| 7 | Cynthia | Vitória confirmada sobre Lucian |
| 8 | **Hall of Fame** | Vitória confirmada sobre Cynthia **mais confirmação própria do motor** |

**Vitória contra Cynthia não conclui automaticamente a Liga**. O `P09_HALL_OF_FAME` exige evento e resultado `engine_hall_of_fame_confirmed` independentes. Os oito registros S21 são planejamento autoral; *nenhum* MapID, evento de batalha ou PBS nativo dessa sequência foi confirmado pelo GitHub. Os times/níveis do Platinum são referências históricas; os níveis reais seguem a política compartilhada do Blue (Normal 70% / Master 90%) e não valores fixos publicados.

## 3. Seis portas de pós-jogo S23

| Evento de referência | Requisito adicional além do Hall of Fame |
| --- | --- |
| Battle Zone / Fight Area | Evento de chegada nativo verificado |
| Heatran / Stark Mountain | Entrada na Battle Zone previamente concluída |
| Cresselia / Fullmoon Island | Evento real verificado |
| Darkrai / Newmoon Island | **Item de evento autorizado** e callback verificado |
| Shaymin / Flower Paradise | **Item de evento autorizado** e callback verificado |
| Revanches oficiais Full Power | **Todas as dez Ligas** concluídas, roster Full Power nativo verificado e callback de batalha |

As cinco equipes de revanche históricas de Aaron/Bertha/Flint/Lucian/Cynthia são **referências Platinum**, não equivalem a equipes fortes nativas do Blue. Os eventos lendários não concedem espécie, item, mapa ou acesso automaticamente. Nem o Hall of Fame, nem o pós-jogo executam viagens entre regiões por conta própria.

## 4. O que a G09 acrescenta

- [Auditor cruzado G09](../scripts/regions/audit_sinnoh_g09_progression.py): reaproveita os validadores existentes S15/S16/S21/S23, confronta 8×ginásios/HMs, 8×checkpoints da Liga e 6×portões de pós-jogo, e rejeita divergência de pré-requisitos, liberação nativa ou ganho de itens.
- [20 testes Python G09](../tests/test_sinnoh_g09_progression.py): cenários de falso MapID, badge adiantado, ordem confundida Fantina/Maylene, HM sem coleta, item estrangeiro, derrota/teleporte indevido, Hall sem confirmação, Heatran sem Battle Zone, Darkrai/Shaymin sem item, Full Power sem dez ligas e dados físicos fabricados.
- [Workflow GitHub Actions G09](../.github/workflows/sinnoh-g09-progression.yml): executa os 20 testes e revalida os auditores S15/S16/S21/S23 mais as **fixtures Ruby reais do repositório**. Publica só o JSON de metadados; nenhum save, Game.exe, sprite ou PBS proprietário é incluído.

### Comandos somente de código

~~~bash
python scripts/regions/audit_sinnoh_g09_progression.py
python -m unittest discover -s tests -p "test_sinnoh_g09_progression.py" -v
~~~

**Status esperado:** `CROSS_STAGE_PROGRESSION_AUDITED_OFFLINE_NATIVE_GATES_PENDING`.

## 5. Portões de aceite que não foram antecipados

- Provar os **oito ginásios físicos** e o resultado verdadeiro da batalha e concessão local de cada insígnia.
- Provar **oito coletas de HM** e as permissões de campo com inventário regional.
- Compilar e testar os PBS da Elite Four, Barry e Cynthia no clone isolado; verificar resultados e saves.
- Confirmar o **Hall of Fame separado de Cynthia** no motor e só depois registrar os eventos reais do pós-jogo.
- Verificar requisitos globais de dez ligas para Full Power e os itens de eventos especiais.
- Completar as comprovações R07 (MapIDs), R08 (recursos) e R09 (execução real), além do fluxo B10/B11 antes de rodar o jogo.

A G09 não altera as barras jogáveis B/C/D, que permanecem **0/13**.

**Próxima entrega — G10:** melhorar os guias de Sinnoh no portal e seus indicadores de progresso, mantendo os estados `planned` e `pendente` explícitos.
