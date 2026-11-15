# Evolução dinâmica de treinadores e selvagens — Blue Story

**Implementado na main:** 15/11/2026. **Aprovação:** testes Ruby isolados automatizados; **teste visual no Game.exe do Windows/Android pendente**.

## Regra e fonte de dados

A evolução é consultada **no catálogo GameData::Species#get_evolutions(true)** do Pokémon Essentials v21.1 já instalado. Não existe tabela manual de Pokémon alterada, nem reescrita de PBS, encontros, times autorais, saves, Pokédex ou arquivos de mapa.

O balanceamento nativo do projeto utiliza os níveis da equipe do jogador:
- Treinadores comuns: `BlueCampaign.trainer_level` = 70% do maior nível da equipe, ou 90% no estágio Master.
- O indicador **progresso para liberar formas selvagens** é o nível do Pokémon **não-ovo mais forte do jogador**, limitado ao nível máximo de GameData::GrowthRate. Atualmente não foi encontrado um número único de "level cap regional" na estrutura persistida de Blue Regions. Se houver futuramente um cap oficial separado, o leitor de progressão deverá consultá-lo.
- BST: `BlueStory.cap` continua 350 / 450 / 540 / ilimitado conforme as conquistas. **Somente evolução regular comprovada pelo nível final** pode ultrapassar o teto de BST; nenhuma espécie forte arbitrária ganha exceção.

### Treinadores: evolução do time já escalado

| Evolução | Regra de escolha |
|---|---|
| Por nível | nível natural + 5 (Bulbasaur → Ivysaur no 21, Ivysaur → Venusaur no 37, Rattata → Raticate no 25) |
| Por pedra ou item de evolução simples | nível 30, sem consumir pedra do treinador |
| Troca simples/com item | nível 40 |
| Felicidade (com gênero ou horário quando exigido) | nível 45 |

As alterações ocorrem em uma cópia temporária dos Pokémon inimigos **depois** de aplicar 70%/90% do nível; recalcula golpes naturais, habilidade e atributos. Mantém a equipe original do PBS e o Pokémon do jogador intactos. Preserva os shinies do Pokémon copiado e não modifica captura ou save. Times autorais de **líderes, Elite Four, campeões e chefes/rivais** não são evoluídos automaticamente.

O adaptador BST de `Story.rb` reconhece uma evolução válida para permitir Ivysaur (BST 405) ou Raticate (BST 413) mesmo no estágio inicial BST 350. **Isso não remove os limites de outros Pokémon que já eram fortes demais.**

### Selvagens: variedade preservada no habitat

Os encontros normais em grama, cavernas, Surf, pesca e outros métodos que passam por `PokemonEncounters.choose_wild_pokemon` conservam **a espécie e a probabilidade original do slot no PBS**. Quando um slot é sorteado, ele pode vir em uma evolução compatível com o progresso.

Distribuição sugerida e implementada **dentro dos slots da mesma família**, não da tabela inteira:

| Cap de progresso relativo ao desbloqueio | Chance de forma evoluída no slot |
|---|---:|
| Abaixo do limiar da evolução | 0% |
| 0–4 acima do limiar | 15% |
| 5–14 acima do limiar | 30% |
| 15–24 acima do limiar | 45% |
| 25 ou mais acima do limiar | 60% |

Para Rattata, o limiar é 25 (nível natural de evolução 20 + 5). Com progresso 30, **aproximadamente 30% dos slots originalmente de Rattata podem se tornar Raticate**; os demais continuam Rattata. O Raticate gerado respeita nível mínimo 25, sem ultrapassar o progresso de referência. Em uma cadeia de dois estágios, cada estágio exige um sorteio válido.

Um encontro estático/evento especial, lendário fixo, inicial ou Pokémon presente na equipe não é modificado pelo seletor de encontros normais.

### Proteções de compatibilidade

- Ramificações com múltiplos destinos possíveis (p.ex. Eevee) **não são escolhidas aleatoriamente**; ficam intactas. O mesmo vale para métodos cujo gatilho não pode ser verificado com segurança (local especial, movimento exigido, tempo/clima, parceiro no time etc.).
- Gênero e horário são respeitados quando a API nativa permite confirmar as condições. Formas regionais não padrão, marcadores de Paradoxo, Mega, Ultra Beast, Lendário, Mítico, Convergente e espécies pendentes são preservados.
- O cálculo não aumenta os níveis básicos dos slots; aplica piso mínimo somente à **forma evoluída**.
- O **Habitat Dex no jogo** mostra tanto a forma original quanto suas evoluções que já podem aparecer; não as marca como vistas/capturadas automaticamente.
- O site estático não recalcula estas chances em tempo real, pois dependem da partida atual.

## Arquivos e testes

- `scripts/battle_polish/EvolutionScaling.rb`: cálculo central e hook `PokemonEncounters`.
- `scripts/battle_polish/Campaign.rb`: evolução dos treinadores após a escala.
- `scripts/battle_polish/Story.rb`: exceção restrita do BST e inicialização do módulo.
- `scripts/battle_polish/Habitat.rb`: índice de encontros dinâmicos no Habitat Dex.
- `scripts/battle_polish/install.py` e `meta.txt`: entregam o módulo pelo mesmo `Blue-Story.exe`, sem executável novo.
- `tests/evolution_scaling_runtime.rb`: evolução/variedade/habitat/cap e exclusões.
- `tests/evolution_battle_runtime.rb`: cadeia real de módulos `Battle.initialize`, BST, 70/90%, chefes e equipe original.
- `tests/test_evolution_install_contract.py`: integridade do instalador e plugins.
- CI: [Evolução dinâmica — GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/evolution-scaling.yml).

**Teste real pendente:** executar `Blue-Story.exe`, continuar o save, confirmar um treinador comum escalado para nível >=21 usando Ivysaur, o mesmo treinador em nível anterior usando Bulbasaur, um encontro que contenha Rattata com progresso >=30 podendo também gerar Raticate, chefes intactos, shinies, captura e troca de região sem alterar os itens-chave/HMs. Testar também no Android.

