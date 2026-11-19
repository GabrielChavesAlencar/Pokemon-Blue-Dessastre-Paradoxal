# Blue-Story — botão "Testar piloto Sinnoh" (Windows)

O Blue-Story.exe passa a apresentar **dois botões** após preparar a instalação principal:

- **Jogar campanha**: inicia o Game.exe normal, preservando o fluxo atual de Decades, Kanto, Hoenn e Johto.
- **Testar piloto Sinnoh**: solicita autorização explícita no clique, cria uma cópia QA nova, isolada, com os nove mapas originais e eventos da J12-E, e inicia o launcher experimental **automaticamente pelo próprio Blue-Story**. Não exige executar um BAT separado nem instalar Python do sistema.

Também há **Fechar**, que encerra o Blue-Story sem iniciar o jogo.

## Correção de inicialização: Kanto 142/145 não bloqueia o menu

A partir desta revisão, o Blue-Story atualiza **somente o código público antes de apresentar a escolha**. As verificações e atualizações de Kanto, Hoenn e Johto ocorrem **apenas quando o jogador seleciona "Jogar campanha"**. Portanto, um Kanto antigo que registre 142 mapas dos 145 previstos **não impede** clicar em **"Testar piloto Sinnoh"**. O piloto continua usando cópia privada QA do jogo existente e não modifica a instalação Kanto parcialmente verificada.

A validação de Kanto **não foi removida ou falsificada**. Ao selecionar a campanha, o instalador ainda exige integridade regional e continua bloqueando a execução quando houver incompatibilidade real (como 142/145). O reparo dos três mapas ausentes depende de fonte original/manifestos apropriados e não pode sobrescrever os MapIDs ou saves existentes automaticamente. Consulte `.blue-work/kanto-install-status.json` e `.blue-work/kanto-install.log` na sua máquina para identificar o Kanto instalado e planejar uma correção segura.

O novo fluxo é: **sincronizar fontes → exibir menu → escolher campanha ou Sinnoh → só instalar/verificar Kanto para a campanha**. Isso evita obrigar o piloto de Sinnoh a passar por uma correção potencialmente arriscada de Kanto.

## Dentro do Game.exe: usar Testar Sinnoh na própria cópia QA

A tela **Sinnoh QA** já é uma cópia experimental criada pelo Blue-Story. Nas versões anteriores, a opção **Testar Sinnoh** do título ainda verificava o formato antigo `Sinnoh pilot.json` e mostrava incorretamente que Twinleaf/Sandgem não estavam instalados.

A correção mantém o título da campanha principal sem alterações de progresso e integra o **novo formato J12-E**: quando o jogo é iniciado dentro de `.blue-work/game-sinnoh-experimental-<token>`, o botão **Testar Sinnoh** valida o manifesto `sinnoh-experimental-qa.json`, o token do perfil, os nove RXDATA e seus hashes SHA-256, os dois registros de mapa/tileset, a configuração de saves isolados, e a confirmação nativa da compilação PBS de Barry. Só então encaminha para **Novo Jogo na MESMA janela QA**, sem iniciar outro Game.exe, sem procurar um BAT `SINNOH_JOGAR_EXPERIMENTAL.bat` e sem tocar no save da campanha principal. A opção **New Game** dentro dessa cópia também ignora o seletor de regiões do Decades e inicia apenas o piloto QA.

O instalador atualiza o arquivo `TitleKanto.rb` **exclusivamente na cópia nova**. Isso é necessário porque a instalação principal pode estar bloqueada pelo Kanto 142/145 e manter um plugin de título antigo; a atualização do repositório, sozinha, não altera esse arquivo no jogo já instalado. Não sobrescreve nem atualiza o plugin na campanha principal.

**Como usar:** substitua o Blue-Story.exe pelo da release mais recente, abra **Testar piloto Sinnoh** no Blue-Story e depois, na janela `Sinnoh QA` criada, selecione **Testar Sinnoh** (ou **New Game**). O procedimento cria uma nova cópia, não repara cópias QA antigas automaticamente. Se aparecer erro de perfil, compilação ou hashes, a operação será bloqueada para não iniciar a região incorreta: preserve e envie os logs. Não apague ou copie saves.

**Limites:** abrir a tela inicial com os mapas não é prova de que Barry, portais, colisões e save/load passaram no Game.exe. Permanecem R07/R08/R09 pendentes, 0/9 instalados na campanha principal e 0/44 QA nativa aprovada.

## Como usar

1. **Atualize seu Blue-Story.exe**, baixando o binário da release [Blue-Story Windows](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/blue-story-windows) **depois da publicação do PR**. A autoatualização do código não substitui por si só um EXE Windows antigo, por isso este download é importante.
2. Abra o **Blue-Story.exe** normalmente. Espere o instalador atualizar a base e os scripts.
3. Clique em **Testar piloto Sinnoh**.
4. O Blue-Story usa seu Python portátil, lê a instalação gerenciada em `%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game` sem alterá-la, procura MapIDs livres **somente para o QA**, prepara dois tilesets e nove mapas e compila os 24 eventos (16 portais, cinco NPCs e três Poké Bolas) com coordenadas verificadas **apenas pelo modelo estático**.
5. O inicializador cria uma nova pasta isolada `.blue-work/game-sinnoh-experimental-<token>`, define um namespace de saves exclusivo e executa, **sem interação manual com o BAT**, o launcher da cópia. O primeiro início tenta compilar os dados do Barry dentro dessa cópia.
6. Se a compilação ou o início falhar, o Blue-Story mostra um erro e o log `.blue-work/launcher.log`; a cópia QA inclui `Data/sinnoh-experimental-compile-error.txt` quando a compilação emitir diagnóstico.

## Garantias e limites

O código principal `scripts/windows/Bootstrap.cs` oferece a escolha somente no Blue-Story, **não no Blue-Battle-Hub**. A ação do botão chama `scripts/windows/launch_sinnoh_pilot.py` com o runtime Python portátil já preparado e recebe um recibo JSON temporário que identifica a cópia criada. O recibo precisa confirmar `main_game_modified=false` e `native_qa_cases_approved=0`, e a cópia precisa estar em `.blue-work` para que o EXE permita iniciar o launcher.

O jogo original, seus MapInfos/Tilesets/PBS e saves **não são alterados ou copiados** pela instalação experimental. A cópia QA pode consumir espaço adicional em disco. O Blue-Story não ativa Sinnoh automaticamente nem altera a escolha de quem clica em **Jogar campanha**.

**Importante:** a existência do botão e os testes automatizados não significam que Game.exe, a batalha com Barry, as colisões, as portas ou save/load foram aprovados em jogabilidade real. **R07/R08/R09 continuam pendentes, Sinnoh oficialmente não jogável, 0/9 mapas instalados no jogo principal e 0/44 QA nativa validada** até evidência de teste. Se o instalador detectar arquivos incompatíveis, bloqueia a operação em vez de sobrescrever o jogo ou inventar aprovação.

## Validação

```powershell
python -m unittest discover -s tests -p test_blue_story_sinnoh_menu.py -v
python -m unittest discover -s tests -p test_sinnoh_j12e_experimental_installer.py -v
python scripts/windows/build.py
```

O workflow `.github/workflows/blue-story-windows.yml` compila os EXEs Windows e testa o menu no PR. A release `blue-story-windows` só é atualizada **após merge na main**. Nenhum dado privado do usuário é necessário nos runners GitHub.

Issue de acompanhamento: [Sinnoh J11 #241](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/241).
