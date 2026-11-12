# Kanto — 8º núcleo funcional (etapa 09): Celadon City e Erika

**Data:** 12/11/2026. **Status de desenvolvimento:** código implementado na branch `main`; **a aprovação do teste completo é pré-requisito para elevar a Barra 1 de 7/16 a 8/16**. Não confundir o **8º núcleo global** com a antiga etapa 08 — Vermilion/Lt. Surge, que já está contada. A tarefa atual é a **etapa 09 — Celadon/Erika**.

## 1. Escopo implementado no piloto isolado

O [manifesto FRLG verificado](../data/regions/kanto-source.json) preserva os **109 MapIDs** já publicados e retira de `preview_only` somente os IDs da fonte:

| ID FRLG | Mapa | Eventos locais importados/adaptados |
| ---: | --- | --- |
| **114** | Celadon City | Somente **3 — porta do ginásio** e **20 — porta do Centro Pokémon**; sem Rocket/Game Corner |
| **115** | Celadon Pokémon Center | Somente **1 — saída para a cidade** e **2 — enfermeira/curar equipe** |
| **124** | Ginásio de Celadon | **1 — Erika**, **7 — Tina**, **42 — Kay**, **43 — Bridget**, **44 — Tamia**, **45 — Lori**, **46 — Lisa**, **47 — Mary**, **5 — saída** |

**Dois pares bidirecionais** de entrada/saída são checados no verificador: cidade ⇄ Centro e cidade ⇄ ginásio. A cidade importa **somente** os dois acessos selecionados; o Centro importa somente cura e saída. Os demais eventos da fonte (Rocket, Game Corner, NPCs genéricos, itens, casas/Hotel/Mansão, árvores e lojas) não são importados.

Dos **11 cenários originais de Celadon**, **3** agora possuem gameplay limitado; **8** permanecem `preview_only` com tabelas de eventos vazias: **Rota 7 (111)** e **Dept. Store 1F–5F/rooftop/elevador (117–123)**. Fuchsia/Safari (**20**) e Saffron/Silph (**30**) também continuam `preview_only`. Total de áreas protegidas **58**.

## 2. Treinadores do ginásio — dados auditados

Map124 da fonte Essentials FRLG 1.1 e `PBS/trainers.txt` mostram **8 treinadores** (Erika + 7), IDs e linhas de visão:

| Evento | Personagem | Gatilho auditado |
| ---: | --- | --- |
| 1 | Erika | Ação manual |
| 7 | Picnicker Tina | Sight(2) |
| 42 | Lass Kay | Sight(3) |
| 43 | Beauty Bridget | Sight(3) |
| 44 | Beauty Tamia | Sight(4) |
| 45 | Beauty Lori | Sight(3) |
| 46 | Lass Lisa | Sight(2) |
| 47 | Cooltrainer Mary | Sight(2) |

**Time de Erika, conforme PBS FRLG verificado** (não estimar stats ou golpes alternativos):

| Pokémon | Nível | Moves |
| --- | ---: | --- |
| Victreebel | 29 | Giga Drain, Acid, Stun Spore, Poison Powder |
| Tangela | 24 | Giga Drain, Constrict, Poison Powder, Ingrain |
| Vileplume | 29 | Giga Drain, Acid, Stun Spore, Sleep Powder |

As oito equipes são importadas do PBS pinado, sem fabricar Pokémon, níveis ou moves. O site passa a exibir **62 treinadores** (54 existentes + 8 de Celadon) em 109 localidades. Com os sete novos `Sight(n)`, a contagem de NPCs de visão ativos passa de 50 para **57**.

## 3. Regras da batalha e da insígnia Rainbow

- Erika usa o treinador local `BLUE_KANTO_LEADER_ERIKA`, com chave estável `KANTO_124_001`.
- Uma derrota em `TrainerBattle.start` **não** concede Rainbow, não ativa a página pós-vitória e permite nova tentativa.
- A vitória chama `BlueRegions.award(progress, "KANTO", "RAINBOW")` **uma única vez**, sem mexer nas insígnias globais da base Decades.
- Após vitória, `BlueKantoPilot.sync_trainer_event` registra o self-switch **A** local; interação posterior não reinicia a batalha. O save regional persiste a flag.
- A obtenção do TM19/Giga Drain e regras de HM dependem de verificar o item concreto da base e o roteiro regional; **não é concedido TM experimental** apenas por usar o atalho.
- Textos provisórios são autorais e não representam tradução integral EN/PT-BR dos diálogos originais FireRed.

## 4. Como testar em Windows

Abra `Game.exe → Testar Kanto` e escolha seu inicial; no menu de pausa da cópia isolada, selecione `Testes Kanto (experimental)`. O piloto mantém **41 atalhos** e não concede insígnias ao teletransportar.

- [ ] Entrar em Celadon City, caminhar ao ginásio **sem apertar ação na porta**, voltar à cidade e entrar no Centro Pokémon; conversar com a enfermeira e sair.
- [ ] Conferir que a porta da Dept. Store, Game Corner, Mansão e outros interiores ainda **não** estão habilitados e que os cenários de prévia não contêm NPCs.
- [ ] Entrar no ginásio e observar os sete treinadores iniciando batalha por linha de visão (com obstáculos e distância coerentes).
- [ ] Desafiar Erika com equipe preparada, **perder de propósito**; conferir ausência de Rainbow.
- [ ] Vencer, receber a Rainbow Badge **uma vez**, afastar-se, retornar e verificar a fala pós-vitória sem segunda recompensa.
- [ ] Salvar em slot exclusivo, fechar e recarregar; conferir vitória, insígnia e estado dos NPCs.
- [ ] Confirmar que o Decades principal e seus saves não foram modificados. Depois validar em JoiPlay.

## 5. Provas e pendências

- [x] IDs de eventos e rosters identificados na fonte FRLG pinada por [auditoria read-only](../scripts/regions/audit_celadon_core.py).
- [x] Importação seletiva de apenas três mapas de gameplay, com whitelist por MapID/EventID em [pilot.py](../scripts/regions/pilot.py).
- [x] Script de Erika/Rainbow, cura e persistência locais implementados; sete NPCs com visão e equipes próprias.
- [x] Verificador estrutural protege 58 mapas sem eventos e valida as portas e a enfermeira.
- [x] Catálogo web com 62 treinadores, incluindo Erika e as sete treinadoras.
- [ ] **CI Windows nativa final:** compilação, teste de derrota/vitória/Rainbow única, save/reload e cópia Decades descartável — registrar execução aprovada.
- [ ] **Regressão padrão e site checks:** passar testes Python, PBS, Windows e navegador.
- [ ] **QA humano:** movimentação, passabilidade, Cut trees, encontros, NPCs, portais, visual e save.
- [ ] **Gameplay completo da etapa 09:** Rocket Hideout, Game Corner, loja de departamentos/andar/elevador, interiores, recompensas, eventos e traduções EN/PT-BR revisadas, sem antecipar Lavender/Saffron.

**Regra das barras:** após CI e regressão aprovadas, **Barra 1 = 8/16 (50%, faltam 8 núcleos)**; **Barra 2 = 1/16 (6,25%, faltam 15 aceites)**. Antes do fechamento da CI, manter **7/16 e 1/16**. Etapa 09 permanece aberta para aceitação integral.
