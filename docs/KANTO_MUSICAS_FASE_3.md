# Kanto — Fase 3/6: BGM de batalhas, chefes e vitórias

**Estado:** implementação reproduzível no piloto e em instalações de Kanto; não é aceite de áudio audível nem de jogabilidade integral. Data: 12/11/2026.

Referências: [plano musical](KANTO_PLANO_APLICAR_MUSICAS.md), [Fase 2](KANTO_MUSICAS_FASE_2.md), [regras](../data/kanto-music-rules.json), [adaptador](../scripts/music/BlueMusic.rb).

## O que muda no jogo

O catálogo mantém **64 arquivos originais** (50 BGM/14 ME); a Fase 3 ativa apenas **8 BGM distintas adicionais**, importadas em `Audio/BGM/Kanto` sem sobrescrever MP3s já presentes, saves ou músicas nativas. Em conjunto com as 17 BGM ambientais, o instalador utiliza **25 BGM** distintas. O compilador gera 142 registros SCOPE com **MapIDs reais**, as 49 regras MAP da Fase 2, os dois modos TRANSPORT, oito regras BATTLE e três assinaturas BASEPOOL das playlists **padrão** de Decades. Nenhum número de MapID FRLG é executado diretamente.

| Contexto comprovado | Música Kanto | Condição |
|---|---|---|
| Pokémon selvagem comum | 1-18 — Battle! (Wild Pokémon) | Kanto ativo + MapID permitido |
| Vitória selvagem | 1-19 — Victory! (Wild Pokémon) | Vitória selvagem, sem tema específico de evento |
| Treinador comum de Kanto | 1-11 — Battle! (Trainer) | Classe real `BLUE_KANTO_*`, que não seja líder/Campeão |
| Vitória contra treinador comum | 1-12 — Victory! (Trainer) | Classificação efetiva salva no contexto de batalha |
| Líder de ginásio | 1-27 — Battle! (Gym Leader) | Uma das 8 classes `BLUE_KANTO_LEADER*` verificadas; incluindo duplas |
| Vitória sobre líder | 1-28 — Victory! (Gym Leader) | Classificação gym da batalha, sem tocar vinheta de insígnia |
| Pokémon lendário selvagem | 1-53 — Battle! (Legendary Pokémon) | A espécie é marcada `Legendary` nos metadados; não basta BST alto, Mythical, UltraBeast ou Paradox |
| Blue Campeão | 1-70 — Final Battle! (Rival) | **Classe real** `BLUE_KANTO_CHAMPION_BLUE` + nome `Blue` + mapa simbólico `CHAMPION_HALL` + Liga de Kanto ativa |

## Prioridades e segurança

1. **Região e mapa:** sem Kanto válido e MapID compilado não-preview, o motor conserva os temas de Decades e eventos originais. Nenhum campo novo é gravado nos saves.
2. **Tema especial de evento:** `nextBattleBGM` e `nextBattleVictoryBGM` vencem as regras de Kanto. O comportamento de sorteio anterior de Decades permanece inalterado.
3. **Preferências do usuário:** `custom`, `mute`, listas aleatórias editadas ou alterações de volume/pitch continuam prioritárias. As três assinaturas BASEPOOL identificam **apenas listas aleatórias idênticas à distribuição padrão**, sem escrever em `Data/blue-music.json` ou `Data/blue-music.rxdata`.
4. **Batalhas duplas / preparação:** a categoria real (comum, gym, campeão, wild, lendário) é armazenada **somente em memória**, durante a batalha. A consulta para abertura, preparação da batalha e vitória usa a mesma classe, evitando mudanças no meio da luta. O motor mantém o comportamento nativo em casos sem identificação suficiente.
5. **Identidade:** as imagens provisórias de líderes não são usadas para classificar. O Blue da Rota 1, Silph Co. ou outra revanche não é confundido com o Campeão. Um Giovanni `ROCKETBOSS` não recebe música de líder de ginásio; Giovanni `LEADER_GIOVANNI` recebe.
6. **Fallback:** se algum dos oito MP3s faltar, o registro de associação correspondente não é emitido e o motor pode tocar o tema preexistente. O importador rejeita arquivos divergentes, acessos por links simbólicos e sobrescrita indevida.

### Assinaturas BASEPOOL

O `data/shared-music.json` define listas aleatórias padrão de Decades para `wild`, `trainer` e `gym`. O compilador emite uma assinatura SHA-256 para cada lista, volume e pitch. Somente quando a seleção global continua **exatamente idêntica** ao preset fornecido, a música regional de Kanto substitui o preset durante uma batalha de Kanto. Isso **não altera** o sorteio em Decades.

*Limite:* uma escolha manual idêntica ao preset original é indistinguível do próprio padrão sem salvar um registro adicional; para priorizar uma playlist em Kanto, configure um `custom` ou altere a lista.

## Faixas pendentes sem evento comprovado

As introduções `1-20` (treinador masculino), `1-33` (feminino), `1-46` (vilão) e a cena tensa `1-26` ficam **desativadas** até haver gatilho de evento comprovado. Não serão usadas como BGM de batalha genérica nem disparadas por suposição. As 14 faixas ME permanecem para a Fase 4.

## Testes automatizados

~~~powershell
python -m unittest discover -s tests -p "test_kanto_music*.py" -v
python scripts/music/install_kanto_music.py --audit
ruby -c scripts/music/BlueMusic.rb
ruby tests/kanto_music_runtime.rb
ruby tests/kanto_music_battles.rb
python scripts/music/install_kanto_music.py --game .blue-work/kanto-pilot --approved
python scripts/music/compile_kanto_music.py --game .blue-work/kanto-pilot
~~~

O [workflow de regressão](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/regression.yml) verifica o comportamento Ruby em fixture sintética e a auditoria de 64 MP3. O [piloto nativo](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml) verifica 142 SCOPE, 49 MAP, 2 TRANSPORT, **8 BATTLE, 3 BASEPOOL e 25 MP3** tanto no piloto isolado quanto no jogo integrado descartável. Não modifica os saves do usuário.

**Não afirmar que a reprodução interativa foi comprovada**: abertura de batalha, transição para vitória, pausa, fuga/derrota, codec/volume/loop e troca de região em uma sessão jogável ainda requerem teste real do Game.exe ou prova nativa específica. **Barra 2 — Aceite integral: inalterada.**

**Próxima etapa:** [Fase 4](KANTO_PLANO_APLICAR_MUSICAS.md#fase-4--as-14-vinhetas-me-disparadas-por-eventos) — aplicar as 14 músicas `ME` às ações confirmadas, sem disparo duplicado e com retorno do BGM.
