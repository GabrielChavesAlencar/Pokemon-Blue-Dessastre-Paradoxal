# Sinnoh — Fase 03: os três times PBS de Barry e o level cap Blue

**Data:** 13/11/2026.  
**Estado:** ferramentas de geração e verificação estática prontas; **os PBS reais ainda não foram compilados na engine, os três combates ainda não foram executados e nenhum marcador de pronto foi criado**. Não instalar na campanha principal.

## 1. Escopo que já foi implementado

- [Gerador de equipes](../scripts/regions/build_sinnoh_barry_pbs.py), que exige uma **instalação local Blue com PBS**. Lê apenas os dados verdadeiros de `PBS/trainer_types.txt`, `PBS/pokemon.txt` e `PBS/moves.txt`. A equipe é independente de Johto e usa `BLUE_SINNOH_RIVAL` / treinador `Barry`.
- [Verificador offline](../scripts/regions/verify_sinnoh_barry_pbs.py), que exige que todos os dois PBS gerados mantenham seus SHA-256, que os três blocos de Barry permaneçam completos e que os arquivos nativos de origem e o código de balanceamento não tenham mudado.
- [Testes do gerador](../tests/test_sinnoh_barry_pbs.py) e [testes do verificador](../tests/test_sinnoh_barry_verify.py), utilizando somente PBS inventados para os testes. **Não incluem ROM, sprites proprietários ou arquivos de terceiro.**

### Relação exata entre o inicial do jogador e o time rival

| Versão de `BLUE_SINNOH_RIVAL` | Inicial do jogador | Pokémon de Barry | Golpes |
|---|---|---|---|
| 0 | Turtwig | Chimchar | Extraídos do `pokemon.txt` nativo até o nível inicial |
| 1 | Chimchar | Piplup | Extraídos do `pokemon.txt` nativo até o nível inicial |
| 2 | Piplup | Turtwig | Extraídos do `pokemon.txt` nativo até o nível inicial |

Cada versão é **um único Pokémon** neste encontro introdutório. Não copiar a composição dos treinadores do Ancient Platinum. Os golpes não são uma lista inventada: o gerador inspeciona o learnset real em `pokemon.txt` e verifica os golpes em `moves*.txt`. A construção falha se o Pokémon ou qualquer golpe não existir, se o tipo de treinador `RIVAL1` estiver ausente ou se `BLUE_SINNOH_RIVAL` já estiver registrado em outro PBS.

### Níveis: manter Blue, NÃO criar um sistema paralelo

`PBS/trainers_sinnoh_barry.txt` contém `Pokemon = <INICIAL>,5` apenas para representar o **nível-base técnico na serialização PBS**, não o nível final do encontro. O motor original do projeto já aplica `BlueCampaign.trainer_level` por meio de `BlueCampaign::Teams`, calculando o adversário a partir do maior Pokémon do jogador:

- Normal: **70%** da maior experiência em nível do time do jogador, com limites do motor.
- Master: **90%**, com a ampliação das equipes conforme as regras existentes do modo; nunca duplicar a lógica por região.
- A contagem global de insígnias/cristais, o estágio da campanha, as evoluções e os golpes adaptados continuam sob `BlueStory`, `BlueRegions` e `BlueTrainerMoves`.
- Este contrato é **checado estaticamente** no código de `scripts/battle_polish/Campaign.rb`. A aplicação real dele no Game.exe será comprovada na cópia experimental; a prévia PBS sozinha **não** certifica nível dinâmico.
- No site, **não** exibir nível fixo de Barry como se fosse o nível da batalha. Mostrar que segue o balanceamento Blue.

## 2. Como gerar os PBS na máquina local

Após conferir `game/PBS` da instalação verdadeira:

```powershell
python scripts/regions/build_sinnoh_barry_pbs.py --game game --output .blue-work/sinnoh-barry-pbs-v1
```

