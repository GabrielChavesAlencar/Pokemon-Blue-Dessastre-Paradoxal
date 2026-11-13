# Johto — auditoria do Map Pack v1 enviado em 13/11/2026

## Fonte realmente recebida (não é a release v3 da página)

**Arquivo:** `Remastered Kanto Johto Map Packv1.zip` (8.533.963 bytes), enviado pelo usuário.

**SHA-256:** `5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715`.

A leitura foi feita sem executar scripts ou eventos Ruby e sem importar o ZIP no repositório. O código do projeto ganhou mapeamento factual em [johto-source.json](../data/regions/johto-source.json) com **74 mapas de origem 79–152**, cada um identificado pela árvore `Johto Enhanced` (ID 76, pastas ID 77 e 78). Os IDs 2–75 são Kanto/auxiliares e 153 não pertence à seleção Johto. Esses são **IDs do pacote**, não IDs finais do Blue.

### Coordenadas e áreas confirmadas

| ID do pacote | Nome | Dimensões |
|---:|---|---:|
| 79 | New Bark Town | 22 × 48 |
| 80 | Cherrygrove City | 86 × 55 |
| 81 | Violet City | 70 × 49 |
| 82 | Azalea Town | 58 × 54 |
| 83 | Goldenrod City | 64 × 47 |
| 84 | Ecruteak City | 82 × 64 |
| 85 | Olivine City | 72 × 70 |
| 86 | Cianwood City | 42 × 66 |
| 87 | Mahogany Town | 47 × 52 |
| 88 | Blackthorn City | 65 × 76 |
| 89 | Ilex Forest | 120 × 86 |
| 90 | Slowpoke Well | 40 × 40 |
| 102 | Mt. Silver | 54 × 42 |
| 103 | Mt. Silver Peak | 46 × 46 |
| 104 | Route 29 | 84 × 38 |
| 105 | Route 30 | 65 × 61 |
| 106 | Route 31 | 73 × 63 |
| 113 | Route 34 | 64 × 58 |

**Correção da documentação anterior:** a versão v1 enviada **possui Mt. Silver e Mt. Silver Peak**. A página da fonte utilizada originalmente descreve outra release; é incorreto inferir que um pacote v1 tenha exatamente o conteúdo da versão v3.

### Conexões externas e limites

- O arquivo original `PBS v16 - v21/map_connections.txt` apresenta **42 conexões entre mapas Johto**; foram transcritas como **dados de referência** em [johto-v1-map-connections.json](../data/regions/johto-v1-map-connections.json).
- **New Bark Town ↔ Route 29:** `79,West,13,104,East,0`.
- **A ligação Route 29 ↔ Cherrygrove não aparece nesse arquivo**. Apenas 40 dos 74 mapas aparecem nas 42 conexões; **34 não têm conexão registrada**. Isso não é um mundo navegável completo.
- Os 74 mapas RMXP de Johto possuem **0 eventos RPG::Event**; **nenhum NPC, warp de porta, item, treinador ou gatilho da história** foi entregue nessa fonte.
- Os **15 OGG** do ZIP são `KM_*.ogg` de Kanto, não uma trilha Johto confirmada.
- Não há os interiores de casa 2F/1F e laboratório de Elm. A geometria para os três interiores depende da auditoria de templates do Blue.
- `Map001.rxdata` falta, mas o `MapInfo 1 = Intro` é metadado fora de Johto. A exceção declarada `source.accepted_missing_mapinfo_ids=[1]` apenas permite esse caso; outros mapas ausentes continuam bloqueados.
- `Graphics/Autotiles/R49Water.png` está ausente para slot 7 do tileset 23. Todas as 74 tabelas de tiles de Johto foram varridas e **nenhuma usa IDs de autotile 336–383**. O staging poderá limpar apenas slots comprovadamente sem uso; se um mapa utilizar o slot, deverá **falhar**.
- Os dois autotiles `.jpg` do pacote são do tileset 21 de Kanto e não são necessários ao escopo de Johto selecionado.

### O que falta executar com o jogo nativo

A fonte real não inclui o `game/` instalado, que está ignorado por Git por segurança. Antes de criar o stage, ainda precisam ser executados `audit_johto.py --game game --archive ...` e `plan_johto.py` contra os **MapIDs e os hashes originais do Blue/Decades**. Só então `stage_johto.py` poderá gerar a cópia segura e `verify_johto.py` verificar a preservação dos mapas base. A partir daí, criar interiores, definir portas/XY reais, compilar NPCs e inspecionar o `Game.exe` isolado.

**Direitos de reprodução e de redistribuição de tiles, mapas, músicas e gráficos ainda exigem revisão.** Os binários do pacote não foram publicados no GitHub. `import_enabled=false` e `can_install=false` são mantidos; não confundir arquivo auditado com Johto jogável.
