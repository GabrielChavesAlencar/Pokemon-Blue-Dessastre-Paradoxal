# Johto — Etapa 11/16: Mahogany, Lake of Rage, Rocket HQ, Pryce e Radio Tower

**Situação: PARCIAL.** Código de eventos Ruby, contratos simbólicos e testes publicados. Não existem mapas RXDATA reais de Johto auditados, treinadores PBS compilados nem execução da fase no Game.exe.  
**Data:** 12/11/2026 · **Dependência:** [Etapa 10 — Jasmine/Ampharos](JOHTO_FASE_10_JASMINE_AMPHAROS_MINERAL.md) · [Acompanhamento](JOHTO_ETAPAS.md).

## Entregas técnicas

| Arquivo | Finalidade |
|---|---|
| [scripts/regions/JohtoMahogany.rb](../scripts/regions/JohtoMahogany.rb) | Regras Ruby para Rotas 42/43, Mahogany, Gyarados vermelho, Lance, base Rocket, Electrode, Pryce/GLACIER, Whirlpool, invasão de Goldenrod e Rota 44 |
| [tests/johto_mahogany_runtime.rb](../tests/johto_mahogany_runtime.rb) | Regressão Ruby com batalhas e itens simulados; derrota, fuga, captura, recompensas únicas, saves e mudança de regiões |
| [tests/test_johto_mahogany_runtime.py](../tests/test_johto_mahogany_runtime.py) | Integra teste Ruby ao Blue Studio |
| [data/regions/johto-phase11.json](../data/regions/johto-phase11.json) | Grafo *simbólico*, locais, equipes PBS futuras, critérios de aceitação e recursos ainda indisponíveis |
| [tests/test_johto_phase11_contract.py](../tests/test_johto_phase11_contract.py) | Validação de GLACIER/Whirlpool, número da insígnia, contratos de treinadores e bloqueio de importação sem mapas reais |

Nenhum desses arquivos é instalado como plugin no Decades/Kanto, altera o Game.exe, entrega Pokémon ao jogador ou atualiza mapas, saves ou a Bag real.

## Eventos e ordem implementados no módulo

### 1. Rota 42, Mahogany, Rota 43 e Lake of Rage

