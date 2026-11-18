# Sinnoh jogável J05 — inicial único, Barry, Rowan e save regional isolado

**18/11/2026.** J04 PR #229 foi integrado na main, com 12/12 checks. Esta J05 trabalha no **código Ruby existente** do `BlueSinnohPilot` e na ligação real entre os comandos de eventos de Poké Bola gerados na J04 e o handler do motor Blue. Não instala conteúdo e não roda Game.exe/JoiPlay.

## Implementação efetiva

- Cinco handlers já existentes e preservados: `BlueSinnohPilot.mother`, `barry_intro`, `rowan_briefcase`, `barry_rival`, `rowan_pokedex`. Não acrescenta falsas equipes/níveis, nem seleciona um starter em diálogos.
- Corrige o bug de J04: os comandos Ruby de `SN_BALL_TURTWIG`, `SN_BALL_CHIMCHAR` e `SN_BALL_PIPLUP` agora chamam **`BlueSinnohPilot.choose_starter_from_ball(:ESPÉCIE)`**, e não `BlueSinnohPilot.choose_starter(:ESPÉCIE)` (método que apenas mostrava diálogo sem conceder Pokémon). Os testes J04 verificam as três chamadas exatas.
- A concessão do inicial exige o contexto `$PokemonGlobal.blue_regions` (Sinnoh atual, save Sinnoh), Rowan ter explicado a maleta, espécies permitidas, equipe com vaga (não enviar starter ao PC), função nativa `pbAddPokemonSilent` e ausência de concessão anterior. Bloqueia reentrada, confere **exatamente um** novo Pokémon com espécie e nível 5, preserva os demais membros e só então altera **um** Hash de flags regionais em operação `replace`. Falhas de retorno, exceção, mudança de região/jogador ou espécie/nível incorretos não persistem a flag, e o membro novo é removido **somente se identificável com segurança**. Não regrava saves nem boxes.
- Barry só pode iniciar quando há prova do piloto QA ou marcador validado, motor `TrainerBattle.start`, e **as três variantes compiladas** do rival são conferidas: Turtwig→Chimchar 0, Chimchar→Piplup 1, Piplup→Turtwig 2. Todas exigem exatamente um oponente PBS de nível 5. Equipes reais e escala 70% Normal/90% Master continuam responsabilidade do sistema `BlueCampaign` e suas provas específicas, **não** são inventadas por este PR. Resultado `nil`, exceção ou equipe inválida não gravam vitória/derrota, `false` como perda `canLose` confirma o tutorial.
- Rowan registra `pokedex_received` apenas quando o campo verdadeiro do jogador aceita a Pokédex; se o setter falha, o checkpoint de Sinnoh é revertido sem tocar outras regiões.
- Salvamento regional: sem pasta paralela criada, novas flags continuam exclusivamente em `$PokemonGlobal.blue_regions["sinnoh_pilot"]`, validado e serializável com Marshal (conforme motor). O perfil de QA de `SinnohQAStart.rb` mantém a checagem por `mkxp.json`, `Game.ini` e SHA de compile; **não é liberado sem proof físico**. Nada é gravado em saves pessoais de Decades/Kanto/Johto/Hoenn.

### Limitações de rollback e evidência

O motor `pbAddPokemonSilent` **não oferece transação nativa**. A compensação só remove o novo membro quando a equipe original está intacta e foi identificado um único membro acrescentado ao fim. Se uma versão desconhecida do motor movimentar Pokémon para boxes ou reordenar a equipe durante a concessão, a ferramenta **bloqueia em vez de tentar sobrescrever a equipe inteira ou storage**. Um teste real de Game.exe isolado ainda é necessário antes de aceitar essa propriedade como validada. Nível 5 é a semente fixa do inicial; nível de treinadores continua dinâmico no BlueCampaign.

## Regressões

`ruby tests/sinnoh_j05_atomic_runtime.rb scripts/regions/SinnohPilot.rb`

A nova suíte exerce sete modos de falha de concessão, reentrância, três iniciais, equipe cheia, saves serializados/recarregados, mudança de região, três equipes Barry, ausência/alteração do PBS, derrota `canLose`, erro/retorno nil, falha do setter da Pokédex e integridade de flags de outras regiões. Regressões anteriores J04/J03/J02/CH07/CH08/G08/portal também rodam no CI.

## Estado e próximos passos

**Engenharia J: 5/8 (62,5% somente após CI); jogabilidade comprovada: 0/8.** Mapas reais instalados **0/9** (cinco faltam: quarto, 1F, casa Barry, Lago Verity, laboratório Rowan); eventos nativos **0/24**, G12 nativo **0/44**, Game.exe/JoiPlay não executados. R07/R08/R09 pendentes, direitos não aprovados. Sinnoh permanece `planned`/não jogável.

Próxima fase: [J06 — launcher/instalador Windows apenas em cópia QA isolada](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/230). O botão do portal usa o JSON `next_stage: "J06"` e abre o pedido de execução para o usuário enviar, sem iniciar ações por conta própria.
