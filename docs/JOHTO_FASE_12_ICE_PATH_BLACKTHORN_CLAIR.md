# Johto — Etapa 12/16: Ice Path, Blackthorn, Clair e Dragon's Den

**Estado:** PARCIAL — núcleo Ruby, regressões automatizadas e contrato de mapas *simbólicos* publicados. **Não jogável no Game.exe.**  
**Data:** 12/11/2026  
**Dependência:** [Etapa 11 — Mahogany/Pryce/Radio Tower](JOHTO_FASE_11_MAHOGANY_ROCKET_PRYCE.md)  
**Acompanhamento:** [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md) · [Plano mestre](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)

## Entregas publicadas

| Arquivo | Conteúdo |
|---|---|
| [scripts/regions/JohtoBlackthorn.rb](../scripts/regions/JohtoBlackthorn.rb) | Núcleo isolado: Route 44 → Ice Path → Blackthorn, quatro rochas e Strength, Waterfall, ginásio, Clair, Dragon's Den, Dragon Master, RISING, Route 45/46 e handoff à Liga |
| [tests/johto_blackthorn_runtime.rb](../tests/johto_blackthorn_runtime.rb) | Regressão Ruby com batalha simulada, inventário simulado, perguntas, saves, derrotas/vitórias, permissões por insígnia e isolamento Kanto/Decades |
| [tests/test_johto_blackthorn_runtime.py](../tests/test_johto_blackthorn_runtime.py) | Integra a suíte Ruby de Blackthorn aos testes do Blue Studio |
| [data/regions/johto-phase12.json](../data/regions/johto-phase12.json) | Contrato de locais e ligações **sem IDs RXDATA**, recursos de puzzle, equipes PBS futuras e itens não confirmados |
| [tests/test_johto_phase12_contract.py](../tests/test_johto_phase12_contract.py) | Confere continuidade da fase 11, RISING como 8ª insígnia, Waterfall/Whirlpool/Strength e proibição de aceite fictício |

**Nenhum** script foi instalado no jogo Decades ou no piloto Kanto. A fonte externa de mapas Johto permanece sem arquivo auditado, hash e MapIDs; o código só será ativado quando um piloto isolado com mapas e PBS reais passar nos testes correspondentes.

## Fluxo da história implementado

### Route 44 → Ice Path

