# Unova G04.2 — Métodos, horários, estações e áreas de encontros selvagens

**Entrega de catálogo e validação offline.** Não cria encontros reais, não altera `Game.exe`, `Data/*.rxdata`, `PBS/encounters.txt`, sprites, saves ou a barra de jogabilidade.

## Fontes que o repositório realmente contém

| Fonte | O que comprova | O que NÃO comprova |
|---|---|---|
| [U03 — 74 áreas simbólicas](../data/regions/unova-u03-areas.json) | Nome, chave, categoria, campanha/pós-jogo/evento | MapIDs, espécies, taxas, slots ou nível real |
| [Parser PBS do Blue](../scripts/regions/pbs.py) | 20 identificadores de métodos reconhecidos | Qual deles existe em cada área de Unova |
| [Habitat Dex](../scripts/battle_polish/Habitat.rb) | Leitura da tabela nativa por mapa/versão quando instalada | Unova possui tabelas importadas |
| [BlueEvolutionScaling](../scripts/battle_polish/EvolutionScaling.rb) | Evolução dinâmica preserva pesos originais de encontros | Chance de evolução é peso de captura/spawn |
| [Sinnoh CH13](../data/regions/sinnoh-symbolic-encounters.json) | Exemplo de perguntas de auditoria por terreno | Dados históricos de Sinnoh válidos automaticamente para Unova |

**Nenhuma fonte acessível neste estado do repositório comprova encontros de White por método/área, horário, estação, versão, espécie, peso, taxa ou nível.** Por isso, nenhum desses números foi criado nesta G04.2. A atribuição de métodos por categoria de terreno é um **roteiro de perguntas para a auditoria**, não uma tabela de encontros real.

## Entregáveis

- [Catálogo versionado por área e método](../data/regions/unova-g04-encounter-methods-contract.json), esquema 1, versão `WHITE_BW`, exatamente as 74 áreas U03 preservadas na ordem original.
- [Validador e planejador somente leitura](../scripts/regions/audit_unova_g04_encounter_methods.py), com auditoria estática dos nomes de métodos a partir de `ENCOUNTER_TYPES` no `pbs.py` sem executar o gerador Kanto.
- [136 testes positivos e negativos](../tests/test_unova_g04_encounter_methods.py), integrados ao CI Linux/Windows; o portal testa Barra G e bloqueio de estados falsamente jogáveis.

## Famílias de métodos aceitas pelo parser PBS

| Família | Métodos base e variantes | Uso na G04.2 |
|---|---|---|
| Grama e terreno | `Land`, `LandMorning`, `LandDay`, `LandAfternoon`, `LandEvening`, `LandNight` | Perguntas para rotas, florestas e outras áreas externas |
| Caverna | `Cave`, `CaveMorning`, `CaveDay`, `CaveAfternoon`, `CaveEvening`, `CaveNight` | Perguntas para cavernas, ruínas e montanhas |
| Surfar/água | `Water`, `WaterMorning`, `WaterDay`, `WaterNight` | Perguntas para água e rotas |
| Pescar | `OldRod`, `GoodRod`, `SuperRod` | Perguntas para água e rotas, sem presumir varas obtidas |
| Interação com rocha | `RockSmash` | Perguntas para cavernas, sem ativar HM |

O Habitat Dex também conhece `HeadbuttHigh`, `HeadbuttLow` e agrega opções em `Fishing`, mas **esses nomes não são entradas PBS aceitas pelo parser utilizado como referência**. Não foram inventados slots de Headbutt no arquivo de Unova.

No catálogo há **34 áreas com métodos candidatos a investigar** e **40 sem atribuição candidata**, incluindo assentamentos, ginásios e locais de eventos. Isso **não significa** que essas 40 áreas não possuam Pokémon nativos; significa apenas que a G04.2 não dispõe de fonte para incluí-los. Em especial, os locais `event_only`, como Liberty Garden e Unity Tower, são excluídos de qualquer sugestão de encontro aleatório.

## Condições de horário, temporada e versão

**Horários:** `MORNING`, `DAY`, `AFTERNOON`, `EVENING`, `NIGHT` e `ANY`. Um método com sufixo de horário só pode ser consultado no horário correspondente: `LandMorning` não pode ser consultado como `NIGHT`. Métodos sem sufixo aceitam todos os horários como perguntas de auditoria. Essa validação de sintaxe **não confirma espécies, disponibilidade ou mudança real de encontro por horário**.

**Temporadas:** `SPRING`, `SUMMER`, `AUTUMN`, `WINTER` e `ANY`. Todas são dimensões potenciais de investigação do Pokémon White. **Nenhuma tabela sazonal, taxa, espécie ou mapa específico foi inferido**. Por isso `method_season_assignments=[]` e `seasonal_species_assignment_verified=false`.

**Versão:** o contrato aceita unicamente a campanha `WHITE_BW`. Não deduz diferenças de Pokémon Black, Black 2 ou White 2, nem faz uma distribuição fictícia por versão.

## Dados desconhecidos permanecem desconhecidos

Todos os 74 registros permanecem com:

```json
{
  "encounter_slots": [],
  "species_method_assignments": [],
  "method_version_assignments": [],
  "method_time_assignments": [],
  "method_season_assignments": [],
  "encounter_rate": null,
  "weight_percentages": null,
  "level_ranges": null,
  "real_species": null,
  "source_map_id": null,
  "destination_map_id": null,
  "native_pbs_verified": false,
  "may_install": false
}
```

`null` significa **não comprovado**. `0` seria um valor numérico específico e por isso também é rejeitado se não houver evidência; não serve para afirmar que uma área tem ausência de encontros.

O validador bloqueia percentuais de 1%, 20% ou 100% que sejam adicionados sem fonte, assim como listas falsas de espécies, slots, níveis, MapIDs, licenças, horário sazonal e permissões de instalação. O código não calcula soma de pesos enquanto todos os valores são desconhecidos; o aceite de pesos reais e a soma por método/variante/período/estação pertencem à futura **G04.4**, após fonte original validada.

A chance `15/30/45/60` de uma **evolução dinâmica** no código compartilhado Blue não é taxa de encontro da espécie no ambiente. A evolução/nível por progresso será tratada separadamente na **G04.3**.

## Exemplo de auditoria, não de spawn

```bash
python scripts/regions/audit_unova_g04_encounter_methods.py --check
python scripts/regions/audit_unova_g04_encounter_methods.py --simulate-demo
python -m unittest discover -s tests -p test_unova_g04_encounter_methods.py -v
```

O demo faz quatro perguntas sem gerar qualquer captura: grama matinal Route 1 na primavera, caverna Wellspring no inverno, pescaria Undella Bay no verão, caverna noturna Giant Chasm no outono. Todas retornam `AUDIT_QUESTION_NOT_AN_ENCOUNTER_ASSIGNMENT`, `encounter_slots=[]` e `weight_percentages=null`.

**Após CI e merge da G04.2:** Barra G **19/32 (59%)**, G04 **2/4**. **Barra A 0/8**, Unova jogável **0/32**, região `planned`. A revisão de conteúdo nativo, direitos, instalação e testes no Game.exe/Android permanece separada.
