# Johto — interiores HGSS reais (Akizakura16 / DonLawride / SirMalo)

**Status em 16/11/2026:** importador de tilesets HGSS privados implementado no código, com integração ao instalador geral Blue-Story e verificações de mapa/evento/save. **As imagens PNG de terceiros não foram incluídas no GitHub e não foram recebidas nesta sessão. Logo, não declarar que todos os interiores já aparecem visualmente com os novos gráficos.** Sem as fontes, o instalador mantém os tiles anteriores.

## Fontes externas — não redistribuir automaticamente

- **Akizakura16 — 4th gen Indoor Tileset**, recomendado para casas, quartos e interiores genéricos: https://www.deviantart.com/akizakura16/art/4th-gen-Indoor-Tileset-624832808 e https://eeveeexpo.com/resources/15/
- **DonLawride — HGSS Center and Mart Tiles**, recomendado para Centros e Poké Marts: https://www.deviantart.com/donlawride/art/HGSS-Center-and-Mart-Tiles-193996545
- **SirMalo — HGSS for RMXP**, complementar para consistência visual; publicação original diz que os interiores ainda estavam sendo desenvolvidos: https://eeveeexpo.com/resources/462/

Os créditos de Akizakura16 são solicitados expressamente no Eevee Expo; o download livre no DeviantArt não é uma licença universal para republicar gráficos em releases públicas. É preciso conferir os termos/licenças de cada autor. Os PNGs devem permanecer na pasta ignorada `.blue-work` até a autorização de redistribuição estar estabelecida.

## Abrangência de interiores no pacote compartilhado (MapIDs 674–699)

| Tipo | MapIDs | Proposta gráfica |
| --- | --- | --- |
| Quarto e casa New Bark | 674–675 | Akizakura16: piso, móveis, parede, decoração HGSS |
| Laboratório Elm | 676 | Akizakura16: piso de laboratório, terminais, balcões |
| Ginásio Violet | 677 | Recursos HGSS compatíveis com o ginásio; conservar puzzles |
| Torre Sprout | 678–680 | Recursos HGSS adequados; preservar escadas, treinadores e colisões |
| Centro Violet | 681 | DonLawride: balcão de cura, prateleiras e decoração |
| Casas New Bark | 682–683 | Akizakura16: casas com móveis coerentes |
| Centro Cherrygrove | 684 | DonLawride |
| Poké Mart Cherrygrove | 685 | DonLawride |
| Casas Cherrygrove | 686–691 | Akizakura16 |
| Interiores regionais | 692–699 | Por tipo: `house`, `center` e `mart` |

**Importantíssimo:** não invadir `Map700+`, que está reservado para Hoenn no jogo principal. A prévia QA separada pode ter conteúdo fora desse intervalo, mas isso NÃO autoriza sobrescrever Hoenn.

## Preparação privada dos arquivos

1. Baixar as imagens diretamente dos autores; verificar a autorização e registrar os créditos.
2. Converter/cortar os tilesheets para **PNG RGBA de 8 bits, não entrelaçado**, alinhado em células de 16×16 ou 32×32 pixels. O importador duplica os pixels dos tiles de 16×16 para 32×32 com nearest-neighbor; não suaviza pixels. A fonte pode ter até 512 px de largura. Remover legendas e áreas de créditos da zona de tiles e registrar os créditos nos metadados.
3. Colocar os PNGs privados em `.blue-work/johto-hgss-tiles/`. Exemplos: `Akizakura16_Indoor.png`, `DonLawride_Center_Mart.png`, `SirMalo_Interior.png`.
4. Criar `.blue-work/johto-hgss-tiles/manifest.json` com o SHA-256 real de cada arquivo e os posicionamentos concretos definidos **após inspeção visual** dos sprites e dos mapas. Não preencher coordenadas por suposição e não usar uma screenshot pequena no lugar da fonte completa.

Exemplo estrutural (as coordenadas de origem são meramente ilustrativas, **não estão aprovadas para jogar**):

```json
{
  "schema": 1,
  "sources": {
    "akizakura16": {
      "filename": "Akizakura16_Indoor.png",
      "sha256": "<SHA-256-REAL-DO-PNG>",
      "tile_px": 32,
      "credit": "Akizakura16"
    },
    "donlawride": {
      "filename": "DonLawride_Center_Mart.png",
      "sha256": "<SHA-256-REAL-DO-PNG>",
      "tile_px": 16,
      "credit": "DonLawride"
    }
  },
  "placements": [
    {
      "kind": "bedroom",
      "source": "akizakura16",
      "sheet_col": 1,
      "sheet_row": 2,
      "x": 5,
      "y": 5,
      "layer": 0,
      "passable": true
    },
    {
      "kind": "center",
      "source": "donlawride",
      "sheet_col": 3,
      "sheet_row": 4,
      "x": 5,
      "y": 5,
      "layer": 1,
      "passable": true
    }
  ]
}
```

Ao usar `kind`, a colocação é repetida em **todos os mapas daquele tipo**. Alternativamente, use `"map": 674` para editar só um mapa. `layer` 0/1/2 representa as camadas RMXP. `passable` deve ser verdadeiro para piso e falso para obstáculos. O compilador rejeita objetos bloqueantes em NPCs, transferências e spawn, além de aceitar apenas Map674–699. O sistema **não identifica sozinho qual célula do PNG representa cama, estante ou piso**, pois isso requer a imagem original para inspeção; não prometer essa automação.

## Instalação e atualização

- **Instalação nova:** `scripts/regions/johto_main_preview.py` invoca `compile_private_art` após a criação dos 100 mapas, acrescenta os pixels reais ao atlas de cada tileset, mapeia os tiles nas posições auditadas, gera as flags RMXP e cria manifestos/hashes. A fonte original não é publicada.
- **Instalação existente:** fechar `Game.exe`, abrir **Blue-Story.exe geral com internet**. `auto_integrate_johto.py` aplica `refresh_installed_private_hgss` quando encontra manifesto+PNG privados íntegros. Atualiza somente os MapIDs selecionados, `Data/Tilesets.rxdata`, os novos atlas `Graphics/Tilesets/BLUE_JOHTO_HGSS_PRIVATE_*.png` e `Data/blue-johto-main-preview.json`, com backups e rollback.
- **Se não houver arquivos privados:** sem alteração gráfica. Não criar falsa flag de conclusão. Johto, Kanto, Hoenn, Decades e saves são preservados.
- **Idempotência:** uma segunda execução com o mesmo hash de manifesto e PNG não refaz a aplicação; substituir fontes em uma instalação já modificada exige migração e auditoria próprias.

## QA necessário

O CI `.github/workflows/johto-local-integration-fixture.yml` cobre estrutura, hash de fonte, flag de passabilidade, remapeamento para Johto e falhas fechadas com PNGs sintéticos. **Não é QA visual dos sprites externos.** Testar num Game.exe real: quarto 2F, ida e volta pelas escadas, conversa com mãe/Elm, primeiro Centro e loja, casas, ginásio e Torre, colisão nas entradas, PC, cura e save/load, depois regressão de Kanto/Hoenn/Decades. Aplicar o pacote aos demais interiores somente após revisão visual.

## Arquivos de implementação

- `scripts/regions/johto_hgss_assets.py` — pixels reais, remapeamento e seleção por tipo de interior.
- `scripts/regions/johto_main_preview.py` — build novo e atualização transacional dos mapas existentes.
- `scripts/regions/auto_integrate_johto.py` — integração pelo Blue-Story.
- `tests/test_johto_hgss_assets.py` — testes sintéticos verificáveis (sem os PNGs de artistas).
