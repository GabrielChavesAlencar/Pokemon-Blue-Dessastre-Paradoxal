# Blue-Story — botão "Testar piloto Sinnoh" (Windows)

O Blue-Story.exe passa a apresentar **dois botões** após preparar a instalação principal:

- **Jogar campanha**: inicia o Game.exe normal, preservando o fluxo atual de Decades, Kanto, Hoenn e Johto.
- **Testar piloto Sinnoh**: solicita autorização explícita no clique, cria uma cópia QA nova, isolada, com os nove mapas originais e eventos da J12-E, e inicia o launcher experimental **automaticamente pelo próprio Blue-Story**. Não exige executar um BAT separado nem instalar Python do sistema.

Também há **Fechar**, que encerra o Blue-Story sem iniciar o jogo.

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
