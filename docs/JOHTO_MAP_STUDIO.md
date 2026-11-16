# Johto Map Studio — editor visual local e publicação direta na main

O projeto contém um editor visual de mapas **nativos RPG Maker XP** de Johto, aberto pelo navegador e executado **somente em `127.0.0.1:8771`**. Os arquivos `Data/Map600.rxdata` a `Data/Map699.rxdata` são lidos da instalação do usuário. **Não** é um editor de imagens geradas por IA.

## Download automático pelo Blue-Story.exe

A partir do instalador compilado na `main` em 16/11/2026, o próprio
`Blue-Story.exe` sincroniza o editor com o GitHub antes de iniciar o jogo.
O conteúdo público do editor é atualizado a cada execução quando a versão
da `main` muda.

Ele instala a pasta **`Johto-Map-Studio`** em dois lugares:

1. **Ao lado do `Blue-Story.exe`** que o usuário executou, quando a pasta
   permitir escrita (exemplo: `Downloads/Blue-Story/Johto-Map-Studio/`).
2. **Na instalação gerenciada do jogo**, sempre que a origem do editor estiver
   íntegra: `%LOCALAPPDATA%\\PokemonBlueDessastreParadoxal\\Johto-Map-Studio\\`.

Dentro da pasta há `EDITAR_MAPAS_JOHTO.bat`,
`CONECTAR_GITHUB_EDITOR_JOHTO.bat`, cópias de referência do código do
editor e o manual. Ambos os atalhos abrem a **mesma instalação gerenciada**
do jogo para que não existam versões divergentes dos mapas ou saves.

O arquivo `scripts/windows/install_johto_editor.py` sincroniza essa pasta
e recusa sobrescrever diretórios que já existem sem identificação do Blue.
Cópias de referência modificadas pelo usuário são preservadas em backup
antes de atualizar. Se o diretório do executável estiver protegido contra
gravação, o editor permanece disponível na instalação gerenciada; o jogo
não é bloqueado por esse motivo.

**Compatibilidade de inicializadores:** o `scripts/install_game.py` baixado
pela `main` também cria a pasta gerenciada em execuções de lançadores antigos.
A cópia **ao lado do executável** exige o novo `Blue-Story.exe` compilado.
O recurso não instala tilesets HGSS externos, nem disponibiliza ZIPs
privados na release pública.

## Como abrir no Windows (Blue-Story)

1. Execute o Blue-Story e instale o jogo principal com Johto. O Blue-Story baixa o código do repositório, incluindo o novo editor.
2. Feche o **Game.exe** antes de salvar mapas.
3. Pressione `Win+R`, cole `%LOCALAPPDATA%\PokemonBlueDessastreParadoxal` e confirme. Essa é a pasta gerenciada padrão.
4. Dê dois cliques em **`EDITAR_MAPAS_JOHTO.bat`**. O navegador abre `http://127.0.0.1:8771/`. Deixe a janela do terminal aberta enquanto edita.
5. Selecione **Map674 — quarto de New Bark**, ou outro mapa de Johto disponível. Use a paleta do tileset real, escolha Piso/Meio/Topo, desenhe com o mouse, use capturar/apagar, grade, zoom e desfazer/refazer.
6. Os círculos dourados/verdes representam eventos; selecione a ferramenta **Evento** ou clique na lista para mover eventos **existentes**. Também é possível alterar **somente** X/Y de uma transferência já existente, mantendo o MapID de destino e todos os scripts/sons/fades de suas páginas.
7. Clique **Salvar no jogo + backup**. Isso grava os tiles e eventuais ajustes de eventos no `Map###.rxdata` local, cria backup com data única em `.blue-backups/johto-editor-...` e salva um **patch JSON sem dados protegidos** em `data/regions/johto-map-edits/Map###.json`. Se o mapa/patch mudou desde que foi aberto, o salvamento é recusado até recarregar.

### Caso especial: escada do quarto New Bark

Na instalação anterior, o evento de sair do quarto é `JH_HOME2F_TO_1F` em **Map674**, inicialmente em `(9,8)`. O retorno à parte superior está em `JH_HOME1F_TO_2F` no **Map675**, com destino antigo `Map674 (9,7)`.

Para mudar a escada à esquerda e manter o jogo funcional:

