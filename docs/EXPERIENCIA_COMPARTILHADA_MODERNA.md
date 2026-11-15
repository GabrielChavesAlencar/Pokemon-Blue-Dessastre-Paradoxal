# Experiência compartilhada moderna — Dessastre Paradoxal

## Objetivo

Ativar nas campanhas normais de **Blue: Dessastre Paradoxal**, incluindo **Testar Kanto/Piloto de Kanto**, o compartilhamento automático de experiência usado nos jogos principais modernos. Não é necessário obter nem equipar `EXPALL` ou `EXPSHARE`. Batalhas de PvP, Battle Lab e Arena permanecem isoladas.

## Regras de experiência

O motor usado pelo projeto é **Pokémon Essentials 21.1** e já inclui `Battle#pbGainExp` com `$player.has_exp_all || $bag.has?(:EXPALL)`. O recurso nativo é o Exp All moderno, **não** o bug de distribuição da primeira geração.

Em uma batalha válida (Pokémon oponente derrotado ou capturado, desde que o jogo autorize EXP):

| Quem recebe | Resultado |
| --- | --- |
| Pokémon da equipe que participou | Sua experiência normal, preservando a fórmula de batalha e as opções de divisão preexistentes |
| Pokémon da equipe não participante, apto | 50% da referência de experiência nativa |
| Desmaiado ou ovo | Não recebe |
| Pokémon na Box | Não recebe |
| Nível máximo | Não ganha mais EXP (EVs continuam respeitando o motor nativo) |

A função nativa já executa EVs, bonificações de treinador/troca/Exp Charm, estatísticas, crescimento, limite de nível, animação da barra e aprendizado de golpes. Não duplicar essas rotinas, criar um segundo cálculo nem somar EXP manualmente. Vários participantes continuam seguindo `Settings::SPLIT_EXP_BETWEEN_GAINERS` do jogo instalado.

## Implementação

- `scripts/battle_polish/PartyExperience.rb` instala um `prepend` em `Battle#pbGainExp`, única vez. Enquanto o cálculo nativo de **batalha interna com experiência habilitada** é executado, a propriedade `$player.has_exp_all` é temporariamente ativada e restaurada em `ensure`.
- Não altera itens na Bolsa, nem salva uma nova propriedade/flag permanente. Saves antigos recebem a regra imediatamente; o jogador que já possuía EXPALL não recebe EXP em dobro.
- Ignora explicitamente `@blue_lab_battle`, `BlueBattleLab::ACTIVE`, `BlueBattleOptions.battle_area?`, batalhas externas e `expGain = false`. Pokémon que não participam de combate não recebem experiência em modos que não devem conceder EXP.
- `scripts/battle_polish/Story.rb` registra a instalação no momento da compilação do plugin. `install.py` e `meta.txt` distribuem o recurso para o jogo principal. `scripts/regions/pilot.py` copia e acompanha o arquivo no hash para reconstruir o piloto isolado de Kanto.
- Todas as regiões de campanha usam a rotina nativa; nenhum mapa, insígnia, treinador, encontro selvagem, evento ou sistema de HP/batalha foi modificado.

## Testes

`ruby tests/party_experience_runtime.rb scripts/battle_polish/PartyExperience.rb` usa uma simulação da distribuição do Essentials para verificar integração com a função nativa, participantes e reservas, desmaiados, ovos, Box, nível máximo, EVs, múltiplos participantes, `EXPALL` já obtido, captura, `expGain=false`, PvP, Battle Lab, Arena e restauração do valor original após erro.

**Validação no Game.exe (pendente):**
1. Atualizar a `main`, reconstruir `Testar Kanto` com `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild` e carregar um save existente com 2 a 6 Pokémon.
2. Vencer um Pokémon selvagem usando somente o primeiro. Verificar EXP normal no participante e EXP reduzida nos demais membros aptos, sem EXP para desmaiados.
3. Trocar dois Pokémon durante a mesma batalha, testar a distribuição segundo a opção já existente de divisão entre participantes.
4. Capturar um selvagem e verificar o recebimento se o motor concede EXP por captura.
5. Verificar que o segundo membro consegue evoluir e aprender golpes normalmente após subir de nível; preservar o save.
6. Testar o jogo principal e uma batalha sem EXP em modo de laboratório: não deve haver distribuição indevida.

**A regressão Ruby prova a integração e os estados simulados, não a jogabilidade real**. A verificação nativa de Kanto na CI pode ficar indisponível enquanto o arquivo FRLG da fonte não corresponder ao SHA-256 exigido.
