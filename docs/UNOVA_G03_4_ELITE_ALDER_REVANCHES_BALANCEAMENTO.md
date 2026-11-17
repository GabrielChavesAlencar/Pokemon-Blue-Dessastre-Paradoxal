# Unova G03.4 — Elite Four, Alder, variantes de dificuldade e revanches

**Entrega GitHub offline — contrato de design e QA, não instalação no jogo.** Integra G01.1–G01.4, G02.2–G02.4 e G03.1–G03.3. Não altera `Game.exe`, PBS, RXDATA, sprites, Pokémon, insígnias ou saves.

## Artefatos e fontes autoritativas

- [Catálogo versionado G03.4](../data/regions/unova-g03-elite-alder-rematch-contracts.json): cinco atores, 19 chaves de variantes e dependências estáveis.
- [Motor G03.4](../scripts/regions/audit_unova_g03_elite_alder.py): valida fonte, planeja nível/composição e delega registros de revanche sem criar um segundo ledger.
- [128 testes positivos e negativos](../tests/test_unova_g03_elite_alder.py): 24 ordens de Elite, bloqueios de Alder, progressão, 70%/90%, cobertura, Full Power e formatos nativos não verificados.
- [Fonte de campanha G02.3](../scripts/regions/audit_unova_g02_elite_finale.py): quatro vitórias da Elite durante **CH10** e entrada no Castelo de N.
- [Fonte de revanche G02.4](../scripts/regions/audit_unova_g02_postgame.py): sessões de pós-jogo, Elite em qualquer ordem, Alder só após quatro vitórias, `LOSS` sem avanço e conclusão idempotente.
- [Balanceamento G03.2](../scripts/regions/audit_unova_g03_leader_scaling.py) e [progresso G03.3](../scripts/regions/audit_unova_g03_rivals_plasma.py): cálculo sintético sem modificar equipes nem recompensas.

As identidades de NPC provêm do [SP04](../data/regions/unova-sp04-npcs.json); as chaves de treinador provêm de [E07](../data/regions/unova-e06-e07-preparation.json). **Todas as equipes, os níveis, os moves, os IDs PBS e os eventos instalados permanecem sem fonte verificada (`null`).**

## Times e acessos

| Personagem | Primeiro desafio White (CH10) | Revanche Normal (CH12) | Revanche Master (CH12) | Full Power |
|---|---|---|---|---|
| Shauntal | Permitido por contrato G02.3 | Planejada | Planejada | Bloqueado |
| Grimsley | Permitido por contrato G02.3 | Planejada | Planejada | Bloqueado |
| Caitlin | Permitido por contrato G02.3 | Planejada | Planejada | Bloqueado |
| Marshal | Permitido por contrato G02.3 | Planejada | Planejada | Bloqueado |
| Alder | **Não é o oponente da primeira campanha White** | Planejada, após a Elite | Planejada, após a Elite | Bloqueado |

São **19 variantes com identificadores estáveis**: quatro da campanha, dez de revanche Normal/Master, cinco de Full Power explicitamente bloqueadas. Uma variante é **metadado de planejamento**, nunca um time gerado.

Na campanha White, a Elite Four pode ser enfrentada em qualquer uma das **24 ordens**; os recibos de vitória ficam **somente na G02.3**. Uma vitória inédita contra membro da Elite durante CH10 é validada pela G02.3, não pela G03.4.

Após o fim da campanha, as revanches dependem de `CH12_POSTGAME`, com créditos da G02.3. O motor inicia uma sessão exclusivamente pelo método G02.4, aceita os quatro membros da Elite em qualquer ordem, bloqueia Alder antes das **quatro vitórias distintas**, permite `LOSS` sem estado novo, registra `WIN` uma única vez e arquiva a sessão somente após derrotar Alder. Repetir eventos é *no-op*. É possível iniciar nova sessão após finalizar a anterior, respeitando o limite sintético defensivo de **25 sessões** já definido na G02.4, que não representa limite no Pokémon White original.

