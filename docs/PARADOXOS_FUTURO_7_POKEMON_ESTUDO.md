# Estudo de criação e balanceamento — 7 Pokémon Paradoxo do Futuro
**Projeto:** Pokémon Blue Dessastre Paradoxal · **Geração de referência:** IX (Scarlet/Violet + DLCs) · **Data:** 11/11/2026 · **Revisão:** nomes, Pokédex, alturas, pesos e proporções físicas

> **Natureza deste documento:** fan game. Os atributos, níveis de aprendizagem, tipagens propostas e compatibilidades de TM de **Iron Oracle, Iron Coil, Iron Echo, Iron Glimmer, Iron Wraith, Iron Raptor e Iron Stinger são criações originais propostas**, não dados oficiais da franquia. Os Base Stats dos sete Pokémon de referência são oficiais. A lista por nível é uma proposta de design, não uma extração de learnsets oficiais. **Os nomes, textos de Pokédex, alturas, pesos e proporções dos Paradox também são propostas inéditas**. Não alteram os seis atributos, os golpes ou as habilidades definidos na primeira versão.

## 1. Materiais analisados e método
- ZIP recebido: `Sprites_Iron_06-11-2026_Completo(1).zip` (sete pastas com sprites normais/shiny, party e imagens de costas/frente).
- Documento prévio: `Estudo_Comparativo_Paradoxos_Futuro_Base_Stats_Movesets_Gen9.md`; regra adotada para Paradox comuns: **570 de BST, Quark Drive e learnset temático**.
- **Iron Coil é baseado em Furret**, confirmado pela aparência do sprite; esse já era um nome original no ZIP e foi preservado. Os outros seis receberam nomes de exibição novos sem alterar os diretórios e arquivos dos sprites.
- As descrições do ZIP indicam tipagens **Terra/Psíquico** para Iron Oracle, **Normal/Voador** para Iron Raptor e **Inseto/Voador** para Iron Stinger, preservadas aqui. Nos outros quatro, a tipagem consta como **proposta** e deve ser confirmada antes de incluir no jogo.
- **Não há golpes inventados:** foram escolhidos nomes de golpes que existem nos jogos de Pokémon, mas seu aprendizado por estes sete fan-Pokémon é proposto; nem todas as TMs são oficialmente compatíveis com as espécies base.

## 2. Regras de criação adotadas
1. **570 BST para cada espécie**: o mesmo patamar dos Paradox comuns, sem tratá-los como lendários de 590/670.
2. **Não copiar integralmente a forma original.** Preservar movimentos-chave de identidade, mudar golpes quando a tecnologia, o tipo e o papel em batalha justificarem.
3. **Quark Drive** como habilidade única. Ativa em Electric Terrain ou mediante Booster Energy. Aumenta o maior atributo **efetivo** (não HP) em 30%, ou 50% se for Speed. Nature, EVs, IVs e estágios de atributos podem mudar o atributo selecionado.
4. **Sem evolução e sem reprodução/egg moves** para as sete espécies, como padrão de Paradox. Aprendizado por nível e TM; o nível 1 indica golpes relembráveis/kit inicial, conforme o motor do fan game.
5. **Curva de aprendizagem:** golpes mais fortes devem surgir geralmente de Lv. 42 em diante; ataques decisivos no Lv. 56–91. O level cap do jogo pode exigir remapeamento posterior.
6. **Sem movimento exclusivo artificial:** a proposta usa golpes existentes na IX geração, mesmo quando são redistribuídos para espécies que não os aprendem oficialmente. A implementação deve confirmar compatibilidade com o banco de moves do jogo.

## 3. Resumo dos Base Stats — originais e propostos
Ordem de atributos: **HP / Atk / Def / SpA / SpD / Spe**. Todos os Paradox sugeridos têm 570 BST.

| Original → futuro | Tipo original → tipo proposto | Original (HP/Atk/Def/SpA/SpD/Spe) | Futuro (HP/Atk/Def/SpA/SpD/Spe) | BST original → futuro | Δ BST |
|---|---|---|---|---:|---:|
| Claydol → Iron Oracle | Terra/Psíquico → **Terra/Psíquico** | 60 / 70 / 105 / 70 / 120 / 75 | **80 / 65 / 125 / 115 / 135 / 50** | 500 → 570 | **+70** |
| Furret → Iron Coil | Normal → **Normal/Aço** | 85 / 76 / 64 / 45 / 55 / 90 | **85 / 105 / 95 / 70 / 80 / 135** | 415 → 570 | **+155** |
| Exploud → Iron Echo | Normal → **Normal/Elétrico** | 104 / 91 / 63 / 91 / 73 / 68 | **110 / 70 / 82 / 140 / 82 / 86** | 490 → 570 | **+80** |
| Lumineon → Iron Glimmer | Água → **Água/Elétrico** | 69 / 69 / 76 / 69 / 86 / 91 | **80 / 65 / 85 / 120 / 95 / 125** | 460 → 570 | **+110** |
| Spiritomb → Iron Wraith | Fantasma/Sombrio → **Fantasma/Elétrico** | 50 / 92 / 108 / 92 / 108 / 35 | **85 / 75 / 105 / 130 / 125 / 50** | 485 → 570 | **+85** |
| Swellow → Iron Raptor | Normal/Voador → **Normal/Voador** | 60 / 85 / 60 / 75 / 50 / 125 | **74 / 140 / 82 / 70 / 72 / 132** | 455 → 570 | **+115** |
| Yanmega → Iron Stinger | Inseto/Voador → **Inseto/Voador** | 86 / 76 / 86 / 116 / 56 / 95 | **88 / 70 / 88 / 135 / 75 / 114** | 515 → 570 | **+55** |

### Variação individual por atributo
| Espécie | ΔHP | ΔAtk | ΔDef | ΔSpA | ΔSpD | ΔSpe |
|---|---:|---:|---:|---:|---:|---:|
| Iron Oracle | +20 | -5 | +20 | +45 | +15 | -25 |
| Iron Coil | +0 | +29 | +31 | +25 | +25 | +45 |
| Iron Echo | +6 | -21 | +19 | +49 | +9 | +18 |
| Iron Glimmer | +11 | -4 | +9 | +51 | +9 | +34 |
| Iron Wraith | +35 | -17 | -3 | +38 | +17 | +15 |
| Iron Raptor | +14 | +55 | +22 | -5 | +22 | +7 |
| Iron Stinger | +2 | -6 | +2 | +19 | +19 | +19 |

### Distribuição dos papéis em batalha
| Pokémon | Principal atributo | Função |
|---|---|---|
| Iron Oracle | Sp. Defense 135 | Tanque especial, controle de campo e removedor de hazards |
| Iron Coil | Speed 135 | Pivot físico extremamente rápido e utilitário |
| Iron Echo | Sp. Attack 140 | Wallbreaker especial de som, lento-médio e com boa resistência |
| Iron Glimmer | Speed 125 | Atacante especial rápido de Água/Elétrico e pivot de campo |
| Iron Wraith | Sp. Attack 130 | Tanque especial lento com status, Hex e cobertura elétrica |
| Iron Raptor | Attack 140 | Atacante físico veloz e pivot aéreo |
| Iron Stinger | Sp. Attack 135 | Atacante especial veloz, reconhecimento aéreo e cobertura técnica |

