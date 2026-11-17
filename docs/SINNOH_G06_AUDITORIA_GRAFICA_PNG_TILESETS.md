# Sinnoh G06 — Auditoria gráfica estática (PNG e tilesets)

**17/11/2026 · Entrega exclusivamente no GitHub.** A G06 acrescenta um auditor de integridade PNG independente da B08 e confronta os manifestos públicos de B01/B06/B07/B08. Não lê o jogo do PC, não transfere PNGs do doador para o GitHub, não executa o `Game.exe` e não aprova Sinnoh como jogável.

## O que os manifestos públicos comprovam

| Elemento | Evidência pública | O que falta |
| --- | --- | --- |
| 648 mapas do jogo base | B01 declara inventário físico e SHA-256 do catálogo | Nova inspeção da instalação real |
| 70 tilesets nativos | `sinnoh-b01-actual-native.json` | Conferir a estrutura serializada e o slot zero |
| Tilesets de origem | `1 — OutsideWorld2.7`, `31 — SinnohCompleteTileset` | Direitos e imagens do doador |
| Tilesets privados esperados | **71 e 72, condicionalmente**: caso a tabela possua 70 registros e um slot 0 reservado, B07 adiciona 2 entradas | A B08 deve verificar os **índices reais** no `Tilesets.rxdata` local; não afirmar que foram confirmados no GitHub |
| Mapas com terreno | 54 candidatos em 442–495; 22 vazios em 496–517 não instalados | Eventos, warps, renderização e testes físicos |
| PNGs privados | B08 exige **14** arquivos, hashes no nome, referências resolvidas e CRC | Os **14 bytes reais não estão no repositório**. A G06 não afirma ter verificado CRC ou zlib dessas imagens |

A B08 existente já calcula CRC por chunk, confere a assinatura, o IHDR, o IEND, os hashes dos arquivos no stage e as referências de Tilesets/Autotiles. A G06 adiciona um validador reutilizável de PNG com verificações **mais profundas**, exercitado com **imagens sintéticas geradas pelos testes**.

## Validador PNG da G06

O [auditor](../scripts/regions/audit_sinnoh_g06_render_static.py) valida:

- Assinatura PNG; estrutura e ordem de `IHDR`, `PLTE`, `IDAT`, `IEND`; rejeição de chunk crítico desconhecido, chunk malformado, IHDR duplicado e bytes posteriores ao IEND.
- CRC-32 de **todos** os chunks; dimensões positivas até limites de segurança, pares válidos de bit depth/color type, parâmetros de compressão/filtro/interlace.
- IDAT contíguo, fluxo zlib válido e completo, contagem exata dos bytes descomprimidos por scanline e dos filtros PNG (0–4), inclusive padrão Adam7.
- Descompressão incremental com blocos pequenos, para reduzir o risco de alocação de dezenas de megabytes em memória. Imagens que excedam os limites de auditoria são recusadas.
- Ausência de alegações de renderização real no resultado, mesmo quando o PNG passa estruturalmente.

A estrutura PNG válida **não** certifica que a imagem seja compatível com o renderizador RGSS, com o OpenGL/DirectX, com a GPU do Windows Sandbox ou com o JoiPlay.

## Imagens muito altas: risco significativo

Os tamanhos abaixo são os **relatados na análise prévia do pacote doador**. O GitHub nesta entrega não reabriu seus PNGs para confirmar as dimensões.

| Tileset de origem | Dimensão relatada | Pixels | Memória teórica RGBA8 |
| --- | --- | --- | --- |
| `OutsideWorld2.7` | 256 × 50.000 | 12.800.000 | **48,83 MiB** |
| `SinnohCompleteTileset` | 256 × 70.000 | 17.920.000 | **68,36 MiB** |

A altura de **50.000/70.000 pixels excede o limite conservador de referência de 16.384 pixels por lado**, comum em determinadas configurações gráficas. Isso sinaliza risco — **não prova que a engine em uso tenha esse limite exato**. Mesmo quando a compressão PNG é pequena, a textura descomprimida pode ser grande. Não dividir ou redimensionar essas imagens automaticamente, pois isso altera índices de tiles e pode quebrar a geometria dos mapas.

A G06 classifica esses casos como **`needs_native_render_test=true`** e **`gpu_runtime_compatibility_confirmed=false`**.

## Entregas e testes GitHub

- [Auditor e parser PNG streaming](../scripts/regions/audit_sinnoh_g06_render_static.py).
- [21 testes sintéticos e negativos](../tests/test_sinnoh_g06_render_static.py): 14 PNGs inventados localmente nos testes; imagens altas de 50.000/70.000 px com dados gerados; corrupção de CRC, zlib, scanline, paleta, profundidade, filtros, ordem de chunks, chunks desconhecidos, IDAT interrompido e metadados de tileset adulterados.
- [Workflow G06](../.github/workflows/sinnoh-g06-render-static.yml): valida metadados públicos, executa testes sintéticos e publica um **JSON de metadados apenas**, sem PNGs, doador, saves, caminhos privados ou binários.

Comando para gerar apenas relatório público:

~~~bash
python scripts/regions/audit_sinnoh_g06_render_static.py
python -m unittest discover -s tests -p 'test_sinnoh_g06_render_static.py' -v
~~~

**Status esperado:** `STATIC_RENDER_METADATA_RECONCILED_PNG_BYTES_NOT_AVAILABLE`.

## O que permanece bloqueado

1. **CRC/zlib dos 14 PNGs reais:** só pode ser comprovado sobre o stage privado B07/B08 em ambiente autorizado. A existência de um número 14 no manifesto não substitui verificar bytes.
2. **Tilesets 71/72:** confirmar o índice de append na tabela `Tilesets.rxdata` real e os caminhos de todos os gráficos vinculados. O cálculo aqui é condicional.
3. **Compatibilidade Windows/JoiPlay:** abrir apenas o clone isolado dentro da VM preparada B10, com saves auditados pela B11, quando houver autorização e equipamento compatível.
4. **Direitos R08 e reservas R07:** não avaliados pela geometria PNG, continuam necessários.
5. **Barras B/C/D:** permanecem **0/13**, sem incremento por CI ou PNG sintético.

**Próxima entrega G07:** checklist auditável de Twinleaf e vínculos entre áreas/eventos, sem inventar MapIDs, coordenadas ou warps.
