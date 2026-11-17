# Sinnoh G08 — Rowan, três Poké Bolas, Barry e nível dinâmico (GitHub-only)

**17/11/2026.** Entrega somente de código, testes e auditoria de contratos públicos. Não lê mapas ou PBS reais da instalação do usuário, não compila nada no `Game.exe`, não cria marcadores de aprovação nem modifica os saves.

## Escopo comprovável por código

A [matriz G08](../scripts/regions/audit_sinnoh_g08_opening_qa.py) reconcilia os contratos de **CH06, G07, S13, S14, CH08, S17, CH12 e CH15** sem substituí-los.

| Passo | Evento autoral / regra | Situação |
| --- | --- | --- |
| 1. Mãe | `mother_intro` após iniciar em Twinleaf | Checkpoint em código; evento físico não instalado |
| 2. Barry | `barry_intro` depois da mãe | Checkpoint em código |
| 3. Rowan | `rowan_briefcase_seen` depois de Barry, no Lago Verity | Checkpoint em código |
| 4. Inicial | **Três objetos físicos** `SN_BALL_TURTWIG`, `SN_BALL_CHIMCHAR`, `SN_BALL_PIPLUP` | Verificação de escolha única, sem diálogo que concede Pokémon; sprites/posição reais pendentes |
| 5. Rival | `rival_fought` somente após uma batalha confirmada, incluindo `false` de derrota `canLose` | Ruby fixture; batalha real pendente |
| 6. Pokédex | `pokedex_received` só depois do confronto de Barry e de acesso ao campo real do jogador | Ruby fixture; evento nativo pendente |

### Versões do PBS (somente rascunho)

| Bola escolhida | Pokémon do Barry | Versão `BLUE_SINNOH_RIVAL,Barry` | Nível no arquivo PBS |
| --- | --- | --- | --- |
| Turtwig | Chimchar | 0 | seed 5 |
| Chimchar | Piplup | 1 | seed 5 |
| Piplup | Turtwig | 2 | seed 5 |

A G08 **não cria** novos PBS ou uma equipe rival fixa. Reutiliza o gerador e o verificador já existentes: [build_sinnoh_barry_pbs.py](../scripts/regions/build_sinnoh_barry_pbs.py) e [verify_sinnoh_barry_pbs.py](../scripts/regions/verify_sinnoh_barry_pbs.py). O teste Python usa PBS sintéticos em diretório temporário e confirma SHA, versões 0/1/2 e ausência do marcador de liberação. **Os PBS da instalação real, seus moves, o sprite do Barry e a compilação Essentials continuam não verificados.**

## Matriz de nove cenários

O [teste Ruby G08](../tests/sinnoh_g08_opening_runtime.rb) carrega o `SinnohPilot.rb` **real do repositório** sobre uma engine falsa, sempre isolada em um diretório temporário. Para cada um dos três iniciais, testa:

- **Vitória `true`:** escreve checkpoint `rival_fought`, cura a equipe, libera evento de Pokédex e proíbe repetir a batalha.
- **Derrota confirmada `false` com `canLose`:** mesma progressão prevista de roteiro, sem tratar derrota válida como falha de execução.
- **Resultado `nil`:** não marca batalha, não cura, não concede Pokédex; um novo resultado confirmado pode ser tentado depois.

O teste também comprova **nas fixtures**: não receber inicial antes de Rowan, falha no `pbAddPokemonSilent` sem escrita parcial, nenhuma segunda Poké Bola, versão oposta correta, ausência de batalha sem autorização, rejeição de equipe PBS falsa (espécie, seed ou quantidade), persistência após serialização de save em memória e ausência de escrita regional ao visitar Kanto, Johto, Hoenn e Decades.

O arquivo de marcador de Barry é criado **exclusivamente durante a simulação em uma pasta temporária** e apagado. Nenhum marcador de liberação é criado pelo auditor ou no jogo. Uma autorização de teste em Ruby **não substitui** o comprovante do clone QA real.

## Balanceamento: reutiliza BlueCampaign

| Modo | Referência | Escala | Observação |
| --- | --- | --- | --- |
| Normal | Maior nível **não ovo** no time do jogador | `floor(nível × 70%)` | Não grava níveis fixos no PBS |
| Master | Maior nível não ovo, estágio de campanha 3 | `floor(nível × 90%)` | Amplia equipes pequenas para 4, dentro do limite global 6 |
| Ambos | Motor de batalha Blue | limites 1..máximo do motor | Evolução/espécies e política de boss continuam sob os contratos CH12/S17 |

Os testes Ruby usam as implementações **reais do repositório** `BlueCampaign`, `BlueStory` e `BlueEvolutionScaling`, com Pokémon/treinadores sintéticos. O estágio Master e suas insígnias não devem ser confundidos com um level cap numérico fixo por região. **O seed 5 do PBS de Barry não é o nível final em batalha**.

## Arquivos da entrega e CI

- [Auditor cruzado G08](../scripts/regions/audit_sinnoh_g08_opening_qa.py): status `ROWAN_BARRY_OFFLINE_CONTRACTS_CROSSCHECKED_NATIVE_BATTLE_PENDING`, matriz de 9 cenários e flags que nunca alegam aprovação nativa.
- [20 testes Python G08](../tests/test_sinnoh_g08_opening_qa.py): falsos MapIDs, atalhos na história, alteração de versões, PBS adulterado, desvio do 70%/90%, level cap fabricado, guardas Ruby suprimidas, falha segura e privacidade.
- [Teste Ruby G08](../tests/sinnoh_g08_opening_runtime.rb): três escolhas × três resultados de combate, persistência e proteção entre regiões.
- [Workflow G08](../.github/workflows/sinnoh-g08-opening-qa.yml): jobs Python e Ruby que também reexecutam as suítes S13/S14/CH08 e S17 anteriores. Publica **apenas matriz JSON de metadados**, sem fontes doadoras, PBS reais, saves ou Game.exe.

Comandos de teste no checkout do repositório:

~~~bash
python scripts/regions/audit_sinnoh_g08_opening_qa.py
python -m unittest discover -s tests -p 'test_sinnoh_g08_opening_qa.py' -v
ruby tests/sinnoh_g08_opening_runtime.rb scripts/regions/SinnohPilot.rb scripts/regions/SinnohIntroContracts.rb scripts/regions/SinnohStarterContracts.rb
~~~

## Pendências que G08 não encerra

1. Vínculo físico entre os 9 mapas de Twinleaf e os 54 terrenos B07, com MapIDs, warps, posições e passabilidade reais.
2. Autorização de redistribuição dos recursos utilizados e verificação dos sprites.
3. Três variantes de Barry efetivamente **compiladas** no `GameData::Trainer` do clone, com golpes/sprite auditados e execução da batalha.
4. Testar vitória/derrota, save/load, 70%/90% e transições no Game.exe **somente após B10/B11** e depois no Android/JoiPlay.
5. Validar R07/R08/R09; **B/C/D permanecem 0/13**.

**Próxima entrega — G09:** auditoria de progressão, ginásios, HMs, Elite Four e Cynthia por contratos, sem criar lutas ou níveis nativos inexistentes.
