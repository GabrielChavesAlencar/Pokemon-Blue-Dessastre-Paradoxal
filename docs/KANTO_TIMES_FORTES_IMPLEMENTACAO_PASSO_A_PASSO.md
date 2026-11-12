# Kanto — implantação dos times oficiais mais fortes (passo a passo)

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data:** 12/11/2026  
**Status desta entrega:** documentação publicada, **implementação de batalhas ainda não realizada**.  
**Estudo-base integral:** [Estudo de times mais fortes de Kanto](ESTUDO_TIMES_MAIS_FORTES_KANTO_LIDERES_ELITE4_CAMPEOES.md).  
**Regras soberanas:** [Plano de regiões v2](PLANO_REGIOES_DESSASTRE_V2.md), [Progressão e Animações](PROGRESSAO_E_ANIMACOES.md) e [Kanto — etapas](KANTO_ETAPAS.md).

> **Objetivo:** construir revanches fiéis aos times mais fortes oficialmente apresentados por líderes, Elite Four e campeões de Kanto, preservando a história, os Pokémon, a IA, o sistema de batalha, o balanceamento dinâmico, a progressão regional e os saves do Blue. Não copiar a equipe de um jogo para um contexto que nunca existiu nele.

## 1. Estado atual e limites

- Kanto está em **desenvolvimento 08/16 (50%)**, com **aceite integral 01/16 (6,25%)**, segundo KANTO_ETAPAS.md. O cenário da fase 09 já tem prévia de Celadon, mas **Erika, seus treinadores e eventos permanecem desativados** por decisão do autor. Nenhuma etapa deve ser marcada concluída por adicionar este documento.
- O jogo principal é Decades, em RPG Maker XP / Pokémon Essentials v21.1. O conteúdo Kanto é preparado por importadores e plugins próprios. **game/**, binários, saves e conteúdo de terceiros não devem entrar no Git.
- A opção **Testar Kanto** executa uma cópia experimental isolada; não pressupor que ela já seja a campanha integrada ou que compartilhe saves com o Decades.
- Os bloqueadores manuais **MAN-01** (portas/interiores), **MAN-02** (gatilhos de treinadores) e **MAN-03** (telas de insígnias) continuam abertos. Ver [feedback de 12/11](KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md).
- Esta proposta é **especificação**, não promessa de que os scripts, PBS, equipes, eventos e EXE já receberam as revanches.

### Duas barras que devem permanecer separadas

| Indicador | Valor documentado no início deste estudo | Quando atualizar |
|---|---:|---|
| Desenvolvimento de Kanto | **08/16 (50%)** | Somente quando uma etapa funcional de Kanto for implementada e testada conforme o roadmap |
| Conclusão validada | **01/16 (6,25%)** | Somente após satisfazer todos os critérios de aceite daquela etapa, inclusive teste manual exigido |

A elaboração dos dados canônicos **não altera nenhuma das duas barras**.

## 2. Quais adversários e quais versões usar

É essencial guardar **o cargo e o contexto da batalha**. O maior time por nível nem sempre é o melhor estrategicamente, mas constitui a referência histórica verificável.

| Personagem | Time canônico para revanche mais forte por nível | Contexto obrigatório | Maior nível histórico |
|---|---|---|---:|
| Brock | HGSS, 6 Pokémon | Ginásio, revanche | 61 |
| Misty | HGSS, 6 Pokémon | Ginásio, revanche | 60 |
| Lt. Surge | HGSS, 6 Pokémon | Ginásio, revanche | 60 |
| Erika | HGSS, 6 Pokémon | Ginásio, revanche | 60 |
| Koga | Let's Go, 5 Pokémon | **Ex-líder**, representação de ginásio | 57 |
| Sabrina | HGSS, 6 Pokémon | Ginásio, revanche | 60 |
| Blaine | HGSS, 6 Pokémon | Ginásio, revanche | 62 |
| Giovanni | FRLG, 5 Pokémon | Ginásio da campanha clássica | 50 |
| Giovanni — chefe extra | Ultra Sun/Ultra Moon, 5 Pokémon, Mega Mewtwo X/Y | **Rainbow Rocket, nunca ginásio comum** | 70 |
| Janine | HGSS, 6 Pokémon | Líder da era posterior a Koga | 59 |
| Blue | HGSS, 6 Pokémon | **Líder** de Viridian na era de Johto | 72 |
| Lorelei | FRLG, 5 Pokémon | Elite Four original, revanche | 66 |
| Bruno | FRLG, 5 Pokémon | Elite Four original, revanche | 68 |
| Agatha | FRLG, 5 Pokémon | Elite Four original, revanche | 70 |
| Lance | FRLG, 5 Pokémon | Elite Four original, revanche | 72 |
| Will | HGSS, 6 Pokémon | Elite Four da era de Johto | 62 |
| Koga | HGSS, 6 Pokémon | **Elite Four**, não o ginásio | 64 |
| Karen | HGSS, 6 Pokémon | Elite Four da era de Johto | 64 |
| Blue | FRLG, 6 Pokémon | **Campeão**, variante por inicial | 75 |
| Trace | Let's Go, 6 Pokémon | Campeão alternativo, variante por versão | 67 |
| Lance | HGSS, 6 Pokémon | **Campeão** da era de Johto | 75 |
| Red | HGSS, 6 Pokémon | Superboss, Monte Silver | 88 |

**Os nomes, as espécies e os níveis exatos estão nas tabelas individuais do estudo-base.** Copiá-los exclusivamente daquela versão evita divergência em futuros patches. As equipes do PWT são elencos de opções nivelados em 50; não podem ser apresentadas como uma batalha canônica de seis Pokémon no formato Singles.

### Escolha narrativa antes de programar

- **Campanha original de Kanto:** ginásios Brock, Misty, Lt. Surge, Erika, Koga, Sabrina, Blaine e Giovanni; Liga Lorelei, Bruno, Agatha, Lance; campeão Blue. Preservar os times da campanha usados hoje e o fluxo das insígnias.
- **Revanches de líderes em poder máximo:** usar HGSS onde indicado e registrar Janine/Blue-líder como desafios da época posterior, sem deslocar Koga/Giovanni da campanha original. A ordem e a localização desses dois desafios alternativos precisam ser aprovadas no roteiro.
- **Desafios opcionais:** Giovanni Rainbow Rocket, Trace, Lance-campeão e Red não substituem automaticamente o campeão Blue nem a Elite Four original. Só ativar eventos e mapas depois de confirmar a posição na narrativa.
- **Campeão Blue:** escolher **uma** das três variantes de FRLG segundo o inicial do jogador; jamais somar os três iniciais e chamar de equipe oficial. Para quem escolheu Bulbasaur, Blue terá Charizard; Charmander → Blastoise; Squirtle → Venusaur.
- **Trace:** manter as duas variantes como referência, não misturar Jolteon e Raichu num único time oficial.

## 3. Regra de desbloqueio — pós-jogo global, não após uma única Liga

A regra aprovada no Plano Regional v2 é: **o time oficial mais forte só fica disponível depois de concluir uma vez as dez campanhas principais do circuito**. Vencer apenas a Liga de Kanto **não** habilita Full Power global.

1. Consultar o estado regional persistido por **BlueRegions**.
2. Usar a condição já definida por **BlueRegions.world_champion?(state)**.
3. Verificar também que se trata de uma **revanche válida**; o seletor existente **BlueRegions.profile(state, verified_rematch)** já diferencia primeira conclusão de revanche pós-circuito.
4. Manter **primeira batalha canônica** sempre que a condição não for satisfeita.
5. Não liberar todos os destinos de transporte antecipadamente; continuam valendo as duas regiões vizinhas após vencer cada Liga.
6. Não conceder de novo insígnias, esmeraldas, recompensas de história ou Hall da Fama ao vencer uma revanche extra, a menos que haja especificação explícita.
7. Preservar saves legados: campos novos devem ter defaults seguros; reabrir um save não deve promover automaticamente batalhas já vencidas.

**Separar desbloqueios diferentes:**

- **Times Full Power dos adversários:** terminar as dez campanhas + revanche verificável.
- **Pokémon especiais na party do jogador:** obter as oito conquistas **da região atual**; ao viajar para outra sem oito, os especiais vão para a Box, respeitando segurança e capacidade de armazenamento.
- **HMs / mobilidade:** insígnias ou eventos **locais** da região atual; conquistas de outras regiões não liberam HMs de Kanto.

O controle de especiais pertence a **BlueRegions.allow_specials?** e **BlueRegionalPolicy**. Não interpretar a restrição da party do jogador como proibição automática de um Pokémon da equipe canônica do adversário.

## 4. Onde integrar no repositório

| Caminho confirmado na main | Papel e cuidado |
|---|---|
| **docs/ESTUDO_TIMES_MAIS_FORTES_KANTO_LIDERES_ELITE4_CAMPEOES.md** | Fonte documental do time canônico, origem e análise |
| **docs/PLANO_REGIOES_DESSASTRE_V2.md** | Políticas regionais e do pós-jogo; não duplicar regras |
| **scripts/battle_polish/Regions.rb** | BlueRegions, world_champion?, profile, estado de ligas e conquistas |
| **scripts/battle_polish/RegionalPolicy.rb** | Depósito e bloqueio de especiais, HMs e save regional |
| **scripts/battle_polish/Campaign.rb** | Preparação e escalonamento de batalhas do Story Mode; expansão Master |
| **scripts/battle_polish/Balance.rb** | Ajustes de golpes por faixa de progressão |
| **scripts/regions/KantoPilot.rb** | Eventos experimentais de Kanto, vitórias e líderes já representados |
| **scripts/regions/pbs.py** | Importação/catalogação de treinadores regionais, sem sobrescrever Decades |
| **scripts/regions/pilot.py** | Montagem de cópia piloto e eventos regionais |
| **data/regions/kanto-source.json** | Fonte/regiões/mapas auditados; manter preview_only intacto |
| **scripts/battle_polish/leaders.py** | Patcher das duplas Full Power **de Decades** — não confundir com as novas revanches de Kanto |
| **tests/** | Testes sintéticos de regressão e políticas já disponíveis |
| **site/public/data/kanto.json** | Referência de mapas e treinadores no portal; futura apresentação de revanches |

**Recomendação de novos arquivos, AINDA NÃO CRIADOS:**  
- **data/regions/kanto-canonical-teams.json** — catálogo imutável e auditável dos times (espécies, níveis, origem, variações).  
- **scripts/regions/kanto_rematches.py** — validação/compilação de manifestos para treinadores PBS, se a engine realmente exigir arquivos de treino.  
- **scripts/battle_polish/KantoRematches.rb** — seleção da variante e do perfil em memória; carregado apenas onde o runtime for compatível.  
- **tests/test_kanto_rematches.py** — testes de elegibilidade, equipe, integração e save.  

Não criar nomes de classes, IDs simbólicos de Pokémon ou arquivos PBS por suposição. Investigar a instalação real e registrar mapeamentos antes de gerar dados executáveis.

## 5. Implementação fase a fase (ordem obrigatória)

### Passo 01 — congelar a referência canônica

- [ ] Adotar o estudo-base como fonte única de espécies/níveis; adicionar checksum ou versão de cada catálogo.
- [ ] Para cada treinador: **trainer_key**, **era**, **role_at_time**, **source_game**, **battle_context**, **variant_key**, lista ordenada de membros.
- [ ] Registrar **os casos de exceção**: Koga líder/Elite Four; Blue líder/campeão; Lance Elite Four/campeão; Giovanni ginásio/Rainbow Rocket; Janine posterior; Red superboss.
- [ ] Marcar se um time possui 5 ou 6 integrantes, sem completar automaticamente com Pokémon inventado.
- [ ] Separar **canonical_team** de **balanced_team** e de **pwt_options**. Os ajustes de gameplay são derivados em memória e não mudam a referência.

**Aceite:** todos os registros têm fonte, tipo de confronto e contagem coerentes com o estudo; nenhuma espécie é silenciosamente trocada.

### Passo 02 — mapear IDs reais de espécies, formas, itens e treinadores

- [ ] Abrir os dados da instalação preparada em **game/PBS/** e a Pokédex da base Decades; cruzar nomes do estudo com **GameData::Species**.
- [ ] Verificar evoluções, disponibilidade de golpes/habilidades, Megas, nomenclatura simbólica e variantes da engine.
- [ ] Confirmar os tipos de treinador/nome/version usados para Brock, Misty, Surge, Erika, Koga, Sabrina, Blaine, Giovanni, Elite Four e Blue, sem sobrescrever nomes iguais de outras regiões.
- [ ] Manter chave regional estável combinando **KANTO + mapa/evento + papel + variante**, com migração para saves antigos quando cabível.
- [ ] Identificar sprites/portraits já presentes antes de desenhar novos; registrar assets ausentes sem falhar silenciosamente.

**Aceite:** validador identifica todos os símbolos e informa precisamente ausências; nunca usa espécie ou ID improvisado.

### Passo 03 — criar catálogo declarativo versionado

Formato **proposto, não implementação existente**:

~~~json
{
  "schema": 1,
  "region": "KANTO",
  "trainer_key": "KANTO_BROCK",
  "role_at_time": "gym_leader",
  "source_game": "HGSS",
  "battle_context": "gym_rematch",
  "variant_key": "default",
  "team_kind": "canonical",
  "members": [
    {"species": "GOLEM", "level": 55},
    {"species": "RELICANTH", "level": 54},
    {"species": "OMASTAR", "level": 56},
    {"species": "KABUTOPS", "level": 55},
    {"species": "RAMPARDOS", "level": 57},
    {"species": "ONIX", "level": 61}
  ]
}
~~~

- [ ] Colocar cada time oficial como **registro distinto**; se necessário, separar array de treinadores por contexto.
- [ ] Guardar o nível original mesmo quando o Blue for escalá-lo em jogo.
- [ ] Armazenar as três equipes de Blue-campeão em variantes diferentes, com exclusividade mútua; idem Trace e Mega Mewtwo X/Y.
- [ ] Checar duplicatas e ausência de membros por script.
- [ ] Não gravar no repositório mapas binários originais, áudio/licenças de terceiros ou saves.

**Aceite:** arquivo parseia, valida 100% das equipes, preserva exatamente as tabelas e permite reproduzir cada seleção.

### Passo 04 — integrar ao sistema de balanceamento existente

- [ ] Reutilizar **BlueCampaign.trainer_level**, **BlueCampaign.Teams** e a lógica de modo/estágio existente, em vez de criar segunda fórmula.
- [ ] Na campanha normal, preservar os times progressivos da história e o escalonamento já implementado.
- [ ] As categorias atuais de BST são: **0–1 esmeralda: 350; 2–4: 450; 5–10: 540; 11+: sem teto**. Verificar o total **global** apenas onde o próprio balanceador o usa.
- [ ] A preparação de trainers normais considera 70% do maior nível do jogador; em Master, a rotina de campanha utiliza 90%. **Confirmar a diferenciação do chefe/líder no código instalado antes de depender dela** e manter o comportamento aprovado.
- [ ] Em Master, times pequenos de 1–3 Pokémon recebem complemento para iniciar com **ao menos quatro**; times já completos de 5–6 não ganham um sétimo.
- [ ] Para time histórico de 5 membros, preservar os cinco se a proposta exigir fidelidade; qualquer sexto opcional deve ser rotulado **adaptação não oficial**.
- [ ] Os níveis originais servem para comparação e possíveis diferenças relativas internas, **não para impor nível 75/88 diretamente em uma batalha escalonada**.
- [ ] Avaliar golpes, itens e habilidades quando gerar o perfil efetivo. Não usar Fada retroativamente numa tabela histórica HGSS; a batalha dentro da engine atual segue suas regras oficiais restauradas.

**Aceite:** modo Iniciante/Intermediário/Avançado/Master continua com as restrições corretas e nenhuma edição destrutiva dos PBS originais é necessária apenas para mudar níveis.

### Passo 05 — ativar perfis apenas em revanches elegíveis

Fluxo conceitual:

~~~text
Entrou em batalha de Kanto
  -> identificar região + treinador + cargo + variante de roteiro
  -> verificar se é primeiro confronto ou revanche
  -> ler estado regional persistido do mesmo save
  -> world_champion? e revanche verificada?
        NÃO -> time normal da campanha / revanche local existente
        SIM -> carregar time canônico máximo daquele personagem/contexto
  -> escolher variante condicional (inicial/versão)
  -> aplicar escalonamento e regras Blue EM MEMÓRIA
  -> iniciar combate sem duplicar prêmios/insígnias
  -> persistir somente flags de vitória/revanche necessárias
~~~

- [ ] Nunca ativar Mega Mewtwo no ginásio comum de Giovanni.
- [ ] Nunca substituir Koga pelo time da Elite Four no ginásio original.
- [ ] Se determinada batalha especial não estiver na campanha do jogador, **não criá-la sem aprovar mapa/evento/narrativa**.
- [ ] Ajudar o usuário a enxergar no jogo se o combate é **História**, **Revanche**, ou **Poder Máximo**; não alterar o menu global de batalhas sem necessidade.
- [ ] Garantir que abandonar, perder ou recarregar uma revanche não consume automaticamente a vitória.

**Aceite:** usando o mesmo save, primeiro confronto e Full Power selecionam equipes diferentes apenas quando a condição correta é satisfeita.

### Passo 06 — integrar mapas e eventos somente quando liberados no roadmap

- [ ] No trecho atual, **Brock, Misty e Surge** já possuem eventos experimentais em KantoPilot.rb; usar seus identificadores como referência, sem registrar a revanche como uma nova insígnia.
- [ ] **Celadon fase 09 está apenas no cenário**: não criar eventos de Erika nem marcar fase 09 concluída enquanto permanecer o bloqueio decidido pelo autor.
- [ ] Quando as fases seguintes liberarem eventos: ligar líderes restantes, Liga e as revanches aos IDs de mapa auditados; auditar portas/interiores e gatilhos por linha de visão.
- [ ] Desbloquear o NPC de transporte **após a Liga da região**, com destinos autorizados; não trocar a equipe para poder máximo antes das dez Ligas.
- [ ] Exibir os oito badges de Kanto e o painel geral com base no save, sem somá-los duas vezes.
- [ ] Preservar ao viajar os especiais depositados na Box e suas restrições locais conforme RegionalPolicy.rb.
- [ ] Em todas as viagens e revanches, manter HMs conforme regras **locais**.

**Aceite:** não há mudanças em mapas preview_only, interiores nem switches de Decades que prejudiquem saves antigos; batalhas da história permanecem alcançáveis em ordem.

### Passo 07 — portal e documentação visível ao jogador

- [ ] No **site**, separar os perfis do treinador em **Campanha original**, **Revanche oficial** e **Desafio especial**.
- [ ] Mostrar os seis Pokémon (ou cinco nos jogos que assim exigem), níveis **originais**, jogo de origem, variantes e condição de desbloqueio.
- [ ] Para times não publicados no Game.exe, marcar claramente **Planejado** ou **Ainda não disponível**.
- [ ] Mostrar retratos/sprites próprios já autorizados e evitar duplicar treinador ao indexar o mesmo personagem em dois cargos.
- [ ] Não divulgar *PWT options* como equipe oficial de seis de combate Singles.
- [ ] Atualizar a data de modificação sem falsamente declarar implementação.

**Aceite:** guia e jogo não contradizem o time ativo, o cargo do personagem ou o estado de implementação.

### Passo 08 — validar, publicar e somente depois atualizar o progresso

**Testes automatizados propostos:**

- [ ] Catálogo completo: espécies existentes, 1–6 integrantes, fontes, variantes e ausência de duplicações involuntárias.
- [ ] Blue: três escolhas de inicial diferentes produzem apenas a variante correspondente.
- [ ] Giovanni: ginásio e chefe Rainbow Rocket nunca compartilham perfil por engano.
- [ ] Koga e Lance: separação de cargos comprovada.
- [ ] Antes de vencer dez Ligas: Full Power **não** disponível, mesmo após vencer Kanto e ter 8 insígnias.
- [ ] Após vencer dez Ligas + revanche válida: Full Power aparece apenas no confronto correto.
- [ ] Não duplicar insígnia nem recompensa após derrota, vitória, save e reload.
- [ ] Em Master: os membros originais não são apagados e nenhum time ultrapassa seis.
- [ ] Viajando para Kanto sem oito insígnias: especiais do jogador depositados, impossibilidade de levar para party, PC cheio com rollback; depois das oito, liberar.
- [ ] Atravessar portas nos dois sentidos, respeitar paredes na linha de visão e manter treinadores obrigatórios no ponto correto.
- [ ] Verificar os casos dos saves antigos Decades e os novos saves Kanto sem reescrever dados da outra campanha.

Comandos existentes para regressão sintética na raiz do repositório:

~~~powershell
python -m unittest discover -s tests
python -m unittest tests.test_regions tests.test_kanto_verifier tests.test_kanto_installer
~~~

**Observação:** a segunda chamada pressupõe descoberta por módulo e pode depender do empacotamento local de testes; se falhar por importação, usar **python -m unittest discover -s tests -p "test_kanto*.py"**. Esses testes existentes **não validam o novo recurso enquanto os testes novos não forem implementados**.

**Validação real no Windows (obrigatória para aceite):**

1. Atualizar **main** e fechar todos os processos do jogo.
2. Manter backup de save em slot separado. Abrir **ABRIR_JOGO.bat** para o fluxo normal ou usar **Testar Kanto** na terceira opção do EXE principal para a cópia experimental.
3. Na cópia experimental, iniciar partida nova, escolher inicial, enfrentar Brock, Misty e Surge onde disponíveis e comparar a equipe real às regras atuais da campanha.
4. Testar **portas, gatilhos de treinador e insígnias** em cada área visitada; não presumir que um smoke CI prova caminhada.
5. Após a futura implantação das revanches, carregar um save elegível **com dez Ligas** e outro **sem dez Ligas**, confirmar que somente o primeiro habilita o time máximo.
6. Testar derrota, vitória, fechar/abrir o EXE, continuar e transferir região. Conferir logs e backups.
7. Repetir em Windows e, quando possível, JoiPlay; falha no Android não deve apagar o aceite parcial específico de Windows.
8. Registrar evidências (nome da equipe, níveis em jogo, perfil, mapa, origem do save, modo, log/print) e atualizar o roadmap **apenas com resultado real**.

## 6. Critérios para revisão e publicação

- O estudo-base e este guia são **documentação**, sem alteração em Game.exe, PBS ou salvamentos.
- Futuras implementações devem ser entregues em commits de arquivos próprios reproduzíveis, **não** pela inclusão de **game/** no Git.
- Qualquer equipe diferente do registro de jogo deve aparecer como **adaptação Blue**. Nunca modificar silenciosamente o time canônico.
- Evitar acoplamento com os **18 líderes Full Power de Decades** descritos em [Líderes Full Power](LIDERES_FULL_POWER.md).
- Before/after: sempre registrar o comportamento anterior do Story Mode para evitar regressões.
- Não fazer **force push**; atualizar a main normalmente conforme AGENTS.md.
- Manter **KANTO_ETAPAS.md** e as duas barras inalteradas enquanto só existir pesquisa e planejamento.

## 7. Ordem mínima de trabalho futuro

| Prioridade | Entrega | Dependência |
|---|---|---|
| P0 | Validar catálogo e origens de todos os times | Este estudo |
| P0 | Confirmar IDs/formatos reais do Essentials e criar testes | Instalação preparada e auditoria |
| P1 | Implementar seleção Full Power por elegibilidade global | Estado BlueRegions e saves |
| P1 | Cobrir Blue/Giovanni/Koga/Lance e variantes | Modelo de papéis/versões |
| P1 | Regressão de escalonamento Master/BST | BlueCampaign e balanceador existente |
| P2 | Conectar eventos de revanche sem afetar história | Mapas e eventos aprovados |
| P2 | Mostrar variantes e desbloqueios no portal | Dados publicados, integração confirmada |
| P3 | Desafios opcionais de Giovanni RR, Trace, Lance-campeão e Red | Narrativa, local e desbloqueios aprovados |
| P3 | Aceite manual Windows/JoiPlay e atualização das barras | Funcionalidade testada |

## 8. Fontes principais

- [Referências e tabelas detalhadas por personagem](ESTUDO_TIMES_MAIS_FORTES_KANTO_LIDERES_ELITE4_CAMPEOES.md#11-fontes-e-conferência).
- [Kanto — critérios de aceite e 16 etapas](KANTO_ETAPAS.md).
- [Regras de pós-jogo, regiões e NPC](PLANO_REGIOES_DESSASTRE_V2.md).
- [Balanceamento dinâmico por esmeraldas](PROGRESSAO_E_ANIMACOES.md).
- [Teste experimental no Game.exe e seus limites](KANTO_TESTE_EXPERIMENTAL.md).
- [Pendências relatadas pelo usuário em 12/11](KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md).

**Resultado esperado ao implementar este documento:** cada um dos treinadores mantém o seu time histórico e contexto corretos na documentação; as revanches globais usam essas equipes apenas após desbloqueio válido; o Blue continua aplicando o balanceamento que já existe; a campanha inicial, Kanto experimental, Decades, HMs, armazenamento e saves antigos não sofrem regressões.
