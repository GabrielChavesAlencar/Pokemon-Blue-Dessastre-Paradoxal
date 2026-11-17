# Unova — G04.3: evolução dinâmica e nível dos selvagens (somente GitHub)

**Campanha:** WHITE_BW · **Região:** UNOVA · **Estado:** planned, sem encontros nativos verificados.

Esta entrega cria um **contrato auditável e um simulador determinístico, exclusivamente com fixtures**. Não instala Unova, não atualiza o runtime Ruby, não modifica Pokémon reais, níveis PBS, RXDATA, Game.exe, mapas, saves ou probabilidades.

## Fontes autoritativas

- [G04.2 — áreas e métodos](../data/regions/unova-g04-encounter-methods-contract.json): 74 referências de área, 20 métodos PBS, horários e estações **candidatos à investigação**, não métodos atribuídos a cada área.
- [G03.2 — escalonamento de treinadores](../data/regions/unova-g03-leader-scaling-contracts.json): referência de progresso `HIGHEST_NON_EGG_PARTY_LEVEL`. Os percentuais 70% e 90% são específicos de **treinadores**, não devem ser aplicados a Pokémon selvagens.
- [EvolutionScaling.rb](../scripts/battle_polish/EvolutionScaling.rb): fonte de execução para evolução automática de Pokémon selvagens, com limite de três evoluções e sem alterar o PBS.
- [Contrato G04.3](../data/regions/unova-g04-wild-scaling-contract.json): a origem de todos os valores afirmados nesta fase. A simulação usa os mesmos limites, mas **não substitui teste no Essentials**.

## Referência de nível

O sinal de progresso é o maior nível da equipe, ignorando ovos. Se a equipe não possuir Pokémon não-ovo, o fallback técnico é nível 1. O limite superior vem de `GameData::GrowthRate.max_level`, e **não** de uma tabela inferida de insígnias.

O nível original do Pokémon do slot selvagem é o ponto inicial, sem aplicar 70%/90%. Se o nível do slot ultrapassar o nível de progresso, o runtime mantém o encontro original. Quando uma evolução é autorizada, seu nível pode subir **apenas até o mínimo da evolução**, respeitando o progresso.

| Método verificado no Ruby | Limiar para evolução dinâmica |
|---|---|
| Evolução por nível (Level e variantes de horário/gênero) | Nível de evolução original + 5 |
| Pedra/item (Item e variantes) | Progresso a partir do nível 30 |
| Troca (Trade e variantes) | Progresso a partir do nível 40 |
| Amizade (Happiness e variantes) | Progresso a partir do nível 45 |
| Localização, golpe, status, clima ou outros métodos especiais | Desconhecido: não converter automaticamente |

A regra por gênero/hora só vale quando aquela condição está conhecida e satisfeita. Quando dois destinos diferentes ficam elegíveis, a espécie original é preservada; nenhum ramo é escolhido arbitrariamente. Formas diferentes de zero e espécies sinalizadas como lendárias, míticas, Ultra Beasts, paradoxos ou outras especiais não podem receber evolução dinâmica.

## Chance **condicional à evolução**, não taxa de captura/encounter

Depois de atingido o limiar de evolução, a diferença entre nível de progresso e limiar define a chance por tentativa:

| Diferença (progresso − limiar) | Chance de evoluir naquele encontro sintético |
|---:|---:|
| Menor que zero | 0% |
| 0–4 | 15% |
| 5–14 | 30% |
| 15–24 | 45% |
| 25+ | 60% |

Exemplo **fictício**, marcado `FIXTURE_*`: um Pokémon base de nível 10 com evolução por nível 20 não evolui antes de progresso 25. Em progresso 30, há chance condicional de 30% de obter o estágio evoluído no **mesmo slot**, com nível mínimo 25. As taxas/weights originais do slot **não são alteradas**. Não é uma atribuição de Rattata/Raticate ou qualquer outra espécie real a Unova.

A simulação usa rolls explícitos de 0 a 99, sem aleatoriedade implícita, até três tentativas para uma cadeia de evolução. Isso permite regressões reproduzíveis, mas não atesta o resultado de batalhas, captura ou encontros no Game.exe.

## Proveniência de Unova

Para todas as 74 áreas:

- `native_level_min`, `native_level_max`, `native_species`, `native_encounter_rate`, `native_slot_weights`, `native_map_id` = **null**;
- `native_pbs_verified` e `scaling_installed` = **false**;
- as espécies do grafo, os níveis, as taxas e o peso inseridos no demo são **dados sintéticos** e são rejeitados se declarados como fonte nativa.

**`null` não quer dizer taxa zero.** Dados reais só serão importados mediante PBS/métodos/MapIDs/proveniência/licença validados. Soma dos percentuais, duplicações e integridade das tabelas reais ficam na **G04.4**.

## Execução offline

```bash
python scripts/regions/audit_unova_g04_wild_scaling.py --check
python scripts/regions/audit_unova_g04_wild_scaling.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g04_wild_scaling.py' -v
```

O validador exige integridade G04.2, fontes e limiares G03.2, assinatura do código Ruby original, região `planned`, 74 áreas sem dados inventados e barras técnicas/jogáveis zeradas. Testes negativos rejeitam valores nativos falsos, nível de insígnia presumido, pesos transformados em chance de evolução, formas especiais, hora/gênero não confirmados e ramificações ambíguas.

**Limites da entrega:** a G04.3 não prova que o módulo Ruby esteja ativado em Unova instalada ou que os encontros reais tenham sido importados. A verificação nativa e o dispositivo Android/JoiPlay permanecem pendentes. A Barra G só deve ser incrementada após CI e publicação; a Barra A e o contador jogável não mudam.
