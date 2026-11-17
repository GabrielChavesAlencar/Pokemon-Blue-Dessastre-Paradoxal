# MapIDs do Pokémon Blue — Decades, Kanto, Johto, Hoenn, Sinnoh e Unova

**Data: 17/11/2026 · Fonte: arquivos reais B01 e B04 enviados pelo usuário.**

Este documento mostra **todos os MapIDs ocupados**, a retenção administrativa de **76 posições para Sinnoh** e os **174 candidatos fisicamente vazios para planejar Unova**. Não muda o Game.exe, não instala mapas e **não comprova reservas futuras**. Ver [inventário JSON B05](../data/regions/sinnoh-b05-mapid-planning.json) e [auditor automático](../scripts/regions/audit_sinnoh_b05_mapid_planning.py).

## Resumo

| Classificação | MapIDs (inclusive) | Quantidade | Estado |
|---|---|---:|---|
| Decades / origem não atribuída aos três manifestos | `1`, `22`, `32–33`, `42–43`, `48`, `76–275` | **207** | Ocupados; não reutilizar |
| Kanto | `300–441` | **142** | Ocupados, manifesto instalado informado |
| Johto | `600–699` | **100** | Ocupados e reservados pela prévia |
| Hoenn | `700–898` | **199** | Ocupados; faixa do instalador protegida até 999 |
| **Ocupados — total** | — | **648** | Inventário B01 |
| **Sinnoh — retenção de planejamento** | **`442–517`** | **76** | Separados para Sinnoh, ainda sem instalação |
| **Unova — candidatos após separar Sinnoh** | Faixas na seção 3 | **174** | Apenas fisicamente vagos; **não alocados** |
| Hoenn — espaço protegido e sem mapa físico | `899–999` | 101 | **Não disponibilizar a Unova** |
| `1000+` | Não homologados | — | Compatibilidade não verificada |

## 1. MapIDs já usados — lista completa por intervalos

A união exata dos **648 IDs ocupados**, sem omissões, é:

**`1`, `22`, `32–33`, `42–43`, `48`, `76–275`, `300–441`, `600–898`.**

| Faixa | Quantos ocupados | Identificação |
|---|---:|---|
| `1–99` | **31** | Base/outros; includes `1`, `22`, `32–33`, `42–43`, `48`, `76–99` |
| `100–275` | **176** | Base/outros |
| `300–441` | **142** | Kanto |
| `600–699` | **100** | Johto |
| `700–898` | **199** | Hoenn |
| **Total** | **648** | **Sem sobreposição entre os três manifestos regionais** |

A categoria **207 mapas da base/outros** significa *ocupados, porém não atribuídos aos três manifestos B04*. Não equivale a prova de que todos pertencem ao Decades puro.

As classificações de Kanto/Johto/Hoenn vieram dos resumos numéricos de `blue-kanto-install.json`, `blue-johto-main-preview.json` e `blue-hoenn-install.json`; os próprios manifestos não vieram no ZIP, portanto ainda dependem de verificação independente se forem usados como prova formal de origem.

## 2. MapIDs separados para Sinnoh — 76 posições

**Retenção administrativa de planejamento: `442–517` (76 IDs).**

Esta retenção foi registrada no [catálogo B05](../data/regions/sinnoh-b05-mapid-planning.json) para **não recomendar o mesmo espaço a Unova**. Os 76 números estão vazios no inventário B01, e há 76 entradas na árvore de mapas Sinnoh do doador: **54 com terreno e 22 vazias**.

**Não é ainda reserva técnica homologada de instalação:** não existe mapeamento `ID origem Sinnoh → destino 442–517`, não foram copiadas imagens nem mapas, e **R07/R08/R09 continuam pendentes**. Se surgirem reservas futuras legítimas de Kanto, Johto ou Hoenn que conflitem com esses IDs, será necessário revisar esta retenção antes de importar.

O piloto antigo de Sinnoh `800–805` usa uma cópia isolada; no Decades multirregional essa faixa está ocupada por Hoenn. **Não reutilizar `800–805`**.

## 3. MapIDs fisicamente livres para planejar Unova

Após descontar os IDs ocupados, separar os 76 de Sinnoh e excluir o espaço protegido `600–999`, restam **174 candidatos entre 1 e 599**:

