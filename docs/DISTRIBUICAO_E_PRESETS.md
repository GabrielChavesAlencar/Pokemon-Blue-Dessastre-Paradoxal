# Inicializadores, Android e times prontos

O site oferece dois inicializadores Windows: **Blue-Story.exe** e **Blue-Battle-Hub.exe**. Ambos usam uma instalação compartilhada. A cada abertura, consultam a main pública, baixam a revisão identificada pelo GitHub e atualizam os scripts. Os arquivos de `game`, saves, equipes, ferramentas privadas e backups ficam protegidos durante essa cópia. Arquivos substituídos recebem backup.

Python e MinGit são baixados de suas distribuições oficiais e conferidos por SHA-256. São cópias portáteis, sem instalação global e sem necessidade de privilégios de administrador. O código do inicializador fica em `scripts/windows/Bootstrap.cs`; o build compila os dois EXEs e executa uma prova de extração com proteção contra caminhos fora da pasta e substituição de arquivos do jogo. O CI também limpa o PATH para comprovar o uso das dependências privadas.

## Uso no Windows

Baixe um dos EXEs em **Downloads**, abra e aguarde a primeira instalação e compilação. A base Decades é obtida separadamente, no commit fixado pelo instalador. Feche o jogo antes de atualizar. O registro da revisão e o log do inicializador ficam em `.blue-work` dentro da instalação.

Quando o EXE está numa instalação de desenvolvimento existente, ele a reconhece pela pasta `scripts` e `game`. Em um computador novo, a pasta padrão é `%LOCALAPPDATA%/PokemonBlueDessastreParadoxal`.

## JoiPlay experimental

O download **Blue-Android-JoiPlay.zip** é um pacote de jogo compilado, não um APK nativo. Instale JoiPlay e RPG Maker Plugin pelos [downloads oficiais](https://www.joiplay.net/), extraia o ZIP inteiro e adicione `Pokemon-Blue-Android/Game.exe` ao JoiPlay. A abertura permite escolher a campanha ou o Hub offline.

O multiplayer e o download de links PokéPaste exigem o auxiliar Python do Windows e são bloqueados com uma mensagem explicativa no pacote Android. Os times prontos e o importador de texto usam os dados incluídos no pacote. O funcionamento em aparelhos Android reais ainda precisa de validação; o build nativo e a preparação do pacote não substituem essa prova.

O empacotador exige confirmação de compilação da engine para os plugins atuais. Exclui saves, times pessoais, logs, caminhos do Python do PC, diretórios Git e backups. O jogo compilado é publicado como arquivo de release; `game/` e seus binários permanecem fora do Git.

## Times prontos

No Hub, use **Importar → Times prontos por jogo e regulamento**. Existem 130 times, dez em cada grupo: Scarlet/Violet A–J e Champions M-A–M-C. Os textos foram baixados dos links diretos do catálogo fornecido pelo usuário e ficam disponíveis sem internet.

Os nomes e a classificação por regulamento seguem esse catálogo. A importação confirma a compatibilidade dos seis Pokémon com a engine; não certifica a legalidade de torneio nem a origem dos spreads. Times Champions usam a conversão para EVs clássicos com limite de 510, mostrando os ajustes na prévia, conforme a preferência já definida.

O importador reconhece as formas do Showdown de Ogerpon, Urshifu e Floette Eternal, além dos aliases encontrados na auditoria dos 130 times. As formas temporárias Terastal de Ogerpon não sobrescrevem o cadastro da máscara normal. As duas habilidades As One são resolvidas separadamente.

## Músicas compartilhadas

`data/shared-music.json` associa cada faixa fornecida pelo mantenedor ao seu arquivo em `assets/music` e ao caminho usado pela engine. O instalador verifica os hashes antes de copiar os áudios e aplica a configuração compartilhada quando a versão desse manifesto muda. Uma configuração local alterada pelo editor é preservada enquanto o manifesto permanece igual.

As 19 faixas anteriores foram mantidas e dez adicionadas: **12 de treinador, 8 selvagens e 9 de líderes**. A música da tela do logo continua incluída. O sorteio já existente permanece separado por categoria e mantém a mesma faixa durante toda a batalha.

Para revisar as listas, use `scripts/music/publish_music.py --extra-source CAMINHO`. Para atualizar o catálogo, use `scripts/battle_lab/import_presets.py CAMINHO_DO_MARKDOWN`. A instalação normal apenas consome os arquivos já versionados.
