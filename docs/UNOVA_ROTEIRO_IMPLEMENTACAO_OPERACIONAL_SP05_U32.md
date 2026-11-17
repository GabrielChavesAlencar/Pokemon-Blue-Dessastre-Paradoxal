# Unova — roteiro operacional de implementação: de Cheren ao jogo completo

**Pokémon Blue: Dessastre Paradoxal | 17/11/2026 | Alvo narrativo: Pokémon White / Black & White | Motor de destino: Decades + Essentials 21.1 / RMXP**

> **Situação verificada ao redigir:** ferramentas SP03, SP04 e SP05 publicadas na main, mas não há ZIP de sprites de Cheren auditado neste ambiente, nem documento de uso autenticado, nem arquivo MapInfos nativo da instalação local com reservas confirmadas para Unova. Não existe teste aprovado de Cheren no Game.exe/JoiPlay. Unova permanece PLANNED, jogável 0/32. Barras A/B/C/D = 0/8, E = 4/8. Este documento define o que fazer; não é implantação.

## 1. Objetivos e limites

**Meta de primeiro marco jogável:** poder iniciar em Nuvema em uma **cópia isolada de QA** do Game.exe, ver Cheren e Bianca na escala correta, conversar com eles, receber/selecionar inicial (Snivy, Tepig ou Oshawott), completar os eventos iniciais e chegar a Accumula Town/Route 1 sem softlocks; salvar/carregar e perder batalhas sem mudar de região acidentalmente. Só depois de QA e direitos, integrar o piloto ao instalador principal.

**Meta final:** incorporar Unova White ao mesmo Game.exe/sistema de saves do Blue com história, oito ginásios, Elite Four, N, Ghetsis, pós-jogo, Pokémon e ferramentas multi-regionais, sem quebrar Decades/Kanto/Johto/Hoenn/Sinnoh nem atualizar Unova para playable no site antes dos testes nativos.

**Não executar:** sobrescrita de Graphics/Characters de outras regiões, PBS de packs antigos, Scripts.rxdata v18, MapInfos global sem remap, saves ativos, duplicação de itens-chave/HMs, redistribuição automática de assets sem licença, mudança de status regional com base em testes sintéticos.

**Regra de evidência:** CI Python/Ruby é prova de contratos, não de funcionamento no Game.exe ou JoiPlay. Arquivos locais de crédito e o nome do fornecedor são pistas, não prova automática de direitos.

## 2. Insumos indispensáveis (gates, não estimativas)

1. ZIP do Gen 5 Overworld Pack (ou sprite alternativo de Cheren) obtido da fonte do autor, preservado privadamente, com hash original e termos de uso por arquivo. Fonte candidata: https://eeveeexpo.com/resources/25/.
2. Permissão de uso e, separadamente, autorização de redistribuição caso o Blue-Story/site vá empacotar o sprite. Se ausente ou restritiva, criar arte própria ou escolher recurso com termos compatíveis; não bloquear toda a implementação por depender de uma única fonte.
3. Pasta Graphics/Characters da instalação atual do Decades para medir o tamanho do NPC e do protagonista, e a versão/hash dessa instalação.
4. Cópia QA isolada e backups reais do Game.exe/MapInfos/mapas/PBS, saves exclusivos de teste e um baseline de regressão.
5. Fonte real editável para Nuvema, Route 1 e Accumula (Pokémon World V18 somente se o ZIP real contiver essas áreas e os direitos forem adequados) ou mapas próprios com tiles permitidos.
6. Manifesto de MapIDs ocupados da instalação real + reservas das regiões existentes; não escolher MapIDs a partir de intervalos teóricos.

## 3. Dependências e gates de aprovação

| Gate | Condição de entrada | Entrega verificável | O que continua proibido |
|---|---|---|---|
| G0 — Baseline protegido | SHA/árvore da main, instalação e backups reais | Matriz de arquivos protegidos + teste de rollback | Alterar Game.exe principal |
| G1 — Fonte do NPC | ZIP de sprite e direitos examinados | SP03 limpo, SP04 Cheren candidato, origem e direitos documentados | Publicar sprite sem permissão |
| G2 — Piloto sprite QA | G0 + G1 + referência Decades | SP05 4×4 com 16 quadros, escala/pivô revisados, sprite somente em QA | Afirmar NPC instalado no jogo |
| G3 — Piloto visual nativo | Cópia real do Game.exe + mapa QA existente e isolado | Cheren move/fala nos quatro sentidos, cena e save/reload testados em Windows | Integrar à main jogável só por screenshot |
| G4 — Nuvema real | MapInfos/mapa original ou próprio, tiles/autotiles e direitos | Cidade, casa e laboratório com eventos, portas e colisão reais | Usar IDs inventados ou transferências não revisadas |
| G5 — Começo White QA | G4, Route 1 e Accumula compatíveis | Juniper, iniciais, Cheren/Bianca, N, encontros, blackout, saves e agente local | Liberar Unova no Novo Jogo antes de teste |
| G6 — Campanha White completa | U08–U27 completas com dados verificados | 8 ginásios, Elite, Castelo de N, final e regras regionais testadas | Marcar fases jogáveis por catálogo/documentação |
| G7 — Release | G6, pós-jogo U28–U31, QA Win/Android e licenças | Manifesto incremental Blue-Story, rollback, downloads, site sem falsas pendências | Publicação silenciosa de assets terceiros |

