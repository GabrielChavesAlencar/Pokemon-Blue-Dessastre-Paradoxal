# Kanto — Tênis de Corrida após Brock (Piloto Windows)

## Regra de história

No **Testar Kanto/Piloto de Kanto**, o treinador precisa vencer Brock e receber **Boulder Badge de Kanto** antes de seguir de **Pewter para a Rota 3** pelo acesso já protegido pelo guarda.

Na primeira tentativa autorizada de atravessar essa saída, **a mãe do protagonista aparece ao lado dele, entrega os Tênis de Corrida e desaparece ao fim da cena**. O gráfico é reaproveitado do evento real da mãe na casa de Pallet (FRLG source `Map007`, evento 13). O evento de cenário é normalmente invisível e atravessável, portanto não cria uma segunda barreira nem aparece antes de Brock.

O jogador então:
- recebe a mensagem de obtenção e o efeito sonoro de item;
- ganha `$player.has_running_shoes = true` (capacidade nativa do Pokémon Essentials);
- passa a usar `$PokemonSystem.runstyle = 1` (**correr por padrão sem pressionar o botão de corrida**);
- registra `pilot_mom_running_shoes = true` no estado regional salvo de Kanto, sem reentrega ou duplicação.

**Tênis de Corrida não são um HM nem um item de Bolsa**: são um equipamento/habilidade nativos do jogador. Não consomem espaço e não substituem golpes. A corrida respeita as restrições normais do jogo (cenas, menus, terrenos em que correr não é permitido, Surf e bicicleta).

## Segurança e compatibilidade

- O desbloqueio exige a **Boulder Badge local de Kanto**, não cristais ou insígnias de outra região.
- O gatilho de caminhada usa as coordenadas do próprio bloqueio de Brock geradas em `Data/blue-kanto-pewter-route3-gate.txt` pela conexão original `Map025 ↔ Map032`.
- Não concede os tênis ao vencer Brock dentro do ginásio, entrar em outro mapa ou caminhar em direção diferente.
- Saves antigos que já venceram Brock recebem os tênis na **primeira travessia elegível**, sem precisar recomeçar.
- O marcador `Kanto pilot.json` limita a entrega à cópia isolada. Decades/Johto/Hoenn/Sinnoh não sofrem alterações na velocidade nem em seus saves.
- A mãe é renderizada somente durante a cena, com `character_name=` no evento; nenhum hook de `Game_Event#refresh` é instalado.

## Testes

`ruby tests/kanto_running_shoes_runtime.rb scripts/regions/KantoPilot.rb` valida ausência do prêmio antes de Brock, insígnia de outra região, posicionamento da saída, entrega única, gráfico visível durante a cena, desaparecimento ao final, novo padrão de corrida, save/reload e isolamento de Decades.

`python -m unittest tests/test_kanto_parcel_story.py -v` valida a montagem do evento invisível e o uso do sprite de Pallet.

Após atualizar a `main`, execute `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`, carregue seu save e siga para a saída da Rota 3. Verifique se **a mãe aparece, fala, entrega os tênis, desaparece e o personagem corre sem segurar nenhum botão**. Recarregue o save e volte ao local: o prêmio não pode reaparecer.

**Aceite jogável permanece pendente até o teste real no Game.exe.** A verificação nativa da CI depende do pacote fonte FRLG com SHA-256 correto.
