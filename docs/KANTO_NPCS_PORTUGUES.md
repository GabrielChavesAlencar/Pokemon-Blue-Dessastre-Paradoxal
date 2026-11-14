# Kanto — traduzir NPCs de ambientação para português (pt-BR)

## Objetivo e limite de escopo

O piloto de Kanto importa **NPCs simples sem efeitos de missão** das coordenadas originais do Essentials FRLG. Os eventos são adaptados por `scripts/regions/kanto_overworld.py`; antes desta etapa, suas falas continuavam em inglês, pois o catálogo normal do Blue não contém necessariamente os textos da fonte FRLG.

**Este processo não traduz NPCs especiais, ginásios, treinadores, escolhas ou eventos não implementados.** Não altera comandos do evento, flags, equipes, scripts, colisões, posição, nome do Pokémon ou disponibilidade de HMs. Preserva o idioma inglês e a campanha principal Decades.

A fonte com o texto real está em `.blue-work/frlg-source/Essentials FRLG/Data/MapXXX.rxdata`, no **computador do jogador**. O repositório público não contém transcrições completas desses diálogos. Portanto, não é correto anunciar 100% de tradução antes de gerar os relatórios com a fonte instalada.

## Fluxo recomendado no Windows

1. Atualize a `main` pelo `Blue-Story.exe` e abra uma vez **Testar Kanto** para ter uma cópia válida do piloto.
2. Na pasta `%LOCALAPPDATA%\PokemonBlueDessastreParadoxal`, execute **`KANTO_TRADUZIR_NPCS_PTBR.bat`**. O BAT seleciona Python 3.10+, usa o Argos Translate instalado (ou tenta instalar via pip), obtém localmente o modelo inglês → português quando necessário e traduz os textos dos NPCs realmente presentes no inventário do piloto. Esse procedimento exige internet para baixar o tradutor/modelo na primeira vez; depois ele pode funcionar offline.
3. O BAT grava a tabela de tradução **somente em** `.blue-work/kanto-npc-ptbr.json`, registra pendências de revisão em `.blue-work/kanto-npc-ptbr-review.json` e reconstrói uma cópia experimental nova via `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`.
4. No jogo, abra **Opções → Language / Idioma → Português (Brasil)**. Fale com os novos NPCs. O idioma inglês continua disponível.
5. Confira, na pasta da **cópia mais recente**, `Data/blue-kanto-npc-translation-audit.json`: informa a contagem real de NPCs, frases únicas, frases localizadas e o que ainda está em inglês. Para revisão textual manual, use o `kanto-npc-ptbr-review.json` local.

Se o modelo Argos ou o pip não puder ser instalado pelo Python portátil, instale o Python 3.10+ com pip e execute novamente o BAT, sem apagar as pastas `.blue-work`, os arquivos da fonte FRLG ou os saves.

## Segurança técnica

- O script `scripts/regions/translate_kanto_npcs.py` lê **somente** `npc_dialogue` que foram realmente aceitos pelo importador anterior, referenciando MapID/EventID exatos, sem executar scripts Ruby da origem.
- Traduções oficiais/locais já existentes em `Data/blue-pt-br.dat` são preservadas. O projeto autoral mantém controle separado em `scripts/battle_polish/Locale.rb`, incluindo chaves de nome próprio.
- O processo automático **não traduz** falas com códigos de controle, placeholders, substituições dinâmicas ou strings Ruby com escape não trivial; elas ficam marcadas para revisão, sem texto inventado.
- O catálogo local passa por validação de códigos/variáveis. A construção registra e ignora entradas inválidas em vez de quebrar o piloto. Apenas textos de NPCs importados podem ser mesclados ao `blue-pt-br.dat` da **cópia isolada**.
- **Textos extraídos do jogo e traduções integrais ficam em arquivos locais ignorados pelo Git**, não são enviados para o repositório.
- Traduções automáticas podem ter termos pouco naturais, erros de gênero ou nomes alterados; **precisam de revisão jogando**. Não devem ser contabilizadas como falas integralmente aprovadas.

## Testes e diagnóstico

- `python -m unittest tests.test_kanto_npc_locale -v`: extração literal segura, conservação de comandos, idioma português da cópia isolada, segurança de controles e não interferência no Decades.
- `python -m unittest tests.test_kanto_overworld -v`: itens, NPCs, rochas e Moon Stone.
- `python -m unittest discover -s tests -v`: regressão geral.
- `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`: reconstrução e verificação estrutural completas, dependentes da fonte original auditada. Os testes headless não substituem jogar no Windows/JoiPlay.
- Em caso de falas ainda em inglês, examine `Data/blue-kanto-npc-translation-audit.json → missing_english_lines_by_npc` da última cópia e não use o texto GBA como se fosse uma chave de evento RPG Maker.
