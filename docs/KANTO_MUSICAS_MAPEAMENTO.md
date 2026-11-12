# Kanto — análise individual das 64 músicas e organização por função

**Fonte:** conjunto de 64 MP3s enviado manualmente pelo proprietário do repositório nos commits `adicionando musicas de kanto p1` a `p7` de 12/11/2026.

**Verificação:** os 64 arquivos foram encontrados na raiz antes da correção, somando **135.768.381 bytes**. A comparação de SHA dos blobs Git com o pacote ZIP original confirma a integridade dos arquivos, sem necessidade de reencodificação.

**Classificação técnica:** deduzida pelo título de cada faixa e pela convenção RPG Maker XP/Pokémon Essentials, **não** por auditoria de reprodução de cada MP3. É uma sugestão funcional que precisa ser ligada aos eventos/mapas caso ainda não tenham seleção musical.

## Estrutura correta dentro do repositório

```text
assets/music/kanto/
├── BGM/        # 50 músicas contínuas (mapas, batalhas, abertura, créditos)
└── ME/         # 14 vinhetas e efeitos musicais de eventos
data/kanto-music.json  # catálogo, destino local, função, tamanho e SHA Git de cada arquivo
```

O jogo instalado usa **`game/Audio/BGM/Kanto/`** e **`game/Audio/ME/Kanto/`**, mas `game/` é ignorado pelo Git porque contém o Decades original e saves privados. Por isso os MP3s ficam versionados em `assets/music/kanto/`; o script de importação os copia para `game/Audio` sem sobrescrever os arquivos originais.

## Significado de cada faixa

Os números abaixo preservam os nomes do pacote recebido e ajudam a configurar mapas, cenas, NPCs e batalhas. Todas as músicas foram movidas sem modificar o conteúdo binário.

### BGM — 50 faixas

Trilhas contínuas de ambientação, eventos e batalhas. Inclui as vitórias de batalha, pois o plugin BlueMusic utiliza a biblioteca BGM nesses casos.

| Nº | Faixa original | Uso indicado no Kanto |
|---:|---|---|
| 02 | Opening Movie | Trilha da animação/cena inicial |
| 03 | Title Screen | Tela de título e menu principal |
| 04 | Game Tutorial | Tutorial e explicação de comandos |
| 05 | Welcome to the World of Pokémon! | Introdução do Professor Oak ao mundo Pokémon |
| 06 | Pallet Town | Tema ambiente de Pallet Town |
| 07 | Professor Oak | Diálogo e aparições do Professor Oak |
| 08 | Professor Oak's Laboratory | Interior do laboratório do Professor Oak |
| 10 | Rival Appears | Aparição do rival antes da cena ou duelo |
| 11 | Battle! (Trainer) | Batalhas normais contra treinadores |
| 12 | Victory! (Trainer) | Música de vitória contra treinador; manter no canal BGM para compatibilidade com BlueMusic |
| 13 | Road to Viridian City - Leaving Pallet Town | Rota 1, saída de Pallet em direção a Viridian |
| 15 | Pewter City | Tema ambiente da cidade de Pewter |
| 16 | Teachy TV Menu | Tela/menu da Teachy TV |
| 17 | Viridian Forest | Tema da Viridian Forest |
| 18 | Battle! (Wild Pokémon) | Combates contra Pokémon selvagens |
| 19 | Victory! (Wild Pokémon) | Música de vitória em encontro selvagem; usar canal BGM |
| 20 | Trainer Appears (Boy) | Tema de introdução de treinador masculino |
| 21 | Pokémon Center | Ambiente interno de Pokémon Center |
| 24 | Guide | Cena ou orientação de guia/tutorial |
| 25 | Pokémon Gym | Ambiente interno de ginásios Pokémon |
| 26 | Tense Battle! | Clima de tensão antes ou durante um confronto importante |
| 27 | Battle! (Gym Leader) | Batalhas contra líderes de ginásio |
| 28 | Victory! (Gym Leader) | Música de vitória contra líder; manter no canal BGM |
| 30 | Evolution | Trilha de animação de evolução |
| 32 | Road to Cerulean City - Leaving Mt. Moon | Rota 4, saída do Mt. Moon para Cerulean |
| 33 | Trainer Appears (Girl) | Tema de introdução de treinadora feminina |
| 34 | Mt. Moon | Tema de exploração do Mt. Moon |
| 35 | Vermilion City | Tema ambiente de Vermilion City |
| 36 | S.S. Anne | Tema de exploração do navio S.S. Anne |
| 37 | Cycling | Tema de deslocamento de bicicleta |
| 38 | Lavender Town | Tema ambiente de Lavender Town |
| 39 | Pokémon Tower | Tema de exploração da Pokémon Tower |
| 40 | Celadon City | Tema ambiente de Celadon City |
| 41 | Rocket Game Corner | Tema ambiente do Rocket Game Corner |
| 45 | Rocket Hideout | Tema de exploração do Rocket Hideout |
| 46 | Trainer Appears (Bad Guy) | Tema de entrada/aparição de antagonista |
| 47 | Silph Co. | Tema de exploração do prédio Silph Co. |
| 48 | Road to Fuchsia City - Leaving Lavender Town | Rota desde Lavender em direção a Fuchsia |
| 50 | Fuchsia City | Tema ambiente de Fuchsia City |
| 52 | Surfing | Tema de navegação com Surf |
| 53 | Battle! (Legendary Pokémon) | Batalha contra Pokémon lendário |
| 55 | Cinnabar Island | Tema ambiente de Cinnabar Island |
| 56 | Pokémon Mansion | Tema de exploração da Pokémon Mansion |
| 57 | Pokémon Net Center | Ambiente do Pokémon Net Center |
| 59 | Sevii Islands - Four Island - Five Island | Tema das Sevii Islands, Four Island e Five Island |
| 60 | Pokémon Jump | Trilha do minijogo Pokémon Jump |
| 70 | Final Battle! (Rival) | Confronto final contra o rival/Campeão |
| 71 | Epilogue | Trilha de epílogo após concluir a história |
| 72 | Hall of Fame | Tema do registro no Hall of Fame; BGM enquanto a tela estiver ativa |
| 73 | Staff Credits | Trilha de créditos finais |