**Gates são cumulativos.** Se um falhar, preservar a etapa anterior e deixar a implementação seguinte isolada.

## 4. Ordem de execução: 16 entregas de engenharia

### P01 — Proteção da baseline (executável agora com arquivos reais, parcialmente sem eles)

- Criar inventário de versões/SHAs do repositório e contratos de arquivos protegidos, sem incluir arquivos binários privados em commits.
- Estabelecer diretório de QA privado, separado do game principal e dos saves; backup/rollback verificáveis com comparação antes/depois.
- Rodar suíte Unova e regressões de Kanto, Johto, Hoenn, Sinnoh, Blue Studio/portal. Falha preexistente fica registrada e não deve ser atribuída automaticamente a Unova.
- **Aceite:** lista exata dos arquivos que podem mudar; relatório de rollback e jogos/saves principais intactos.

### P02 — Direitos e seleção do Cheren (G1)

- Executar UNOVA_AUDITAR_SPRITES.bat no ZIP real; gerar SP03 com hashes, formato, nomes e grade.
- Executar UNOVA_CATALOGAR_NPCS.bat; escolher apenas candidatos SP04 associados a UNOVA_NPC_CHEREN.
- Revisar visualmente se a arte representa Cheren da versão BW White, não um NPC genérico/B2W2, e identificar autor + origens derivadas + condições de uso/redistribuição.
- Preferir recurso autoral/licenciado quando a cadeia de direitos do pack não for suficientemente clara.
- **Aceite:** fonte/hashes verificáveis, sprite escolhido manualmente, direitos examinados; sem download público do pack.

### P03 — SP05: sprite, quadros e proporção (G2)

- Executar UNOVA_CHEREN_SP05_QA.bat com ZIP, relatórios SP03/SP04, comprovante e referência real Decades.
- Exigir PNG RGBA8 4×4: 16 quadros presentes, direção presumida down/left/right/up, pivô, alpha, pé e quadros parado/caminhada visualmente conferidos.
- Medir altura/largura **visíveis** contra NPC real Decades; guardas SP05 existentes: altura 0,80–1,20 e largura 0,80–1,25. Não redimensionar sem autorização/revisão de pixel art.
- Guardar só o sprite renomeado UNOVA_NPC_CHEREN.png e manifesto no QA local .blue-work/unova/qa/sp05-cheren/<hash>/.
- **Aceite:** relatório técnico + revisão visual assinada; sem afirmar que o arquivo funciona no Game.exe antes do G3.

### P04 — Preview nativo de Cheren, ainda sem Nuvema (G3)

- Na cópia QA, inspecionar um MapID já existente e passável, reservado **apenas para teste privado**; nunca inventar ID nem usar mapa vivo da main.
- Injetar um evento de teste isolado de NPC com sprite UNOVA_NPC_CHEREN, 4 direções, animação padrão, interação PT-BR curta, auto-repetição sem duplicação e flags de teste namespaced.
- Rodar lado a lado com o jogador e NPCs Decades em diferentes resoluções/zoom; verificar eixo dos pés, colisão, iluminação e save/reload. Documentar screenshot/log e versão.
- **Aceite:** Game.exe Windows realmente executado + piloto visual funcionando; mapa QA descartável removível por rollback. Android ainda não está automaticamente aprovado.

### P05 — Auditoria real de mapas e reservas (G4 pré-requisito)

- Usar o pipeline U02/E04/E05/E06: obter ZIP Pokémon World V18 se adequado, conferir MapInfos, MapNNN, eventos, tilesets, créditos; cruzar com as 74 áreas planejadas.
- Diagnosticar o MapInfos da **instalação Decades atual**, as regiões atuais e seus overlays; gerar proposta MapID fonte→MapID destino somente depois de conferir IDs desocupados.
- Mapas inexistentes na fonte devem ser marcados MISSING e recriados por editor/tiles permitidos, nunca fingidos como importados.
- **Aceite:** matriz de colidência vazia, fonte da geometria identificada, direito de tiles e objetos verificado, nenhuma mudança nativa ainda.

### P06 — Converter Nuvema para QA

