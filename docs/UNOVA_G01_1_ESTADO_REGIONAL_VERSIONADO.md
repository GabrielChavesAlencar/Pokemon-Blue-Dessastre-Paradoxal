# Unova G01.1 — Esquema versionado do estado regional (v1)

**17/11/2026 — entregue como CONTRATO DE DADOS OFFLINE, sem escrita em saves e sem instalar mapas.**

## Objetivo e arquivos

- [Contrato de estado G01.1](../data/regions/unova-g01-state-contract.json): especifica versão 1, identidade regional, capítulos, flags, missões e checkpoint.
- [JSON Schema v1](../data/regions/unova-g01-state.schema.json): campos e enums explícitos com `additionalProperties: false`.
- [Validador Python](../scripts/regions/audit_unova_g01_state_schema.py): valida a especificação, compara com U03 (74 áreas), U07 (13 eventos iniciais) e registro público de regiões, e aceita apenas snapshots sintéticos estruturalmente válidos.
- [52 testes G01.1](../tests/test_unova_g01_state_schema.py): versões, namespaces, atributos extras, capítulo, missão, flag e checkpoint indevidos.
- Comando CI: `python scripts/regions/audit_unova_g01_state_schema.py --check`. Não existe opção de importar/aplicar este estado no `Game.exe`.

## Modelo v1

O `default_state` tem campos obrigatórios, incluindo:

| Campo | Tipo | Regra |
|---|---|---|
| `schema_version` | inteiro igual a 1 | Outras versões rejeitadas, sem migração implícita |
| `region` e `campaign` | `UNOVA` e `WHITE_BW` | Não aceita estado cruzado de outra região |
| `state_status` | `SIMULATED_ONLY_NOT_GAME_SAVE` | Nunca é um save oficial |
| `current_chapter` | uma das 13 chaves `UNOVA_CH00…CH12` | Estado inicial `UNOVA_CH00_NOT_STARTED` |
| `flags` | objeto de valores booleanos | 25 chaves registradas: 13 eventos U07 e 12 marcas de conclusão de capítulo |
| `missions` | objeto de estados string | 12 missões; valores `not_started`, `active`, `completed`, `blocked` |
| `checkpoint` | objeto de 7 campos | áreas simbólicas U03 ou null; `map_id`, `x`, `y` obrigatoriamente null e `verified_in_game=false` |

**Semântica de ausência:** flag ausente equivale a `false`; missão ausente equivale a `not_started`. O snapshot inicial contém `flags={}`, `missions={}` e checkpoint vazio.

Os **13 capítulos** representam pré-jornada, sequência White de Nuvema até Castelo de N, e pós-jogo. As **12 missões** correspondem a capítulos 1–12 e se conectam a uma área simbólica do catálogo U03. Não existem MapIDs, NPCs físicos ou switches numéricos atribuídos.

O validador verifica a **estrutura**, a coerência com os catálogos versionados, as chaves permitidas e a ausência de reivindicações nativas; ele **não autoriza** passar de um capítulo ao próximo, conceder uma recompensa ou salvar/ler um save real. Isso será responsabilidade das fases seguintes.

## Compatibilidade e falha fechada

1. Somente `schema_version=1`, número inteiro real (não booleano).
2. Versão mais recente/antiga ou campos desconhecidos **bloqueados**.
3. Não converter automaticamente versões; migração explícita continua pendente na **G01.4**.
4. Não habilitar máquinas de estado, alterações automáticas nem regras de recompensa; essas implementações são **G01.2/G01.3**.
5. O validador recusa falsificação de `game_exe_tested`, `can_install`, checkpoints verificados ou os IDs numéricos nativos.
6. Teste CI sintético não é execução de `Game.exe`, JoiPlay, integração PBS/RXDATA ou validação de um save local.

## Barra GitHub e barras nativas

Ao passar testes Linux/Windows/portal, somente **G01.1** muda para `done`. A barra **G** passa para **9/32 (28%)**, enquanto **Barra A permanece 0/8** e Unova jogável permanece **0/32**. Status da região: **planned**.

Próxima etapa proposta: **G01.2 — máquina de estados de capítulos** usando este contrato como entrada, com condições de progressão e transições testadas *sem engine*. Não avançar automaticamente G01.2/3/4 somente porque o esquema está definido.
