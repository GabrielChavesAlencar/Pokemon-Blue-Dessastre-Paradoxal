# Unova G05.4 — blackout, Centros Pokémon e preservação de estado

**WHITE_BW · fase somente GitHub · Unova planned · nenhum mapa, Game.exe ou save alterado.**

## Fontes canônicas

- [RegionalRespawn.rb](../scripts/battle_polish/RegionalRespawn.rb): o hook de `pbSetPokemonCenter` registra um Centro regional válido; antes do `pbStartOver`, substitui o checkpoint de outra região por um Centro lembrado da região atual ou por um fallback, caso exista. O motor Essentials continua responsável pela cura, derrota e transporte real.
- [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb): os HMs e itens-chave ficam guardados por região na Bolsa e no PC de itens. TMs e consumíveis permanecem compartilhados; Pokémon depositados ficam nas Boxes globais, e as mecânicas são restauradas por região.
- [Regions.rb](../scripts/battle_polish/Regions.rb): insígnias locais, esmeraldas globais e marcos regionais são aditivos; insígnias nativas de Decades não devem ser alteradas.
- [Economy.rb](../scripts/battle_polish/Economy.rb) e [Campaign.rb](../scripts/battle_polish/Campaign.rb): o saldo real de dinheiro pertence ao jogador e as mecânicas ativas pertencem à campanha; a G05.4 não inventa penalidades monetárias do Essentials.
- [Teste Ruby real](../tests/regional_respawn_runtime.rb): verifica em fixture separada o retorno a Kanto/Viridian, Decades/Cherryhill e Johto/Cherrygrove, com `pbStartOver` invocado uma vez, sem abrir um save real.

## Entrega da G05.4

- [Contrato auditável](../data/regions/unova-g05-blackout-state-contract.json), com campos desconhecidos de Unova como `null`.
- [Auditor e simulador em Python](../scripts/regions/audit_unova_g05_blackout_state.py), que verifica assinaturas relevantes do código Ruby e permite testes somente com identificadores `FIXTURE_*`, nunca com MapIDs reais.
- [122 testes automatizados](../tests/test_unova_g05_blackout_state.py), incluindo casos positivos, negativos e injeção de falhas após checkpoint, proprietário, cura sintética e transporte sintético.

O registro de Unova continua `planned`: **não existem MapIDs comprovados de seus Centros Pokémon, metadata de healing spot, pontos de fallback, eventos de nurse ou recibos de QA nativo**. Não é legítimo declarar que o jogador já pode perder uma batalha em Unova e aparecer corretamente na cidade inicial.

## Política de recuperação

1. Se o checkpoint nativo pertence a um Centro **verificado na região atual** e a propriedade é coerente, a simulação o preserva.
2. Caso contrário, utiliza o **último Centro verificado lembrado na região atual**.
3. Se não houver, utiliza um **fallback comprovado dentro dessa mesma região**.
4. Se nenhum dos anteriores existir, a simulação retorna `BLOCKED_NO_VERIFIED_LOCAL_CENTER` sem alterar o estado.

A prioridade não usa um checkpoint estrangeiro nem transforma `null` em MapID ou coordenadas. O Centro da outra região continua lembrado para um eventual retorno. Um atendente só registra novo ponto quando o mapa de origem corresponde a um Centro local verificado. O cenário de Unova é bloqueado como `PLANNED_REGION_RESPAWN_UNVERIFIED`.

### Duas limitações nativas observadas

O contrato documenta, **sem esconder como sucesso**, duas lacunas do hook Ruby atual:

- Quando não há fallback local válido, `before_blackout!` pode simplesmente retornar, deixando o checkpoint nativo antigo intacto. O simulador é mais rigoroso e bloqueia, mas **isso não corrige o jogo nativo**.
- O caminho `owner == current` do Ruby aceita um checkpoint estruturalmente válido sem confirmar novamente a qual região o mapa pertence. O simulador exige prova explícita de propriedade. Uma correção nativa e testes no Game.exe ainda serão necessários para garantir comportamento seguro em todos os casos.

Esses riscos ficam registrados como evidência de engenharia pendente, não como aprovação da região jogável.

## O que é preservado nas simulações

| Dados | Comportamento testado |
|---|---|
| Dinheiro e moedas | Saldos originais não mudam na transição simulada |
| Boxes e party | Pokémon não são duplicados, removidos ou teleportados para outra Box |
| TMs e consumíveis | Conteúdo compartilhado não muda |
| HMs e itens-chave | Bolsa, PC de itens, atalhos e cofres regionais permanecem iguais |
| Insígnias e esmeraldas | Insígnias nativas e conquistas por região permanecem iguais |
| Ligas, eventos de campo | Progresso fica intacto |
| Mecânicas | Configurações ativas e perfis por região permanecem intactos |
| Checkpoint | Apenas ponto de retorno e região proprietária são atualizados na simulação autorizada |

**Importante:** as regras de dinheiro real, possível perda de dinheiro pelo `pbStartOver`, autosave, transferência de cena e cura nativa são controladas pelo Essentials e não são validadas aqui. A G05.4 garante *somente* que a simulação offline não altera o saldo, os itens ou o progresso. Não faz afirmação falsa sobre uma penalidade monetária que o jogo possa aplicar.

Qualquer falha sintética após preparar checkpoint, owner, chamada do handler ou posição produz **rollback integral em memória** de todos os campos, inclusive contadores de cura e blackout. Nenhum save é aberto ou migrado.

## Executar e validar

~~~bash
python scripts/regions/audit_unova_g05_blackout_state.py --check
python scripts/regions/audit_unova_g05_blackout_state.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g05_blackout_state.py' -v
ruby -c scripts/battle_polish/RegionalRespawn.rb
ruby tests/regional_respawn_runtime.rb scripts/battle_polish/RegionalRespawn.rb
~~~

O CI de Unova executa os checks, a suíte Python, o teste Ruby isolado no Linux, os testes G05.4 no Windows e a validação do portal. Somente com todas as validações aprovadas a G05.4 será concluída na **Barra G 25/32 (78%)**, frente **G05 4/4**. Barra técnica A continua **0/8**, Unova jogável continua **0/32**.

## Próxima tarefa da Barra G

**G06.2 — Criar os guias das 74 áreas e da progressão da história**, com estados planejados/pendentes, fontes auditadas, ginásios e capítulos sem inventar conteúdo nativo instalado.
