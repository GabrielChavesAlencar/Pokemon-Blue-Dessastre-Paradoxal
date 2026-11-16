# Sinnoh — CH15: equipes de ginásios, Elite Four e Cynthia

**Data:** 16/11/2026 · **Status:** inventário/documentação e auditoria concluídos, **jogabilidade não comprovada**.  
**Fontes versionadas:** [Detonado Platinum](SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md) · [Revisão de treinadores](../data/regions/detonados-content-review.json) · [Regras de progressão](../site/public/data/regions.json).

## Quatro níveis de evidência — não confundir

1. **Equipe do primeiro confronto em Platinum:** espécies e seus níveis **históricos** constam do detonado. São referências de composição, não times presentes na build Blue.
2. **Revanche histórica Platinum:** documentada no detonado apenas para **Aaron, Bertha, Flint, Lucian e Cynthia**. Não foram inventadas revanches dos oito líderes.
3. **Variante mais forte / Full Power do Blue:** **desconhecida / não verificada** para todos os 13 nomes. Exige definição autoral e confronto com PBS nativo real, variantes e critérios do jogo; não foi copiada do catálogo `strongest-teams.json` usado por Kanto/Johto.
4. **Equipe efetivamente instalada no PBS/engine:** **zero comprovadas** nesta auditoria. Nenhum `GameData::Trainer`, versão PBS, vínculo de evento NPC, hash de compilação ou Game.exe foi auditado em uma instalação real de Sinnoh. O catálogo usa campos `null` e flags `false` para todos os 13.

## Referências por líder e campeão

A tabela exibe **somente espécies de Platinum**, sem o nível histórico para impedir que a apresentação pareça nível efetivo do Blue. Os níveis de Platinum existem no [manifesto auditável](../data/regions/sinnoh-trainer-teams-ch15.json) com `historical_levels` e `levels_are_not_runtime_levels=true`; **não** devem ser usados para configurar combate, PBS ou UI de nível.

| Treinador | Posição | Primeiro time histórico (Platinum) | Revanche histórica (Platinum) |
|---|---|---|---|
| Roark | Ginásio 1 · COAL | GEODUDE, ONIX, CRANIDOS | *Sem revanche nessa fonte* |
| Gardenia | Ginásio 2 · FOREST | TURTWIG, CHERRIM, ROSERADE | *Sem revanche nessa fonte* |
| Fantina | Ginásio 3 · RELIC | DUSKULL, HAUNTER, MISMAGIUS | *Sem revanche nessa fonte* |
| Maylene | Ginásio 4 · COBBLE | MEDITITE, MACHOKE, LUCARIO | *Sem revanche nessa fonte* |
| Crasher Wake | Ginásio 5 · FEN | GYARADOS, QUAGSIRE, FLOATZEL | *Sem revanche nessa fonte* |
| Byron | Ginásio 6 · MINE | MAGNETON, STEELIX, BASTIODON | *Sem revanche nessa fonte* |
| Candice | Ginásio 7 · ICICLE | SNEASEL, PILOSWINE, ABOMASNOW, FROSLASS | *Sem revanche nessa fonte* |
| Volkner | Ginásio 8 · BEACON | JOLTEON, RAICHU, LUXRAY, ELECTIVIRE | *Sem revanche nessa fonte* |
| Aaron | Elite Four 1 | YANMEGA, SCIZOR, VESPIQUEN, HERACROSS, DRAPION | YANMEGA, SCIZOR, VESPIQUEN, HERACROSS, DRAPION |
| Bertha | Elite Four 2 | WHISCASH, HIPPOWDON, GOLEM, GLISCOR, RHYPERIOR | WHISCASH, HIPPOWDON, GOLEM, GLISCOR, RHYPERIOR |
| Flint | Elite Four 3 | HOUNDOOM, RAPIDASH, FLAREON, INFERNAPE, MAGMORTAR | HOUNDOOM, RAPIDASH, FLAREON, INFERNAPE, MAGMORTAR |
| Lucian | Elite Four 4 | MRMIME, BRONZONG, ESPEON, ALAKAZAM, GALLADE | MRMIME, BRONZONG, ESPEON, ALAKAZAM, GALLADE |
| Cynthia | Campeã | SPIRITOMB, ROSERADE, MILOTIC, TOGEKISS, LUCARIO, GARCHOMP | SPIRITOMB, ROSERADE, MILOTIC, TOGEKISS, LUCARIO, GARCHOMP |

