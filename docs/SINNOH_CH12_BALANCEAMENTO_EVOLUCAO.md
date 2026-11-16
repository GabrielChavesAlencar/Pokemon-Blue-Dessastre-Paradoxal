# Sinnoh — CH12: contratos de balanceamento e evolução pelo runtime Blue

**Data:** 16/11/2026. **Status:** concluída quanto a **contrato + auditor + testes isolados**, não jogável.  
**CI:** [CH12 no GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43968704804).

## Fonte de verdade — sem duplicar os cálculos

A CH12 **não criou um segundo scaler nem reescreveu o conteúdo do PBS**, pois já existe implementação compartilhada em `scripts/battle_polish/Campaign.rb`, `Story.rb` e `EvolutionScaling.rb`:

| Regra | Contrato |
|---|---|
| Normal | `floor(maior_nível_não_ovo × 70/100)` |
| Master | `floor(maior_nível_não_ovo × 90/100)` |
| Limite mínimo e máximo | **1** e `GameData::GrowthRate.max_level` |
| Gatilho de Master | `BlueStory.stage == 3`, atualmente a partir de **11 esmeraldas/conquistas totais** |
| Equipe Master de treinador comum | Expansão de equipes pequenas até **4 Pokémon**, com no máximo **6 adversários** por lado |
| BST separado | `BlueStory.cap`: **350 / 450 / 540 / ilimitado**, condicionado ao estágio; evolução natural comprovada pode manter BST maior |
| Preservação PBS | Cópias da equipe oponente são escaladas; fontes de treinador, chefes, líderes, rival e equipes autorais não são reescritos |

**Atenção ao nome level cap:** o código de save regional **não tem um campo confiável de número de level cap por insígnia**. O que existe hoje para ajustar níveis é o maior nível não-ovo da equipe do jogador (limitado ao máximo do motor), e separadamente um limite de BST por estágio. Adicionar um novo cap numérico por insígnias seria **outra funcionalidade**, que exigiria contrato e integração próprios; a CH12 não inventou esse valor.

## Evoluções automáticas testadas

Depois do escalonamento para o nível efetivo do inimigo, o runtime consulta o catálogo nativo `GameData::Species#get_evolutions(true)`:

| Método | Limiar |
|---|---|
| Por nível | Nível da evolução **+ 5** |
| Pedra/item simples | Nível **30** |
| Troca | Nível **40** |
| Felicidade | Nível **45** |

No teste com fontes **sintéticas**, as famílias de Turtwig → Grotle → Torterra, Chimchar → Monferno → Infernape e Piplup → Prinplup → Empoleon evoluem conforme o nível escalado. Roselia → Roserade, Graveler → Golem e Riolu → Lucario cobrem pedra, troca e felicidade condicionada a horário. As formas especiais, ramos ambíguos (ex.: Eevee) e condições nativas não verificáveis continuam protegidas: nenhum destino é adivinhado.

Os testes confirmam que os chefes não têm suas espécies trocadas automaticamente, a fonte PBS não é modificada, os ovos não aumentam a referência de progressão, a forma selvagem inicial preserva possibilidade de encontro, e o sistema não escala batalhas fora do modo História. A inclusão de 8 insígnias locais de Sinnoh no cálculo de esmeraldas **não sobrescreve as insígnias nativas de Decades**.

## Arquivos, execução e bloqueios

- [Manifesto CH12](../data/regions/sinnoh-trainer-evolution-contract.json): fontes reais, limites e famílias sintéticas, `planned` e `can_install=false`.
- [Auditor CH12](../scripts/regions/audit_sinnoh_trainer_evolution.py): rejeita divergências ou falsas afirmações de nível, cap, estágio, evolução e jogabilidade.
- [Testes negativos Python](../tests/test_sinnoh_trainer_evolution_ch12.py): **15** casos.
- [Teste Ruby integrado](../tests/sinnoh_evolution_ch12_runtime.rb): roda `Battle.initialize` com os módulos Blue verdadeiros e dados autorais em memória, sem ROM ou executável.

```bash
python scripts/regions/audit_sinnoh_trainer_evolution.py
python -m unittest discover -s tests -p 'test_sinnoh_trainer_evolution_ch12.py' -v
ruby tests/sinnoh_evolution_ch12_runtime.rb tests/regions_data_fixture.rb scripts/battle_polish/Regions.rb scripts/battle_polish/EvolutionScaling.rb scripts/battle_polish/Story.rb scripts/battle_polish/Campaign.rb data/regions/sinnoh-trainer-evolution-contract.json
```

**Não executado:** `Game.exe`, compilador Pokémon Essentials, partidas nativas de Sinnoh e JoiPlay. Os casos usam espécies e treinadores de teste em memória, sem criar encontros, sprites, times reais, NPCs ou salvar alterações em `game/`. As barras A/B/C/D permanecem inalteradas.
