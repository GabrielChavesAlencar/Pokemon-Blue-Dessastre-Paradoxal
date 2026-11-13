# Johto — Etapa 14/16: lendários, Bell Tower, Whirl Islands e pós-jogo

**Estado: PARCIAL — contratos Ruby, testes e topologia simbólica publicados; nada instalado no Game.exe.**  
**Data:** 13/11/2026  
**Anterior:** [Etapa 13 — Liga Johto](JOHTO_FASE_13_LIGA_ELITE_FOUR_LANCE.md) · **Controle:** [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md).

## Arquivos criados

| Arquivo | Finalidade |
|---|---|
| [scripts/regions/JohtoLegendaries.rb](../scripts/regions/JohtoLegendaries.rb) | Núcleo isolado: versão escolhida, Raikou/Entei, cinco Kimono Girls, Wings/Bells, Bell Tower, quatro entradas Whirl, Lugia/Ho-Oh, Ruins of Alph e eventos que permanecem fechados |
| [tests/johto_legendaries_runtime.rb](../tests/johto_legendaries_runtime.rb) | Teste Ruby de progressão e recompensas, derrotas/fugas, rematch auditado, save/reload, três variantes e isolamento Kanto/Decades |
| [tests/test_johto_legendaries_runtime.py](../tests/test_johto_legendaries_runtime.py) | Executa o teste Ruby na CI do Blue Studio |
| [data/regions/johto-phase14.json](../data/regions/johto-phase14.json) | Contrato simbólico de Bell Tower/Whirl/Ruins, versões e itens, mapas ainda ausentes e critérios completos de aceite |
| [tests/test_johto_phase14_contract.py](../tests/test_johto_phase14_contract.py) | Verifica a integridade do plano, as diferenças HGSS/Crystal, bloqueios e ausência de MapIDs inventados |

