# Kanto — Correção do Centro Pokémon e da entrega de Oak (Viridian)

**Escopo:** piloto isolado de Kanto e seu instalador; sem sobrescrever mapas, flags, áudio ou saves de Decades/Johto/Sinnoh.

## Fluxo da primeira visita

1. Escolher o inicial no laboratório de Oak. A recompensa antecipada de cinco Poké Bolas foi removida (as duas Potions de partida permanecem).
2. Entrar pela primeira vez no **Poké Mart de Viridian**. Um evento **Autorun** isolado, invisível e de uso único (self-switch A), faz o funcionário chamar o jogador, caminhar dois passos automaticamente e iniciar o diálogo. O pacote é persistido exclusivamente em `pilot_oak_parcel_received`, sem importar um item estranho ao catálogo do Decades.
3. Voltar ao laboratório de Oak e conversar com ele. A música da cena de Oak é iniciada; após adicionar com sucesso **cinco Poké Bolas** à Bolsa, a Pokédex é habilitada e `pilot_oak_parcel_delivered` é gravado. Bolsa sem espaço: o evento não é concluído e pode ser tentado novamente.
4. As entradas importadas que fazem **transferência para Viridian Forest** passam a consultar `BlueKantoPilot.forest_unlocked?`. Antes da entrega, exibem aviso e **não transferem**; depois, preservam as coordenadas e a direção originais.
5. Centros Pokémon de Kanto chamam `BlueMusic.kanto_me_play("healed")` **após** curar e registrar o Centro. Decades mantém seus próprios eventos/áudio.

O Poké Mart continua vendendo itens normalmente após a cena. Interagir com o funcionário também recupera a entrega em saves antigos que não executaram o novo evento automático. As flags continuam locais à campanha Kanto; saves com a Boulder Badge local já conquistada mantêm o caminho aberto, evitando bloquear campanhas existentes.

## Verificações e restrições

- A nova cena é compilada a partir do verdadeiro NPC do Mart, sem usar gráficos ou scripts estrangeiros não auditados; no novo piloto deve haver uma página Autorun e uma segunda página vazia por self-switch A.
- O bloqueio vale para **warps de entrada na floresta**; conexões externas ou atalhos explicitamente experimentais devem ser auditados manualmente. O menu de teletransporte de teste não representa progressão de história.
- O movimento automático é uma rota curta de dois passos para cima, com proteção contra travamento; **confirmar no jogo gráfico** que o trajeto ficou natural com a geometria específica do Mart.
- Save/reload: verificar pacote adquirido, sem Pokédex/bolas antes de Oak; depois de entregar, Pokédex e cinco Poké Bolas persistem sem duplicar, e a floresta libera.
- Em saves que já receberam as cinco Poké Bolas **na versão antiga**, elas não são removidas automaticamente da Bolsa. A nova recompensa também será concedida ao concluir Oak; conferir caso a caso, sem apagar inventário.
- `python -m unittest tests.test_kanto_parcel_story -v`
- `python -m unittest discover -s tests -v`
- `ruby -c scripts/regions/KantoPilot.rb`
- A CI nativa de Kanto constrói `.blue-work/kanto-pilot` usando a fonte fixada e executa `KantoNativeCheck.rb`. A execução nativa automatizada não substitui teste visual/sonoro e verificação no JoiPlay.

**Aplicação:** alterações nos scripts-fonte não atualizam automaticamente um `Game.exe` ou APK já distribuído. Reconstruir o piloto/empacotamento Kanto com os comandos documentados em `KANTO_JOGAR_EXPERIMENTAL.bat` e `docs/ANDROID_PILOTOS_KANTO_JOHTO.md` e atualizar a instalação.
