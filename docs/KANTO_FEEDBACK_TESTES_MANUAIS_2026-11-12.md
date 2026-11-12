# Kanto — feedback de teste manual (12/11/2026)

**Origem:** arquivo enviado pelo usuário `tetes de mapas.txt`. Registro literal do conteúdo informado, com nomes de locais normalizados para facilitar o checklist. Este documento **não** equivale a aprovação completa de fase.

## 1. Locais percorridos no teste

O usuário informou ter testado os seguintes locais:

- [x] Pallet Town — visitado/testado
- [x] Rota 1 — visitada/testada
- [x] Rota 2 — visitada/testada
- [x] Viridian City (referida como "veridian") — visitada/testada
- [x] Viridian Forest (referida como "veridian florest") — visitada/testada
- [x] Pewter City — visitada/testada
- [x] Rota 4 — **somente lado esquerdo** testado
- [x] Mt. Moon — visitada/testada (andares e eventos **não especificados**)

**Interpretação:** "[x]" nesta seção significa **apenas que o jogador informou ter passado pela área**, não que portas, colisões, NPCs, batalhas, capturas, save/reload ou todas as conexões estejam aprovados. O TXT não identifica versão exata do executável, coordenadas de falhas, andares da caverna nem resultados por local. Não fechar as etapas 02/03/07/08 só com esta lista.

## 2. Pendências descritas pelo jogador

### KANTO-MAN-01 — Entradas de casas e estabelecimentos internos

> "falta ligar os estabelecimentos internos as casas"

**Prioridade:** alta. Auditar **porta por porta** em todas as áreas importadas: residência, Centro Pokémon, Poké Mart, laboratório, portarias, ginásios e outros interiores presentes. Exigir transferência correta do exterior para o interior **e de volta**, coordenadas dentro do mapa, direção de saída, colisão/trigger apropriados e nenhum teletransporte para ID do Decades por engano.

**Aceite:** lista de entradas/saídas por `source_map_id,event_id`, cobertura bidirecional no verificador, caminhada real atravessando cada porta e retorno, testes em save novo e existente; não substituir interiores por telas genéricas que escondam os mapas.

### KANTO-MAN-02 — Treinadores devem iniciar os combates previstos

> "falta colocar os eventos dos treinadores não deixar eu passar antes de enfrentar eles"

**Prioridade:** alta. Para treinadores de rota e ginásio com linha de visão prevista, implementar gatilho de aproximação/linha de visão, direção, alcance, detecção de obstáculos e disparo único. Em **pontos de história explicitamente obrigatórios**, impedir o jogador de avançar até iniciar/concluir o confronto conforme a regra do evento original; **não tornar todo treinador opcional um bloqueio obrigatório sem auditar a fonte**. Registrar vitória por mapa + evento, preservar derrota/revanche e manter as regras de balanceamento Blue; impedir repetição de premiação.

**Aceite:** em caminhada real, cada treinador da amostra reage ao jogador; barreiras de progressão só desaparecem quando o requisito for satisfeito; derrotas não registram vitória; save/reload restaura flags corretas; nenhum treinador dispara através de paredes.

### KANTO-MAN-03 — Telas de insígnias regional e geral

> "falta fazer um layount com as insegenas de kanto e um layount com todas as gerações com insegneas"

**Prioridade:** média; requisito de interface. Criar **duas visualizações** no jogo e, opcionalmente, espelhar no portal:

1. **Insígnias de Kanto:** oito posições com nome/ícone quando houver recurso autorizado, estado conquistada/não conquistada, contagem `0/8` a `8/8`, e líder/local correspondente. Ler as conquistas persistidas `BlueRegions.local_achievements(state, "KANTO")`; não conceder badges pela tela.
2. **Circuito de regiões/gerações:** visão consolidada por região das conquistas locais + progresso global Blue. Identificar ginásios convencionais (Kanto/Johto etc.), as provas de Alola e as esmeraldas/marcos de Decades sem inventar insígnias onde não existem. Hisui precisa de categoria de marcos própria. Exibir bloqueios regionais e progresso por região, com o mesmo save e sem somar duas vezes.

**Aceite:** visual consistente com a UI existente, navegação por controle/teclado e mouse, atualização após obter insígnia e após recarregar, persistência, correspondência do total com o balanceamento Blue, legibilidade no Windows e JoiPlay. Não modificar contador global por desenhar o layout.

## 2.1. Análise do código atual (causas prováveis, não correções aplicadas)

A inspeção de [pilot.py](../scripts/regions/pilot.py) e [kanto-source.json](../data/regions/kanto-source.json) aponta causas técnicas coerentes com o relato:

- **Interiores ausentes:** `extract_warps(event, mapping)` ignora a transferência quando o mapa de destino não pertence ao catálogo regional atual. O manifesto ainda não inclui diversas casas e outros interiores do FRLG. Assim, o importador simplesmente descarta parte das portas, mesmo que elas existam na fonte; precisamos auditar os IDs de destino de cada entrada e importar os interiores autorizados.
- **Treinadores sem visão/agressão automática:** em `install_events`, os NPCs de batalha criados a partir de `TRAINERS` recebem `new_event(..., trigger=0, actor(event))`. Esse valor corresponde à ativação por ação/interação, não a um sistema de alcance/linha de visão. O importador também fixa `@move_type = 0` em todos os eventos adaptados e reduz as páginas para uma só, perdendo comportamentos originais dependentes de páginas e condicionais. O teste nativo chama diretamente as funções de batalha, sem reproduzir a aproximação do jogador.
- **UI de insígnias:** o estado de conquistas por região já existe em `BlueRegions`, porém o pedido é uma nova camada visual: duas telas distintas lendo esse estado. Não há evidência no TXT de que essa interface exista ou esteja correta.

**Conclusão técnica:** os problemas MAN-01 e MAN-02 têm explicações plausíveis na implementação atual. Ainda faltam testes em sessão gráfica para demonstrar cada falha/solução em coordenadas concretas. Esta análise **não muda código de gameplay nem declara os defeitos corrigidos**.

## 3. Relação com as 16 etapas

- **02 — Caminhada real:** recebeu **evidência parcial de percurso**; segue aberta até teste real dos elementos internos e os demais cenários do checklist.
- **03 — Corrigir Pallet → Pewter:** registrar os problemas MAN-01 e MAN-02 como bloqueadores de aceite.
- **07 — Mt. Moon/Cerulean:** testes manuais de Mt. Moon informados, mas sem detalhamento por andar, batalha ou aprovação; não marcar concluída.
- **08 — Vermilion/Lt. Surge:** não há declaração de testes manuais do novo trecho no TXT.
- **09–16:** reaplicar a auditoria de interiores, gatilhos e layout em cada expansão regional, sem tratar esses problemas como falhas já corrigidas.

**Contadores nesta data:** Barra 1 **8/16 (50%)** implementadas experimentalmente; Barra 2 **1/16 (6,25%)** aceita integralmente. O feedback **não** muda essas barras.

## 4. Ordem recomendada antes do fechamento de Kanto

1. Corrigir/validar portas e interiores (MAN-01) no percurso já visitado.
2. Corrigir gatilhos e barreiras de treinadores (MAN-02) com regressão no trajeto Pallet → Pewter / Mt. Moon.
3. Implementar as duas telas de progresso (MAN-03) sem alterar a lógica de badges.
4. Pedir verificação manual específica dos três itens acima e registrar resultados por mapa e evento.
