# Unova G01.3 — Recompensas únicas e reentrada segura (somente simulação)

**Fase:** G01.3, baseada em G01.1 (`schema_version=1`) e G01.2 (máquina de estados). **Não é integração com o Game.exe, inventário, saves, mapas RXDATA, scripts Ruby ou Android/JoiPlay.**

## Entrega de código e dados

- [Política estrita e lista das 13 recompensas/eventos U07](../data/regions/unova-g01-reentry-policy.json).
- [Máquina offline de recibos e reentrada](../scripts/regions/audit_unova_g01_reentry_ledger.py), somente em memória. Não escreve arquivos.
- [95 testes positivos e negativos](../tests/test_unova_g01_reentry_ledger.py), execução Linux e Windows no GitHub Actions.
- Comandos de verificação: `python scripts/regions/audit_unova_g01_reentry_ledger.py --check` e `python scripts/regions/audit_unova_g01_reentry_ledger.py --simulate-demo`.

A G01.3 envolve o `state` original, que continua **estritamente igual ao schema G01.1**, em um envelope com `schema=1`, `region=UNOVA`, `campaign=WHITE_BW`, `scope=SIMULATED_ONLY_NOT_GAME_SAVE`, `event_receipts` e `reward_intents`. A estrutura nova não autoriza migração de save real; G01.4 continuará responsável por qualquer contrato de serialização/migração sintética.

## Recompensas derivadas da fonte U07

Cada concessão é uma **intenção offline**, não um item recebido no jogo.

| Evento U07 | Intenção de recompensa | Quantidade |
|---|---|---:|
| MOM_XTRANSCEIVER | `KEY_ITEM:XTRANSCEIVER` | 1 |
| JUNIPER_LAB_POKEDEX | `KEY_ITEM:POKEDEX` | 1 |
| MOM_TOWN_MAP | `KEY_ITEM:TOWN_MAP` | 1 |
| JUNIPER_CAPTURE_TUTORIAL | `ITEM:POKE_BALL` | **5** |
| ROUTE2_PASSAGE | `STORY_TOKEN:ROUTE_2_PASSAGE_READY` | 1 |

Os cinco tokens e quantidades são lidos e conferidos contra `data/regions/unova-u07-nuvema-events.json`, sem inventar recompensas ou valores. O catálogo U07, suas equipes e seus requisitos também são validados pelas ferramentas U07 existentes.

**Invariante:** cada evento concluído possui exatamente um recibo, na mesma ordem dos eventos U07; seus campos e as intenções acumuladas devem corresponder exatamente aos dados da fonte. É proibido acrescentar um recibo, token ou quantidade, trocar resultados de batalha, reescrever a escolha do inicial ou alterar uma flag sem atualizar a evidência coerentemente. Regras inválidas bloqueiam a operação, sem mutar o estado recebido.

## Comportamento do simulador

| Operação | Primeira execução | Replay ou reentrada |
|---|---|---|
| `begin` | Inicia CH01 de G01.2 | Nenhuma nova concessão, nenhum reinício do progresso |
| `record_u07` | Usa G01.2 para validar ordem e pré-requisitos e acrescenta recibo/intenções | Mesmo evento e argumentos originais = **no-op**; argumentos diferentes = **rejeição** |
| `complete` | Marca missão e flag do capítulo com `SIMULATED_ONLY_NO_NATIVE_APPROVAL` | Repetição da mesma conclusão = **no-op**, sem alterar recompensas |
| `advance` | Avança somente para o próximo capítulo de G01.2 | Repetição da transição já realizada = **no-op** |
| `reenter` | Revisita capítulo atual ou anterior apenas para leitura | Mantém o capítulo corrente, o checkpoint, as flags, as missões e todas as intenções sem mudanças |

As primeiras batalhas de Bianca e Cheren podem avançar mesmo com resultado simulado `LOSS`; o resultado é registrado no recibo e não pode ser trocado depois. A primeira batalha contra N exige `WIN`; uma tentativa com `LOSS` retorna `BATTLE_LOST_RETRY_REQUIRED` sem criar recibo ou progresso, permitindo uma tentativa futura. Uma derrota registrada depois de uma vitória do mesmo evento é rejeitada.

**Atenção:** reentrar em um capítulo *não teleporta o jogador*, não executa evento Ruby e não reseta checkpoint. Todos os retornos `native_save_modified`, `actual_items_granted`, `game_exe_tested` e `can_install` permanecem falsos. O `reward_intents` é registro de quantidades *planejadas*, não inventário real.

## Limitações e testes restantes

- **G01.4**: esquema explícito de serialização, validação de round-trip, versão e migração de envelopes sintéticos. Não está incluída nesta entrega.
- Eventos U08–U32, Pokémon recebidos, times, itens de NPCs, liga e pós-jogo precisam de fontes/contratos próprios. A G01.3 **não inventa** recompensas de capítulos posteriores.
- Sincronização com a bag, switches, party e saves reais exige integração controlada e teste no Game.exe, preservando a instalação principal.
- A aprovação de CI não valida MapIDs, RXDATA, condições nativas nem Android.

## Barra G e barras técnicas

Após o CI aprovado, a barra GitHub passa de **10/32 para 11/32 (34%)**; **G01 = 3/4**. A Barra A permanece **0/8**, Unova jogável **0/32** e status do portal **planned**.
