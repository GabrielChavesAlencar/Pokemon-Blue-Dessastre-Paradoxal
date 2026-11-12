# Johto — Etapa 04 (continuação): primeira história em New Bark Town

**Data:** 12/11/2026  
**Estado:** núcleo Ruby de eventos implementado e protegido; **sem mapas reais, ligação a NPCs ou Game.exe de Johto jogável**. A Etapa 04 continua **PARCIAL**.  
**Plano:** [16 etapas](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) · [Progresso](JOHTO_ETAPAS.md)

## Arquivos adicionados ao GitHub

- [scripts/regions/JohtoPilot.rb](../scripts/regions/JohtoPilot.rb): primeiro núcleo dos eventos de Johto, **exclusivo de um futuro piloto isolado**.
- [tests/johto_pilot_runtime.rb](../tests/johto_pilot_runtime.rb): simula Ruby/Essentials sem mapas ou assets.
- [tests/test_johto_story_runtime.py](../tests/test_johto_story_runtime.py): executa o teste Ruby no conjunto de testes Python.
- [scripts/regions/prepare_johto_source.py](../scripts/regions/prepare_johto_source.py): prepara um pacote ZIP original em pasta temporária e ignora scripts/EXE.
- [tests/test_johto_source_prepare.py](../tests/test_johto_source_prepare.py): usa ZIPs artificiais para testar extração, hashes, traversal, links, isolamento e imutabilidade.

## Primeiros eventos da história preparados

| Local de Johto (destino futuro) | Evento e função Ruby | Estado |
|---|---|---|
| Casa do jogador, New Bark | Mãe: `BlueJohtoPilot.mother` | Função pronta; interior e interação ainda pendentes |
| Laboratório de Elm | Introdução: `BlueJohtoPilot.elm` | Função pronta; ligação ao NPC pendente |
| Laboratório de Elm | Escolha de Chikorita, Cyndaquil ou Totodile: `BlueJohtoPilot.choose_starter` | Regra pronta, nível 5, bloqueio de duplicação |
| Rota inicial / rival | `BlueJohtoPilot.rival` | Função pronta, mas batalha **bloqueada** até três versões reais de treinador no PBS do piloto |
| Progressão regional | `$PokemonGlobal.blue_regions["johto_pilot"]` | Persistência isolada do estado; não usa flags de Kanto nem do Decades |

**Rival:** a escolha lógica adotada neste protótipo é Chikorita → Cyndaquil (versão 0), Cyndaquil → Totodile (versão 1), Totodile → Chikorita (versão 2). Só autorizar o combate quando o piloto tiver compilado os três registros `BLUE_JOHTO_RIVAL` e criado o marcador local `Data/blue-johto-rival-ready.txt` com conteúdo `BLUE_JOHTO_RIVAL_V1_READY`. Esse arquivo **não foi criado no jogo**. Os scripts **não** importam dados de batalha ou eventos do Map Pack automaticamente.

**Integridade:** as funções recusam execução fora de uma campanha cujo estado regional seja `JOHTO`; escolha de inicial cancelada ou malsucedida não grava espécie. Repetir diálogo não concede outro inicial e a batalha não repete depois do evento registrado. O arquivo Ruby não é carregado automaticamente no jogo principal.

## Entrada da fonte ZIP sem risco de importação

O Map Pack original não está versionado no repositório; obtê-lo por fonte legítima e manter apenas localmente. Colocar um **ZIP** em `.blue-work/johto-source/original.zip` (se vier RAR, descompactar manualmente e auditar, sem executar programas).

Execute a partir da raiz do projeto, **sem mexer em game/**:

```powershell
python scripts/regions/prepare_johto_source.py --archive ".blue-work/johto-source/original.zip" --output ".blue-work/johto-source/project"
python scripts/regions/audit_johto.py --source ".blue-work/johto-source" --archive ".blue-work/johto-source/original.zip" --game "game" --output ".blue-work/johto-audit.json"
```

A primeira linha **não baixa nada nem habilita Johto**; aceita um único projeto RMXP por pacote e extrai somente `Data/Map*.rxdata`, `MapInfos.rxdata`, `Tilesets.rxdata` e PNGs em `Graphics/Tilesets` e `Graphics/Autotiles`. Rejeita atalhos/symlinks e caminhos de travessia de pastas. Não traz `Game.exe`, scripts, outras ferramentas, músicas nem saves. O SHA do pacote é informado para preenchimento **após revisão manual**, sem presumir direitos de distribuição.

Se houver múltiplos projetos RMXP no ZIP, o importador recusa em vez de misturar mapas de Kanto e Johto. Extrair o conteúdo confiável manualmente em outra subpasta isolada e executar o auditor na pasta que contém um único `Data/`.

**A etapa de mapeamento** exige conferir nomes reais de `MapInfos.rxdata`, distinguir mapas de Kanto presentes no mesmo pacote, escolher símbolos `JOHTO_*` e criar a prévia com `plan_johto.py`, `stage_johto.py` e `verify_johto.py`, conforme [Etapa 03](JOHTO_FASE_03_PREVIA_SEGURA.md).

## Próximos arquivos que dependem da fonte real

1. Casa do jogador e quarto com interior de New Bark (colisões, escadas, porta e spawn).
2. Exterior de New Bark, laboratório de Elm e portas bidirecionais validadas.
3. Eventos nos mapas ligados **explicitamente** às funções locais acima, sem copiar scripts externos.
4. Três equipes PBS do rival para os três iniciais; o código de evento só permite a batalha após o conteúdo ser efetivamente compilado.
5. Montador de `.blue-work/johto-pilot` com Game.exe em cópia separada, `Johto pilot.json`, música protegida e `mkxp.json` com diretório de saves exclusivo.
6. Só então criar `JOHTO_JOGAR_EXPERIMENTAL.bat`, ativando o botão **Testar Johto** no mesmo menu de Testar Kanto. Antes disso, o botão permanece como aviso de preparação.

## Testes e prova

```powershell
python -m unittest discover -s tests -p "test_johto_story_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_source_prepare.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
```

Aprovado no teste de lógica Ruby **não implica** mapa jogável. Para aceitar integralmente a Etapa 04 é necessário executar no Game.exe a saída do quarto → laboratório de Elm → escolha do inicial → rival → save/reload, além dos testes de Kanto e Decades, sem regressões.

**Progresso técnico integral:** 0/16. **Aceite integral de jogabilidade:** 0/16. A Etapa 04 continua parcial porque depende da implantação e validação de mapas reais.
