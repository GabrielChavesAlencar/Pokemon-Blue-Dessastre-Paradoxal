# Regiões fora de Decades — regras de balanceamento e times Full Power

> Contrato de implementação · 14/11/2026 · referência: pedido de correções de Kanto.
> **Decades permanece inalterado.** Este documento registra regras novas; o código precisa ser validado antes de ser considerado implementado.

## 1. Objetivo

Para **Kanto, Johto, Hoenn, Sinnoh e demais regiões que forem integradas**, separar o **primeiro desafio** contra líder de ginásio, Elite Four e Campeão de uma futura **revanche com o time mais forte (Full Power)**.

- **Primeiro confronto:** não aplicar os limites de **BST (soma dos base stats)** nem de **base power (potência base de golpes)** que hoje dependem das insígnias/esmeraldas. O oponente conserva espécies, formas, golpes, itens e habilidade definidos no time original da sua região. Não reduzir artificialmente a potência nem substituir um Pokémon forte por um mais fraco.
- **Revanche Full Power:** aplicar as regras de balanceamento de BST e base power por estágio global às equipes explicitamente marcadas e auditadas como **Full Power**, conforme o comportamento solicitado. Não aplicar automaticamente a toda revanche, batalha comum, rival ou chefe.
- **Decades:** conservar o comportamento atual em todas as batalhas, com os limites por estágio já existentes.
- **Treinadores comuns:** manter a regra vigente, exceto se forem futuramente classificados de maneira explícita e documentada como líderes/Elite/Campeão.

**A exceção se refere somente a BST e base power**. As regras já implementadas de level cap, escalonamento de nível dos adversários (inclusive Master: 90% em vez de 70%), progressão, insígnias por região, itens e restrições de Pokémon especiais continuam em vigor e não podem ser desativadas como efeito colateral.

## 2. Regras vigentes a preservar

Em `scripts/battle_polish/Story.rb`, `BlueStory.stage` usa a contagem global de cristais/esmeraldas, incluindo as conquistas regionais únicas (`BlueRegions.crystal_total`), mas não edita as insígnias nativas. A transformação de espécies via `BlueStory.adjust` aplica o teto BST:

| Estágio | Total global para entrar no estágio | Limite BST atual |
|---|---:|---:|
| Inicial | 0–1 | 350 |
| Intermediário | 2–4 | 450 |
| Avançado | 5–10 | 540 |
| Master | 11+ | Sem limite |

Em `scripts/battle_polish/Balance.rb`, `BlueTrainerMoves.apply` impõe limites de potência base aos golpes do adversário: 60 no Inicial, 90 no Intermediário e sem limite no Avançado/Master. Esses limites são aplicados **somente se o contexto e o modo permitirem**; a nova política de região/primeiro confronto/Full Power precisa ser consultada por **ambos** os adaptadores, não só por um.

## 3. Tabela de decisão (obrigatória)

| Região | Tipo de oponente | Tipo de encontro | Aplicar teto BST? | Aplicar teto base power? |
|---|---|---|---|---|
| Decades | Qualquer | Qualquer | Sim, conforme regra atual | Sim, conforme regra atual |
| Fora de Decades | Líder de ginásio | Primeiro confronto | **Não** | **Não** |
| Fora de Decades | Elite Four | Primeiro confronto | **Não** | **Não** |
| Fora de Decades | Campeão | Primeiro confronto | **Não** | **Não** |
| Fora de Decades | Líder/Elite/Campeão | Revanche marcada Full Power | **Sim**, estágio global | **Sim**, estágio global |
| Fora de Decades | Líder/Elite/Campeão | Revanche sem perfil Full Power | Preservar regra original até definição | Preservar regra original até definição |
| Fora de Decades | Treinador comum | Combate normal | Sim, regra atual | Sim, regra atual |

**Não usar só o nome visível do treinador** para decidir: pode haver um Giovanni chefe da Equipe Rocket distinto de Giovanni líder de Viridian, além de versões de Campeão. A chave deve considerar **região + tipo do oponente + ID/versão do time + contexto do encontro**. O primeiro encontro não pode virar Full Power apenas porque o jogador tem muitas esmeraldas.

## 4. Contrato de implementação do Full Power