- Abra **Map674**, desenhe a escada no novo local (e remova os tiles antigos).
- Selecione **`JH_HOME2F_TO_1F`** e altere sua **posição** para o tile de ativação da nova escada, por exemplo `(4,4)`, sem mudar o destino.
- Abra **Map675**, selecione **`JH_HOME1F_TO_2F`** e altere **Destino X/Y** para um tile de chegada livre do novo quarto, por exemplo `(4,5)`. A lista de comandos 250 (som), 223 (fade), 106 (espera), 201 (transferência) continua intacta.
- Salve e publique os **dois** mapas separadamente. Teste subida, descida, collision, entrar/sair, save/load e a sequência inicial no `Game.exe`.

A ferramenta **não cria NPCs, não edita scripts nem eventos novos**, não redimensiona mapas e não altera os tilesets originais. Ela usa os tiles já instalados: os gráficos HGSS de terceiros ainda exigem instalação autorizada separada.

## Publicar diretamente na branch main — sem PowerShell nem comandos manuais

**O Blue-Story prepara o Johto Map Studio e a GitHub CLI automaticamente.**
A CLI é baixada exclusivamente da release oficial `cli/cli`, verificada pelo SHA-256 publicado e guardada em `tools/gh/gh.exe`. O usuário não precisa instalar GitHub CLI, abrir PowerShell, executar `gh auth login` nem fazer `git pull` por conta própria.

1. Execute **Blue-Story.exe** uma vez com internet. Ele busca a `main`, atualiza o editor e prepara a CLI automaticamente.
2. Abra **Johto-Map-Studio/EDITAR_MAPAS_JOHTO.bat**, edite o mapa e clique **Salvar no jogo + backup**.
3. Clique **Publicar este mapa na main**. A verificação do GitHub é automática; não é necessário apertar **Verificar GitHub** antes.
4. Se ainda não houver autorização, o editor inicia a autenticação oficial no navegador. O usuário confirma o código mostrado na interface **somente na primeira conexão**; depois o programa retoma a publicação.
5. O editor mostra o commit publicado em `data/regions/johto-map-edits/MapXXX.json`. O Blue-Story sincronizará o patch nas próximas atualizações.

A primeira publicação de um mapa que **ainda não existe** na `main` é aceita mesmo com edições locais. Se a `main` já contém um patch diferente ou mudou após a verificação, o editor interrompe a publicação por segurança: não sobrescreve o trabalho remoto. O botão **Verificar GitHub** continua disponível para diagnóstico opcional.

É necessário ter permissão de escrita no repositório. A autorização oficial do GitHub exige aprovação do usuário na primeira conexão. O servidor do editor não guarda tokens; as credenciais são gerenciadas pela GitHub CLI.

## Segurança e limites

- Interface escutando exclusivamente `127.0.0.1`, com token anti-CSRF aleatório, validação de origem e limites de tamanho.
- IDs aceitos: **600–699**, sem sobrescrever Kanto, Hoenn ou Decades.
- Toda edição exige map hash e patch hash iguais ao estado lido, com verificação prévia de colisões em eventos/spawns/teleportes.
- O evento crítico `JH_NEW_GAME_PROFILE` não pode ser deslocado.
- O patch registra posições de eventos e transferências, nunca o conteúdo dos comandos/scripts.
- Salvamento local e atualização pelo Blue-Story usam backups e tentativa de rollback se a escrita falhar.
- Se um patch tiver tileset diferente ou célula antiga incompatível após atualização do jogo, o instalador bloqueia a aplicação e pede revisão, em vez de escolher um tile incorreto.
- Os testes automatizados cobrem salvamento, aplicação em novas instalações, reexecução idempotente, eventos, transferências, proteção de saves, conflitos e API de publicação simulada. **A interface e os mapas ainda precisam de teste de jogabilidade visual no Game.exe real do usuário.**

## Arquivos do projeto

- `EDITAR_MAPAS_JOHTO.bat` — abrir o editor visual.
- `CONECTAR_GITHUB_EDITOR_JOHTO.bat` — autenticação GitHub CLI oficial.
- `scripts/regions/johto_map_editor.py` — servidor local de edição, salvamento e publicação.
- `web/johto-map-editor.html` — paleta, canvas de três camadas, eventos, zoom, undo/redo e botões.
- `scripts/regions/johto_map_patches.py` — patch sem assets, validação e sincronização com o instalador.
- `scripts/regions/johto_main_preview.py` — aplicar patches depois da construção dos mapas Johto novos.
- `scripts/regions/auto_integrate_johto.py` — sincronizar patches publicados em mapas previamente instalados.
- `tests/test_johto_map_editor.py` — regressões automatizadas.