## 3.1. Novos nomes, descrições de Pokédex e proporções

### Padrão de nomenclatura
Os Paradox do futuro seguem a convenção de **duas palavras iniciadas por “Iron”**, evocando uma característica marcante da espécie mecânica — não apenas o nome do Pokémon-base. Os sete nomes têm no máximo 12 caracteres contando o espaço, facilitando a utilização em interfaces de jogos. **Iron Coil** já possuía um nome adequado no pacote, então permanece inalterado.

| Nome na Pokédex | Identificador do sprite no ZIP | Pokémon de referência | Nome escolhido por quê? | Tipagem proposta/mantida |
|---|---|---|---|---|
| **Iron Oracle** | `Iron_Claydol` | Claydol | Esfera de sensores e anéis de observação, como um oráculo eletrônico | Terra/Psíquico (mantida do ZIP) |
| **Iron Coil** | `Iron_Coil` | Furret | Corpo segmentado e flexível, semelhante a bobina mecânica | Normal/Aço (proposta) |
| **Iron Echo** | `Iron_Exploud` | Exploud | Boca-subwoofer e amplificadores que reproduzem ondas sonoras | Normal/Elétrico (proposta) |
| **Iron Glimmer** | `Iron_Lumineon` | Lumineon | Nadadeiras holográficas que brilham como placas de luz | Água/Elétrico (proposta) |
| **Iron Wraith** | `Iron_Spiritomb` | Spiritomb | Aparição digital projetada por um reator de energia | Fantasma/Elétrico (proposta) |
| **Iron Raptor** | `Iron_Swellow` | Swellow | Ave de caça com asas de propulsão e silhueta aerodinâmica | Normal/Voador (mantida do ZIP) |
| **Iron Stinger** | `Iron_Yanmega` | Yanmega | Libélula mecânica predadora, com corpo perfurante e sensores | Inseto/Voador (mantida do ZIP) |

### Dimensões: espécies originais vs. Paradox criados
Alturas e pesos **originais** são dados da Pokédex oficial; dimensões **futuras** são sugestões autorais para o fan game. Altura não deve ser confundida com a altura de voo e, para criaturas alongadas, a dimensão principal pode representar o comprimento nominal do corpo, conforme a convenção usada na ficha.

| Pokémon original | Altura original | Peso original | Nome Paradox | Altura ou comprimento proposto | Peso proposto | Variação de altura | Variação de peso |
|---|---:|---:|---|---:|---:|---:|---:|
| Claydol | 1,5 m | 108,0 kg | **Iron Oracle** | **1,8 m** | **172,0 kg** | +20,0% | +59,3% |
| Furret | 1,8 m | 32,5 kg | **Iron Coil** | **2,2 m** | **54,0 kg** | +22,2% | +66,2% |
| Exploud | 1,5 m | 84,0 kg | **Iron Echo** | **1,9 m** | **205,0 kg** | +26,7% | +144,0% |
| Lumineon | 1,2 m | 24,0 kg | **Iron Glimmer** | **1,5 m** | **29,0 kg** | +25,0% | +20,8% |
| Spiritomb | 1,0 m | 108,0 kg | **Iron Wraith** | **1,4 m** | **126,0 kg** | +40,0% | +16,7% |
| Swellow | 0,7 m | 19,8 kg | **Iron Raptor** | **1,0 m** | **31,0 kg** | +42,9% | +56,6% |
| Yanmega | 1,9 m | 51,5 kg | **Iron Stinger** | **2,2 m** | **83,0 kg** | +15,8% | +61,2% |

