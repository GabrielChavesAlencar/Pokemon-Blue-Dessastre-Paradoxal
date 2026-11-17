# Unova G03.3 — Rivais, Team Plasma, chefes e progressão por capítulo

**Entrega offline GitHub:** vínculo de fontes G01.1–G01.4, G02.2–G02.4 e balanceamento G03.2. Sem alterar `Game.exe`, `.rxdata`, PBS, save do jogador, mapas, equipes ou itens.

## Arquivos

- [Catálogo versionado de 15 referências](../data/regions/unova-g03-rivals-plasma-story-contracts.json)
- [Motor de contratos G03.3](../scripts/regions/audit_unova_g03_rivals_plasma.py)
- [132 testes positivos e negativos](../tests/test_unova_g03_rivals_plasma.py)
- [Barra G](UNOVA_GITHUB_32_TAREFAS_PROGRESSO.md)

A fonte principal dos personagens e arquétipos é o catálogo [SP04](../data/regions/unova-sp04-npcs.json). As referências de treinadores estão na [E07](../data/regions/unova-e06-e07-preparation.json) — **todos os PBS, equipes e níveis continuam não verificados**. As áreas são *nomes de referência U03*, nunca MapIDs físicos.

## Quinze referências com IDs estáveis

| Capítulo | Participantes/contatos | Origem dos dados |
|---|---|---|
| CH01 Nuvema/Accumula | Bianca, Cheren, discurso da Plasma/Ghetsis, N | **4 vínculos read-only** da G01.3/U07 |
| CH02 Striaton | Cheren | Planejamento G03.3 |
| CH03 Nacrene | Grunt Plasma em referência a Pinwheel | Planejamento G03.3 |
| CH04 Castelia | Grunt Plasma | Planejamento G03.3 |
| CH05 Nimbasa | Bianca, Cheren | Planejamento G03.3 |
| CH06 Driftveil | Grunt Plasma em referência a Cold Storage | Planejamento G03.3 |
| CH07 Mistralton | N em referência a Chargestone Cave | Planejamento G03.3 |
| CH08 Icirrus | Grunt Plasma em referência a Dragonspiral Tower | Planejamento G03.3 |
| CH09 Opelucid | Cheren em referência a Route 10 | Planejamento G03.3 |
| CH11 Castelo de N | N e Ghetsis | **2 vínculos read-only** da G02.3 |

**Essas nove posições intermediárias são contratos originais de design e testes, não transcrições comprovadas de batalhas nativas do Pokémon White.** Não certificam que o confronto ocorreu naquele lugar, nem criam NPC, diálogo, espécie, golpe, item ou treinador real. A documentação de origem é explícita sobre essa limitação.

Cada encontro possui identificador `UNOVA_G033_CH##_ATOR`, identidade de NPC SP04, referência E07 onde existente, capítulo G01.1, local U03, status de fonte, pré-requisitos, variante simbólica de time e campos nativos **null**. O arquétipo `PLASMA_GRUNT` não recebe `trainer_reference_key` inventado.

### Fonte autoritativa e idempotência

- Os primeiros encontros de Bianca e Cheren continuam com **ADVANCE_ON_LOSS**, e o primeiro N com **WIN_REQUIRED**, segundo [U07](../data/regions/unova-u07-nuvema-events.json). São lidos do ledger [G01.3](../scripts/regions/audit_unova_g01_reentry_ledger.py), sem novos recibos.
- N e Ghetsis no Castelo são lidos dos cinco eventos ordenados da [G02.3](../scripts/regions/audit_unova_g02_elite_finale.py); a G03.3 não concede vitória ou créditos novamente.
- Para os **nove** confrontos *planejados*, só `WIN` produz um recibo com chave e variante estáveis. `LOSS` deixa o estado intacto. Repetir `WIN` dá no-op e tentar trocar uma vitória por `LOSS` é bloqueado.
- Cada vitória de design emite **uma intenção simbólica única** de categoria `STORY_MILESTONE_INTENT_NOT_INVENTORY`, derivada dos recibos. Não concede Pokémon, experiência, dinheiro, TM, item, badge nem flag de save.
- Pré-requisitos dos atores são verificados antes de cada vitória: não há salto de Cheren para CH09, N para CH07 ou uma sequência da Plasma anterior sem a referência prévia adequada.

