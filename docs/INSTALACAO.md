# Baixar e instalar Pokémon Blue

O portal reúne os dois downloads e os respectivos passos em **[Downloads — jogo e Hub](https://pokemondessastreparadosal.vercel.app/downloads)**. Os dois botões também estão na página inicial.

**[⬇ Baixar a versão atual (ZIP)](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/archive/refs/heads/main.zip)**

O link baixa o instalador, as modificações Blue, o editor e os assets autorais. O instalador obtém a base Pokémon Decades separadamente. Enquanto este repositório for privado, somente pessoas com acesso no GitHub poderão baixar. Torná-lo público libera o mesmo link para os demais jogadores; este procedimento não altera a visibilidade do repositório.

## Primeira instalação — Windows 64 bits

1. Instale **[Python 3.10 ou superior](https://www.python.org/downloads/windows/)** e **[Git para Windows](https://git-scm.com/downloads/win)**. Feche e abra o Explorador após a instalação.
2. Baixe o ZIP acima e use **Extrair tudo**. Abra a pasta extraída, que contém `INSTALAR_JOGO.bat`. Não execute de dentro do ZIP.
3. Abra **`INSTALAR_JOGO.bat`**. Mantenha o CMD aberto enquanto ele baixa a base e as referências e aplica as alterações. A primeira instalação é grande e pode demorar. Se falhar, a mensagem permanece na tela; corrija a causa e execute novamente.
4. Quando aparecer **`[OK] Instalado`**, abra **`ABRIR_JOGO.bat`**. Na primeira abertura, aguarde a compilação dos plugins e dos dados. As próximas aberturas usam os dados compilados.
5. Para a campanha com balanceamento novo, escolha **Story Mode → Traditional Starters ou Monotype Starters**. Use **`TESTAR_BATALHA.bat`** para o laboratório separado, que não carrega nem salva a campanha.

O instalador funciona a partir do ZIP, sem executar comandos Git na pasta do Blue. O Git é utilizado somente para obter a base em `game/`. Não é necessário instalar Node, RPG Maker XP ou criar conta na Vercel para jogar. O desenvolvimento e os testes atuais são para Windows; estes atalhos não geram APK.

## O que será instalado

- Base Decades fixada no commit `ff6091b23603b3298ad72a7584b02a51e1d01c0e` (referência 3.0.8).
- Restauração dos Pokémon/golpes para as referências oficiais do projeto.
- Geração Dessastre Paradoxal, sprites, cries, descrições e pedras autorais.
- IA Blue Radical, laboratório, opções de mecânicas, controles por mouse, animações e progressão Traditional Starters.
- Editor de músicas. As músicas MP3 da coleção pessoal do autor não estão no ZIP; a instalação usa a trilha da base até você [importar suas próprias listas](EDITOR_MUSICAS.md).

## Atualizar e preservar a campanha

Feche o jogo antes de atualizar. Quem clonou o repositório pode usar o atualizador `RUN.bat`. Quem baixou o ZIP pode baixar o ZIP novo e copiar suas pastas de código sobre a instalação anterior, preservando `game/` e `.blue-work/installation.json`; depois execute `INSTALAR_JOGO.bat` novamente. A restauração oficial concluída fica registrada e não é repetida sobre os PBS que você editou. Os plugins e assets próprios são atualizados com backup em `.blue-backups/`.

Não copie pastas de um segundo jogo sobre `game/`. Uma pasta parcial desconhecida é recusada pelo instalador para preservar seus arquivos. Não apague saves ou `.blue-backups/` para resolver uma falha de instalação.

**`ABRIR_JOGO.bat`** prepara os plugins e pede recompilação quando necessário. **`RUN.bat`** abre o Blue Studio. **`ABRIR_SITE.bat`** abre o portal local e depende de Node; é uma ferramenta opcional, separada do jogo.

## Verificações

Os testes automáticos verificam instalação a partir de pasta sem `.git`, retomada das etapas, versão fixada da base, proteção de pastas parciais e instalação dos plugins com reversão. Os recursos de batalha são validados no motor instalado. O fluxo de download completo em uma máquina vazia depende da disponibilidade dos servidores da base e das referências; não é um pacote autossuficiente com o jogo embutido.
