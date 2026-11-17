# Unova G05.1 — HMs e itens-chave exclusivos por região

**Campanha:** WHITE_BW · **Estado:** somente GitHub, Unova `planned` · **Sem instalação ou alteração de saves.**

## Objetivo e fonte de verdade

Definir e testar o isolamento regional da **Bolsa, atalhos e PC de itens** na integração futura de Unova, conforme o comportamento já implementado no Blue compartilhado:

- [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb): `regional_item?` classifica por `GameData::Item.try_get`; itens com `is_HM?` ou `is_key_item?` são guardados em `region_key_items` na região de origem e restaurados apenas ao voltar; `pcItemStorage` é isolado de forma semelhante; atalhos locais são salvos/filtrados.
- [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb): ao verificar movimentos de campo, exige a permissão regional e a presença do HM no inventário ativo. Fora de Kanto, o comportamento específico depende do registro regional; a G05.1 não altera esse runtime.
- [Regions.rb](../scripts/battle_polish/Regions.rb): o catálogo de Unova usa eventos simbólicos locais `CUT_LOCAL` etc.; a checagem do evento antecede a ferramenta. Em Sinnoh existem recibos de coleta regional específicos; **Unova ainda não possui recibos nativos verificados**.
- [Sinnoh S16](../data/regions/sinnoh-hms-s16.json): referência contratual de integridade, sem instalar itens/alterar outros sistemas.
- [G01.1 de Unova](../data/regions/unova-g01-state-contract.json): snapshot sintético, sem adaptador de save nativo.
- [Registro das regiões](../site/public/data/regions.json): Unova ainda está `planned`.

O [contrato G05.1](../data/regions/unova-g05-regional-items-contract.json) e o [auditor G05.1](../scripts/regions/audit_unova_g05_regional_items.py) verificam assinaturas relevantes dessas fontes, e **bloqueiam alterações incompatíveis**.

## Regras de inventário

| Categoria reconhecida pela API do Essentials | Tratamento previsto |
|---|---|
| HM (`is_HM?`) | Exclusivo da região ativa; guardar/restaurar no cofre `region_key_items` |
| Item-chave (`is_key_item?`) | Exclusivo da região ativa; não transportar para outra região |
| TMs/TRs | Permanecem no inventário global, conforme runtime |
| Consumíveis e itens comuns | Permanecem globais |
| Mega Stones (não classificadas como chave) | Permanecem globais |
| Atalhos de HM/item-chave | Remover ao sair; recuperar somente atalhos válidos daquela região |
| PC de itens (`pcItemStorage`) | Guardar/restaurar HMs e itens-chave por região, sem misturar com Pokémon Boxes |

O simulador testa uma viagem **Kanto → Unova → Kanto** com `FIXTURE_*`: um HM e item-chave de Kanto desaparecem da Bolsa de Unova e voltam quando a simulação retorna a Kanto. Itens do PC recebem o mesmo isolamento; TMs, consumíveis e Mega Stones continuam disponíveis. Se houver erro de capacidade no destino, a operação sintética é rejeitada **antes** de qualquer mudança, com estado de entrada intacto. Isso **não substitui** o algoritmo de capacidade/rollback real do Essentials.

Não é feito inventário inventado de itens-chave reais de Unova: nomes, IDs PBS, fontes, entrega por NPC, eventos nativos e MapIDs permanecem `null`.

## Movimentos de campo previstos em Unova

| Ação | Evento simbólico registrado | HM/item nativo | Evento nativo |
|---|---|---|---|
| CUT | `CUT_LOCAL` | desconhecido | pendente |
| FLY | `FLY_LOCAL` | desconhecido | pendente |
| SURF | `SURF_LOCAL` | desconhecido | pendente |
| STRENGTH | `STRENGTH_LOCAL` | desconhecido | pendente |
| WATERFALL | `WATERFALL_LOCAL` | desconhecido | pendente |
| DIVE | `DIVE_LOCAL` | desconhecido | pendente |

Em simulação, a checagem exige (1) **região atual = Unova**; (2) um evento local explicitamente sinalizado; e (3) um HM presente na Bolsa *simulada*. Mesmo quando todos passam, o resultado é `SIMULATED_GATES_PASS_NOT_NATIVE_AUTHORIZED`: **não autoriza** o uso do movimento no jogo. A G05.1 não cria recibos de pickup nem equipara indevidamente a Bolsa à comprovação de obtenção local; há trabalho nativo pendente.

A mecânica de insígnias e restrições de especiais será tratada em **G05.2**. O NPC/instalação e retorno físico ficam em **G05.3**. Blackout e integração de estado compartilhado ficam em **G05.4**.

## Salvamentos e compatibilidade

O modelo manipula **apenas objetos sintéticos em memória**, nunca lê ou grava o Game.exe, RXDATA, PBS, saves, mapas, eventos ou o `$PokemonGlobal` real. Uma campanha Decades legada que nunca viajou mantém as regras nativas; não foi criado migrador de saves.

Em caso de entrada inválida, IDs diferentes de `FIXTURE_*`, atalho regional duplicado, quantidade não positiva, destino sem capacidade ou origem/destino incorretos, a simulação falha de forma fechada e mantém o estado original.

## Como validar no repositório

```bash
python scripts/regions/audit_unova_g05_regional_items.py --check
python scripts/regions/audit_unova_g05_regional_items.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g05_regional_items.py' -v
```

São **98 novos testes**, incluindo casos negativos de cruzamento entre regiões e de falso estado jogável. O CI de Unova executa checks, demonstração, testes e compilação sintática no Linux e regressões no Windows; o site valida o progresso da Barra G.

**Critério de conclusão:** apenas após o CI aprovado, a Barra G vai de 21/32 para 22/32; Barra A continua 0/8 e Unova jogável 0/32. A G05.1 encerra apenas o contrato auditável, **não a implementação nativa**.
