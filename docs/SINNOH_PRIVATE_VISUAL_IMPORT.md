# Sinnoh — importação visual privada (VIS01–VIS07)

## Arquivos locais
- `Sinnoh Maps.zip`: SHA-256 `79a7a4e4d176039daa9d3a2866540ced4daad4c9043a9a82378dae45a60e9e26`.
- `Ultimate Gen 4 Overworlds Pack.zip`: SHA-256 `e9d240918b62460c76d56ec9e5d4067a4ee853979d16a6657c05917d9bfd2b99`.
- Inventário da fonte recebida: 238 Map RXDATA, 25 registros de Tilesets, 24 PNG de tilesets, 40 autotiles, 495 PNG no pacote de overworlds. Parte dos 238 mapas não é Sinnoh. Não copiar o banco global nem o projeto de origem.
- Créditos: PhantomFae, Game Freak, autores originais dos tilessets e PurpleZaffre (overworlds). A nota do pacote proíbe redistribuição. R08 continua pendente.

## Como testar após integração do código
1. Manter os dois ZIPs originais, sem descompactar, em Downloads ou junto do Blue-Story.exe atualizado (ou em `.blue-work/sinnoh-private-input` da instalação gerenciada).
2. Abrir Blue-Story.exe → Testar piloto Sinnoh. O importador usa somente arquivos locais, valida SHA-256 e cria uma nova cópia QA. Sem ZIPs continua o piloto original; um ZIP incorreto bloqueia em vez de ser aceito.
3. Novo jogo. A base Platinum Lucas usa registro nativo 9 quando metadata e os gráficos de movimento existem. Dawn (registro 10) é validada separadamente; quando ambos os cadastros existem, o Novo Jogo do piloto oferece Lucas ou Dawn.
4. Conferir mãe, Barry e Rowan; testar portas, warp, escolha dos iniciais, batalha, retorno. Não usar saves pessoais.

## Mapeamento de origem
| Área | MapID de origem | Dimensão | Células na componente caminhável do modelo |
|---|---:|---|---:|
| Twinleaf Town | 194 | 36x36 | 417 |
| Route 201 | 193 | 64x30 | 720 |
| Sandgem Town | 192 | 38x32 | 517 |
| Route 202 | 191 | 46x31 | 664 |
| Lake Verity | 196 | 62x50 | 128 |

O registro de origem 24 é Outdoors (256x29984). O registro 25 fornece 95 tiles usados nos novos interiores, compactados em um atlas 256x384. A auditoria local independente verificou todos os recortes e 24 posições de evento/16 chegadas recíprocas em células caminháveis. A união dos cinco mapas usa 291 tiles normais; o atlas compacto é 256x1184 (última linha com preenchimento). No ambiente de análise, a compactação equivalente foi comparada com a imagem original e os 291 recortes coincidiram pixel a pixel. As tabelas de colisão, prioridade e terreno são remapeadas sem mudança de ordem das camadas. O importador verifica sete autotiles associados (nenhum dos cinco mapas usa IDs de autotiles diretamente).

IDs de destino são alocados apenas pela instalação QA, a partir de vagas verificadas na faixa 442–517; não publicar IDs definitivos nem aprovar R07. Os cinco mapas preservam geometria da fonte e recebem novamente os 24 eventos próprios do piloto (não os eventos do pacote). Portas e coordenadas são candidatas modeladas, não homologadas no motor. Lakefront (195) e Verity Cavern (197) ficam para expansão; a transição atual ainda segue a topologia de nove mapas.

Overworlds locais (folhas 256x256; 4x4 quadros de 64x64):
- NPC_126_Mom.png (candidata para mãe), NPC_140_Barry.png, NPC_138_Prof_Rowan.png.
- NPC_199_Lucas.png e NPC_202_Dawn.png encontrados na fonte; preferir o cadastro de jogador já existente no jogo-base e suas animações.
- Interiores específicos não vieram no ZIP. Quarto 12x10, casa 16x12, casa de Barry 14x12 e laboratório 18x13 são novos layouts autorais compostos com o tileset real 25 (indoors.png), preservando 24 eventos próprios e as tabelas originais de colisão/prioridade/terreno. Componentes caminháveis do modelo local: 47, 106, 91 e 118 células, respectivamente. A revisão visual nativa continua pendente.

## Limites
A ferramenta é código original, não distribui os ZIPs/PNGs/RXDATA da fonte. Não importa scripts, eventos doador, áudio, encontros, conexões PBS ou metadados globais. A auditoria local dos arquivos não é execução do Game.exe. A validação nativa do novo piloto, revisão nativa dos interiores, correspondência de tags no runtime, R07/R08/R09 e Android continuam pendentes. Não usar a campanha principal para QA.
