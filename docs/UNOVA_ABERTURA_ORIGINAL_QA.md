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

MapIDs, encontros, personagens e enredo continuam pendentes. A instalação do corredor depende da [revisão F01 das faixas](UNOVA_F01_BASELINE_WINDOWS_ANDROID.md) e das evidências Windows e JoiPlay do [roadmap](UNOVA_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md).
