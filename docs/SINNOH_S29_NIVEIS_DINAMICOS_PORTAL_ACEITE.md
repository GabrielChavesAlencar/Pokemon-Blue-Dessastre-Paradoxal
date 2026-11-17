# Sinnoh S29 — níveis dinâmicos no site sem inventar dados jogáveis

**Objetivo da Barra A:** concluir **S29 — Exibição sem níveis fixos no site**. Esta entrega publica regras de apresentação de níveis do Blue, **não** números lidos de uma partida real nem batalhas Sinnoh instaladas.

## Fontes e implementação

1. [`scripts/battle_polish/Campaign.rb`](../scripts/battle_polish/Campaign.rb): `BlueCampaign.scaled_level` usa o maior nível da equipe **ignorando ovos**; em modo Normal, `70%`, em Master, `90%`; aplica mínimo e máximo da engine. Os valores por treinador só são calculados durante a batalha no jogo.
2. [`scripts/battle_polish/EvolutionScaling.rb`](../scripts/battle_polish/EvolutionScaling.rb): evolução contextual também parte do Pokémon de maior nível não-ovo. O arquivo documenta que **não existe um campo numérico de level cap regional no save atual**.
3. [`data/regions/sinnoh-trainer-teams-ch15.json`](../data/regions/sinnoh-trainer-teams-ch15.json): dados históricos de Platinum são **referências não compiladas**; `ui_policy.publish_historical_fixed_levels=false`, `dynamic_balance.reference_level=highest_non_egg_party_level`.
4. [`data/regions/sinnoh-symbolic-encounters.json`](../data/regions/sinnoh-symbolic-encounters.json): `global_progress.regional_numeric_level_cap=null`, encontros planejados sem níveis/slots/PBS nativos.
5. [`data/regions/sinnoh-badges-hms-contract.json`](../data/regions/sinnoh-badges-hms-contract.json): insígnias e HMs são **regionais**, não substituem nível calculado da equipe e não podem ser herdados de outra região.

O [gerador do guia](../site/scripts/sinnoh-guide.mjs) acrescenta uma política `levelPolicy` derivada desses contratos, sem inventar número de cap, nível de encontro ou versão de treinador. O [validador do portal](../site/src/assets/sinnoh-search.js) recusa cap fictício, níveis fixos/históricos ou metadados que aleguem níveis verificados. A [página Sinnoh](../site/src/assets/sinnoh-guide.js) explica **em todas as oito abas**: referência da equipe sem ovos, Normal 70%, Master 90%, função regional das insígnias e esmeraldas, falta de leitura de save no portal e necessidade de PBS/jogo real.

## Validação efetiva pelo GitHub Actions

- [Portal Blue — run 43988876576](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43988876576): **build aprovado e 151/151 testes do site passaram**, incluindo os 8 testes S29; 0 falhas.
- [Sinnoh CH19 — run 43988876549](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43988876549): **Python e Ruby aprovados** na matriz isolada, incluindo a consistência dos registros de progresso e auditorias de Sinnoh.
- [Sinnoh CH20 — run 43988876422](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43988876422): pré-voo estático de 44 casos **aprovado**, sem os converter em playtest executado.
- O pipeline geral Blue Studio é independente e **não** deve ser declarado aprovado apenas por esses três workflows.

## Testes e critérios de aceite

Os [8 testes S29](../site/tests/sinnoh-s29-dynamic-levels.test.mjs) verificam:

- Regra 70/90 e referência real; 8 abas explicativas.
- Ginásios, Elite Four, Cynthia, HMs e esmeraldas não convertem referência documental em níveis numéricos fixos.
- Negativos para `effective_level`, `levelCap`, níveis históricos, verificação de runtime falsa, alteração de percentual e nível numérico de cap vindo do catálogo.
- Geração determinística do `site/dist/data/sinnoh-guide.json` pelo build, sem injetar mapas/itens/níveis jogáveis.

Executar `cd site && npm run build && npm test`. A comprovação requer **GitHub Actions do portal aprovado**, além da regressão de Sinnoh e consistência da Barra A. Com CI de código concluído e após integração na `main`, **S29 = done** e a Barra A passa de **9/32 (28%)** para **10/32 (31%)**, permanecendo 7 parciais e 15 pendentes.

**Limitações:** o site não consulta os saves dos jogadores, não comprova localização de Pokémon, presença de NPCs, abertura de mapas ou níveis no Game.exe/JoiPlay. Mesmo com a S29 concluída, **B/C/D continuam 0/13** e os **44 casos nativos seguem pendentes**. A Barra E continua 20/20 (100%).