| Faixa | Quantidade | Prioridade para planejar Unova |
|---|---:|---|
| **`518–599`** | **82** | **Melhor intervalo contínuo disponível no inventário** |
| `276–299` | 24 | Expansão potencial |
| `49–75` | 27 | Expansão potencial |
| `2–21` | 20 | Expansão potencial |
| `23–31` | 9 | Expansão potencial |
| `34–41` | 8 | Expansão potencial |
| `44–47` | 4 | Expansão potencial |
| **Total** | **174** | **Ainda sem reserva aprovada para Unova** |

**Sugestão:** priorizar **`518–599` (82 IDs)** no planejamento de Unova; usar as outras 92 posições apenas com revisão específica. Unova permanece `planned` e o catálogo `data/regions/unova-u03-areas.json` ainda não possui MapIDs de destino definidos.

**Cuidado:** fisicamente vazio significa somente que o ID não foi encontrado no snapshot. **Não significa autorização imediata para sobrescrever, importar ou usar no jogo.** As reservas futuras dos demais instaladores precisam ser verificadas; `1000+` depende de avaliação de compatibilidade.

## 4. Faixas adicionais protegidas por código

- **Johto:** `600–699` já ocupados. Código de prévia protege esse bloco.
- **Hoenn:** `700–999` protegidos pelo alocador; somente `700–898` estão ocupados neste snapshot, mas **`899–999` não devem ser oferecidos a Unova**.
- **Sinnoh:** `442–517` retidos administrativamente para planejamento, **não instalados**, sujeitos à auditoria R07.
- **Unova:** nenhuma reserva homologada ou MapID instalado registrado nesta etapa.

## 5. Erro encontrado no coletor B04 (617 em vez de 648)

O arquivo real B04 apresentou **617 MapIDs físicos**, apesar de os hashes de `MapInfos.rxdata` e `Tilesets.rxdata` serem **idênticos aos da B01**, que havia identificado 648 MapIDs.

A causa foi confirmada no script `coletar_b04_sinnoh.ps1`: o filtro `^Map([0-9]{3,5})\.rxdata$` ignorava IDs de **um ou dois algarismos**. Os **31 IDs omitidos** foram:

**`1`, `22`, `32–33`, `42–43`, `48`, `76–99`.**

O conjunto relatado pelo B04 é um subconjunto **exato** do B01; nenhum desses 31 IDs deve ser contado como livre. A versão corrigida do coletor (filtro aceitando 1–5 algarismos) foi fornecida separadamente nesta conversa.

O auditor B04 passou a identificar **esse caso legado específico** e indicar que precisa de uma nova coleta, sem declarar falsamente que o B04 observou 648 mapas. Os três manifestos regionais informam IDs acima de 99, de forma que seus mapeamentos numéricos continuam coerentes com o B01.

## 6. Identificação dos documentos e hashes

| Comprovante | SHA-256 |
|---|---|
| ZIP original B01 | `1da47ce2c4ebc6317d2df7548d128937e623cef45b41838f4e69162aa9e9be9d` |
| ZIP original B04 | `7e8a696a650034f85d397bb3fc8ccd9dcd116f9d100b2aae7e7cbe070d1396e7` |
| `MapInfos.rxdata` | `8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420` |
| `Tilesets.rxdata` | `2fd4551a5767615a159a8b5b65a604d1e486009d37953ca6a1955affffabf675` |
| Manifesto Kanto declarado no B04 | `cd4c07603222de90ba20cbe92befd100b90de617333f135f95993ac2d2d62372` |
| Manifesto Johto declarado no B04 | `bdce76a0d6d32c2d8f5ad7a1f9bb765dfd2e3ff748e7a2ea18a4f1cbbc737c0b` |
| Manifesto Hoenn declarado no B04 | `78a13097149b5005dc3b014a9dc25eb61912bb36d159e84946127bce526494f7` |

**Proteções:** nenhuma alteração de `game/Data`, `MapInfos`, `Tilesets`, saves, imagens, áudio ou Game.exe; barras **B/C/D = 0/13**. Este MD é um inventário e planejamento, não liberação de região jogável.

**Regra de manutenção:** ao instalar qualquer região, refazer o levantamento B01/B04 e auditar novas colisões **antes** de atribuir um destino; não promover retenções administrativas a reservas nativas sem revisão de origem e direitos.