Todos os marcadores de prontidão em \`Data/blue-johto-*\` são **nomes futuros**, não arquivos instalados. Somente um instalador de piloto isolado, após validar mapas, itens, APIs e encontros, poderá criá-los.

## 1. Versões e diferenças importantes

A chave \`johto_pilot["johto_campaign_version"]\` aceita **HEARTGOLD**, **SOULSILVER** e **CRYSTAL**. \`choose_version\` exige um marcador de versão validada e impede alterar o valor depois da primeira escolha. **O jogo principal não possui essa seleção de Johto instalada**; não existe versão presumida.

| Variante | Lendário principal | Fluxo previsto | Outro lendário |
|---|---|---|---|
| HeartGold | **Ho-Oh** | Rainbow Wing + Clear Bell, Kimono Girls, Bell Tower | Lugia após a Liga, Silver Wing e Whirl Islands |
| SoulSilver | **Lugia** | Silver Wing + Tidal Bell, Kimono Girls, Whirl Islands | Ho-Oh após a Liga, Rainbow Wing e Bell Tower |
| Crystal | **Suicune** | Narrativa distinta envolvendo Eusine/Tin Tower | Sem reaproveitar indevidamente as cerimônias HGSS |

Os identificadores de item \`:RAINBOWWING\`, \`:SILVERWING\`, \`:CLEARBELL\`, \`:TIDALBELL\` são **provisórios**. A rotina de concessão exige \`GameData::Item.exists?\` e \`pbReceiveItem == true\`; a cerimônia verifica também se os itens estão de fato na Bag.

**Diferença canônica a resolver antes da integração:** em HGSS, a cerimônia e o encontro do mascote **ocorrem antes** da ida à Liga. A Etapa 13 deste projeto já preparou um handoff à Liga sem impor esse evento. Na instalação HGSS definitiva, adicionar um requisito de mascote por versão ao handoff de Johto, com testes de captura/derrota/fuga, **sem alterar saves existentes de Kanto/Decades**. A Etapa 14 não muda retroativamente o script da Liga enquanto mapas/callbacks não forem verificados.

Referências: [Nintendo — folheto oficial HGSS](https://www.nintendo.com/eu/media/downloads/migration_1/BROCHURE_POK_GOLD_SILVER_PT.pdf), [Bulbapedia — versões HGSS](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_HeartGold_and_SoulSilver_Versions).

## 2. Burned Tower, Raikou, Entei e Suicune

A Etapa 08 já produz \`burned_tower_beasts_awakened\` depois da vitória contra o rival e da sequência de despertar.

- \`register_roamer(:RAIKOU | :ENTEI, :registered)\` **só registra o estado lógico** após marcador e confirmação de que o motor realmente criou o roamer. Não implementa encontros em grama, rotas, localização aleatória, deslocamento, persistência de HP/status ou sprites.
- \`roamer_result(species, :fled | :lost)\` não registra captura nem remove o roamer.
- \`:caught\` marca definitivamente capturado; o código não adiciona Pokémon na party nem no Box por conta própria.
- \`:defeated\` marca \`awaiting_verified_rematch\`. \`reactivate_roamer\` requer Johto com Hall of Fame concluído e um retorno **específico de rematch confirmado pelo motor**, não basta recarregar o jogo. Não reativa um já capturado.
- **Suicune HGSS**: a cadeia de Eusine e o encontro de **Route 25 em Kanto** não estão instalados; \`hgss_suicune_route25\` retorna \`false\`.
- **Suicune Crystal**: a sequência especial de Tin Tower/Eusine é outra; \`crystal_suicune\` também retorna \`false\` até análise do cenário real.

**Não considerar os testes sintéticos como um motor de roaming.** As condições de encontro e movimento precisariam ser ligadas aos encontros efetivos do jogo com saves persistentes e sem permitir duplicação.

## 3. Kimono Girls, Bell Tower e Whirl Islands

\`kimono_girl(index)\` reserva cinco treinadoras \`BLUE_JOHTO_KIMONO_GIRL\`, versões **0–4**, com vitória obrigatória na ordem. Exige oito insígnias locais, conclusão da Radio Tower, Wing no inventário e PBS autorizado. Derrota não avança. \`kimono_bell_reward\` entrega o Bell correto **uma vez**, com confirmação de item. \`kimono_ritual\` registra a cerimônia apenas com as cinco vitórias e os itens corretos em mãos.

\`bell_tower_enter\` e \`bell_tower_roof\` são **checkpoints de história**. Não inserem os andares, pisos, warp, NPCs, texturas ou efeitos da Bell Tower. Além do marcador da torre, exigem um marcador **independente de saídas seguras auditadas**.

\`whirl_entrance("NW"|"NE"|"SW"|"SE", surf_tool, whirl_tool)\` exige Route 41, HM obtido, **FOG/Surf**, **GLACIER/Whirlpool**, entrada real auditada e saídas de retorno. \`whirl_chamber\` apenas marca o destino lógico. A entrada física mantida bloqueada na [Etapa 10](../scripts/regions/JohtoJasmine.rb) **não foi habilitada**: um piloto real deverá vincular os novos eventos somente após provar mapas, saídas e colisões.

\`legendary_begin(:HOOH | :LUGIA)\` exige a espécie realmente no catálogo, marcadores de mapa/batalha e pré-requisitos distintos por versão. O principal depende da cerimônia; o secundário exige Liga de Johto concluída e Wing correspondente. \`legendary_result\` aceita apenas resultado real de captura ou derrota, após um combate autorizado. Fugir/perder não conclui o encontro. Espécie capturada não reaparece, e um encontro derrotado só pode ser rearmado após **rematch de Hall of Fame verificado**.

**Não há chamada \`pbWildBattle\`**, nem Pokémon criado ou concedido, nem nível/moveset fictício. Antes da instalação verificar como o Essentials do projeto retorna captura, desmaio, fuga, blackout e resultado de save; gerar adaptadores por tipo sem assumir que qualquer valor \`true\` significa captura.

## 4. Ruins of Alph e Unown

\`ruins_enter\` exige mapa auditado. \`ruins_puzzle(0..3)\` prepara quatro checkpoints simbólicos independentes, sem repetir puzzles já resolvidos. \`unown_research_ready?\` informa somente que pelo menos um puzzle foi registrado.

**Ainda faltam**: desenhos dos quatro puzzles, mapas e interiores, interações de HM, janelas dos alfabetos Unown, encontros e formas da Dex, puzzles de saída, rádio/som e testes de colisão. Não foram acrescentados Unown falsos ao jogo, à Dex ou às tabelas de encontro.

## 5. Pós-jogo e recursos deliberadamente bloqueados

**Bug-Catching Contest, Pokéathlon, Mt. Silver e Red** não são simulados como jogáveis: os respectivos métodos retornam \`false\`. Mt. Silver está explicitamente ausente no Map Pack de Johto, conforme [johto-source.json](../data/regions/johto-source.json). Só criar a área se houver **mapas com direitos verificados** ou mapas originais documentados.

A lógica de equipes de líderes/Elite/Campeões mais fortes após concluir **todas** as regiões permanece centralizada em \`BlueRegions.world_champion?\` e \`BlueRegions.profile\`. **Nenhuma equipe rematch foi compilada nesta fase**, nem é permitido burlá-la com uma flag de Johto. A regra das oito insígnias locais para Pokémon lendários/míticos/Ultra Beasts/paradoxos e o depósito no Box ao trocar de região permanecem responsabilidades do sistema regional e da Etapa 16.

## 6. Testes automatizados

\`\`\`powershell
python -m unittest discover -s tests -p "test_johto_legendaries_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase14_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
\`\`\`

A suíte Ruby simula versões HGSS/Crystal, roamer capturado/derrotado/fugido, Wings e Bells não duplicados, cinco batalhas Kimono, Ho-Oh e Lugia no timing correspondente, quatro entradas possíveis, exigência de saídas seguras, Ruins, save/reload e isolamento Kanto/Decades. A suíte de contrato confirma que **nada disso é um mapa instalado**.

## 7. Critérios de aceite integral ainda pendentes

- [ ] Auditar fonte legítima, licenças, hashes, MapIDs e conexões **reais** de Bell Tower, Whirl Islands, Burned Tower e Ruins of Alph.
- [ ] Implementar e testar 4 entradas de Whirl Islands com saídas de retorno, colisões, correntes e navegação; provar que o jogador não fica preso.
- [ ] Validar tabelas de roaming de Raikou/Entei, persistência e reativação pós-Hall of Fame sem ressuscitar capturados.
- [ ] Implementar Kanto Route 25 com Eusine/Suicune e ramificação exclusiva de Crystal, sem combinar narrativas.
- [ ] Auditar códigos reais dos Wings/Bells e compilar Kimono Girls com balanceamento normal/Master Mode do Decades.
- [ ] Ligar cerimônias de mascotes às batalhas reais, com retorno claro de captura, desmaio, fuga e derrota.
- [ ] Definir e testar a correção de ordem do encontro obrigatório de HGSS antes da Liga, preservando campanhas anteriores.
- [ ] Instalar puzzles e encontros reais dos Unown, além de arte, efeitos, música e verificações de Dex.
- [ ] Criar Mt. Silver/Red somente com mapas de origem comprovada e times/sistema pós-Liga verificados.
- [ ] Verificar rematches de campeão mundial, Box/party restritos por região, dois cartões de treinador, saves e CI.
- [ ] Testar visualmente no Game.exe Windows e JoiPlay. Não habilitar a área por sucesso exclusivo de teste Ruby.

**Barras oficiais:** 0/16 integral técnico; 0/16 gameplay integral. Etapa 14 **PARCIAL**, aguardando pacote de mapas.
