# Pokémon FireRed — Guia de inventário e tradução dos diálogos (EN → PT-BR)

**Objetivo:** criar um catálogo de todas as entradas de texto encontradas nos scripts locais de Pokémon FireRed, preservando o **identificador original**, a **origem por mapa/arquivo**, o **texto em inglês** e um **campo separado para a tradução em português brasileiro**.

> **Importante:** este guia não reproduz o roteiro original completo do jogo. Os resumos de cenas abaixo são descrições próprias, **não transcrições ou traduções literais**. O texto integral de FireRed é protegido por direitos autorais. Para montar a versão fala a fala, use o extrator anexo em uma cópia dos arquivos locais à qual você tenha acesso autorizado.

## 1. Arquivos entregues

1. **`Guia_Dialogos_Pokemon_FireRed_EN_PT.md`** — este documento, com o mapeamento de áreas, critérios de tradução e exemplos.
2. **`extrair_traduzir_dialogos_firered.py`** — script Python que lê a descompilação **local**, identifica entradas e cria um único Markdown EN/PT, com tradução automática opcional.

O script não vem acompanhado de textos do jogo. Ele não modifica ROMs nem o código do jogo.

## 2. Onde os textos estão organizados

Referência estrutural: repositório público de descompilação [pret/pokefirered](https://github.com/pret/pokefirered).

| Origem na estrutura local | Conteúdo | Cobertura do extrator |
|---|---|---|
| `data/maps/<Mapa>/text.inc` | Falas de NPCs, treinadores, placas e cenas | Leitura de blocos `.string` |
| `data/maps/<Mapa>/scripts.inc` | Lógica dos eventos, ramificações e chamadas às falas | Arquivo útil para contextualização; mensagens literais `.string` eventualmente presentes também são extraídas |
| `data/text/*.inc` e subpastas | Textos globais, itens, comerciantes e outros sistemas | Leitura de `.string` |
| `data/**/*.s` | Textos de evento e outras mensagens globais | Leitura de `.string` |
| `src/**/*.c` | Mensagens em C, incluindo algumas macros `_()` | Extração da forma comum `_ ("...")` sem o espaço; revisão recomendada |

**Atenção à abrangência:** detectar todos os literais de texto em arquivos de código é diferente de demonstrar que todas as falas *alcançáveis no jogo* foram capturadas. Algumas dependem de scripts, composições dinâmicas, dados especiais e versões do jogo. O exportador cobre os padrões descritos, sem garantir 100% de todos os caminhos possíveis.

### Campos gerados para cada fala

```text
### 00001 — <IDENTIFICADOR_DA_FALA>
- Fonte: <CAMINHO_DO_ARQUIVO>:<LINHA>
- Chave: <IDENTIFICADOR_DA_FALA>

Texto original (inglês)
[Obtido dos arquivos locais na execução]

Português (pt-BR)
[Obtido por tradução local opcional ou revisão manual]

Estado: pendente / tradução automática — revisar
```

O conteúdo entre colchetes no exemplo é apenas uma explicação de formato, **não é uma fala de FireRed**.

## 3. Como gerar o Markdown completo no Windows

### Pré-requisitos

- Python 3 instalado no Windows.
- Git instalado (apenas se você ainda precisar obter os arquivos-fonte).
- Acesso legítimo aos arquivos da descompilação que deseja processar.
- Internet na primeira instalação do modelo Argos Translate, caso queira tradução automática. Depois de instalado, o tradutor pode funcionar localmente.

### Passo A — preparar a pasta

Se você já tem uma pasta local de `pokefirered`, **não precisa baixá-la novamente**. Caso contrário, consulte a documentação do repositório [pret/pokefirered](https://github.com/pret/pokefirered) e obtenha uma cópia conforme as condições aplicáveis.

Exemplo de estrutura esperada:

```text
C:\Projetos\pokefirered\
  data\
    maps\
    text\
  src\
```

### Passo B — gerar um índice sem tradução

No PowerShell, na pasta em que você salvou o arquivo Python:

```powershell
py .\extrair_traduzir_dialogos_firered.py "C:\Projetos\pokefirered" --saida "FireRed_Dialogos_EN_PT.md"
```

A saída inclui uma seção individual por entrada textual e deixa o campo português marcado como pendente.

### Passo C — instalar o tradutor e gerar a tradução automática

```powershell
py -m pip install argostranslate
py .\extrair_traduzir_dialogos_firered.py "C:\Projetos\pokefirered" --traduzir --saida "FireRed_Dialogos_EN_PT.md"
```

O Argos Translate instalará um modelo **inglês → português** caso não esteja disponível. A tradução é **automática e não revisada**; nomes de Pokémon, piadas, gênero das falas e mensagens com variáveis devem ser conferidos manualmente.

Para testar as primeiras 50 entradas sem processar tudo:

```powershell
py .\extrair_traduzir_dialogos_firered.py "C:\Projetos\pokefirered" --traduzir --limite 50 --saida "FireRed_Teste_50_Falas.md"
```

Para não incluir mensagens em C, use `--sem-c`.

## 4. Padronização recomendada para pt-BR

| Termo no jogo | Padronização sugerida | Observações |
|---|---|---|
| Pokémon | Pokémon | Não traduzir nome da franquia |
| Pokédex | Pokédex | Preservar acentuação |
| Poké Ball | Poké Ball | Preservar nome de item para correspondência com bancos de dados |
| Team Rocket | Equipe Rocket | Nome da organização |
| Gym Leader | Líder de Ginásio | Função |
| Gym Badge | Insígnia de Ginásio | Conceito; as insígnias individuais precisam de glossário próprio |
| Elite Four | Elite dos Quatro | Padronizar em todas as regiões |
| Professor Oak | Professor Oak | Preservar nome usado em FireRed; apelidos só se forem intencionais |
| Rival | Rival / nome configurado | Usar `{RIVAL}` quando houver variável |
| TM | MT (Máquina Técnica) | Alterar apenas se a interface do fangame também usar MT |
| HM | MO (Máquina Oculta) | Manter consistente com itens e mecânicas |
| Move | Golpe | Não confundir com habilidade (`Ability`) |
| Ability | Habilidade | Distinta de golpe e característica |
| PC | PC | Sistema de armazenamento |

**Regra principal:** mantenha literalmente tokens como `{PLAYER}`, `{RIVAL}`, `{STR_VAR_1}` e demais substituições dinâmicas. O programa tenta protegê-los durante a tradução, mas a revisão manual continua necessária.

### Quebras e tamanho de caixa

Em uma descompilação GBA, certos símbolos indicam janela nova, linha nova ou fim de string. O extrator os transforma em separadores de leitura no Markdown. Isso **não garante** que o resultado traduzido caiba nas caixas originais do GBA. Para usar no jogo, faça uma etapa própria de quebra de linhas e de teste visual, considerando fonte, largura e caracteres acentuados.

## 5. Mapeamento de cenas importantes — resumos em português

As descrições abaixo são resumos próprios dos **assuntos** que você encontrará no roteiro. Não são falas originais nem uma lista completa das variações condicionais.

### 5.1. Pallet Town, começo e tutorial

| ID | Local / personagem | Assunto do diálogo (resumo em PT-BR) |
|---|---|---|
| KAN-001 | Casa do protagonista | Orientações iniciais da família e saída para explorar a região |
| KAN-002 | Laboratório do Professor Oak | Apresentação do professor, do rival e dos três Pokémon iniciais |
| KAN-003 | Laboratório / rival | Competição pela escolha do inicial e desafio de batalha |
| KAN-004 | Laboratório / Oak | Explicação básica sobre criação, evolução e batalhas Pokémon |
| KAN-005 | Rota 1 / entregas | Pedido de levar um pacote da loja de Viridian ao professor |
| KAN-006 | Laboratório / Oak | Entrega da Pokédex, bolas de captura e objetivo de pesquisa |
| KAN-007 | Casa do rival | Obtenção do mapa da região e comentários da família do rival |
| KAN-008 | Viridian City | Orientação sobre captura, Centro Pokémon, loja e ginásio inicialmente fechado |
| KAN-009 | Rota 22 / rival | Desafio opcional antes da Liga Pokémon e conversa de rivalidade |
| KAN-010 | Viridian Forest | Orientações sobre Pokémon selvagens, treinadores e status |

### 5.2. Pewter, Mt. Moon e Cerulean

| ID | Local / personagem | Assunto do diálogo (resumo em PT-BR) |
|---|---|---|
| KAN-011 | Pewter City | Dicas de treinamento e informações sobre o ginásio local |
| KAN-012 | Museu de Pewter | Fósseis e explicações sobre a história dos Pokémon |
| KAN-013 | Ginásio / Brock | Apresentação do líder, combate e premiação pela vitória |
| KAN-014 | Rota 3 | Desafios com treinadores durante o avanço rumo ao Mt. Moon |
| KAN-015 | Mt. Moon / Equipe Rocket | Exploração da caverna, confronto com criminosos e disputa por fósseis |
| KAN-016 | Mt. Moon / pesquisador | Escolha de um fóssil e consequências da decisão |
| KAN-017 | Cerulean City | Informações sobre a ponte ao norte, loja de bicicletas e habitantes |
| KAN-018 | Ginásio / Misty | Prova de batalha do tipo Água e conquista da insígnia |
| KAN-019 | Nugget Bridge / rival | Novo encontro com o rival e provocação antes da batalha |
| KAN-020 | Nugget Bridge / Rocket | Sequência de treinadores, recompensa e tentativa de recrutamento |
| KAN-021 | Route 25 / Bill | Situação científica incomum, recuperação de Bill e recompensa de viagem |
| KAN-022 | Cerulean / casa invadida | Investigação de roubo e confronto com membro da Equipe Rocket |

### 5.3. Vermilion, S.S. Anne e Lavender

| ID | Local / personagem | Assunto do diálogo (resumo em PT-BR) |
|---|---|---|
| KAN-023 | Vermilion City | Histórias dos marinheiros, porto, troca e pesca |
| KAN-024 | S.S. Anne / passageiros | Conversas e desafios durante a exploração do navio |
| KAN-025 | S.S. Anne / rival | Batalha contra o rival antes de chegar ao capitão |
| KAN-026 | S.S. Anne / capitão | Ajuda ao capitão e obtenção do recurso para cortar árvores |
| KAN-027 | Ginásio / Lt. Surge | Desafio de mecanismos elétricos e combate pela insígnia |
| KAN-028 | Diglett's Cave e Route 2 | Travessia alternativa e recompensas condicionadas ao progresso na Pokédex |
| KAN-029 | Rock Tunnel | Treinadores, escuridão e dicas para atravessar a caverna |
| KAN-030 | Lavender Town | Explicações sobre memória, perda e cuidados com Pokémon falecidos |
| KAN-031 | Pokémon Tower / rival | Encontro com o rival e batalha dentro da torre |
| KAN-032 | Pokémon Tower / espíritos | Mistério dos fantasmas e obstáculos que impedem a passagem |
| KAN-033 | Pokémon Tower / Mr. Fuji | Resolução do conflito com a Equipe Rocket e recompensa especial |

### 5.4. Celadon, esconderijo Rocket e Saffron

| ID | Local / personagem | Assunto do diálogo (resumo em PT-BR) |
|---|---|---|
| KAN-034 | Celadon City | Conversas sobre o grande comércio e os locais da cidade |
| KAN-035 | Celadon Department Store | Falas de balconistas, clientes e serviços do prédio |
| KAN-036 | Celadon Game Corner | Indícios de operações clandestinas da Equipe Rocket |
| KAN-037 | Rocket Hideout | Interrogatórios, escaramuças, mecanismos e acesso ao chefe |
| KAN-038 | Rocket Hideout / Giovanni | Primeiro grande confronto com o chefe da Equipe Rocket |
| KAN-039 | Ginásio / Erika | Desafio especializado em Grama e recompensa pela vitória |
| KAN-040 | Acesso a Saffron | Como liberar a entrada pelos portões de segurança |
| KAN-041 | Saffron / Fighting Dojo | Batalhas em sequência e escolha de Pokémon como prêmio |
| KAN-042 | Silph Co. / funcionários | Funcionários protegidos ou ameaçados pela invasão Rocket |
| KAN-043 | Silph Co. / rival | Confronto competitivo durante a missão de resgate |
| KAN-044 | Silph Co. / Giovanni | Confronto central contra a Equipe Rocket e libertação da empresa |
| KAN-045 | Silph Co. / presidente | Agradecimento e recebimento de recompensa rara |
| KAN-046 | Ginásio / Sabrina | Teletransportes, poderes psíquicos e conquista da insígnia |

### 5.5. Fuchsia, Cinnabar e último ginásio

| ID | Local / personagem | Assunto do diálogo (resumo em PT-BR) |
|---|---|---|
| KAN-047 | Fuchsia City | Informações sobre natureza, Safari Zone e zoológico |
| KAN-048 | Safari Zone | Regras da área, limite de passos e exploração por itens |
| KAN-049 | Safari Zone / casa secreta | Recompensa associada à exploração da zona |
| KAN-050 | Fuchsia / Warden | Procura de objeto perdido e recompensa por devolvê-lo |
| KAN-051 | Ginásio / Koga | Desafio com obstáculos visuais e combate pela insígnia |
| KAN-052 | Routes 12 e 16 / Snorlax | Bloqueio de passagem e uso de um item especial para acordar Pokémon |
| KAN-053 | Cinnabar Island | História do laboratório e possibilidade de restaurar fósseis |
| KAN-054 | Pokémon Mansion | Pistas científicas sobre experimentos e surgimento de Mewtwo |
| KAN-055 | Cinnabar Gym / Blaine | Perguntas e combate do líder especialista em Fogo |
| KAN-056 | Viridian Gym / Giovanni | Revelação do líder final e último confronto pela insígnia |
| KAN-057 | Professor Oak / progresso | Avaliação do avanço da Pokédex e mudanças após novos marcos |

### 5.6. Liga Pokémon, campeão e pós-jogo

| ID | Local / personagem | Assunto do diálogo (resumo em PT-BR) |
|---|---|---|
| KAN-058 | Route 23 | Conferência das insígnias para acesso ao desafio final |
| KAN-059 | Victory Road | Batalhas de preparação e obstáculos antes da Liga |
| KAN-060 | Elite Four / Lorelei | Apresentação da integrante e batalha de alto nível |
| KAN-061 | Elite Four / Bruno | Filosofia de treinamento físico e combate com sua equipe |
| KAN-062 | Elite Four / Agatha | Comentários sobre o Professor Oak e batalha especializada |
| KAN-063 | Elite Four / Lance | Apresentação do especialista em Dragão e sua equipe |
| KAN-064 | Champion / rival | Revelação do campeão e última batalha da campanha principal |
| KAN-065 | Hall of Fame | Reconhecimento da conquista e registro da equipe vencedora |
| KAN-066 | Laboratório / Oak | Expansão do projeto de pesquisa e atualização da Pokédex |
| KAN-067 | Cerulean Cave | Exploração pós-jogo e presença de um Pokémon lendário |

### 5.7. Ilhas Sevii

| ID | Local / personagem | Assunto do diálogo (resumo em PT-BR) |
|---|---|---|
| SEV-001 | One Island / Celio | Apresentação do sistema de comunicação e pedidos técnicos |
| SEV-002 | Mt. Ember | Exploração vulcânica e busca por uma gema importante |
| SEV-003 | Two Island / Game Corner | Procura por uma criança desaparecida e pedido de ajuda |
| SEV-004 | Three Island | Conflito com motoqueiros que ocupam o local |
| SEV-005 | Berry Forest | Resgate e reencontro familiar após uma situação perigosa |
| SEV-006 | Four Island | Novos encontros com o rival e avanço de missão na região |
| SEV-007 | Icefall Cave / Lorelei | Ajuda contra integrantes da Equipe Rocket |
| SEV-008 | Five Island / Rocket Warehouse | Acesso a um armazém e desmantelamento de operações Rocket |
| SEV-009 | Resort Gorgeous / Lost Cave | Busca por uma pessoa e exploração de salas com regras de navegação |
| SEV-010 | Six Island / Dotted Hole | Descoberta de artefato e conflito com criminosos |
| SEV-011 | Six Island / Pattern Bush | Exploração e encontros com treinadores em área de vegetação |
| SEV-012 | Seven Island / Trainer Tower | Desafios de batalha e comentários dos treinadores |
| SEV-013 | Tanoby Ruins | Mistério dos Unown e resolução de quebra-cabeça |
| SEV-014 | One Island / Celio | Finalização de consertos e habilitação de recursos de conexão |

### 5.8. Textos transversais e condicionais

Não esqueça de indexar também:

- NPCs que mudam de mensagem antes/depois de insígnias, eventos, derrotas e rematches;
- falas de treinadores **antes da batalha**, **após perder** e **quando abordados outra vez**;
- livros, cartazes, diários, computadores, máquinas e placas;
- Pokémon Centers, Poké Marts, Move Tutors, Day Care, pesca, troca e rede;
- mensagens de obtenção/perda de itens, falta de espaço na bolsa, armazenamento e cura;
- textos do tutorial de captura e de navegação da interface;
- escolhas **Sim/Não**, nomes dinâmicos, Pokémon presentes na equipe e eventos alternativos.

## 6. Estratégia de tradução fala a fala

1. **Extração:** inventariar todas as chaves literais possíveis, sem misturar textos de NPCs diferentes.
2. **Contexto:** quando necessário, ler `scripts.inc` e tabelas de eventos para descobrir quem fala, em que momento e sob qual condição.
3. **Tradução inicial:** aplicar inglês → português brasileiro em cada entrada, preservando variáveis dinâmicas.
4. **Revisão:** corrigir nomes, pronomes, termos de interface, ambiguidades e diálogos de humor.
5. **Ajuste visual:** dividir falas conforme largura, altura e número de linhas da caixa de texto do jogo de destino.
6. **Testes:** validar primeira visita, falas repetidas, escolhas, antes/depois de batalha, insígnias e pós-jogo.

## 7. Uso recomendado no fangame Dessastre Paradoxal

Para aproveitar esta pesquisa na implementação de Kanto:

- Guarde a **chave de origem** (`PalletTown_..._Text_...`) como referência histórica, mas não como identificador obrigatório do jogo novo.
- Crie um **ID de diálogo do projeto**, separado do texto exibido. Exemplo inventado: `kanto.pallet.oak.inicial.apresentacao`.
- Separe `locale/en` e `locale/pt-BR` para suportar idiomas e atualizações independentes.
- Trate escolhas, recompensas e batalhas como **eventos**, não como parte do texto traduzido.
- Evite copiar diretamente o roteiro para redistribuição pública sem a licença ou permissão aplicável; prefira roteiro original inspirado na progressão do jogo.
- Para o modo **Testar Kanto**, mantenha um verificador que sinalize IDs sem tradução, caixas que cortam texto e NPCs sem falas após um estado de missão.

## 8. Validação do inventário

Depois de gerar `FireRed_Dialogos_EN_PT.md`, confira:

- [ ] Quantas entradas foram extraídas, conforme contador do script.
- [ ] Se estão presentes `data/maps`, `data/text`, `.s` e `src`.
- [ ] Se os principais diálogos de Oak, rival, Giovanni, líderes e Liga aparecem.
- [ ] Se as Ilhas Sevii estão incluídas.
- [ ] Se a tradução preserva `{PLAYER}`, `{RIVAL}` e outras variáveis.
- [ ] Se há textos em outro idioma ou códigos de controle a revisar.
- [ ] Se todas as mensagens condicionais relevantes aparecem durante testes de jogo.
- [ ] Se houve correção manual do português e das quebras de texto.

**Fontes de estrutura (sem reprodução do roteiro):**
- https://github.com/pret/pokefirered
- https://github.com/pret/pokefirered/blob/master/data/event_scripts.s
- https://github.com/pret/pokefirered/tree/master/data/maps