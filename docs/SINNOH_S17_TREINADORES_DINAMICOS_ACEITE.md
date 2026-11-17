# Sinnoh S17 — Treinadores com balanceamento dinâmico

**18ª entrega da Barra A, escopo código/testes.** A S17 valida o comportamento real do *runtime compartilhado* de treinadores do Blue — **não instala treinadores, Pokémon, ginásios, MapIDs, NPCs ou equipes PBS reais** nos mapas de Sinnoh.

## Implementação efetiva

O Blue já possui as rotinas de balanceamento em:
- [`BlueCampaign`](../scripts/battle_polish/Campaign.rb): níveis de treinadores a **70% no Normal** e **90% no Master**, calculados com divisão inteira a partir do maior Pokémon **não-ovo** da equipe do jogador, limitados ao máximo da engine; as equipes são clonadas antes de qualquer alteração;
- [`BlueStory`](../scripts/battle_polish/Story.rb): progresso por insígnias locais e insígnias nativas, Master somente no estágio 3; a faixa BST **350/450/540 não é** um nível numérico fixo por insígnia;
- [`BlueEvolutionScaling`](../scripts/battle_polish/EvolutionScaling.rb): espécies comuns evoluem **depois** do nível efetivo ser calculado, usando os métodos da engine e sem decidir evolução ambígua; o elenco autoral dos líderes/Elite/campeã não é substituído pelo escalador de espécies.

A **integração de teste S17** em [`sinnoh_s17_trainer_balance_runtime.rb`](../tests/sinnoh_s17_trainer_balance_runtime.rb) carrega a fixture CH12 e executa os arquivos Ruby reais usando `Battle.prepend`. Amplia a cobertura de forma auditável:

1. Normal com equipe múltipla, 70% arredondado para baixo e ovo de nível alto ignorado.
2. Pokémon iniciais evoluindo após determinar o nível, sem modificar os treinadores de origem.
3. Identidade de líderes, Elite Four e campeã preservada na primeira batalha regional; rivais/administradores seguem o limite BST do modo Story, sem alterar o PBS original.
4. Master com equipes de 1, 2 ou 3 Pokémon expandidas para **4**; equipes autorais de 4–6 preservadas.
5. Batalhas duplas com **máximo de seis adversários no total**, sem criar equipes ilegais de oito Pokémon.
6. Pokémon com nível inferior a 1 ou superior ao máximo da engine são bloqueados pela regra de escala.
7. Modo Battle/VGC não recebe alterações de Story, e a regra compartilhada de Kanto/Hoenn/Johto mantém o seu comportamento.
8. Os hashes de `Marshal.dump` dos treinadores originais e da equipe do jogador são comparados antes/depois da batalha sintética.

O [contrato S17](../data/regions/sinnoh-trainer-balance-s17.json) é validado pelo [auditor Python](../scripts/regions/audit_sinnoh_s17_balance.py) contra os contratos CH12 e CH15. O auditor rejeita níveis numéricos fixos, alterações de política 70/90, alegações de `Game.exe`, equipes/PBS já instaladas e MapIDs de Sinnoh inventados. [10 testes negativos](../tests/test_sinnoh_s17_trainer_balance.py) acompanham a regressão.

Os arquivos reais `Campaign.rb`, `Story.rb` e `EvolutionScaling.rb` **não foram modificados nesta entrega**, pois a regra dinâmica já era usada e testada em CH12. A S17 adiciona a validação específica, incluindo duplas, chefes e invariantes de não mutação. A [suíte CH19](../scripts/regions/sinnoh_ci_ch19.py) inclui os novos runners Python e Ruby; a matriz [S30](../scripts/regions/audit_sinnoh_s30_suite.py) exige sua presença.

## Segurança, fontes e limitações

O [catálogo CH15](../data/regions/sinnoh-trainer-teams-ch15.json) contém **13 referências históricas Platinum**, não times PBS compilados em Sinnoh. **Não** publicar níveis históricos como níveis efetivos, deduzir equipes a partir de nomes de NPCs nem classificar uma batalha de fixture como executada no jogo. O teste também **não valida** o encontro físico do jogador com esses treinadores, saves no Windows, JoiPlay ou comportamento de chefes no Game.exe.

**Aceite de código após CI/merge:** S17 pode ser marcada `done` como validação/integração de regras compartilhadas, elevando a Barra A para **18/32 (56%)** (5 parciais, 9 pendentes). **Barra E 20/20; B/C/D 0/13; 44 casos nativos pendentes.** As S15/S16/S18–S23 continuam sem instalação de mapas, NPCs e batalhas reais.

## Evidências CI

Resultados do CI desta entrega devem ser inseridos **após execução** e verificação dos jobs CH19 (Python/Ruby), S30 (5 jobs), portal e CH20 estático. Nenhum resultado futuro ou teste nativo é presumido aprovado.