**Fonte das medidas originais:** [Pokémon Database — Height & Weight](https://pokemondb.net/pokedex/stats/height-weight) e as fichas individuais listadas na seção 8. Os números propostos **não vêm dos sprites**, porque o ZIP contém artes em resoluções variadas e sem escala física. As proporções a seguir são guias de design, não medições da imagem ou exigências do motor.

### 3.1.1. Iron Oracle — “Pokémon Oráculo Orbital”
- **Origem:** Claydol · **Tipo:** Terra/Psíquico · **Altura:** 1,8 m · **Peso:** 172,0 kg.
- **Entrada de Pokédex (curta):** “Seu corpo abriga sensores que giram sem cessar. Dizem que ele consegue antecipar movimentos adversários por meio de cálculos feitos em frações de segundo.”
- **Descrição expandida:** Uma unidade de observação construída a partir de um corpo em formato de ídolo antigo. Seus olhos vermelhos alinhados ao redor da cabeça captam o ambiente; os anéis cianos emitem padrões de leitura que lembram rituais esquecidos. Move braços desacoplados ao redor do núcleo para reorientar energia psíquica.
- **Proporções físicas:** altura total de 1,8 m do topo do chapéu-sensor à ponta inferior, **largura aproximada de 2,1 m** incluindo os módulos laterais. A cúpula superior representa cerca de **35%** da altura, o núcleo central **40%** e a extremidade inferior **25%**. Os braços não devem ultrapassar a cúpula em massa visual.
- **Justificativa dimensional:** maior e mais pesado que Claydol porque contém blindagem, sensores múltiplos e anel estabilizador. **Não somar altura de flutuação à altura da Pokédex.**
- **Coerência com o moveset:** Cosmic Power, Psychic, Psyshock e Future Sight expressam previsão e cálculo; Rapid Spin e Stealth Rock reforçam controle de campo.

### 3.1.2. Iron Coil — “Pokémon Bobina Móvel”
- **Origem:** Furret · **Tipo:** Normal/Aço · **Comprimento:** 2,2 m · **Peso:** 54,0 kg.
- **Entrada de Pokédex (curta):** “As placas de seu corpo se articulam como uma corrente flexível. Ao acelerar, ele se enrola e desliza pelo chão quase sem produzir ruído.”
- **Descrição expandida:** A silhueta delicada de Furret foi reproduzida com segmentos marrons de liga leve e sensores cianos. O longo tronco pode curvar-se ao redor de obstáculos, enquanto pequenos emissores nas costas ajustam o equilíbrio. Apesar do aspecto amistoso, pode atingir velocidades difíceis de acompanhar.
- **Proporções físicas:** **2,2 m do focinho à ponta da cauda**, e não de altura quando em pé; **altura ereta típica de cerca de 0,9 m**, variando conforme a curvatura. Cabeça com aproximadamente **20%** do comprimento projetado, tronco articulado **45%** e cauda **35%**. Evitar engrossar demais o tronco, preservando o perfil esguio de Furret.
- **Justificativa dimensional:** o corpo modular é mais comprido, com estrutura interna reforçada, mas ainda deve parecer leve e veloz. Em batalha, o sprite pode aparecer enrolado e, por isso, parecer menor que a medida de comprimento.
- **Coerência com o moveset:** Coil, Tidy Up e U-turn reforçam a identidade de deslocamento e flexão; Iron Head representa as placas metálicas.

### 3.1.3. Iron Echo — “Pokémon Amplificador”
- **Origem:** Exploud · **Tipo:** Normal/Elétrico · **Altura:** 1,9 m · **Peso:** 205,0 kg.
- **Entrada de Pokédex (curta):** “Sua boca contém um emissor de ondas ultrapotente. Quando todos os amplificadores entram em ressonância, o solo vibra mesmo a grandes distâncias.”
- **Descrição expandida:** Seu tronco robusto sustenta um grande alto-falante circular no interior da boca e diversas colunas acústicas nas costas. A carcaça violeta e os anéis luminosos lembram um equipamento industrial móvel. Ele pode transformar oscilações sonoras em descargas elétricas.
- **Proporções físicas:** **1,9 m de altura**, cerca de **1,5 m de largura máxima** entre as peças laterais. Cabeça, boca e amplificadores devem dominar a silhueta: aproximadamente **45% da altura visual**. Tronco perto de **35%** e pernas robustas nos **20% restantes**. O círculo do emissor bucal deve ocupar cerca de **um terço da largura do tronco**.
- **Justificativa dimensional:** massa elevada pela presença de subwoofers, bobinas, blindagem acústica e estabilizadores; não tornar o tronco tão alto que apague os detalhes da boca.
- **Coerência com o moveset:** Echoed Voice, Hyper Voice e Boomburst formam uma progressão acústica; Discharge e Thunderbolt acrescentam a conversão elétrica.

### 3.1.4. Iron Glimmer — “Pokémon Néon Abissal”
- **Origem:** Lumineon · **Tipo:** Água/Elétrico · **Comprimento:** 1,5 m · **Peso:** 29,0 kg.
- **Entrada de Pokédex (curta):** “Nadadeiras translúcidas projetam padrões de luz sobre a água. Esses sinais atraem presas e podem descarregar eletricidade ao menor contato.”
- **Descrição expandida:** Um corpo de peixe escuro e elegante sustenta grandes nadadeiras holográficas azuis, recortadas por linhas semelhantes a circuitos. O brilho pulsante pode enganar sistemas de localização submarinos. Em vez de nadar rapidamente apenas com movimentos musculares, utiliza impulso eletromagnético para manobras precisas.
- **Proporções físicas:** **1,5 m do focinho à extremidade da cauda**. O corpo fusiforme representa aproximadamente **60% do comprimento**, enquanto cauda e pontas externas completam **40%**. As nadadeiras superiores e laterais ampliam a **largura visual para cerca de 2,3 m**, mas devem permanecer finas e translúcidas. Manter a cabeça compacta para não transformar o desenho em peixe robusto.
- **Justificativa dimensional:** cresceu em comprimento e envergadura das nadadeiras sem ganhar muita massa, porque a superfície luminosa é leve; isso combina com Speed 125.
- **Coerência com o moveset:** Aqua Ring e Surf mantêm o tema aquático; Charge Beam, Discharge e Thunderbolt usam as nadadeiras como condutores; Flip Turn representa movimentação rápida.

### 3.1.5. Iron Wraith — “Pokémon Aparição Digital”
- **Origem:** Spiritomb · **Tipo:** Fantasma/Elétrico · **Altura:** 1,4 m · **Peso:** 126,0 kg.
- **Entrada de Pokédex (curta):** “Um reator mantém uma sombra digital suspensa sobre o chão. Seus inúmeros olhos observam tudo ao redor, como se fossem fragmentos de uma única mente.”
- **Descrição expandida:** A formação espectral violeta com olhos verdes brilhantes é projetada por um pedestal de metal circular. Anéis e fragmentos de luz orbitam o rosto digital. Arquivos misteriosos encontrados no núcleo indicam padrões de consciência, embora ninguém saiba de onde eles vieram.
- **Proporções físicas:** **1,4 m da base do reator ao topo da manifestação**, com **largura máxima aproximada de 1,7 m** para a projeção. O pedestal ocupa cerca de **30% da altura**, a aparição superior **70%**. O rosto espectral deve ser maior que o suporte metálico, e o peso se concentra no pedestal — a projeção não pesa 126 kg por si só.
- **Justificativa dimensional:** o peso se deve à unidade energética, ao anel de contenção e às blindagens; a nuvem digital é visualmente grande, porém sem massa convencional.
- **Coerência com o moveset:** Hex, Shadow Ball e Confuse Ray representam a projeção fantasmagórica, enquanto Discharge e Thunder Wave derivam do reator elétrico.

### 3.1.6. Iron Raptor — “Pokémon Caça Supersônico”
- **Origem:** Swellow · **Tipo:** Normal/Voador · **Altura/comprimento nominal:** 1,0 m · **Peso:** 31,0 kg.
- **Entrada de Pokédex (curta):** “Suas asas rígidas cortam o ar como lâminas. Durante mergulhos de caça, rastreia alvos com sensores que brilham no peito e nas penas.”
- **Descrição expandida:** A ave mantém o bico, a cauda e a silhueta inconfundível de Swellow, mas apresenta plumagem metálica escura, linhas azuis energizadas e estabilizadores longos nas costas. Seu comportamento lembra uma aeronave de interceptação em miniatura, com aceleração e curvas abruptas.
- **Proporções físicas:** **1,0 m de dimensão corporal nominal** do bico à cauda, com **envergadura aproximada de 2,4 m** quando as asas estão totalmente abertas. Peito e cabeça ocupam cerca de **40% do comprimento**, tronco **35%** e cauda/estabilizadores **25%**. As asas devem parecer finas e pontiagudas, sem se transformar em grandes placas pesadas.
- **Justificativa dimensional:** cresce em relação a Swellow e ganha peças aerodinâmicas resistentes; manter a massa bem menor que a de um robô terrestre de porte parecido, favorecendo Speed 132.
- **Coerência com o moveset:** Brave Bird, Dual Wingbeat, Agility e U-turn refletem velocidade e ataques de passagem; Double-Edge reforça mergulho agressivo.

### 3.1.7. Iron Stinger — “Pokémon Libélula de Combate”
- **Origem:** Yanmega · **Tipo:** Inseto/Voador · **Comprimento nominal:** 2,2 m · **Peso:** 83,0 kg.
- **Entrada de Pokédex (curta):** “Seus olhos mecânicos rastreiam movimentos quase imperceptíveis. As quatro asas vibram em frequências distintas para emboscar alvos sem perder altitude.”
- **Descrição expandida:** Carapaça preta e vermelha, olhos eletrônicos e quatro asas translúcidas com padrões avermelhados transformam Yanmega em uma unidade de reconhecimento. Articulações finas e membros em forma de garras permitem mudanças bruscas de direção durante a perseguição.
- **Proporções físicas:** **2,2 m do focinho ao final do abdômen**; **envergadura total de cerca de 3,4 m** considerando as quatro asas estendidas. Cabeça e tórax somam aproximadamente **55% do corpo**, e abdômen segmentado **45%**. As asas devem permanecer grandes em relação ao tronco, mas leves e alongadas; os membros devem ser finos, evitando aspecto de robô humanoide.
- **Justificativa dimensional:** mais comprido e pesado que Yanmega pela blindagem e pelos sensores, embora o conjunto aerodinâmico ainda privilegie a velocidade.
- **Coerência com o moveset:** Detect, Air Slash, Bug Buzz e Tailwind representam rastreamento e mobilidade; Psychic Noise e Discharge funcionam como interferência de sensores.

### Regras de integração das dimensões e dos sprites
1. Campos recomendados na Pokédex: `displayName`, `speciesCategory`, `pokedexDescription`, `heightM`, `weightKg`, `baseSpecies`, `spriteAssetId` e `bodyProportionsNotes` (nomes **conceituais**; adaptar ao schema real do projeto).
2. **Não renomear automaticamente os arquivos no ZIP.** O nome de exibição muda, mas `Iron_Claydol`, `Iron_Coil`, `Iron_Exploud`, `Iron_Lumineon`, `Iron_Spiritomb`, `Iron_Swellow`, `Iron_Yanmega` continuam como identificadores de sprites até uma migração explícita.
3. Dimensões da Pokédex são **escala de mundo**. Sprite em pixels não determina metros ou quilos; normalizar visualmente sem distorcer as proporções internas dos personagens.
4. Em batalha, ajustar altura, pivô e enquadramento conforme a silhueta: peixes e Furret alongados devem ocupar o quadro horizontal, aves e libélulas precisam preservar asas, Claydol deve incluir seus anéis, e Spiritomb deve manter o pedestal visível.
5. **Não aplicar a massa como multiplicador de BST**: altura e peso são dados independentes de HP/Defense. O peso pode afetar golpes dependentes de massa, caso implementados no motor (por exemplo, Heavy Slam e Low Kick); testar com os valores desta tabela.
6. Todas as entradas e dimensões desta seção são **fan-made**, enquanto os valores das espécies originais foram extraídos da Pokédex de referência.

## 4. Fichas completas, movesets por nível e TMs propostas

### 4.1. Iron Oracle — origem: Claydol
**Tipo:** Terra/Psíquico · **Habilidade:** Quark Drive · **BST:** 570 · **Função:** Tanque especial, controle de campo e removedor de hazards.
**Status da tipagem:** Tipagem indicada no LEIA-ME do ZIP (mantida).

Mantém a silhueta flutuante e a especialidade defensiva de Claydol, mas transforma o corpo em uma plataforma de processamento com placas e braços mecânicos. A redução de Speed reforça o papel de sentinela pesada.

| Atributo | Base original | Novo Paradox | Diferença |
|---|---:|---:|---:|
| HP | 60 | **80** | +20 |
| Attack | 70 | **65** | -5 |
| Defense | 105 | **125** | +20 |
| Sp. Attack | 70 | **115** | +45 |
| Sp. Defense | 120 | **135** | +15 |
| Speed | 75 | **50** | -25 |
| **TOTAL (BST)** | **500** | **570** | **+70** |

**Análise comparativa dos golpes**
- **Golpes/temas preservados:** Rapid Spin, Cosmic Power, Earth Power, Psychic, Ancient Power, Explosion, Trick Room e Stealth Rock preservam a ideia de clay doll levitante/controle do campo.
- **Golpes/temas adicionados:** Psyshock, Iron Defense e maior potência de golpes especiais deixam de depender do Attack 70 do original. Quark Drive substitui Levitate.
- **Mudança ou perda de função:** Perde a imunidade a Terra decorrente de Levitate; o visual de flutuação não a concede automaticamente. Não recebe Recover ou Quiver Dance, evitando durabilidade excessiva.

#### Learnset completo por nível — proposta para o fan game
| Nível | Golpe |
|---:|---|
| 1 | Confusion |
| 1 | Rapid Spin |
| 1 | Harden |
| 1 | Mud-Slap |
| 7 | Psybeam |
| 14 | Rock Tomb |
| 21 | Cosmic Power |
| 28 | Ancient Power |
| 35 | Earth Power |
| 42 | Psyshock |
| 49 | Iron Defense |
| 56 | Psychic |
| 63 | Stealth Rock |
| 70 | Power Gem |
| 77 | Earthquake |
| 84 | Future Sight |
| 91 | Explosion |

#### TMs e tutores propostos (15 golpes)
`Protect`, `Psychic`, `Psyshock`, `Earth Power`, `Earthquake`, `Rock Slide`, `Flash Cannon`, `Body Press`, `Trick Room`, `Calm Mind`, `Sandstorm`, `Reflect`, `Light Screen`, `Substitute`, `Tera Blast`.

> A lista de TM é uma proposta de compatibilidade para o fan game; **não indica que o Pokémon de referência aprenda cada TM em Scarlet/Violet**. Golpes repetidos entre nível e TM significam duas rotas possíveis de aprendizagem.

#### Sets de teste para balanceamento
- **Controle resistente:** Nature Calm; EVs 252 HP / 4 Def / 252 Sp. Def; `Earth Power / Psychic / Rapid Spin / Stealth Rock`. Paredes especiais e utilidade; Quark Drive costuma reforçar Sp. Def.
- **Ofensivo lento:** Nature Modest; EVs 252 HP / 252 Sp. Atk / 4 Sp. Def; `Earth Power / Psyshock / Power Gem / Trick Room`. Atacante de Trick Room, sem recuperação confiável.

**Risco específico de balanceamento:** Com Sp. Defense 135, Quark Drive pode reforçar a defesa especial, em vez do Sp. Attack 115. Isso é intencional. Electric Terrain funciona apenas se a criatura for considerada grounded no motor.

### 4.2. Iron Coil — origem: Furret
**Tipo:** Normal/Aço · **Habilidade:** Quark Drive · **BST:** 570 · **Função:** Pivot físico extremamente rápido e utilitário.
**Status da tipagem:** Proposta de tipagem baseada no corpo segmentado metálico; ZIP não fixa tipo.

O corpo alongado e segmentado de Furret vira uma corrente articulada de peças de metal; o nome Iron Coil corresponde ao nome do ZIP e faz referência ao seu movimento circular.

| Atributo | Base original | Novo Paradox | Diferença |
|---|---:|---:|---:|
| HP | 85 | **85** | +0 |
| Attack | 76 | **105** | +29 |
| Defense | 64 | **95** | +31 |
| Sp. Attack | 45 | **70** | +25 |
| Sp. Defense | 55 | **80** | +25 |
| Speed | 90 | **135** | +45 |
| **TOTAL (BST)** | **415** | **570** | **+155** |

**Análise comparativa dos golpes**
- **Golpes/temas preservados:** Quick Attack, U-turn, Double-Edge, Super Fang e Tidy Up mantêm a função de pivot incômodo e móvel de Furret.
- **Golpes/temas adicionados:** Metal Claw, Iron Tail, Iron Head, Iron Defense e Coil definem o STAB Aço e a mecânica de articulações mecânicas.
- **Mudança ou perda de função:** Frisk, Run Away e Keen Eye dão lugar a Quark Drive. Pela tipagem Normal/Aço surge fraqueza **4× a Lutador** e também a Fogo e Terra. Não conceder Extreme Speed para não somar prioridade alta à Speed 135.

#### Learnset completo por nível — proposta para o fan game
| Nível | Golpe |
|---:|---|
| 1 | Quick Attack |
| 1 | Defense Curl |
| 1 | Tail Whip |
| 1 | Metal Claw |
| 7 | Swift |
| 14 | Iron Tail |
| 21 | U-turn |
| 28 | Spark |
| 35 | Iron Head |
| 42 | Agility |
| 49 | Double-Edge |
| 56 | Tidy Up |
| 63 | Iron Defense |
| 70 | Coil |
| 77 | Wild Charge |
| 84 | Super Fang |
| 91 | Giga Impact |

#### TMs e tutores propostos (15 golpes)
`Protect`, `Iron Head`, `U-turn`, `Volt Switch`, `Thunder Wave`, `Thunder Punch`, `Brick Break`, `Trailblaze`, `Substitute`, `Body Press`, `Heavy Slam`, `Tera Blast`, `Double-Edge`, `Giga Impact`, `Metal Sound`.

> A lista de TM é uma proposta de compatibilidade para o fan game; **não indica que o Pokémon de referência aprenda cada TM em Scarlet/Violet**. Golpes repetidos entre nível e TM significam duas rotas possíveis de aprendizagem.

#### Sets de teste para balanceamento
- **Pivot rápido:** Nature Jolly; EVs 252 Attack / 4 Sp. Def / 252 Speed; `Iron Head / Double-Edge / U-turn / Tidy Up`. Pivot que remove hazards; Quark Drive favorece Speed.
- **Setup mecânico:** Nature Adamant; EVs 252 Attack / 4 Defense / 252 Speed; `Iron Head / Coil / Super Fang / Quick Attack`. Variante focada em ataque sustentado; revisar o atributo efetivamente amplificado.

**Risco específico de balanceamento:** Tidy Up aumenta Attack e Speed em um estágio e remove hazards dos dois lados; combinar com Coil é possível, mas exige dois turnos. Testar Quark Drive + Tidy Up para não tornar a criatura difícil demais de enfrentar.

### 4.3. Iron Echo — origem: Exploud
**Tipo:** Normal/Elétrico · **Habilidade:** Quark Drive · **BST:** 570 · **Função:** Wallbreaker especial de som, lento-médio e com boa resistência.
**Status da tipagem:** Proposta baseada em alto-falantes e amplificadores elétricos; ZIP não fixa tipo.

O alto-falante no interior da boca substitui a expressão orgânica de Exploud. A grande potência em Sp. Attack cria o paralelo de Iron Moth: ofensiva imediata, sem grande dependência de setup.

| Atributo | Base original | Novo Paradox | Diferença |
|---|---:|---:|---:|
| HP | 104 | **110** | +6 |
| Attack | 91 | **70** | -21 |
| Defense | 63 | **82** | +19 |
| Sp. Attack | 91 | **140** | +49 |
| Sp. Defense | 73 | **82** | +9 |
| Speed | 68 | **86** | +18 |
| **TOTAL (BST)** | **490** | **570** | **+80** |

**Análise comparativa dos golpes**
- **Golpes/temas preservados:** Echoed Voice, Hyper Voice, Supersonic, Screech e Boomburst mantêm a identidade de ataques sonoros.
- **Golpes/temas adicionados:** Thunder Shock, Shock Wave, Discharge, Thunderbolt, Charge e Eerie Impulse representam o som convertido em pulsos elétricos com STAB adicional.
- **Mudança ou perda de função:** A troca de Soundproof/Scrappy por Quark Drive faz o Pokémon deixar de ignorar imunidade Fantasma a golpes Normais; Boomburst não atinge Fantasmas por padrão. Não disponibilizar Nasty Plot ou Calm Mind no pacote inicial.

#### Learnset completo por nível — proposta para o fan game
| Nível | Golpe |
|---:|---|
| 1 | Echoed Voice |
| 1 | Thunder Shock |
| 1 | Supersonic |
| 1 | Howl |
| 7 | Charge |
| 14 | Snarl |
| 21 | Shock Wave |
| 28 | Hyper Voice |
| 35 | Thunder Wave |
| 42 | Discharge |
| 49 | Screech |
| 56 | Thunderbolt |
| 63 | Metal Sound |
| 70 | Eerie Impulse |
| 77 | Thunder |
| 84 | Boomburst |
| 91 | Hyper Beam |

#### TMs e tutores propostos (15 golpes)
`Protect`, `Thunderbolt`, `Thunder`, `Charge Beam`, `Volt Switch`, `Electric Terrain`, `Hyper Voice`, `Snarl`, `Metal Sound`, `Thunder Wave`, `Electro Ball`, `Light Screen`, `Substitute`, `Tera Blast`, `Hyper Beam`.

> A lista de TM é uma proposta de compatibilidade para o fan game; **não indica que o Pokémon de referência aprenda cada TM em Scarlet/Violet**. Golpes repetidos entre nível e TM significam duas rotas possíveis de aprendizagem.

#### Sets de teste para balanceamento
- **Quebra-paredes:** Nature Modest; EVs 252 HP / 252 Sp. Atk / 4 Sp. Def; `Boomburst / Thunderbolt / Volt Switch / Snarl`. Boomburst como golpe principal; sem boost adicional de Nasty Plot.
- **Controle eletroacústico:** Nature Modest; EVs 124 HP / 252 Sp. Atk / 132 Speed; `Hyper Voice / Discharge / Thunder Wave / Volt Switch`. Alternativa menos explosiva, com status e pivot.

**Risco específico de balanceamento:** Boomburst com STAB Normal, Sp. Attack 140 e Quark Drive pode ser muito forte: liberar apenas no nível 84 e testar PP, cobertura de tipos e uso de Booster Energy. NUNCA dar Scrappy como habilidade extra simultânea.

### 4.4. Iron Glimmer — origem: Lumineon
**Tipo:** Água/Elétrico · **Habilidade:** Quark Drive · **BST:** 570 · **Função:** Atacante especial rápido de Água/Elétrico e pivot de campo.
**Status da tipagem:** Proposta baseada nas nadadeiras holográficas de circuito; ZIP não fixa tipo.

Conserva a silhueta fina de Lumineon, mas as nadadeiras tornam-se painéis luminosos com circuitos ciano. Em vez de depender de chuva e de Storm Drain, usa energia de Electric Terrain.

| Atributo | Base original | Novo Paradox | Diferença |
|---|---:|---:|---:|
| HP | 69 | **80** | +11 |
| Attack | 69 | **65** | -4 |
| Defense | 76 | **85** | +9 |
| Sp. Attack | 69 | **120** | +51 |
| Sp. Defense | 86 | **95** | +9 |
| Speed | 91 | **125** | +34 |
| **TOTAL (BST)** | **460** | **570** | **+110** |

**Análise comparativa dos golpes**
- **Golpes/temas preservados:** Aqua Ring, Water Pulse, Soak, Surf, Rain Dance e Hydro Pump mantêm a identidade aquática e de suporte.
- **Golpes/temas adicionados:** Charge Beam, Discharge, Thunderbolt, Thunder e Volt Switch adicionam STAB Elétrico. Flip Turn reforça a função de pivot aquático.
- **Mudança ou perda de função:** A troca de Swift Swim/Storm Drain por Quark Drive remove a imunidade e o aumento de Sp. Attack proporcionados por Storm Drain quando atingido por golpe de Água. Não herda a duplicação de Speed por Swift Swim na chuva.

#### Learnset completo por nível — proposta para o fan game
| Nível | Golpe |
|---:|---|
| 1 | Water Gun |
| 1 | Charm |
| 1 | Supersonic |
| 1 | Thunder Shock |
| 7 | Aqua Ring |
| 14 | Water Pulse |
| 21 | Charge Beam |
| 28 | Icy Wind |
| 35 | Flip Turn |
| 42 | Discharge |
| 49 | Soak |
| 56 | Surf |
| 63 | Tailwind |
| 70 | Thunderbolt |
| 77 | Rain Dance |
| 84 | Hydro Pump |
| 91 | Thunder |

#### TMs e tutores propostos (15 golpes)
`Protect`, `Surf`, `Hydro Pump`, `Ice Beam`, `Icy Wind`, `Scald`, `Chilling Water`, `Volt Switch`, `Thunderbolt`, `Electric Terrain`, `Charge Beam`, `Dazzling Gleam`, `Rain Dance`, `Substitute`, `Tera Blast`.

> A lista de TM é uma proposta de compatibilidade para o fan game; **não indica que o Pokémon de referência aprenda cada TM em Scarlet/Violet**. Golpes repetidos entre nível e TM significam duas rotas possíveis de aprendizagem.

#### Sets de teste para balanceamento
- **Pivot veloz:** Nature Timid; EVs 252 Sp. Atk / 4 Sp. Def / 252 Speed; `Surf / Thunderbolt / Flip Turn / Ice Beam`. Pivot com STAB duplo e cobertura Gelo; Quark Drive tende a Speed.
- **Controle aquático:** Nature Timid; EVs 252 HP / 4 Sp. Atk / 252 Speed; `Surf / Volt Switch / Tailwind / Aqua Ring`. Suporte de velocidade e reposicionamento; não tem grande Attack físico.

**Risco específico de balanceamento:** Como Speed 125 supera Sp. Attack 120 em base, Quark Drive pode favorecer Speed — especialmente com EVs em velocidade. Para usar Sp. Attack como alvo, é preciso verificar os atributos efetivos ou alterar a distribuição de EVs.

### 4.5. Iron Wraith — origem: Spiritomb
**Tipo:** Fantasma/Elétrico · **Habilidade:** Quark Drive · **BST:** 570 · **Função:** Tanque especial lento com status, Hex e cobertura elétrica.
**Status da tipagem:** Proposta baseada no núcleo energético e nos anéis de energia do sprite; ZIP não fixa tipo.

As 108 almas assumem a aparência de um programa de consciência fragmentado em um reator. Mantém a aura Fantasma de Spiritomb, mas abandona Sombrio como tipo secundário.

| Atributo | Base original | Novo Paradox | Diferença |
|---|---:|---:|---:|
| HP | 50 | **85** | +35 |
| Attack | 92 | **75** | -17 |
| Defense | 108 | **105** | -3 |
| Sp. Attack | 92 | **130** | +38 |
| Sp. Defense | 108 | **125** | +17 |
| Speed | 35 | **50** | +15 |
| **TOTAL (BST)** | **485** | **570** | **+85** |

**Análise comparativa dos golpes**
- **Golpes/temas preservados:** Confuse Ray, Night Shade, Spite, Shadow Sneak, Hex, Will-O-Wisp, Shadow Ball, Nasty Plot, Curse e Dark Pulse preservam a dimensão sobrenatural.
- **Golpes/temas adicionados:** Thunder Shock, Shock Wave, Thunder Wave, Discharge e Thunder criam ataques elétricos sustentados e aumentam a sinergia entre paralisia/queimadura e Hex.
- **Mudança ou perda de função:** Perde STAB Sombrio e imunidade a Psíquico (a imunidade Psíquico vinha de Sombrio); agora sofre fraqueza a Terra, Fantasma e Sombrio. Mantém imunidades de Fantasma a Normal e Lutador. Não recebe Recover.

#### Learnset completo por nível — proposta para o fan game
| Nível | Golpe |
|---:|---|
| 1 | Confuse Ray |
| 1 | Night Shade |
| 1 | Thunder Shock |
| 1 | Spite |
| 7 | Shadow Sneak |
| 14 | Hex |
| 21 | Thunder Wave |
| 28 | Shock Wave |
| 35 | Will-O-Wisp |
| 42 | Shadow Ball |
| 49 | Curse |
| 56 | Nasty Plot |
| 63 | Dark Pulse |
| 70 | Discharge |
| 77 | Memento |
| 84 | Thunder |
| 91 | Destiny Bond |

#### TMs e tutores propostos (15 golpes)
`Protect`, `Hex`, `Shadow Ball`, `Will-O-Wisp`, `Thunderbolt`, `Thunder Wave`, `Foul Play`, `Snarl`, `Trick`, `Taunt`, `Nasty Plot`, `Reflect`, `Light Screen`, `Substitute`, `Tera Blast`.

> A lista de TM é uma proposta de compatibilidade para o fan game; **não indica que o Pokémon de referência aprenda cada TM em Scarlet/Violet**. Golpes repetidos entre nível e TM significam duas rotas possíveis de aprendizagem.

#### Sets de teste para balanceamento
- **Controle de status:** Nature Calm; EVs 252 HP / 4 Sp. Atk / 252 Sp. Def; `Hex / Will-O-Wisp / Thunderbolt / Confuse Ray`. Status e atrito; o atributo escolhido por Quark Drive depende dos EVs.
- **Quebra-paredes lento:** Nature Modest; EVs 252 HP / 252 Sp. Atk / 4 Sp. Def; `Shadow Ball / Thunderbolt / Nasty Plot / Will-O-Wisp`. Precisa de um turno de preparação e é vulnerável a Ground/Dark/Ghost.

**Risco específico de balanceamento:** Hex dobrado em alvo com status, Nasty Plot e Quark Drive são uma combinação potencialmente muito forte. Contra times defensivos, revisar acesso a Will-O-Wisp e a Thunder Wave no mesmo conjunto.

### 4.6. Iron Raptor — origem: Swellow
**Tipo:** Normal/Voador · **Habilidade:** Quark Drive · **BST:** 570 · **Função:** Atacante físico veloz e pivot aéreo.
**Status da tipagem:** Tipagem indicada no LEIA-ME do ZIP (mantida).

Preserva a forma aerodinâmica da ave e a paleta metálica do corpo, mas utiliza asas e propulsores tecnológicos. Ganha força física para combinar Brave Bird e Double-Edge.

| Atributo | Base original | Novo Paradox | Diferença |
|---|---:|---:|---:|
| HP | 60 | **74** | +14 |
| Attack | 85 | **140** | +55 |
| Defense | 60 | **82** | +22 |
| Sp. Attack | 75 | **70** | -5 |
| Sp. Defense | 50 | **72** | +22 |
| Speed | 125 | **132** | +7 |
| **TOTAL (BST)** | **455** | **570** | **+115** |

**Análise comparativa dos golpes**
- **Golpes/temas preservados:** Quick Attack, Wing Attack, Aerial Ace, Facade, Agility, Brave Bird, Double-Edge, Endeavor e Reversal mantêm a base da ave agressiva de Hoenn.
- **Golpes/temas adicionados:** U-turn e Dual Wingbeat promovem pressão constante e reposicionamento; maior Attack dá força mesmo sem Guts.
- **Mudança ou perda de função:** Guts deixa de fornecer bônus quando há status e Scrappy deixa de permitir que Normal/Lutador acerte Fantasma. Quark Drive pode melhorar Attack ou Speed conforme os atributos calculados.

#### Learnset completo por nível — proposta para o fan game
| Nível | Golpe |
|---:|---|
| 1 | Peck |
| 1 | Quick Attack |
| 1 | Focus Energy |
| 1 | Growl |
| 7 | Wing Attack |
| 14 | Steel Wing |
| 21 | Aerial Ace |
| 28 | Agility |
| 35 | U-turn |
| 42 | Facade |
| 49 | Dual Wingbeat |
| 56 | Brave Bird |
| 63 | Double-Edge |
| 70 | Roost |
| 77 | Endeavor |
| 84 | Reversal |
| 91 | Giga Impact |

#### TMs e tutores propostos (15 golpes)
`Protect`, `Brave Bird`, `Aerial Ace`, `Acrobatics`, `U-turn`, `Tailwind`, `Double-Edge`, `Facade`, `Agility`, `Thief`, `Substitute`, `Air Slash`, `Reversal`, `Tera Blast`, `Giga Impact`.

> A lista de TM é uma proposta de compatibilidade para o fan game; **não indica que o Pokémon de referência aprenda cada TM em Scarlet/Violet**. Golpes repetidos entre nível e TM significam duas rotas possíveis de aprendizagem.

#### Sets de teste para balanceamento
- **Ataque prioritário:** Nature Adamant; EVs 252 Attack / 4 Sp. Def / 252 Speed; `Brave Bird / Double-Edge / Quick Attack / U-turn`. Em muitos spreads Adamant favorece Attack em Quark Drive; conferir valores efetivos.
- **Velocidade extrema:** Nature Jolly; EVs 252 Attack / 4 Sp. Def / 252 Speed; `Brave Bird / U-turn / Roost / Facade`. Jolly pode levar Quark Drive a amplificar Speed, em vez de Attack.

**Risco específico de balanceamento:** Attack 140 e Speed 132 já são ofensivos. Não dar Extreme Speed, Swords Dance nem habilidade secundária Guts; recoil de Brave Bird e Double-Edge é a contrapartida principal.

### 4.7. Iron Stinger — origem: Yanmega
**Tipo:** Inseto/Voador · **Habilidade:** Quark Drive · **BST:** 570 · **Função:** Atacante especial veloz, reconhecimento aéreo e cobertura técnica.
**Status da tipagem:** Tipagem indicada no LEIA-ME do ZIP (mantida).

A libélula ganha carapaça robótica e asas com circuitos, mantendo a silhueta original e a movimentação aérea. A melhoria ocorre principalmente em Sp. Attack, Sp. Defense e Speed.

| Atributo | Base original | Novo Paradox | Diferença |
|---|---:|---:|---:|
| HP | 86 | **88** | +2 |
| Attack | 76 | **70** | -6 |
| Defense | 86 | **88** | +2 |
| Sp. Attack | 116 | **135** | +19 |
| Sp. Defense | 56 | **75** | +19 |
| Speed | 95 | **114** | +19 |
| **TOTAL (BST)** | **515** | **570** | **+55** |

**Análise comparativa dos golpes**
- **Golpes/temas preservados:** Detect, Quick Attack, Supersonic, Ancient Power, U-turn, Bug Buzz, Air Slash, Screech e Tailwind preservam a identidade do Yanmega.
- **Golpes/temas adicionados:** Psychic Noise, Discharge e Flash Cannon representam sensores e armas tecnológicas; as duas últimas são coberturas sem STAB.
- **Mudança ou perda de função:** Não conserva Speed Boost nem Tinted Lens. Speed sobe diretamente de 95 para 114, mas não cresce automaticamente a cada turno; golpes resistidos continuam resistidos.

#### Learnset completo por nível — proposta para o fan game
| Nível | Golpe |
|---:|---|
| 1 | Tackle |
| 1 | Detect |
| 1 | Quick Attack |
| 1 | Supersonic |
| 7 | Air Cutter |
| 14 | Struggle Bug |
| 21 | Ancient Power |
| 28 | Agility |
| 35 | U-turn |
| 42 | Bug Buzz |
| 49 | Air Slash |
| 56 | Psychic Noise |
| 63 | Screech |
| 70 | Discharge |
| 77 | Hurricane |
| 84 | Tailwind |
| 91 | Hyper Beam |

#### TMs e tutores propostos (15 golpes)
`Protect`, `Air Slash`, `Bug Buzz`, `Hurricane`, `U-turn`, `Psychic Noise`, `Psychic`, `Giga Drain`, `Flash Cannon`, `Electro Ball`, `Energy Ball`, `Solar Beam`, `Tailwind`, `Substitute`, `Tera Blast`.

> A lista de TM é uma proposta de compatibilidade para o fan game; **não indica que o Pokémon de referência aprenda cada TM em Scarlet/Violet**. Golpes repetidos entre nível e TM significam duas rotas possíveis de aprendizagem.

#### Sets de teste para balanceamento
- **Special attacker:** Nature Timid; EVs 252 Sp. Atk / 4 Sp. Def / 252 Speed; `Bug Buzz / Air Slash / Discharge / Psychic Noise`. Cobertura especial ampla; Quark Drive geralmente aumenta Sp. Attack.
- **Controle aéreo:** Nature Timid; EVs 4 HP / 252 Sp. Atk / 252 Speed; `Bug Buzz / Hurricane / Tailwind / U-turn`. Ajuda times ofensivos sem contar com Speed Boost.

**Risco específico de balanceamento:** Bug/Flying continua 4× vulnerável a Rock e sujeito a Stealth Rock se o campo estiver sem proteção; testar equilíbrio com Quark Drive e Boots. Não adicionar Quiver Dance ao pool inicial.

## 5. Quais golpes são mantidos e quais realmente mudam?

| Paradox | Identidade herdada | Alteração principal | Custo / fraqueza intencional |
|---|---|---|---|
| Iron Oracle | Rapid Spin, Earth Power, Psychic, Cosmic Power | Defesa reforçada e SpA de 70 → 115; toolkit de Aço auxiliar | Perde Levitate e Speed 75 → 50 |
| Iron Coil | Quick Attack, U-turn, Double-Edge, Tidy Up | Novo STAB Aço; Speed 90 → 135 | Fraqueza 4× a Lutador e sem Extreme Speed |
| Iron Echo | Hyper Voice, Boomburst, Supersonic | STAB Elétrico e SpA 91 → 140 | Perde Scrappy/Soundproof; Boomburst só no Nv. 84 |
| Iron Glimmer | Aqua Ring, Soak, Surf, Hydro Pump | STAB Elétrico, SpA 69 → 120 e Speed 91 → 125 | Sem Swift Swim/Storm Drain; fraqueza a Terra |
| Iron Wraith | Hex, Will-O-Wisp, Shadow Ball, Nasty Plot | Fantasma/Elétrico e SpA 92 → 130 | Perde imunidade Psíquico, SpD muito mais crucial que Speed |
| Iron Raptor | Quick Attack, Brave Bird, Facade, Double-Edge | Attack 85 → 140 mantendo Speed alta | Perde Guts/Scrappy e sofre recoil |
| Iron Stinger | Bug Buzz, Air Slash, Detect, Ancient Power | SpA 116 → 135, Speed 95 → 114, cobertura tech | Perde Speed Boost/Tinted Lens e mantém fraqueza 4× a Pedra |

## 6. Regras para integrar no Blue Dessastre Paradoxal
1. Cadastrar sete espécies **separadas** das originais. Definir os **nomes de exibição** `Iron Oracle`, `Iron Coil`, `Iron Echo`, `Iron Glimmer`, `Iron Wraith`, `Iron Raptor` e `Iron Stinger`, mas manter por enquanto os identificadores originais dos assets no ZIP: `Iron_Claydol`, `Iron_Coil`, `Iron_Exploud`, `Iron_Lumineon`, `Iron_Spiritomb`, `Iron_Swellow`, `Iron_Yanmega`.
2. Usar **stats exatamente** da tabela da seção 3 e habilidade **Quark Drive**. Não reutilizar habilidades das originais nem adicionar uma segunda habilidade sem novo balanceamento.
3. Criar os learnsets por nível listados e um conjunto de compatibilidades TM. `TM` não é um nível: manter estruturas separadas no banco e no editor.
4. Cada espécie Paradox deve usar grupo ovo `Undiscovered`, ser sem gênero, não evoluir e não possuir egg moves, se o sistema seguir a lógica dos Paradox oficiais.
5. Manter o STAB conforme a **tipagem futura**, não a original: Iron Wraith perde STAB Sombrio; Iron Echo ganha Elétrico; Iron Coil ganha Aço; Iron Glimmer ganha Elétrico.
6. Validar a seleção do atributo que Quark Drive potencializa **com os stats efetivos**, Nature/EV/IV; não simplesmente selecionar o maior valor dos Base Stats. Atenção especial a Iron Raptor e Iron Glimmer.
7. Validar no motor a condição de Electric Terrain: um sprite visualmente suspenso não implica imunidade a Terra; a habilidade Levitate não foi herdada por Iron Oracle. Uma condição de altitude/grounding tratada por código pode mudar o efeito.
8. Validar quais movimentos já existem no jogo-base e atualizar a tabela de golpes apenas para os ausentes; não atribuir IDs novos sem checagem.
9. Se houver limites de níveis inferiores a 91, deslocar os aprendizados tardios preservando a ordem: ataques STAB fortes antes de ataques de final de campanha.
10. Conferir se o importador de espécies reconhece `species`, `baseStats`, `types`, `abilities`, `levelUpLearnset` e `tmCompatibility` sem sobrescrever formas normais; os nomes aqui são conceituais e precisam ser ajustados ao schema real do projeto.

## 7. Testes de regressão / aceitação
- [ ] Cada BST resulta em **570** e nenhum stat individual é negativo ou acima do limite do motor.
- [ ] Tipagens Terra/Psíquico (Claydol), Normal/Voador (Swellow) e Inseto/Voador (Yanmega) reproduzem o metadata do ZIP.
- [ ] Tipagens de Coil, Exploud, Lumineon e Spiritomb foram aprovadas antes de serem aplicadas.
- [ ] Todos os Pokémon possuem exatamente uma habilidade: Quark Drive.
- [ ] Golpes por nível são gravados e reaprendidáveis; golpes de TM aparecem somente se a TM estiver habilitada.
- [ ] Booster Energy e Electric Terrain ativam Quark Drive corretamente; troca de atributos após EV/Nature não é ignorada.
- [ ] Iron Oracle é afetado por ataques Terra se não existir efeito adicional de levitação; sua sprite flutuante não é uma habilidade.
- [ ] Iron Coil recebe dano 4× de Lutador por Normal/Aço.
- [ ] Iron Echo não atinge Fantasma com Boomburst sem um efeito extra do jogo.
- [ ] Iron Glimmer não ativa Swift Swim nem Storm Drain (habilidades não herdadas).
- [ ] Iron Wraith recebe ataque Psíquico normalmente, conforme Fantasma/Elétrico.
- [ ] Iron Raptor aplica recoil corretamente a Brave Bird e Double-Edge.
- [ ] Iron Stinger recebe dano 4× de Pedra e dano de Stealth Rock correspondente, se não houver proteção.
- [ ] Sprites normal/shiny e sprites de costas são específicos de cada espécie; nenhuma sprite base foi sobrescrita.
- [ ] Novos nomes aparecem na Pokédex e em batalha, enquanto os identificadores dos sprites continuam funcionais.
- [ ] Entradas de Pokédex curtas, categoria, altura e peso foram cadastrados conforme a seção 3.1, e os sete sprites mantêm escala/pivô coerentes.
- [ ] Golpes dependentes de peso (como Heavy Slam e Low Kick) respeitam os novos valores, se estiverem implementados.

## 8. Fontes dos dados oficiais e referências de design
**Nota:** estes links validam as espécies-base e a inspiração em Pokémon Scarlet/Violet. **Não** validam os novos stats/learnsets, que são propostos neste estudo.
- https://pokemondb.net/pokedex/stats/height-weight — altura e peso oficiais das espécies de referência
- https://pokemondb.net/pokedex/claydol
- https://pokemondb.net/pokedex/furret
- https://pokemondb.net/pokedex/exploud
- https://pokemondb.net/pokedex/lumineon
- https://pokemondb.net/pokedex/spiritomb
- https://pokemondb.net/pokedex/swellow
- https://pokemondb.net/pokedex/yanmega
- https://pokemondb.net/pokedex/iron-hands
- https://pokemondb.net/pokedex/iron-moth
- https://pokemondb.net/pokedex/iron-treads
- https://bulbapedia.bulbagarden.net/wiki/Quark_Drive_(Ability)

---
**Resultado:** sete fichas com nomes únicos, descrições de Pokédex, altura, peso e proporções, mantendo stats e golpes anteriores; **nenhuma alteração no repositório ou no jogo foi realizada**. As quatro tipagens não definidas no ZIP continuam propostas, mesmo com movesets completos.