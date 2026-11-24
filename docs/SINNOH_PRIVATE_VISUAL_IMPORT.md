# Sinnoh — importação visual privada (VIS01–VIS07)

## Arquivos locais
- `Sinnoh Maps.zip`: SHA-256 `79a7a4e4d176039daa9d3a2866540ced4daad4c9043a9a82378dae45a60e9e26`.
- `Ultimate Gen 4 Overworlds Pack.zip`: SHA-256 `e9d240918b62460c76d56ec9e5d4067a4ee853979d16a6657c05917d9bfd2b99`.
- Inventário da fonte recebida: 238 Map RXDATA, 25 registros de Tilesets, 24 PNG de tilesets, 40 autotiles, 495 PNG no pacote de overworlds. Parte dos 238 mapas não é Sinnoh. Não copiar o banco global nem o projeto de origem.
- Créditos: PhantomFae, Game Freak, autores originais dos tilessets e PurpleZaffre (overworlds). A nota do pacote proíbe redistribuição. R08 continua pendente.

## Como testar após integração do código

1. Use o Blue-Story.exe que já possui a opção **Testar piloto Sinnoh**. Ele sincroniza os scripts da main antes de abrir o menu; não é necessário baixar outra versão do executável para esta mudança.
2. Clique em Testar piloto Sinnoh. O launcher procura os arquivos originais em cache, ao lado do instalador e em Downloads. Se faltarem, baixa diretamente dos links publicados por PhantomFae e PurpleZaffre (Eevee Expo → MEGA/MediaFire), sem espelhos ou redistribuição.
3. Os arquivos baixados ficam em `.blue-work/sinnoh-private-input/` (apenas os ZIPs validados por tamanho e SHA-256). Arquivos parciais são removidos. Arquivos válidos são reutilizados. Se a fonte estiver indisponível, exigir login, mudar ou devolver conteúdo divergente, a operação para antes de preparar o piloto, sem regressar silenciosamente aos sprites provisórios. Não há tentativa de contornar autenticação ou restrições dos provedores.
4. O importador cria uma cópia QA separada e posiciona mapas, tilesets e personagens nos caminhos adequados, sem tocar no jogo principal nem em saves pessoais.
5. Novo jogo: seleção dos registros Platinum Lucas/Dawn quando ambos estiverem disponíveis. Conferir mãe, Barry e Rowan, portas, warps, iniciais, batalha e retorno.

**Limite de verificação:** testes automatizados usam fontes sintéticas e vetores de AES no Windows. A obtenção real dos dois ZIPs pelos provedores depende da rede e disponibilidade pública; não declarar aprovação nativa nem download real sem evidência.


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


## Correção de continuidade e áudio (24/11/2026)

A importação anterior conservava somente a geometria de cinco mapas e os warps locais; por isso o limite norte de Twinleaf podia aparecer preto e os mapas não tinham BGM. A correção usa o PBS de conexões do ZIP fixado por SHA-256 e preserva os registros já existentes do jogo-base.

| Conexão nativa | Registro da fonte | Células de passagem comuns alcançáveis (modelo) |
|---|---|---:|
| Twinleaf → Rota 201 | 194,N,2,193,S,0 | 8 |
| Rota 201 → Sandgem | 193,E,0,192,W,4 | 5 |
| Sandgem → Rota 202 | 192,N,0,191,S,6 | 6 |

Os seis eventos de transferência desses pares conservam seus IDs, mas não executam warp redundante; os dez demais warps, cinco handlers e três Poké Bolas permanecem. O índice compilado e PBS são acrescentados somente na cópia QA, com proteção contra reescrita pelo compilador. A metadata regional inclui área externa e snap de câmera nos interiores e lago, sem bloquear as três conexões. Não é uma expansão do piloto para Jubilife/Verity Lakefront: os mapas adicionais ainda não foram alocados. A passagem para Lake Verity permanece por warp (não há costura caminhável entre os mapas atuais do lago e Rota 201).

O ZIP também contém quatro BGM de ambiente e três variantes noturnas: Twinleaf Town, Route 201, Lake e Sandgem Town. O importador usa nomes exclusivos SNQA_*, conserva os bytes OGG, ativa autoplay nos nove mapas e verifica seus hashes na supervisão. A auditoria local decodificou as sete faixas até o fim com FFmpeg sem erros. Não são adicionadas trilhas de batalha/vitória que não existam na fonte; as regras atuais de batalha são preservadas. O teste real do CI usa exclusivamente uma fixture de mapas e cache temporário dos ZIPs originais, sem executar Game.exe ou publicar recursos.

A atualização será usada ao abrir o Blue-Story já existente e clicar em Testar piloto Sinnoh, depois do merge. QA visual/sonora nativa ainda necessária; não declarar R09 aprovado.


## Extensão Verity Lakefront e abertura da história

- Importação do Map195 real, 26 × 22, com um MapID provisório adicional livre na cópia QA. O corredor inferior contém 103 células caminháveis no modelo; quatro células comuns alinham a conexão original 195,E,0,193,W,4.
- Duas ligações visuais do próprio PBS alinham a floresta do lago a Verity Lakefront e Rota 201, sem passagem caminhável comum. Não são rotas alternativas de acesso.
- As duas entradas reais de Lakefront (10,2) e (11,2) levam a Lake Verity (44,42) e (45,42). Os retornos (44,43)/(45,43) levam a (10,3)/(11,3). São eventos Blue novos com coordenadas do doador, sem copiar scripts. Entrada depende da conversa com mãe e Barry; retorno sempre aberto.
- A abertura apresenta seleção Lucas/Dawn e entrada de nome pelo pbTrainerName após a inicialização real do quarto. O estado de perfil só é marcado após sucesso. Cinco cenas de execução única apresentam perfil, mãe, Barry, Rowan no lago e Pokédex no laboratório; NPCs manuais continuam presentes, e a escolha de Pokémon exige confirmação e tenta a batalha Barry somente pelo guard nativo existente.
- Escopo: 10 mapas, 32 eventos (incluindo IDs dos warps desativados), 4 costuras caminháveis, 2 ligações visuais, 2 pares de portais e 7 BGM. Sem ampliar até Jubilife ou Verity Cavern e sem declarar recriação integral das cutscenes oficiais. A história permanece a versão autoral Blue.
- O CI repete a importação do ZIP real e executa testes Ruby isolados. Testes de Game.exe, visual, áudio e R09 continuam pendentes. Os saves das cópias anteriores ficam intactos; para testar a abertura é necessário novo jogo em nova cópia QA.


## Recuperação do erro de abertura do perfil (QA 1e2b9d26ec48)

O relato mostra apenas EventScriptError do Interpreter, linha 177; a exceção original não está na captura. O diagnóstico exato do erro ocorrido no PC depende do log local. A correção usa a sequência nativa de Essentials 21.1: cadastro 9/10 validado, seleção, entrada explícita de nome não vazio via pbEnterPlayerName, pbTrainerName(nome), refresh de sprite e marcação do perfil apenas após sucesso. Não usar nome automático do sistema nem confirmar um perfil cancelado.

O autorun da primeira tentativa termina mesmo quando a interface falha. A escada do quarto reexecuta o setup se necessário e só transfere após perfil completo. O log local sinnoh-profile-error.txt guarda etapa e exceção original, dentro da cópia QA. Não envia diagnóstico pela rede. O arquivo pode ser solicitado ao jogador se o problema reaparecer. Mantém dez mapas, 32 eventos, sete BGM e os saves anteriores. Ruby simulado cobre duas escolhas, cancelamento, falha e nova tentativa; não declarar Game.exe nativo validado.