Observação de progressão: **Fantina é o 3º ginásio (Relic) e Maylene o 4º (Cobble)** em Platinum. A lista de HMs da CH11 pode estar em ordem de campo, mas não define a ordem narrativa de ginásios; ambas mantêm a associação correta entre badge e líder. As formas e espécies em equipes autorais não devem ser alteradas automaticamente durante o balanceamento dos líderes/Elite/Campeã.

## Balanceamento do Blue: não congelar níveis

A CH15 **não escreveu PBS nem alterou `Campaign.rb`, `Story.rb` ou `EvolutionScaling.rb`**. O [auditor](../scripts/regions/audit_sinnoh_teams_ch15.py) preserva estes contratos compartilhados:

- **Normal 70% e Master 90%:** o nível efetivo vem do maior nível não-ovo da equipe do jogador, limitado por `GameData::GrowthRate.max_level`, com o modo Master dependente do estágio de progresso da campanha.
- **Líder, Elite e Cynthia:** a escala de nível e as limitações de BST são aspectos separados. `BlueCampaign.boss?` preserva as espécies da equipe autoral; `BlueStory.regional_first_boss?` trata o primeiro confronto regional sem substituição artificial de espécies. A lógica de equipe mais forte precisa de uma versão autoral confirmada e provas posteriores.
- **Interface do site:** jamais converter `historical_levels` em níveis estáticos na página de equipes; só exibir nível calculado quando houver referência concreta do próprio motor e condições de batalha disponíveis. Não rotular a composição histórica como "equipe PBS instalada" ou "Full Power confirmado".

## Sondagem local PBS opcional

O auditor não precisa de fonte externa para a verificação padrão, mas aceita um arquivo PBS **informado explicitamente** para identificar possíveis entradas por nome/classe/versão, sem alterar nada:

```bash
python scripts/regions/audit_sinnoh_teams_ch15.py
python -m unittest discover -s tests -p 'test_sinnoh_teams_ch15.py' -v

# Opcional, após obter um PBS autorizado numa cópia local:
python scripts/regions/audit_sinnoh_teams_ch15.py --pbs "/caminho/da/copia/PBS/trainers.txt"
```

O resultado opcional inclui `pbs_candidate_source_sha256` e `pbs_candidates`, sempre com `status=UNTRUSTED_PBS_CANDIDATE_NOT_COMPILED`. Reconhecer um cabeçalho no texto **não** comprova compilação nativa, existência de evento de batalha, número da versão ou vínculo com NPC real. Duplicidade de identidade, equipe vazia, mais de seis Pokémon, linhas inválidas, arquivos ausentes e symlink são bloqueados. O comando é somente leitura e não modifica `game/`, arquivos de site ou saves.

Antes de tornar uma equipe jogável ainda serão necessários: PBS local de origem autorizado com hash, classe/nome/versão efetivamente compilados por `GameData::Trainer`, confirmação do NPC/mapa e evento de batalha, seleção de equipe Normal/Master/Full Power, Game.exe de teste e QA visual/reload, preservando as outras regiões.

## Testes e CI

[**GitHub Actions — run 43974961958**](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43974961958): **23 testes CH15** e **324 testes Python isolados de Sinnoh**, aprovados; a regra do Windows `RUN.bat` também passou. O pipeline geral de outras disciplinas é acompanhado separadamente e não equivale à certificação nativa de Sinnoh.

**Barras:** E **15/20 (75%)**, A **8/32 (25%)**, B/C/D **0/13**. As 13 fases nativas continuam com zero certificações.