1. \`route42\`: exige **MINERAL de Johto** e Ecruteak visitada; registra uma só vez.
2. \`mahogany_arrive\` e \`route43\`: progridem até o lago, sem sobrescrever switches de regiões existentes.
3. \`lake_arrive\`: registra a chegada ao Lake of Rage.
4. \`red_gyarados_begin\` exige um **evento revisado** com Gyarados presente no catálogo e marcador exclusivo do piloto. Não chama \`pbWildBattle\` antecipadamente.
5. \`red_gyarados_result(:caught | :defeated)\` registra o encontro concluído **somente** após um adaptador de batalha real confirmar captura ou derrota. Fugir, perder, passar resultado desconhecido ou voltar ao save não marca conclusão. O código **não cria um Gyarados na party**.
6. \`red_scale\` oferece **uma** Red Scale caso o item e a entrega real tenham sido verificados. O identificador \`:REDSCALE\` é provisório.
7. \`lance_meeting\` depende do resultado do lago e da Red Scale recebida. Lance apresenta o problema da Equipe Rocket em Mahogany.

**Atenção:** os testes com resultados \`:caught\`/\`:defeated\` não provam que a versão atual do motor retorna esses símbolos. Antes de ativar a fase, um adaptador do jogo deve converter **resultados reais verificados** para esse contrato; nunca tratar qualquer retorno verdadeiro como captura/derrota.

### 2. Rocket Hideout

Sequência lógica programada:

- \`rocket_hq_enter\` após a conversa com Lance.
- \`hq_grunt(0)\`, \`hq_grunt(1)\`: ordem fixa e derrota sem avanço.
- \`hq_security_off\`: desligar o sistema de vigilância, condicionado a **evento de mapa auditado**.
- \`hq_door\`: dois grunts, segurança desligada e evento da porta verificado.
- \`hq_petrel\` → \`hq_lance_help\` → \`hq_ariana\`: encontros separados e idempotentes.
- \`hq_electrode_begin(index)\` / \`hq_electrode_result(index, resultado)\`: três Electrode do jogador, distintos, sem baixar flags em caso de fuga/derrota. Outro evento controlado representa Lance desativando seus três.
- \`hq_finish\`: só conclui após todos os três Electrode e a intervenção de Lance.
- \`whirlpool_reward\`: candidata a entregar \`:HM06\` **após** a conclusão do esconderijo, se o catálogo e o adaptador forem validados. Falha na entrega não cria flag de item recebido.

Os pisos B1F, B2F e B3F, pisos com alarme, estátuas, senhas, portas, gerador, sprites e movimentos dos NPCs estão planejados, mas **não construídos**. A batalha de Ariana com apoio de Lance é um **marcador de vitória lógico**, não uma implementação de combate em dupla. Equipes e parceiros precisam ser instalados em PBS e testados dentro do motor.

### 3. Ginásio de Pryce — GLACIER (7ª insígnia)

- \`pryce_ice_puzzle\`: exige que HQ esteja concluído, MINERAL local e marcador de puzzle físico auditado. Não cria o chão de gelo nem prova colisões.
- \`pryce\`: exige puzzle concluído, equipe PBS compilada e marcador \`BLUE_JOHTO_PRYCE_V1_READY\`.
- **Derrota:** não grava \`mahogany_pryce_defeated\`, não concede insígnia ou esmeralda.
- **Vitória:** \`BlueRegions.award(state, "JOHTO", "GLACIER")\`, única vez. A **7ª insígnia** soma uma esmeralda no cartão global pelo sistema existente, sem incremento manual.
- \`whirlpool_allowed?(tool_ready)\`: apenas **GLACIER local + uso real da ferramenta** dão permissão. Não usa badges de Kanto nem total global para ignorar pré-requisitos.

**Whirl Islands permanecem bloqueadas.** A função de entrada da [Etapa 10](../scripts/regions/JohtoJasmine.rb) continua retornando \`false\` mesmo quando GLACIER + HM estão disponíveis: não há warps nem saídas físicos comprovados. O programa não deve prender o usuário em caverna sem saída.

### 4. Goldenrod — invasão da Radio Tower e continuação para Route 44

Este arco só começa **após vencer Pryce**, conforme a sequência escolhida para o piloto:

\`radio_takeover\` → \`radio_petrel\` → \`radio_rival\` → \`radio_underground_puzzle\` → \`radio_director_rescue\` → \`radio_executive(0,1,2)\` → \`radio_finish\`.

A batalha do rival usa a versão 0/1/2 compatível com o inicial do laboratório de Elm. Os executivos estão reservados como Proton, Ariana e Archer. A chave real do Underground, Card Key, elevadores, salas, portas, interruptores e restauração da transmissão **não estão implementados**. A flag do Diretor serve apenas para progressão futura; **nenhum item Key é inventado ou entregue no código**.

\`route44\` só sinaliza a próxima etapa depois de GLACIER e da Radio Tower liberada. **Não efetua teleporte.** O caminho físico e Ice Path virão na Etapa 12.

## Marcadores de prontidão exclusivos do piloto

| Área | Arquivo esperado | Regra |
|---|---|---|
| Gyarados | \`Data/blue-johto-lake-ready.txt\` | \`BLUE_JOHTO_LAKE_V1_READY\` |
| Red Scale | \`Data/blue-johto-red-scale-ready.txt\` | \`BLUE_JOHTO_RED_SCALE_V1_READY\` |
| Trainers HQ | \`Data/blue-johto-rocket-hq-ready.txt\` | \`BLUE_JOHTO_ROCKET_HQ_V1_READY\` |
| Senhas/segurança HQ | \`Data/blue-johto-rocket-hq-puzzle-ready.txt\` | \`BLUE_JOHTO_ROCKET_HQ_PUZZLE_V1_READY\` |
| Electrode | \`Data/blue-johto-electrode-ready.txt\` | \`BLUE_JOHTO_ELECTRODE_V1_READY\` |
| Whirlpool | \`Data/blue-johto-whirlpool-item-ready.txt\` | \`BLUE_JOHTO_WHIRLPOOL_ITEM_V1_READY\` |
| Pryce PBS e gelo | \`Data/blue-johto-pryce-ready.txt\` + \`Data/blue-johto-pryce-puzzle-ready.txt\` | Tokens específicos de cada área |
| Radio Tower PBS/puzzle | \`Data/blue-johto-radio-tower-ready.txt\` + \`Data/blue-johto-radio-puzzle-ready.txt\` | Tokens específicos de cada área |

**Nenhum desses marcadores foi instalado.** Só o futuro instalador de Johto poderá criá-los **após** provar que recursos correspondentes realmente funcionam. Uma flag de prontidão é uma defesa operacional, não uma prova independente.

## Treinadores, Master Mode e bloqueios

As entradas PBS reservadas (ainda **não compiladas**) são \`BLUE_JOHTO_HQ_GRUNT\` v0/1, \`BLUE_JOHTO_HQ_PETREL\` v0, \`BLUE_JOHTO_HQ_ARIANA\` v0, \`BLUE_JOHTO_PRYCE\` v0, \`BLUE_JOHTO_RADIO_PETREL\` v0, \`BLUE_JOHTO_RADIO_RIVAL\` v0/1/2 e \`BLUE_JOHTO_RADIO_EXEC\` v0/1/2. Treinadores comuns e demais grunts deverão ser inventariados no pacote real.

A implementação final deve usar os **hooks de balanceamento de Decades**, incluindo normal e Master Mode com quatro Pokémon e 90% segundo as regras do projeto, sem calcular níveis fictícios diretamente nos eventos.

As duas páginas de cartão de treinador devem refletir **GLACIER no cartão de Johto** e sua contribuição de **+1** ao total mundial de esmeraldas. O total é calculado por \`BlueRegions.crystal_total\`, não por um contador isolado do Rocket HQ.

## Mapas simbólicos

[johto-phase11.json](../data/regions/johto-phase11.json) contempla:

**Ecruteak → Route 42 → Mahogany → Route 43 → Lake of Rage.**

O arquivo também relaciona Rocket HQ B1F–B3F, a loja/casa de fachada, Centro Pokémon/Mart/Ginásio de Mahogany, saída Route 44, Goldenrod Radio Tower 1F–5F e Underground/Warehouse. **São nomes de locais, não MapIDs, nem warps instalados.** A continuidade Goldenrod → Mahogany e o retorno seguro devem ser testados com MapInfos/tilesets reais, sem substituir IDs de Kanto/Decades.

## Verificações

\`\`\`powershell
python -m unittest discover -s tests -p "test_johto_mahogany_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase11_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
\`\`\`

Os testes simulados validam viagens com a região ativa, ordem dos Rocket Grunts/executivos, marcador inexistente ou inválido, batalha perdida, Red Gyarados fugido, Electrode não resolvido, recompensa com \`pbReceiveItem\` falha, GLACIER única, Whirlpool com e sem ferramenta, Radio Tower bloqueada antes de Pryce e save/reload sem recompensas duplicadas.

## Aceitação integral pendente

- [ ] Receber Map Pack autorizado, fixar SHA-256, créditos e tilesets utilizáveis.
- [ ] Auditar e remapear MapIDs verdadeiros; ligar portas/andares/portarias de ida e volta.
- [ ] Compilar PBS para Rockets, rival, Pryce e NPCs das rotas com balanceamento de Decades e Master Mode.
- [ ] Testar no motor verdadeiro callbacks de batalha de Red Gyarados/Electrode (captura, derrota, fuga, derrota do jogador) e o item Red Scale.
- [ ] Construir puzzle dos Rockets, alarme, senhas, porta, gerador, parceiro Lance e Ice Gym com colisões reais.
- [ ] Conferir item real de Whirlpool, GLACIER, uso regional de campo, save/reload e bloqueio seguro das Whirl Islands.
- [ ] Finalizar eventos físicos da Radio Tower, chaves e elevadores, música e sequência de lutas; não confundir flags simuladas com eventos jogáveis.
- [ ] Verificar portas, encontros selvagens e acesso à Route 44 após conclusão da Radio Tower.
- [ ] Observar 1 vitória sem dupla recompensa e 1 derrota sem prêmio de Pryce, com cartões Johto/global.
- [ ] Reexecutar CI Blue Studio, piloto Kanto, saves Decades e testes Windows/JoiPlay antes de marcar a etapa concluída.

**Barras oficiais:** 0/16 núcleos totalmente aceitos; 0/16 jogabilidade integralmente aprovada. A fase 11 está **PARCIAL**, mesmo após os testes de lógica.