1. Identificar pelo tipo de treinador e por **IDs regionais estáveis** cada um dos oito líderes de Kanto, os quatro membros da Elite e o Campeão (com variantes do inicial). Adotar o mesmo padrão ao integrar Johto, Hoenn, Sinnoh etc. Não inventar NPCs ou times sem um catálogo auditado.
2. Preservar a equipe original em PBS como **versão inicial**. Criar equipe Full Power em **outra versão/identidade explícita**, sem substituir o original nem reatribuir suas vitórias.
3. Acesso à revanche Full Power somente **após concluir todas as dez Ligas do circuito** (`BlueRegions.profile(state, true) == :world_champion_rematch`), tendo vencido o confronto inicial da região e dispondo de equipe canônica verificada. **Uma única Liga, inclusive Kanto, não desbloqueia Full Power.**
4. Full Power: usar o **time oficial mais forte documentado por jogo e cargo**, em `docs/ESTUDO_TIMES_MAIS_FORTES_KANTO_LIDERES_ELITE4_CAMPEOES.md` e `docs/KANTO_TIMES_FORTES_IMPLEMENTACAO_PASSO_A_PASSO.md`. Preservar os cinco integrantes quando o oficial tiver cinco, duplicatas canônicas e os níveis de referência, sem misturar elencos de jogos diferentes. O jogo usa escalonamento de nível durante a batalha. **O teto BST/base power solicitado continua ativo nesta modalidade**; qualquer equipe equilibrada derivada deve ser diferenciada da referência oficial.
5. Durante a batalha, carregar contexto do time **antes** de `Battle.new`/`BlueStory::Teams` e de `BlueTrainerMoves.apply`, e limpar o contexto em bloco `ensure`, inclusive em derrota, fuga permitida, exceção e mudança de mapa.
6. Vitória inicial entrega a insígnia **uma única vez**; revanche Full Power não entrega segunda insígnia, não reescreve progresso da Liga nem altera a quantidade global de esmeraldas.
7. Em saves anteriores sem esse estado, o combate inicial permanece inicial; migração não destrutiva e sem zerar derrotas, Pokédex ou conquistas.
8. Para equipes Full Power ausentes ou não auditadas, bloquear a revanche **com mensagem clara** e registrar pendência, em vez de lançar batalha com uma equipe fictícia.

## 5. Aplicação regional e isolamentos

- **Kanto piloto:** mudanças no `scripts/regions/KantoPilot.rb`, catálogo PBS regional e construtor `scripts/regions/pilot.py`; cópia isolada em `.blue-work`.
- **Campanha principal:** adaptadores de `scripts/battle_polish/Story.rb` e `Campaign.rb`/`Balance.rb`, com predicado de região e contexto de batalha. O código de Decades não deve mudar de efeito.
- **Outras regiões:** adotar os mesmos contratos quando seus encontros reais estiverem conectados; não marcar como jogáveis apenas por existir documentação.

## 6. Aceite e regressão

- Testar primeiro Brock, Misty, Giovanni, Lorelei, Bruno, Agatha, Lance e Blue sem substituir espécies nem reduzir golpes por BST/base power, inclusive com muitas esmeraldas globais.
- Testar equipes Full Power com todas as faixas de esmeraldas, demonstrando os limites BST 350/450/540/sem limite e base power 60/90/sem limite/sem limite.
- Confirmar que 1 Liga, 9 Ligas e 10 Ligas geram bloqueio, bloqueio e disponibilidade de revanches Full Power respectivamente; não duplicar Hall of Fame ou insígnias.
- Testar Kanto com e sem insígnias locais: a região atual é a fonte de classificação, a insígnia só é entregue na vitória inicial e o Full Power só surge após o desbloqueio.
- Executar provas de regressão de Decades (e dos saves anteriores), Johto e modo Battle Lab, preservando níveis, itens, música, times e flags.
- Distinguir **testes estáticos de CI**, **teste de engine nativa** e **jogabilidade manual no Windows**. Só registrar aprovação total quando houver evidência de cada camada.

## 7. Outras correções de Kanto solicitadas (fora do escopo deste MD)

Portas comuns de casas/cidades sem exigir Enter, placas interativas, árvores de Cut que existem na fonte, bloqueio Pewter → Rota 3 até vencer Brock, e duas páginas de Trainer Card (insígnias de Kanto e somatório global de insígnias/esmeraldas). Cada item exige implementação e verificação separadas; este documento **não declara esses itens concluídos**.
