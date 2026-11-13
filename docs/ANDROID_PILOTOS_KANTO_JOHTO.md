# Android — pilotos Kanto e Johto separados

**13/11/2026 — estado:** há um pacote principal Android JoiPlay na release, mas ainda não existem os ZIPs regionais de Kanto e Johto. A interface do portal exibe as duas opções e só ativa cada link se o arquivo real estiver anexado à release.

## Arquivos esperados
- Modo História / Decades: Blue-Android-JoiPlay.zip (já existe na release).
- Piloto de Kanto: Blue-Android-Kanto-Piloto.zip (**pendente**).
- Piloto de Johto: Blue-Android-Johto-Piloto.zip (**pendente**).

Os pilotos são ZIPs completos de RPG Maker XP para JoiPlay + RPG Maker Plugin, não APKs. Não reutilizar ou renomear o pacote geral como se fossem pilotos.

## Por que ainda não estão publicados
- O botão Testar Kanto do jogo principal usa o launcher Windows (cmd.exe). Não pode ser executado pelo JoiPlay. É necessária uma instalação já montada como piloto, em que Novo Jogo começa na casa do jogador em Kanto. A montagem isolada de Windows depende de scripts/regions/pilot.py, da fonte FRLG correta e do processo de compilação nativa.
- Johto ainda depende da preparação dos interiores, eventos e arquivos nativos que ficam fora da main. A documentação docs/JOHTO_FASE_04_STAGE_REAL_PRIVADO_77_MAPAS.md afirma que a prévia não está jogável; data/regions/johto-source.json registra distribution_approved: false. Não publicar dados de terceiros sem autorização.
- Cada piloto precisa de seu próprio diretório de save, compilação, trilha de teste e identificação de versão. Não deve modificar game/ nem sobrepor saves da história Decades ou do outro piloto.

## Critérios para liberar cada botão
1. Preparar o piloto em uma cópia isolada e verificar os mapas, warps, PBS, gráficos, plugins, início da campanha e direitos de distribuição dos recursos incluídos.
2. Executar a compilação nativa na cópia regional e comprovar que os dados compilados correspondem à versão dos plugins.
3. Testar início, escolhas, batalhas, movimentação, save/load e controles touchscreen num aparelho Android real com versões identificadas de JoiPlay e RPG Maker Plugin.
4. Empacotar a instalação inteira (Game.exe, Game.ini, configurações, mapas, PBS, gráficos, plugins e dados compilados), excluindo saves, logs e caminhos locais.
5. Publicar o ZIP regional com o nome exato da tabela acima, checksum SHA-256 e notas de experimentalidade na GitHub Release corrente. Não adicionar arquivos enormes diretamente ao Git.
6. Verificar na API releases/latest que o asset está em estado uploaded, tem tamanho positivo e pertence à release correta. O portal detecta o arquivo e converte a opção em link automaticamente.

## Contrato do portal
A página /downloads usa site/src/assets/android-release.js para ler a última release pública e determinar a disponibilidade de cada ZIP por seu **nome exato**. Sem asset confirmado, mostra "Piloto Kanto · indisponível" ou "Piloto Johto · indisponível", sem hyperlink. O pacote geral permanece disponível separadamente.

**Importante:** mostrar as duas opções no site não significa que os pilotos já podem ser instalados no celular. A aprovação e a publicação dependem dos pré-requisitos acima.
