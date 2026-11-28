# KA01 — auditoria de fonte e escolha do primeiro corredor

A [baseline KA00](KA00_BASELINE_EXECUCAO.md) foi concluída no
[PR #406](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/406).
Esta fase decide o que entra na futura construção. Não instala, aloca IDs,
reescreve tilesets, distribui mídia ou valida jogabilidade.

| Fonte examinada | Resultado |
|---|---|
| [Fire Ash de Luc-ker, índice nativo fixado](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/MapInfos.rxdata) | 56.722 bytes, blob Git `1622efe230a813229eb89b9d53b4bf463161b587`, SHA-256 `96d3ad8327fc27f2e0c00ff33ce845404475b921767043d731c05a74aed0bbe9`. 996 entradas no jogo todo. Leitura inerte registrou 4 rótulos de Santalune e 13 de Lumiose, nenhum para Vaniville ou Aquacorde. Nomes não comprovam terreno, cobertura, licença ou compatibilidade. Não usar mapa, evento, tile ou scripts. |
| [Virtualization](https://eeveeexpo.com/threads/8573/) e [World Project](https://eeveeexpo.com/resources/1877/) | Virtualization é outra campanha, sem confirmação de geometria, dependências e direitos por arquivo. World Project não oferece cobertura homologada de Kalos. Nenhum pacote foi inspecionado para reaproveitamento ou aceito. |
| [pokex](https://github.com/peanutseagull/pokex) | Base de outro motor; não extrair ROM, gráficos, áudio ou scripts. |
| [Atlas KD05](../KALOS_KD05_ATLAS_VISUAL_E_TILES_KANTO.md) | Fotos e grafo X/Y como referência, nunca como mídia incorporada. Começar com geometrias autorais para Vaniville–Aquacorde–Santalune. |
| [Assets/credits da base Decades](https://github.com/HazyCrazy/Pokemon-Decades/tree/ff6091b23603b3298ad72a7584b02a51e1d01c0e) | Direção visual: tiles de Kanto já usados pelo Blue, sem redependência de outro fangame. Uso e atribuição por componente ainda serão verificados no recorte de tiles de KA03; presença no jogo/creditar não autoriza redistribuição. Não trocar os arquivos globais de Kanto. |

O contrato de fonte registra 11 áreas simbólicas, 10 conexões e o
retorno pelo mesmo percurso, sem reservar IDs ou copiar mapas. Onde
não houver peça aprovada, usar composição autoral apropriada ao estilo
de Kanto. A prova de fonte não é prova de renderização ou compatibilidade
no Game.exe/JoiPlay. Para um doador futuro, estas regras de
[proveniência e escopo](../KALOS_KD01_FONTES_E_DIREITOS.md) permanecem.

**Próximo gate:** KA02 precisa reconciliar ocupação, conflitos e
reservas correntes antes de qualquer destino numérico. O recorte
simbólico não cria vaga, não ativa Kalos e não autoriza MapIDs de
quatro dígitos. Não iniciar jogo, release ou modificar saves por aqui.