A ferramenta cria uma pasta **nova** com apenas `PBS/trainer_types_sinnoh_barry.txt`, `PBS/trainers_sinnoh_barry.txt` e `sinnoh-barry-pbs-report.json`. O relatório registra hashes dos três PBS nativos, SHA do contrato de balanceamento, três variantes, flags `pbs_compiled:false`, `battle_proven:false`, `ready_marker_created:false`, `can_install:false`.

**Verificação de integridade do draft (não compila PBS):**

```powershell
python scripts/regions/verify_sinnoh_barry_pbs.py --draft .blue-work/sinnoh-barry-pbs-v1 --game game
python -m unittest discover -s tests -p "test_sinnoh_barry*.py" -v
ruby tests/sinnoh_pilot_runtime.rb scripts/regions/SinnohPilot.rb
```

A segunda ferramenta rejeita um dos três treinadores ausente, hash alterado, learnset/nível-base trocado, mudança do `Campaign.rb`, alteração no `game/PBS` e presença indevida de `Data/blue-sinnoh-rival-ready.txt` no draft. **Nenhuma das duas escreve no `game/` ou libera o marcador.**

## 3. Integração e aceite exclusivamente na cópia isolada

1. Auditar MapIDs reais, direitos de mapa/sprite e arquitetura do piloto. O script legado [pilot_sinnoh.py](../scripts/regions/pilot_sinnoh.py) atualmente usa IDs **800–805**, que se sobrepõem à faixa **600–999 protegida para Johto** no planejador conservador. Isso pode ser aceitável em uma cópia totalmente independente, mas **não pode ser mesclado cegamente no mundo multi-regional**. O Codex deve conciliar ambos os caminhos e registrar a decisão antes de instalar qualquer mapa.
2. O piloto legado [SinnohPreview.rb](../scripts/regions/SinnohPreview.rb) apresenta uma escolha por diálogo com Rowan, enquanto o roteiro novo usa **três Poké Bolas físicas** e `BlueSinnohPilot`. **Não usar os dois plugins ao mesmo tempo** sem refatoração consciente, auditoria de eventos e teste de compatibilidade de saves.
3. Copiar os fragmentos gerados **somente** para uma nova cópia de QA do Game.exe; compilar PBS no Essentials real e confirmar `GameData::Trainer` com ``BLUE_SINNOH_RIVAL,Barry,0/1/2` e uma equipe em cada versão. Validar sprite do treinador no catálogo local.
4. Confirmar no Game.exe que `TrainerBattle.start(:BLUE_SINNOH_RIVAL, "Barry", version)` lê cada versão, com a espécie contrária correta, sem importação dos eventos do jogo doador.
5. Testar time jogador com níveis e insígnias distintos, tanto em Normal (70%) quanto Master (90%). Inspecionar o **nível final em batalha**; manter o nivel-base 5 só para PBS. Conferir se o modo Master aumenta a equipe conforme as regras compartilhadas.
6. Testar vitória, derrota com `canLose`, save/load, não duplicar starter, não repetir rival e retorno a Decades, Kanto, Johto e Hoenn. Salvar logs e screenshots fora de áreas versionadas.
7. **Somente após todos os testes**, documentar os hashes reais compilados e criar o arquivo `Data/blue-sinnoh-rival-ready.txt` com conteúdo `BLUE_SINNOH_BARRY_V1_READY` **exclusivamente dentro da cópia de QA**, nunca na instalação principal. O gerador não tem essa função deliberadamente.

**Checklist para aprovar I07 (ainda NÃO aprovado):** três PBS compilados, três espécies e golpes verificados, sprite, marcador no QA, balanceamento 70%/90% testado, save/load sem regressões. Uma verificação Python bem-sucedida **não** substitui o QA no jogo.

## 4. Progresso correto

- As ferramentas e o draft de Barry são um trabalho de **código**; não implicam que o jogo agora possua equipes compiladas.
- No [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md), a introdução Twinleaf/Sandgem mantém **5/8 subetapas completas** até as auditorias e a integração nativa; o trabalho de PBS pode ter uma barra interna própria.
- As 13 fases técnicas/jogáveis/QA permanecem em **0/13** até haver demonstração real de funcionalidade.
