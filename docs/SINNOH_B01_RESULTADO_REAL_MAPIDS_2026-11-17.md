# Sinnoh — B01: inventário real Decades recebido e comparado (17/11/2026)

**Situação:** o usuário enviou `SINNOH_B01_INVENTARIO_DECADES.zip`, contendo somente `MapInfos.rxdata`, `Tilesets.rxdata` e `native_inventory.json`. Os dois hashes declarados foram conferidos sobre os arquivos do ZIP. A leitura de `MapInfos` foi feita como Ruby Marshal inerte; nenhum script do jogo foi executado. O conteúdo binário do usuário **não foi publicado no repositório**.

## Identificação dos arquivos

- ZIP de inventário SHA-256: `1da47ce2c4ebc6317d2df7548d128937e623cef45b41838f4e69162aa9e9be9d`.
- `MapInfos.rxdata` SHA-256: `8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420`.
- `Tilesets.rxdata` SHA-256: `2fd4551a5767615a159a8b5b65a604d1e486009d37953ca6a1955affffabf675`.
- Doador Sinnoh anteriormente auditado: Pokémon World V18, ZIP SHA-256 `ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35`.

## Diagnóstico de colisões

| Indicador | Resultado |
|---|---:|
| MapIDs físicos no Decades | **648** |
| MapIDs no índice MapInfos | **648** |
| Mapa presente no índice, mas sem arquivo físico | **0** |
| Arquivo físico sem registro no índice | **0** |
| IDs Sinnoh da árvore original | **76** |
| IDs Sinnoh já ocupados no Decades | **72** |
| IDs Sinnoh sem ocupação física nessa cópia | **5, 899, 900 e 906** |
| IDs fisicamente não ocupados entre 1 e 599 | **250** |
| Maior bloco contíguo não ocupado nessa faixa | **442–599 (158 IDs)** |

Distribuição observada: **349** IDs ocupados entre 1–599, **100** entre 600–699 (Johto), **100** entre 700–799 (Hoenn), **99** entre 800–899 (Hoenn). A faixa 600–999 continua excluída do remapeamento de Sinnoh, e IDs >=1000 não foram homologados.

Os **72 MapIDs de origem em colisão** são:

`165, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 250, 251, 252, 253, 254, 255, 256, 257, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 302, 408, 888, 892, 897, 898`

Os IDs originais Sinnoh fora da faixa conservadora de 1–599 são `888, 892, 897, 898, 899, 900, 906`. A existência física de vagas **não comprova** sua disponibilidade jurídica, lógica ou reserva futura; nenhum dos 250 IDs foi alocado a Sinnoh.

## Conflito de tilesets: mesmo número, gráfico diferente

| ID | No doador Pokémon World V18 | No Decades atual |
|---|---|---|
| `1` | `OutsideWorld2.7` | `Outside stock` |
| `31` | `SinnohCompleteTileset` | `FRLG_Preview_Mart interior` |

Os números dos tilesets do doador **não podem ser transferidos diretamente**. A conversão precisará tratar imagens, autotiles e referências por mapa, com permissões individuais e sem sobrescrever tilesets Kanto/Johto/Hoenn/Decades.

## Estado das proteções

- **B = 0/13:** a Barra B exige integração técnica homologada, não apenas inventário.
- **C = 0/13, D = 0/13:** sem teste de Game.exe e JoiPlay (adiados conforme combinado).
- R07 (reservas futuras) permanece pendente; R08 (importação física autorizada) e R09 (QA nativa) continuam pendentes.
- Nenhum arquivo `MapNNN.rxdata` original, save, gráfico, áudio, script ou `Game.exe` foi modificado ou publicado nesta entrega.

## Próxima ação técnica

Auditar os IDs futuros reservados para Kanto/Johto/Hoenn (incluindo conteúdo ainda não instalado) e obter a aprovação/licença específica dos tilesets e outros recursos. Só depois elaborar o **plano explícito de destinos e renumeração de tilesets**, com dry-run/staging em cópia isolada e rollback.

O [recibo JSON derivado](../data/regions/sinnoh-b01-actual-native.json) registra os hashes, contagens, conflitos e limites da análise, sem conter os arquivos do jogo do usuário.
