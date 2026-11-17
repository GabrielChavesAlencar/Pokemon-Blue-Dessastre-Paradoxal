# Unova G02.3 — Elite Four em qualquer ordem, N, Ghetsis e créditos

**Entrega de código offline:** contratos simbólicos da primeira Liga de **Pokémon White**, baseados em G01.1–G01.4 e G02.2. **Não altera** o Game.exe, mapas RXDATA, saves, Pokémon capturados, itens ou insígnias reais.

## Arquivos

- [Contratos estruturados do clímax](../data/regions/unova-g02-elite-finale-contracts.json): quatro membros da Elite, cinco eventos do Castelo e tokens de história únicos.
- [Motor offline G02.3](../scripts/regions/audit_unova_g02_elite_finale.py): validadores, batalha simulada, capítulos e créditos, sem qualquer escrita de arquivos.
- [106 testes positivos e negativos](../tests/test_unova_g02_elite_finale.py): todas as 24 permutações da Elite, derrotas, duplicidades e conteúdo nativo falsificado.
- [G02.2](UNOVA_G02_2_CONTRATOS_HISTORIA_OITO_GINASIOS.md): oito insígnias necessárias para entrar em CH10; o motor G02.3 reconstrói os pré-requisitos por G01 e G02.2, sem pular etapas.

## Elite Four — ordem totalmente livre

| Membro | Especialidade | Resultado exigido para avanço |
|---|---|---|
| Shauntal | Ghost | WIN |
| Grimsley | Dark | WIN |
| Caitlin | Psychic | WIN |
| Marshal | Fighting | WIN |

Os quatro contratos são simbólicos, sem IDs de treinador, equipes, níveis, sprites ou salas instaladas. A escolha da ordem é livre: **todas as 24 permutações são aceitas**. Uma vitória é registrada uma única vez; replay de vitória é no-op. Uma derrota não registra vitória e informa a área simbólica segura `UNOVA_POKEMON_LEAGUE` para teste de retorno, sem teleporte real. Reescrever vitória anterior como derrota é bloqueado.

Somente **quatro vitórias diferentes**, oito badges da G02.2 e `complete_elite` com marcador `SIMULATED_ONLY_NO_NATIVE_APPROVAL` permitem avançar de **CH10_LEAGUE** para **CH11_NS_CASTLE**. A primeira passagem para o Castelo não se apresenta como desafio do campeão Alder (conteúdo separado de pós-jogo).

## Castelo de N e campanha White

Os eventos só podem ser concluídos na seguinte ordem, sem saltos ou duplicações:

1. `UNOVA_G023_CASTLE_ENTRY`: entrada simbólica no Castelo
2. `UNOVA_G023_ZEKROM_STORY_GATE`: gate narrativo da variante White, **sem captura real de Zekrom**
3. `UNOVA_G023_N_BATTLE`: derrota simulada de N exige **WIN**; LOSS é tentativa retriável sem avanço
4. `UNOVA_G023_GHETSIS_BATTLE`: exige vitória sobre N; LOSS não avança nem modifica a campanha
5. `UNOVA_G023_CREDITS`: créditos simbólicos exclusivamente após vitória sobre Ghetsis

Os eventos geram recibos únicos `OFFLINE_G023_NOT_A_NATIVE_BATTLE_OR_CREDITS` e tokens derivados dos recibos: `ZEKROM_GATE_READY_NOT_CAPTURED`, `CREDITS_SIMULATED` e `POSTGAME_ACCESS_SIMULATED`. **Esses tokens não significam Pokémon recebido, cutscene ou créditos executados**.

Para ambas as batalhas contra N e Ghetsis, derrota retorna o estado inalterado e aponta apenas para a área simbólica `UNOVA_NS_CASTLE`. O simulador não executa blackout, retorno de Centro Pokémon ou teleporte.

Após os cinco recibos, `complete_castle` conclui CH11 com o marcador sintético e `unlock_postgame` ativa somente a missão **CH12_POSTGAME**. Conteúdo de Looker, sábios, lendários adicionais, exploração pós-jogo e batalhas de revanche está pendente em **G02.4**.

## Integração e limites

O estado G02.3 acrescenta a um envelope G02.2 previamente validado: `elite_wins` (conjunto ordenado pelos resultados, sem impor ordem aos membros), `castle_receipts` (prefixo estrito) e `unique_story_tokens` (derivados de eventos, sem escrita em inventário). O esquema v1 da G01.1 não muda.

O codec da G01.4 pode serializar e restaurar **somente a projeção G01** desse envelope. **Ainda não serializa os campos G02.2/G02.3**, e os retornos simbólicos não alteram o checkpoint do jogador. A integração com saves reais exigirá adaptação nativa, testes no Game.exe e preservação regional.

Em todos os resultados, `game_exe_tested=false`, `native_save_modified=false`, `real_credits_shown=false`, `legendary_captured=false` e `can_install=false`. Testes Python/CI não podem promover Unova a jogável.

## Validar sem usar o PC

```bash
python scripts/regions/audit_unova_g02_elite_finale.py --check
python scripts/regions/audit_unova_g02_elite_finale.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g02_elite_finale.py' -v
```

A execução do demo percorre a jornada sintética desde a G01, os oito ginásios G02.2, quatro membros da Elite em ordem diferente, derrotas retriáveis e créditos G02.3 até a abertura do CH12. Não inicia Game.exe.

## Barras

Após CI Linux/Windows e portal aprovados e integração à main: **Barra G 14/32 (44%)**, **G02 3/4**. Barra A técnica **0/8**, Unova jogável **0/32**, região **planned**. Próxima: **G02.4 — Looker, sábios, lendários e pós-jogo**, também inicialmente com contratos simbólicos.