1. **Entrada da Route 44:** \`route44\` exige as **sete insígnias anteriores de Johto**, \`goldenrod_radio_tower_cleared\` e \`route44_ready\` produzida ao final da fase 11.
2. **Entrada da Ice Path:** \`ice_path_enter\` exige marcador exclusivo do piloto validado. A passagem real ainda não foi construída.
3. **Gelo:** \`ice_slide\` registra apenas um checkpoint de puzzle físico que o futuro evento RMXP deve verificar. O movimento deslizante, os tiles, colisões e escadas **não** estão implementados por essa flag.
4. **Strength:** \`ice_boulder(index, tool_ready)\` aceita quatro índices distintos (0–3), não inventa ordem física e exige **PLAIN de Johto + ferramenta disponível**, conforme a API \`BlueRegions.field_access\`. Exige um marcador independente de puzzle de rochas instalado.
5. **Waterfall:** \`waterfall_item\` prepara a concessão única de \`:HM07\` como **chave candidata, não auditada**, somente se o catálogo real e o adaptador \`pbReceiveItem\` confirmarem entrega e o marcador local for válido. A técnica **não** pode ser usada antes de RISING, mesmo que esteja na Bag.
6. **Saída da Ice Path:** \`ice_path_exit\` exige slide + quatro rochas e mapa verificado; não efetua warp. O mapa verdadeiro pode ter entradas/saídas/soluções diferentes, a confrontar com o pacote RMXP antes de registrar sucesso.

### Blackthorn City e Ginásio de Clair

- \`blackthorn_arrive\` registra a chegada após Ice Path.
- \`clair_gym_puzzle\` é **apenas o checkpoint** do futuro quebra-cabeça do ginásio (plataformas giratórias em HGSS). Não cria pisos, switches ou rotas por programação.
- \`clair\` exige puzzle e sete insígnias locais, treinador PBS \`BLUE_JOHTO_CLAIR\` v0 realmente compilado e marcador auditado. **Perder não avança nada.**
- **Vencer Clair NÃO entrega RISING.** A vitória apenas grava \`blackthorn_clair_defeated\` e inicia a ida obrigatória à Dragon's Den.

### Dragon's Den e Dragon Master

1. \`dragons_den_enter\`: exige vitória contra Clair e evento real da entrada validado. Não concede a insígnia.
2. \`dragon_shrine_access(tool_ready)\`: exige entrada na Den, Whirlpool adquirido de Lance na fase 11, **GLACIER local + ferramenta real**, e marcador de mapa. O acesso físico ao santuário ainda não está montado.
3. \`dragon_master_trial\`: três perguntas originais de relacionamento treinador/Pokémon. Resposta errada/cancelar não conclui o teste. A versão de referência é **HeartGold/SoulSilver**; a variante Crystal e a possível exigência de Dragon Fang precisam de análise e implementação separadas.
4. \`clair_rising_badge\`: após vitória contra Clair, chegada ao santuário e aprovação do Dragon Master, a conversa posterior com Clair chama **\`BlueRegions.award(state, "JOHTO", "RISING")\`** uma única vez. Nada é concedido por entrar no ginásio, vencer a batalha ou passar pela Den sem prova.

A RISING é a **8ª insígnia de Johto**. O cartão local deve mostrar 8 badges e o cartão mundial recebe mais **uma esmeralda** pelo cálculo existente \`BlueRegions.crystal_total\`. Nenhum evento faz \`total += 1\` manualmente.

### Oitava insígnia, especiais e acesso à Liga

- \`waterfall_allowed?(tool_ready)\`: exige RISING **local + ferramenta real**. Nenhuma badge de Kanto substitui a RISING.
- \`specials_unlocked?\` consulta **\`BlueRegions.allow_specials?(state, "JOHTO")\`** somente para a região ativa. Após 8 badges, a regra global atual prevê a autorização local de lendários, míticos, Ultra Beasts e paradoxos; **isso não instala o controle de party/Box no piloto nem libera espécies antes de sua integração**.
- \`route45\`/\`route46\` apenas registram visitas. As conexões físicas, encontros e portarias de **Dark Cave** continuam pendentes. \`dark_cave_entry\` retorna sempre \`false\`.
- \`league_handoff\` verifica as 8 badges, Clair/Dragon Master e Radio Tower; grava **apenas** \`johto_league_approach_ready\` para a **Etapa 13**. Não atravessa Tohjo Falls, não termina a Liga, não ativa Hall of Fame nem desbloqueia outra região ficticiamente.

## Mapas e sistemas pendentes

[Contrato simbólico da Etapa 12](../data/regions/johto-phase12.json):

**Mahogany → Route 44 → Ice Path (1F/B1F/B2F/saída) → Blackthorn**, com Centro Pokémon, Mart, ginásio, Dragon's Den, Shrine e ramificações planejadas Route 45/46/Dark Cave.

Os nós são **nomes de planejamento** e não MapIDs, coordenadas, conexões efetivas ou uma prova de que Ice Path tem exatamente essa estrutura no pacote fonte. As portas reais, descidas, rochas, pisos deslizantes, trainer NPCs, sprites e encontros devem ser auditados antes de importar e preservar Decades/Kanto.

**Marcadores do piloto ainda inexistentes:** \`BLUE_JOHTO_ICE_PATH_V1_READY\`, \`BLUE_JOHTO_ICE_BOULDERS_V1_READY\`, \`BLUE_JOHTO_WATERFALL_ITEM_V1_READY\`, \`BLUE_JOHTO_BLACKTHORN_GYM_V1_READY\`, \`BLUE_JOHTO_BLACKTHORN_PUZZLE_V1_READY\`, \`BLUE_JOHTO_DRAGONS_DEN_V1_READY\`, \`BLUE_JOHTO_DRAGON_MASTER_V1_READY\`. Eles **não devem** ser criados apenas para contornar as proteções.

**PBS ainda não compilados:** Clair e as equipes do ginásio, treinadores de Ice Path e Dragon's Den. Usar o balanceamento **real** de Decades, com as regras já configuradas do Master Mode (quatro Pokémon, níveis e cobertura), sem inserir times fictícios.

## Verificações automatizadas

\`\`\`powershell
python -m unittest discover -s tests -p "test_johto_blackthorn_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase12_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
\`\`\`

Os testes cobrem isolamento regional, sequência da Route 44, marcadores de mapas/puzzles inválidos, boulders incompletos, Strength/Whirlpool com e sem ferramenta, Waterfall sem e com badge, entrega única do HM, derrota de Clair, vitória sem prêmio, teste do Dragon Master errado/cancelado/correto, RISING única, habilitação local dos especiais, save/reload e handoff da Liga sem prêmio prematuro.

**Passar nesses testes sintéticos NÃO valida o Game.exe.** A equipe de Clair, os mapas, colisões e a Bag da instalação real ainda não foram verificados.

## Critérios para declarar 12/16 integralmente concluída

- [ ] Obter e auditar fonte legítima de mapas/tilesets com SHA-256, direitos e créditos; remapear IDs sem sobrescrever Kanto/Decades.
- [ ] Integrar Ice Path com gelo deslizante, quatro rochas reais, escadas, passabilidade e retorno garantido.
- [ ] Validar HM Waterfall no catálogo e o método de adicionar/remover itens da versão real do motor.
- [ ] Compilar equipes PBS de Clair e treinadores (normal/Master Mode) com nível/escala de Decades.
- [ ] Fazer o puzzle físico do ginásio, batalha de Clair, derrota sem badge e vitória que **não** dê RISING antecipadamente.
- [ ] Testar entrada, uso real de Whirlpool e Dragon Shrine; resposta errada/correta à prova do Master e entrega **exatamente única** da 8ª insígnia.
- [ ] Conferir as duas páginas de treinador e os oito badges locais; testar restrição/liberação de especiais e viagem com Box e saves separados.
- [ ] Implementar Route 45/46/Dark Cave com warps bidirecionais auditados; não ativar cavernas sem saída.
- [ ] Comprovar handoff à Liga sem permitir teleporte a Tohjo Falls/Indigo Plateau antes da Etapa 13.
- [ ] Executar regressões Blue Studio/Kanto e jogar o percurso no Game.exe Windows e JoiPlay.

**Progresso oficial:** barra integral 0/16; barra de gameplay 0/16; fases 01–12 **parciais**.