Nenhuma revanche concede uma segunda insígnia, EXP, dinheiro, TM ou itens no jogo, nem pode mover o jogador ou modificar a party. `suggested_safe_return_area_key` é apenas sugestão simbólica da G02.4.

## Escalonamento e composição

O `plan_team` G03.4 reutiliza o motor G03.2:

| Perfil | Cálculo de nível sintético |
|---|---|
| Normal — estágios 0, 1 e 2 | **70%** do maior nível não-ovo |
| Master — estágio 3 | **90%** do maior nível não-ovo |
| Level cap por insígnia | **Não presumido:** `null` |
| Limite máximo de nível | Parâmetro obrigatório, proveniente futuramente do motor nativo |
| Slots Master | Alvo de 4 somente **se o tamanho autoral sintético for informado** |
| Tamanho de equipe nativa | **`null`**, porque nenhum PBS foi auditado |

O primeiro desafio na Elite preserva conceitualmente espécies e golpes originais; não autoriza substituir equipes canônicas por Pokémon genéricos. A prévia do Master sugere só a quantidade de vagas adicionais, sem escolher monstros, configurar evolução ou inserir personagens no editor.

## Cobertura de fraquezas

A prévia aceita **fixtures sintéticos** explicitamente fornecidos pelo teste (`FIXTURE_*`) e chama a função `coverage_plan` da G03.2. A pontuação considera multiplicadores informados, ameaças de fraqueza, resistências, imunidades e diversidade defensiva. Rejeita multiplicadores inválidos, dados de espécies reais não auditadas e lendários/míticos/paradoxos como candidatos genéricos. A resposta expõe `native_type_coverage_verified=false` e `can_add_to_real_team=false`.

A composição efetiva só poderá ser comprovada com `GameData::Species` e `Effectiveness.calculate` em ambiente nativo. **Não criar Pokémons oficiais ou percentuais de cobertura inventados.**

## Full Power — bloqueio obrigatório

Todas as cinco variantes `FULL_POWER_LOCKED` têm `eligible=false`. O contrato exige simultaneamente um perfil comprovado de campeão mundial/dez Ligas e **equipes nativas auditadas e identificadas**; nenhum desses artefatos existe aprovado no fluxo G03.4. Nem informar `story_stage=3` nem inserir um número de dez títulos no pedido de prévia remove o bloqueio. Só uma entrega futura poderá revisar essa política após obter provas verificáveis, sem promoção automática.

## Contratos, evolução e persistência

- A G03.4 lê os estados completos da G03.3 (que contém G02.4, G02.3, G02.2 e G01), e aplica novas revanches **exclusivamente** pelo motor G02.4.
- O motor valida o envelope antes/depois das transições, evita mutações dos objetos recebidos e garante que as recompensas/recibos G03.3 permaneçam idênticos.
- Evoluções seguem as regras contratuais da G03.2, mas **não são executadas em Pokémon nativos** nesta fase.
- A serialização G01.4 valida por round-trip **somente a projeção G01**; não grava estados G02–G03.4 nem converte saves reais.

## Rodar pela CI sem analisar o PC

```bash
python scripts/regions/audit_unova_g03_elite_alder.py --check
python scripts/regions/audit_unova_g03_elite_alder.py --simulate-demo
python -m unittest discover -s tests -p test_unova_g03_elite_alder.py -v
```

Os testes rejeitam Alder na primeira campanha, rematch antes dos créditos, ordens/IDs falsos, repetição conflitante de resultados, Full Power, equipes, moves, MapIDs, PBS ou presença nativa inventados. O demo reusa a jornada G01/G02/G03.3 até o pós-jogo, projeta níveis Normal/Master e percorre uma sessão completa em ordem inversa de Elite até Alder.

**Somente após CI aprovado e merge:** Barra G **18/32 (56%)**, frente **G03 4/4 (100%)**. Barra A **0/8**, Unova jogável **0/32**, região **planned**. Próxima etapa GitHub planejada: **G04.2 — métodos, horários e áreas de encontros selvagens**, ainda sem instalar dados nativos.