### Progressão de capítulos G01.1/G02.2/G02.3

O motor oferece `complete_gym` e `advance_gym` para CH02–CH09: antes de concluir um capítulo, exige as vitórias de design daquele capítulo **e** delega aos cinco eventos do ginásio e à insígnia simbólica da [G02.2](../scripts/regions/audit_unova_g02_gym_story.py), com o marcador `SIMULATED_ONLY_NO_NATIVE_APPROVAL`. O `advance_gym` segue a transição G01.2/G01.3 validada por G02.2.

Uma simulação integral percorre os 13 eventos de U07, os nove confrontos do meio, os oito ginásios, a Elite Four e N/Ghetsis (G02.3) até CH12. **Esse bloqueio adicional atua somente quando a transição é feita pela interface G03.3.** As APIs anteriores e o Game.exe não são alterados retroativamente.

Reentrada nos capítulos anteriores usa `G02.4 → G02.3 → G02.2 → G01.3` e é read-only: nenhum recibo ou recompensa é duplicado. A G01.4 executa round-trip **somente da projeção G01** do estado; o envelope G03.3 e seus tokens ainda não possuem codec persistente.

### Progressão dos times e dificuldades

As variantes `UNOVA_G033_TEAM_ATOR_01/02/...` identificam o estágio narrativo de cada ator, não o time oficial. `plan_team` reutiliza o cálculo de [G03.2](../scripts/regions/audit_unova_g03_leader_scaling.py):

- Normal: **70%** do maior nível não-ovo da party sintética; Master (estágio 3): **90%**. Arredondamento para baixo e máximo recebido explicitamente do engine, não presumido como cap regional numérico.
- Com *quantidade autoral sintética conhecida*, Master planeja até quatro vagas. Sem fonte de time auditada, tamanho de equipe e vagas futuras continuam `null`; **não cria Pokémon**.
- Espécies, evoluções reais, golpes e cobertura de fraquezas dependem do `GameData` nativo verificado. As novas variantes não provam conteúdo instalado.

### Revanche e segurança

Após o token de créditos G02.3 e entrada em CH12, estão disponíveis **sessões de teste** de revanche somente para Bianca e Cheren, desde que exista vitória registrada em ao menos um confronto planejado do próprio rival. IDs de sessão começam em 1, sem saltar ou duplicar (máximo defensivo de oito por rival, não limite do jogo oficial). `LOSS` permite tentar novamente sem mexer no histórico; `WIN` gera um recibo único **sem nova intenção de recompensa**. Revanche com N, Ghetsis ou Grunt não é inferida.

A revanche real depende de equipes/locais auditados e de um adaptador nativo futuro; o código **não** afirma que as sessões são encontros efetivamente presentes na versão White.

## Verificação e barreiras negativas

```bash
python scripts/regions/audit_unova_g03_rivals_plasma.py --check
python scripts/regions/audit_unova_g03_rivals_plasma.py --simulate-demo
python -m unittest discover -s tests -p test_unova_g03_rivals_plasma.py -v
```

A suíte cobre vínculo autoritativo sem duplicação, 15 contratos/9 slots planejados, atores/IDs estáveis, recompensas idempotentes, oito transições de ginásio, derrotas, reentrada, duas séries de rivais, versões/times/MapIDs/PBS fictícios e a campanha completa. CI roda Linux e Windows, e o portal testa a barra.

**Somente após CI e merge na main:** G03 **3/4**, Barra G **17/32 (53%)**, com **15 tarefas restantes**. Barra A **0/8**, Unova jogável **0/32**, região **planned**. Próxima G03.4: Elite Four, Alder e rematches com contratos de time auditáveis.
