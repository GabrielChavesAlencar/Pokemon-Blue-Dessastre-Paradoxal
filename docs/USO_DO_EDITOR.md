# Guia de uso do Blue Studio

1. Selecione o arquivo PBS na lateral.
2. Pesquise pelo ID ou pelo nome do registro.
3. Abra um Pokémon, golpe, habilidade, forma, item, encontro ou treinador.
4. Altere valores no painel **Campos** ou escolha **PBS avançado** para editar o texto integral do registro.
5. Clique em **Salvar alterações**. Um backup é criado automaticamente antes da escrita.
6. Clique **⟲ Backups** para recuperar a versão anterior, se necessário.
7. Recompile os PBS com a engine para observar mudanças no jogo; o botão **Testar jogo** apenas abre `Game.exe`.

## Adição de Pokémon

- Selecione `pokemon.txt` e clique em `＋`.
- Digite o ID único da espécie, por exemplo `CAVEFANG`.
- Configure os campos (`Types`, `BaseStats`, `Abilities`, `Moves`, `TutorMoves`, `Evolution`, etc.).
- Importe os sprites nos diretórios `game/Graphics/Pokemon/Front`, `Back`, `Front shiny`, `Back shiny` conforme as convenções do Essentials.
- Ajuste animações, cry e métricas no RPG Maker XP/PBS apropriado.
- Adicione encontros e/ou treinadores, recompile e teste.

### Atenção

O editor não faz validação semântica completa de todos os campos PBS. Um ID ou valor inexistente pode causar erro durante compilação do jogo. Usar sempre backup e fazer testes com uma cópia de saves.
