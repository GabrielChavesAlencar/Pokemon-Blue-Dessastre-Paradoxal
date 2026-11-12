# Kanto — harmonização Decades, Pallet e cartões regionais

Status: ajuste corretivo do **núcleo funcional 10/16**. Não contabilizar como uma nova etapa, e não marcar a etapa como integralmente aceita sem QA jogável.

## Regras globais (compartilhadas, sem duplicar engine)

| Esmeraldas totais | Estágio | Nível adversário | BST máximo | Power máximo |
| --- | --- | --- | --- | --- |
| 0–1 | Inicial | \`floor(maior_nível_sem_ovos * 0,70)\` | 350 | 60 |
| 2–4 | Intermediário | \`floor(maior_nível_sem_ovos * 0,70)\` | 450 | 90 |
| 5–10 | Avançado | \`floor(maior_nível_sem_ovos * 0,70)\` | 540 | Sem teto |
| 11+ | Master | \`floor(maior_nível_sem_ovos * 0,90)\` | Sem teto | Sem teto |

Limitar sempre níveis a 1..100. Pokémon selvagem: \`floor(maior_nível_sem_ovos * 0,45)\`; o Decades usa a mesma regra.

Fonte do cálculo: \`BlueStory.stage\`, \`BlueCampaign.trainer_level\`, \`BlueCampaign.wild_level\`, \`BlueStory.adjust\` e \`BlueTrainerMoves\`. **Não criar lógica paralela por região.** Essas rotinas já atuam nas batalhas de Kanto quando a campanha Story e os iniciais tradicionais estão ativados; testes Ruby verificam o contrato compartilhado.

**Contagem global:** \`cristais_do_Decades + soma(insígnias_distintas_por_região)\`. Uma insígnia da mesma região nunca conta duas vezes. Não escrever insígnias regionais nos flags nativos de Decades.

## Cartões de treinador

Menu de pausa: **Cartão do treinador · 2 páginas**.

1. **Região atual:** nome da região, insígnias locais desbloqueadas (ou cristais nativos se Decades), total mundial de esmeraldas e dificuldade calculada.
2. **Todas as regiões:** contagem individual das regiões do circuito e total global que determina o estágio.

Usar esquerda/direita para alternar, Voltar para sair. Cartão tradicional também mostra total global, não apenas Decades.

## Pallet Town e novo jogo

Fonte Essentials FRLG 1.1 (SHA-256 definido em \`data/regions/kanto-source.json\`), auditada em \`scripts/regions/audit_pallet_home.py\`:

- Pallet Map5 evento1 (casa do jogador) → Map7, com saída Map7 evento1 → Pallet.
- Pallet Map5 evento2 (casa do Blue) → Map8, com saída Map8 evento1 → Pallet.
- Pallet Map5 evento3 → laboratório Oak Map6, com saída Map6 evento1 → Pallet.
- As três entradas usam **Player Touch**, não botão de ação.
- Casa Map7 possui escadas internas eventos3/4; novo jogo surge no **quarto do andar superior**, Map7 (25,7), sem executar o evento de saída da casa.
- Eventos mínimos da mãe e Daisy usam diálogos de segurança locais, sem importar scripts estrangeiros.
- O NPC de viagem tem evento próprio na cidade (Pallet) e informa os bloqueios antes de concluir a Liga.
- Ao **viajar para Kanto** vindo de outra região, a chegada é **Pallet Town**, não o quarto; o início no quarto é exclusivo de Novo Jogo.

## Agentes regionais

- **Kanto:** Pallet Town, NPC local no evento9 (substitui um NPC secundário da fonte). O agente mostra região atual, desbloqueadas, e opções indisponíveis.
- **Decades:** Cherryhill City, mapa nativo 77. NPC criado apenas **em memória** na entrada desse mapa, sem modificar Map077.rxdata, apenas em campanha regional instalada. Usa o visual de NPC já existente na cidade e procura um tile livre/passável.
- Regiões ainda não instaladas: não criar agente físico em mapas ausentes. Quando um mapa inicial for realmente integrado, instalar o agente nessa cidade com o mesmo mecanismo e regressão.
- As viagens normais só são efetivadas após conclusão verificável da Liga e reservas seguras no PC, como antes. Não liberar regiões por simples interação com o NPC.

## Testes e critérios de aceite

- \`tests/region_cards_runtime.rb\`, \`tests/kanto_balance_runtime.rb\`: contagem sem duplicatas e escalonamento compartilhado.
- \`tests/test_kanto_installer.py\`: instalação transacional e marcador inicial novo sem alterar \`Game.exe\`, saves, Intro de Decades ou arquivos gráficos da base.
- \`scripts/regions/verify_pilot.py\`: entradas/saídas de Pallet, andar superior, NPC, marcadores.
- \`scripts/regions/KantoNativeCheck.rb\` e \`KantoIntegratedCheck.rb\`: prova na engine, início e troca de região.
- QA manual pendente: colisões nas casas, iniciais e Oak, transições, sprite do NPC em Cherryhill, menus em português e menus em Windows/JoiPlay.

**Limitações:** nenhum mapa de região não instalada é ativado por esta correção; não declara que todo conteúdo da campanha 16/16 foi completado.