### ME — 14 faixas

Vinhetas musicais curtas, prêmios, efeitos de interface e fanfarras pontuais. Não confundir com SE (ruídos e efeitos não musicais).

| Nº | Faixa original | Uso indicado no Kanto |
|---:|---|---|
| 01 | Game Freak Logo | Vinheta breve do logotipo na abertura |
| 09 | Obtained a Pokémon! | Vinheta ao receber um Pokémon |
| 14 | Obtained an Item! (Version 1) | Vinheta ao obter um item comum |
| 22 | Jigglypuff's Song | Canto musical de Jigglypuff em evento |
| 23 | Pokémon Healed | Vinheta de Pokémon restaurados no Centro Pokémon |
| 29 | Obtained a Gym Badge! | Vinheta de recebimento de insígnia do ginásio |
| 31 | Congratulations, Your Pokémon Evolved! | Vinheta de conclusão da evolução |
| 42 | Winning! | Vinheta ao ganhar em minijogo |
| 43 | Jackpot! | Vinheta de jackpot em minijogo |
| 44 | Pokémon Printer | Vinheta musical da impressora Pokémon |
| 49 | The Poké Flute | Execução musical da Poké Flute, usada em evento como Snorlax |
| 51 | Move Deleted | Vinheta ao apagar um movimento |
| 54 | Caught a Pokémon! | Vinheta ao capturar um Pokémon |
| 58 | Professor Oak's Evaluation | Vinheta de avaliação da Pokédex pelo Professor Oak |

## Aplicação automática por fases neste chat

Existe agora um [plano detalhado para aplicar as 64 faixas aos mapas, batalhas, eventos e cenas via ChatGPT](KANTO_PLANO_APLICAR_MUSICAS.md), com **Fases 0–6**, arquivos a modificar, critérios de aceite, cuidados de Kanto versus Decades e mensagens prontas para pedir a próxima fase. O plano ainda não representa os hooks de música implementados.

## Como importar para a instalação local do jogo

Após atualizar o projeto (`git pull`), execute na raiz:

```powershell
py -3 scripts/music/install_kanto_music.py --audit
py -3 scripts/music/install_kanto_music.py
py -3 scripts/music/install_kanto_music.py --apply
```

Ou execute **`INSTALAR_MUSICAS_KANTO.bat`** no Windows. A primeira verificação confere os **64 arquivos e hashes**; a segunda mostra a previsão do que será copiado; a terceira instala somente músicas ausentes e não sobrescreve arquivos diferentes. Se o áudio já estiver instalado com o mesmo hash, será reaproveitado.

Para aplicar também no piloto de Kanto, monte-o depois da instalação local — a cópia isolada leva consigo a pasta `Audio` da base. Uma cópia piloto existente não é alterada automaticamente.

**IMPORTANTE:** instalar os MP3s não troca automaticamente a música dos eventos dos mapas. O editor **Blue Studio → Editor de ROM → Músicas** pode selecionar os nomes `Kanto/1-xx...mp3` nos mapas ou nas batalhas. BGM de vitória foi intencionalmente mantido em BGM porque o plugin de seleção usa `Audio/BGM` para os temas de vitória.

**Licenças e distribuição:** o repositório é público e os MP3s aparentam ser trilhas originais de Pokémon. Não há comprovação de licença de redistribuição. Esta organização reutiliza os arquivos que já haviam sido enviados pelo dono do repositório, sem mudar direitos ou atribuir autoria; a disponibilidade pública deve ser revisada pelo responsável.