- Instalar apenas em QA uma Nuvema com casa/quarto do jogador, laboratório, saídas, portais, eventos básicos, passabilidade, tileset/autotiles, BGM via BlueMusic e nomes PT-BR.
- Verificar todas as transferências pelo remap, spawn válido, porta reversível e nenhuma saída para mapa não instalado.
- Adicionar NPCs de Nuvema com nomes únicos; Cheren do P04 entra somente após direitos confirmados.
- **Aceite:** entrar e sair de casa/laboratório, conversar, atravessar cidade e salvar sem crash/softlock.

### P07 — Roteiro inicial White: Nuvema → Route 1 → Accumula (G5)

- Construir eventos autorais de Juniper, escolha do starter (Snivy/Tepig/Oshawott), Cheren, Bianca, primeira batalha e encontro com N, com diálogos PT-BR.
- Planejar e testar condições de progresso idempotentes: ao revisitar ou carregar, nenhuma recompensa ou item regional é concedido duas vezes.
- Integrar regras de escolha regional sem menus indesejados ao viajar para Decades, com itens-chave/HMs locais e Pokémon/boxes compartilhados.
- Validar encontros, cap, evoluções dinâmicas, XP compartilhada, modos de dificuldade e retorno ao Pokémon Center local.
- **Aceite:** jogador conclui o primeiro ciclo, salva/recarrega e segue viagem em QA, sem carregar flags de Kanto/Johto/Hoenn/Sinnoh indevidamente.

### P08 — Primeiro ginásio: Route 2, Striaton e Dreamyard

- Mapas e eventos auditados; líderes Cilan/Chili/Cress conforme inicial; primeiro badge, Cut local, personagens Fennel/Amanita, progressão sem softlock.
- **Aceite:** badge reconhecido uma vez; efeito HM e bloqueios corretos, revisitas e saves.

### P09 — Segundo e terceiro ginásios

- U09–U13: Route 3/Wellspring, Nacrene/Lenora/Pinwheel, Skyarrow/Castelia/Burgh, Route 4, deserto/Relic Castle.
- **Aceite:** 3 insígnias, Team Plasma coerente e referências de evento/trainer sem colisão.

### P10 — Quarto e quinto ginásios

- U14–U16: Nimbasa/Elesa, Route 5, Driftveil/Cold Storage/Clay. Validar grama, NPCs, progressão e mudanças após derrotar líderes.
- **Aceite:** 5 insígnias; impossibilidade de softlock nas pontes/gates.

### P11 — Sexto e sétimo ginásios

- U17–U22: Chargestone, Mistralton/Skyla, Celestial Tower, mar/rotas opcionais, Twist Mountain/Icirrus/Brycen/Dragonspiral.
- **Aceite:** 7 insígnias; Surf/HM locais, eventos do N, estações e retorno testados.

### P12 — Oitavo ginásio e acesso à Liga

- U23–U25: Relic Castle II/Tubeline/Opelucid; **Iris é líder na campanha White**, Drayden referência da variante Black; Route 10/Victory Road.
- **Aceite:** 8 insígnias, checkpoints e restrições de Pokémon especiais consistentes, acesso à Liga liberado corretamente.

### P13 — Elite Four, Castelo de N e final

- U26–U27: quatro salas, N, Zekrom na versão White, Ghetsis, créditos e estado de vitória. Definir retry após derrota, reentrada, saves seguros e regras de batalha/região.
- **Aceite:** final completo com reinício/retorno e nenhuma perda de progresso.

### P14 — Pós-jogo

- U28–U31: Looker/Sete Sábios, áreas orientais, White Forest, Giant Chasm, lendários, atividades opcionais, revanche Elite/Alder e guias completos.
- **Aceite:** eventos pós-jogo idempotentes, encontros/itens validados, português, música e portal com fonte auditável.

### P15 — Release Windows e Blue-Story (G7 parcial)

- Gerar overlay incremental de arquivos **novos ou efetivamente alterados**, com SHA antes/depois, allowlist, verificação de licenças, backup, rollback e instalação automática pelo Blue-Story; sem exigir PowerShell ou cópia manual de arquivos do usuário.
- NUNCA empacotar um asset cujo autor não permita o uso/distribuição pretendidos. Usar recurso próprio/licenciado em substituição.
- Testar Novo Jogo em Unova, Agente Regional em Nuvema, não repetir seleção do personagem ao entrar Decades, itens-chave regionais, save/reload, blackout e regressões de todas as regiões.
- **Aceite:** Windows Game.exe real testado, atualizador resiliente, manifesto assinado/validado e rollback comprovado.

### P16 — Android, portal e anúncio de Unova (G7 completo)

