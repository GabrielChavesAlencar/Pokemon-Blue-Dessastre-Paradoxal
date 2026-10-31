# Editor exclusivo de golpes dos Pokémon

Implementado no Blue Studio v0.4, para Pokémon Blue Dessastre Paradoxal (base Pokémon Decades / Pokémon Essentials v21.1).

## Como abrir

1. Execute `RUN.bat`; ele atualiza o código pela branch `main`.
2. Na interface, entre em **Editor de ROM → ⚔️ Golpes dos Pokémon**.
3. Pesquise um Pokémon pelo nome ou identificador, inclusive espécies adicionadas e formas alternativas.
4. Edite os campos em três grupos:
   - **Golpes por nível (`Moves`)**: nível e ID do golpe, adição/remoção e botão para ordenar por nível.
   - **Golpes de tutor/TM (`TutorMoves`)**: lista de golpes disponíveis por tutor/máquinas conforme o motor.
   - **Golpes de ovo (`EggMoves`)**: movimentos aprendidos por reprodução.
5. Se a espécie for uma forma, use **Herdar da espécie base** ou desmarque para criar golpes próprios.
6. Clique em **Salvar moveset**. O servidor valida os IDs contra todos os `moves*.txt` do projeto, salva com backup e impede sobrescrita se o arquivo foi alterado em paralelo.
7. Para usar os golpes dentro do jogo, realize a compilação pelo menu de Debug do Pokémon Essentials. O Blue Studio ainda não confirma essa compilação de ponta a ponta.

## Integridade e formato

- O editor lê arquivos `PBS/pokemon*.txt` de espécies e formas, inclusive arquivos de gerações adicionais.
- Cada gravação modifica **somente** os campos `Moves`, `TutorMoves` e `EggMoves` do registro selecionado.
- Não muda stats, nome, habilidades, formas, sprites, outras espécies ou os dados de definição dos golpes (`PBS/moves*.txt`).
- Mantém o cabeçalho do Pokémon, comentários e campos desconhecidos; usa a rotina central de escrita atômica, arquivo de backup e detecção de concorrência por hash.
- Golpes só podem ser adicionados se a definição correspondente já existir no PBS; para criar novos golpes com novos efeitos será necessária uma ferramenta separada.
- Sem limite numérico de slots GBA: a busca inclui Fakémon adicionados ao Essentials.
- Para formas que não declaram um tipo de moveset, são mostrados os golpes herdados da espécie base.

## Testes de regressão

Os testes automatizados executados a cada atualização da `main` cobrem:

- listagem de espécies nos arquivos adicionais e formas;
- leitura e gravação de todos os três tipos de golpe;
- herança de formas e sobrescrita local sem alterar o Pokémon base;
- IDs de golpes inexistentes, níveis inválidos e caminhos maliciosos;
- preservação de UTF-8/BOM, CRLF, dados de outras espécies e backups;
- conflitos de edição simultânea (HTTP 409);
- interface Chromium: selecionar espécie, adicionar golpe por nível, salvar no PBS e confirmar espécie anterior intacta;
- teste do iniciador `RUN.bat` em Windows.

Execute `TESTAR.bat` para testes locais. A suíte do Chromium roda no GitHub Actions.

## Limitações conhecidas

- Ainda não é uma ferramenta para *criar novos golpes e seus efeitos*. O editor atual modifica **quais golpes cada Pokémon aprende**.
- O carregamento de catálogos muito grandes depende do desempenho da máquina local e da quantidade de arquivos PBS.
- A compilação efetiva e o teste de aprendizado em batalha ainda dependem do ambiente Windows e do runtime do Decades.
