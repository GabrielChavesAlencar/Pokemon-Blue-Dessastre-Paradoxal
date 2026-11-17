# Sinnoh — Barra B, B06: prévia técnica dos 76 MapIDs reais

**Data:** 17/11/2026  
**Estado:** prévia de remapeamento baseada nos **ZIPs reais** de fonte Sinnoh (Pokémon World V18), base Decades (B01) e proveniência B04 V2. **Nenhuma alteração do jogo e nenhuma reserva nativa definitiva.** A Barra B continua 0/13 aprovações técnicas, C/D 0/13; R07, R08 e R09 seguem pendentes.

## O que avançou tecnicamente

A [prévia determinística](../data/regions/sinnoh-b06-technical-candidate.json) agora apresenta **76 pares MapID de origem → ID candidato**, usando a **retenção administrativa de planejamento 442–517** já existente. É uma **tabela explícita, não instalável**, que pode orientar o futuro importador de mapas e seus testes de colisão.

| Fonte doadora | ID candidato no Decades | Situação do mapa |
|---|---:|---|
| `Map209` — Twinleaf Town | `442` | terreno real; **sem NPC/evento inicial** |
| `Map210` — Sandgem Town | `443` | terreno real |
| `Map211` — Jubilife City | `444` | terreno real |
| `Map212` — Oreburgh City | `445` | terreno real |
| Demais mapas com terreno | `446–495` | 50 mapas, na ordem dos MapIDs de origem |
| 22 mapas sem terreno (placeholders/interiores) | `496–517` | identificados, **não jogar como mapas prontos** |
| **Total** | **76 IDs candidatos** | **54 terrenos + 22 placeholders** |

**Regra:** ordenar os **54 MapIDs de origem que realmente contêm terreno** de forma crescente e associar a 442–495; depois os **22 vazios** de forma crescente a 496–517. Os IDs de origem não foram alterados; toda a relação pode ser lida no JSON. **A ordem dos IDs não estabelece conexões, posição de NPCs ou história.**

O relatório B00 conferiu **0 comandos nativos de transferência de mapa** no material, portanto o plano de 76 posições não cria warps inexistentes. As conexões, interiores, eventos Rowan/Barry, ginásios e testes no Game.exe continuam tarefas separadas.

## Integridade das fontes reais e limites

Ao preparar a B06, foram verificados **76 arquivos `MapNNN.rxdata` individualmente no ZIP original recebido**, comparando SHA-256 com a auditoria profunda anterior. Resultado: **76/76 hashes iguais, 0 arquivos ausentes ou alterados**.

| Objeto | SHA-256 |
|---|---|
| ZIP Pokémon World V18 | `ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35` |
| MapInfos do doador | `a5de4d870ae08aa3730942496734c7a0917505a6d435ff178ce5a10f73fc6495` |
| Tilesets do doador | `ddd1e57f033e9ad061870d2cb72288e17ab4f28bb2ace7cea69336a95f8cd1f1` |
| SHA-256 canônico da lista dos 76 pares `source_id + sha256(MapNNN)` | `55799526a92740134b81575c5c731193e985d6abdf0ee363e4b2ce1899c8778e` |
| MapInfos da instalação Decades B01 e B04 V2 | `8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420` |

O [auditor B06](../scripts/regions/audit_sinnoh_b06_technical_candidate.py) confirma que a prévia respeita o B00/B01/B04 V2/B05, não utiliza IDs ocupados no Decades e **preserva os 174 candidatos físicos de Unova**. A opção adicional de **verificação de arquivos reais** aceita os ZIPs localmente, sem extrair conteúdo ou escrever `game/Data`:

```bash
python scripts/regions/audit_sinnoh_b06_technical_candidate.py

# Somente na máquina privada com ZIPs de fonte e inventário já recebidos:
python scripts/regions/audit_sinnoh_b06_technical_candidate.py \
  --source-zip "Pokemon World V18.zip" \
  --native-inventory "SINNOH_B01_INVENTARIO_DECADES.zip"
```

A opção com ZIPs lê os bytes da fonte e do inventário, confere o arquivo doador pelo hash, os **76 mapas individuais**, MapInfos/Tilesets do doador, os hashes do B01 e a ocupação de 648 MapIDs. **O CI público só executa a auditoria de metadados e testes sintéticos**, porque os dois ZIPs binários privados **não** são armazenados no GitHub. Nenhum sprite, tileset, mapa, música ou save de terceiros é distribuído pelo PR.

## Bloqueio de tilesets (não resolvido pela renumeração de MapIDs)

Os mapas originais Sinnoh referenciam os tilesets de origem **1 `OutsideWorld2.7` e 31 `SinnohCompleteTileset`**. Na base Decades os IDs 1 e 31 já pertencem a **tilesets diferentes**. Portanto, **não é permitido importar a referência numérica de tileset original**.

O campo `source_to_native_tileset_mapping` da B06 fica **vazio**. Só será definido após conferir **direitos individuais**, arquivos de imagem/autotiles, tabela Tilesets nativa atual e prévia em staging privado **append-only**, preservando os tilesets já instalados.

## Segurança da Barra B e próximas ações

- **B06 entregue como engenharia técnica preliminar**, com 21 testes negativos/positivos, mas **não marca R07 concluído**: a B04 comprova ocupação instalada, não todas as reservas futuras Kanto/Johto/Hoenn.
- **R08 não concluído:** geometria/tilesets reais ainda não foram convertidos nem colocados em um piloto privado; há 22 mapas vazios e permissões de redistribuição em aberto.
- **R09 não concluído:** Game.exe/JoiPlay continuam sem testes manuais, conforme combinado.
- **Barra B aprovada = 0/13**, não 1/13, pois o fato de existirem 76 candidatos sem colisão **não prova integração funcional**.
- **Unova continua protegida:** 174 posições fisicamente candidatas, com maior bloco **518–599 (82)**, sem reserva homologada.

**Próxima tarefa técnica útil:** criar o **pipeline privado de staging/dry-run de geometria** que consuma esse candidato, verifique recursos permitidos e permita checar as 54 geometrias reais **somente em cópia isolada**, sem alterar a instalação principal. Antes de chamá-lo de aprovado, resolver R07 e as autorizações dos assets.
