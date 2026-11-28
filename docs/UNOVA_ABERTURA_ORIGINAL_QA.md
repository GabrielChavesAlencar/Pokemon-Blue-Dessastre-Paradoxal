# Unova — geometria original do primeiro corredor

O recorte de QA tem sete geometrias RMXP originais. Ele usa a paleta original do Blue gerada para autoria, registrada em `generate_sinnoh_original_j10a.py`. As plantas foram desenhadas para o Dessastre Paradoxal em torno de um canal, uma travessia em cotovelo e uma praça com fonte. Não há recursos de uma ROM ou do World V18 no pacote.

| Ambiente | Dimensões | Ligação prevista |
| --- | --- | --- |
| Quarto | 18 × 13 | Escada para o térreo |
| Térreo | 22 × 14 | Quarto e saída para a vila |
| Nuvema | 30 × 23 | Casa, laboratório e Rota 1 |
| Laboratório | 22 × 15 | Saída para Nuvema |
| Rota 1 | 30 × 24 | Nuvema e Accumula |
| Accumula | 32 × 23 | Rota 1 e centro |
| Centro | 20 × 13 | Saída para a praça |

Na raiz do repositório, execute `python scripts/regions/unova_original_opening.py --build`. A saída fica em `.blue-work/unova/original-opening/` e inclui o PNG, os RXDATA de três camadas, as prévias e o manifesto com SHA-256. O comando recusa substituir uma exportação existente. Sem `--build`, valida em memória.

Os testes releem os sete RXDATA e conferem o grafo de seis ligações, as células de retorno distintas e a alcançabilidade geométrica. As coordenadas são candidatas para compilação em eventos. A tabela de passagem de um tileset compartilhado e os eventos do RPG Maker ainda precisam ser vinculados e testados.

## Overlay descartável com portas RMXP

Os sete mapas usam 276–282 no perfil de QA, na ordem da tabela. A escolha usa o primeiro trecho contíguo da alternativa histórica 276–299. O compilador rejeita colisões com arquivos ou entradas de MapInfos, inventário Android, transferências estáticas, conexões, pontos nativos e manifestos regionais. A leitura estática produz evidência para o piloto e deixa a reserva pública em aberto.

```powershell
python scripts/regions/unova_opening_stage.py --base-game "<base Windows>" --android-manifest "<update.json multiregional>"
```

A exportação privada em `.blue-work/unova/opening-rmxp-qa/` contém um tileset com passagens, sete mapas e doze eventos Player Touch com comando nativo 201. As coordenadas de chegada ficam fora de todos os gatilhos. O manifesto indica os hashes da base e da saída. Use o overlay somente no ambiente descartável para o qual foi gerado.

O [workflow Windows de QA](../.github/workflows/unova-opening-native.yml) instala uma base pinada em um runner descartável e cria um perfil de saves exclusivo. A prova inicia no quarto, percorre as doze portas caminhando, verifica o destino aplicado pela cena e faz save/reload no centro em Accumula. O recibo de CI registra a revisão e cada travessia confirmada pelo Game.exe.

A reserva pública dos MapIDs, a história, os encontros, o JoiPlay em aparelho e as releases pareadas seguem os gates do [roadmap](UNOVA_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md). A fonte dos números e as faixas excluídas estão na [revisão F01](UNOVA_F01_BASELINE_WINDOWS_ANDROID.md).