- Verificar instalador/update incremental Android via JoiPlay: caminho de arquivo, compatibilidade de PNG, scripts Ruby suportados, tilesets, saves persistentes, input e retorno inter-regional.
- Somente após QA real, publicar opção Android/Windows atualizada e alterar status de Unova no registro/portal de planned para o estado verdadeiramente comprovado (pilot/prototype/playable conforme cobertura).
- **Aceite:** relatório Windows e Android separados com versões, casos aprovados/falhos e evidências; links e guias não anunciam mapa incompleto como jogável.

## 5. O que pode ser feito AGORA sem os ZIPs/ROM

Para a próxima implementação de código, trabalhar somente em:
- **T01:** gerador de checklist SP05 e relatório QA vinculados a ZIP/sprite reais somente quando existirem (sem falsificar resultados).
- **T02:** auditor read-only de MapInfos, reservas e colisões por região sobre arquivos reais; na ausência deles, fixture sintética com estado BLOCKED.
- **T03:** catálogo de eventos iniciais de Nuvema com IDs simbólicos, dependências e flags UNOVA_*; criar testes negativos de duplicidade.
- **T04:** checklist de regressão com hashes protegidos e rollback sobre cópia QA, jamais overwrite direto do Game.exe.
- **T05:** guias no site em planned/pendente, links para auditorias SP03–SP05, sem novas opções jogáveis.

Essas tarefas **não autorizam** subir as barras A–D; a única meta desse lote é preparar os gates de integração.

## 6. Matriz de QA mínima para cada gate jogável

| Caso | Python/CI | Game.exe Windows QA | Android/JoiPlay |
|---|---|---|---|
| Integridade ZIP, CRC, hashes, MapIDs, rights manifests | Obrigatório | Conferir manifesto | Conferir assets instalados |
| NPC Cheren 4×4: 16 quadros, pivô, altura, largura | PNG + bounding alpha | Direções/escala animadas | Direções/escala animadas |
| Transições e colisões | IDs/conexões sem referências mortas | Caminhar portas/rotas | Caminhar portas/rotas |
| Eventos e flags do roteiro | Contratos e idempotência | Falar/revisitar/salvar | Falar/revisitar/salvar |
| Treinadores, selvagens, cap, XP, evolução | Dados e smoke mocks | Combate real | Combate real |
| HMs, itens-chave, insígnias por região | Estado/regressões | Viagem/retorno/blackout | Viagem/retorno/blackout |
| Atualizador incremental e rollback | Hash e manifesto | Instalar/desfazer na cópia | Instalar/desfazer na cópia |

Reportar separadamente TESTE SINTÉTICO, TESTE NATIVO WINDOWS e TESTE NATIVO ANDROID. Nenhum desses estados deve ser promovido por ter um único dos demais aprovado.

## 7. Barras de progresso, sem inflação

Estado da baseline nesta data: A — mapas e MapIDs **0/8**; B — história, NPCs e ginásios **0/8**; C — selvagens, treinadores e música **0/8**; D — Game.exe, Blue-Story e Android **0/8**; E — documentação, catálogos e ferramentas **4/8**. Campanha Unova aceita **0/32**.

SP03/SP04/SP05 são **ferramentas de preparação**, não fases de jogabilidade. Atualizar E04/E05/E06/E08 apenas com evidência real conforme os critérios existentes. Atualizar cada fase U01–U32 somente quando seu contrato concreto e os testes exigidos forem cumpridos, sem deduzir que U01–U06 já estão completos.

## 8. Referências e rastreabilidade

- Plano histórico U01–U32: [UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md](UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md)
- Auditor de sprites SP03: [UNOVA_AUDITOR_SPRITES_SP03.md](UNOVA_AUDITOR_SPRITES_SP03.md)
- Catálogo de 73 NPCs SP04: [UNOVA_SP04_CATALOGO_NPCS.md](UNOVA_SP04_CATALOGO_NPCS.md)
- Piloto Cheren SP05: [UNOVA_SP05_CHEREN_PILOTO_QA.md](UNOVA_SP05_CHEREN_PILOTO_QA.md)
- Conciliação de evidências E04–E06: [UNOVA_E04_E06_CONFERENCIA_EVIDENCIAS.md](UNOVA_E04_E06_CONFERENCIA_EVIDENCIAS.md)
- Pokémon Essentials GitHub: https://github.com/Maruno17/pokemon-essentials
- Exemplos de eventos RMXP: https://pokeliberty.github.io/Essentials-BES-docs/events/Introduction/
- Ficheiro sprites de Essentials v21.1 (módulo): https://github.com/silveredmeadow/pokemon-essentials-v21.1-github/blob/master/Data/Scripts/015_Trainers%20and%20player/003_Trainer_Sprites.rb

**Condição final:** não comitar assets de terceiros nem tratar este plano como aprovação técnica/nativa ou autorização legal.
