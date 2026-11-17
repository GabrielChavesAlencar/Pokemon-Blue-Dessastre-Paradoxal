# Unova G03.2 — Líderes, level cap, evolução dinâmica, cobertura e dificuldades

**Escopo:** contrato e motor de QA **somente offline** para os oito líderes simbólicos de Pokémon White, utilizando os contratos G01.1–G01.4, G02.2–G02.4 e o sistema de batalha compartilhado. **Nenhum PBS, Game.exe, mapa RXDATA, save, Pokémon ou time nativo é alterado.** O motor usa fixtures com prefixo `FIXTURE_` para impedir confusão com espécies e equipes oficiais.

## Arquivos

- [Catálogo G03.2](../data/regions/unova-g03-leader-scaling-contracts.json): oito líderes vinculados aos capítulos e insígnias [G02.2](../data/regions/unova-g02-gym-story-contracts.json), fonte e limites explícitos.
- [Motor offline G03.2](../scripts/regions/audit_unova_g03_leader_scaling.py): `validate_policy`, `plan_battle`, `evolve_fixture`, `coverage_plan`, `demo`.
- [120 testes](../tests/test_unova_g03_leader_scaling.py): casos positivos e negativos, rodados no Linux e Windows pelo CI.

As especialidades **FIRE/WATER/GRASS**, NORMAL, BUG, ELECTRIC, GROUND, FLYING, ICE e DRAGON são **referências de design**, não tipos derivados de um time, Pokémon ou golpe PBS verificado. Striaton seleciona Chili para Snivy, Cress para Tepig e Cilan para Oshawott. Opelucid White usa Iris, não Drayden. Os líderes e as insígnias vêm da G02.2.

## Level cap e escalonamento coerentes com Blue

Fontes locais: [`BlueCampaign`](../scripts/battle_polish/Campaign.rb), [`BlueStory`](../scripts/battle_polish/Story.rb), [`BlueEvolutionScaling`](../scripts/battle_polish/EvolutionScaling.rb), [contrato compartilhado de S17](../data/regions/sinnoh-trainer-balance-s17.json) e [contrato de evolução](../data/regions/sinnoh-trainer-evolution-contract.json).

| Regra | Normal | Master |
|---|---|---|
| Percentual do maior nível **não-ovo** do jogador | 70% | 90% |
| Arredondamento | Inteiro para baixo | Inteiro para baixo |
| Estágio BlueStory aplicável | 0–2 | 3 |
| Equipe de tamanho 1–3 | Preservada | Planeja completar até 4 |
| Equipe já com 4–6 | Preservada | Preservada |
| Limite máximo adversário | 6 | 6 |
| Pokémon e moves do líder no primeiro desafio | Preservados | Preservados |

**Não existe atualmente campo de cap numérico regional por insígnia persistido no save.** O sinal de progresso disponível no código é o maior nível não-ovo (fallback 1); o máximo aceito pelo engine deve vir da origem nativa `GameData::GrowthRate.max_level`. Assim, o QA exige que o limite do engine seja passado como **parâmetro explícito**, sem cravar 100 ou criar cap numérico fictício.

**BST não é nível.** `BlueStory.cap` aplica os tetos BST 350 / 450 / 540 / sem limite nos estágios 0–3. Não os converter em nível 35, 45 ou 54. O planejador informa separadamente ambos os dados e não gera equipe adversária.

## Evolução dinâmica de treinadores

A G03.2 mantém a regra compartilhada de evoluir a espécie **depois** do escalonamento, conforme `GameData::Species#get_evolutions(true)` no runtime. No teste sintético:

- Evoluções naturais por nível: nível requerido **+5**.
- Item/pedra de evolução simples: a partir de **30**.
- Troca simples/com item: a partir de **40**.
- Amizade: a partir de **45**.

Gênero e horário não são supostos: precisam de contexto explícito. Ramos ambíguos são bloqueados; espécies especiais, formas alternativas, condições não suportadas, IDs de espécies reais não verificados e ciclos não são convertidos. O teste não altera PBS, IVs, EVs, golpes, características ou Pokémon existentes. **Não se trata de importação de Dex ou tabela de evoluções nativa**: os dados dos testes são exclusivamente `FIXTURE_*`.

## Cobertura defensiva e composição Master

A lógica de referência vem de `BlueCampaign.master_weaknesses` e `master_partner`:

- Calcular, para cada tipo ofensivo, vulnerabilidades combinadas contra a equipe (multiplicadores que indicam fraqueza, resistência ou imunidade).
- Valorizar imunidades e resistências contra os maiores riscos; penalizar novas fraquezas; favorecer diversidade de tipos.
- Analisar candidatos sintéticos com BST **440–570**, sem espécies especiais e sem duplicatas.

O teste recebe os multiplicadores explicitamente e **não inventa uma tabela de tipos do engine**. Só `Effectiveness.calculate` com `GameData::Type` e espécies reais poderá comprovar a cobertura de um time compilado. Os resultados apenas ordenam candidatos `FIXTURE_*`, com `can_add_to_real_team=false`; não inserem Pokémon no elenco.

No Master, o motor calcula o **número de vagas teóricas** até quatro, sem escolher Pokémon inexistentes. Times autorais nativos de quatro a seis Pokémon permanecem intactos.

## Primeiro desafio e revanche Full Power

Segundo [o contrato compartilhado das regiões](REGIOES_BALANCEAMENTO_PRIMEIRO_DESAFIO_E_FULL_POWER.md), o **primeiro desafio** de líderes, Elite e Campeão regionais preserva espécies, formas, golpes e habilidades originais — **não** aplica substituição BST nem limite de potência de golpes, inclusive no estágio Master. Essa exceção não desliga o escalonamento de nível nem os demais controles de progressão.

A G03.2 bloqueia **toda revanche Full Power** enquanto não houver equipe canônica auditada e sinal de perfil `world_champion_rematch` (após completar dez Ligas). Não cria equipes Full Power genéricas. Revanche Full Power e balanceamento detalhado da Elite/Alder ficam para etapas posteriores.

## Restrições de fonte e testes negativos

Os oito contratos possuem `trainer_pbs_id=null`, `trainer_version=null`, `trainer_party=null`, `trainer_levels=null`, `moves=null`, `ability_data=null` e `source_map_id=null`. Nenhuma dessas lacunas vira equipe "oficial" de Unova, pois os catálogos existentes não contêm esses dados nativos verificados.

A suíte exige ordens de insígnias da G02.2, variantes corretas de Striaton/Opelucid, estágios e percentuais corretos, tamanhos 1–6, cap do engine válido, rejeição de números inventados, evolução ambígua/especial, cobertura com tipos inválidos e candidatos lendários, falsos PBS/MapIDs, falso estado jogável e desbloqueio precoce de Full Power.

```bash
python scripts/regions/audit_unova_g03_leader_scaling.py --check
python scripts/regions/audit_unova_g03_leader_scaling.py --simulate-demo
python -m unittest discover -s tests -p test_unova_g03_leader_scaling.py -v
```

**Progresso após aprovação do CI e merge:** Barra G **16/32 (50%)**, frente G03 **2/4**. Barra A **0/8** e Unova jogável **0/32** permanecem inalteradas. Próxima: **G03.3 — rivais, Plasma e chefes por capítulo**, com times ainda dependentes de fonte auditada.
