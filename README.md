# Pokémon Blue: Dessastre Paradoxal

> Fangame **em planejamento**, derivado para uso local de **Pokémon Decades** (HazyCrazy), feito com RPG Maker XP e Pokémon Essentials v21.1. Este repositório contém o **Blue Studio**, o editor próprio. **A ROM/arquivos do jogo original não estão neste repositório**; o desenvolvimento do fangame ainda não substituiu os mapas, a história ou os assets do Decades.

![Prévia do Blue Studio usando registros de teste](docs/blue-studio-preview.png)

*Prévia com dados demonstrativos: o jogo original não faz parte do download.*

## Interface inspirada no editor de ROM do Emerald Studio (v0.2)

A navegação do **Blue Studio** foi reorganizada com o mesmo conjunto de **14 abas principais + 6 ferramentas avançadas** do editor de ROM do [Emerald Studio](https://github.com/Lancelioti/emerald-studio). O tema foi adaptado para **Pokémon Essentials / RPG Maker XP**.

- **Áreas superiores:** Visão geral, Editor de ROM e Ver MD de Movesets.
- **Funcionais hoje:** Pokédex (`pokemon.txt`), Itens (`items.txt`), Treinadores (`trainers_story_mode.txt`) e Selvagens (`encounters.txt`) usam o editor PBS real.
- **Planejadas:** Projeto, História e eventos, Flags, Iniciais, Mapas, Logo inicial, Fundo animado, Músicas, Estúdio MIDI, Test Lab e as 6 avançadas. Os painéis identificam claramente o que falta, sem salvar dados falsos.
- **Testes contínuos:** `.github/workflows/regression.yml` roda testes Python de PBS/API e contratos UI, valida JS e testa a navegação/salvamento real no Chromium (Playwright) em cada push para main e a cada PR, quando GitHub Actions está habilitado.
- **Testes locais:** execute `TESTAR.bat`. Os testes Python não precisam do jogo; o teste Chromium é executado no CI.
- **Plano:** [docs/PLANO_EDITOR_EMERALD_BLUE.md](docs/PLANO_EDITOR_EMERALD_BLUE.md).

A equivalência atual é **visual e de navegação**. Não utiliza offsets de ROM GBA, BPS ou sprites 4bpp; novos módulos serão construídos sobre arquivos PBS, plugins e dados RXDATA do Essentials.

## Sprites estáticos e animados (Pokédex)

A Pokédex do Blue Studio possui **quatro campos de imagem** por Pokémon: frente, costas, frente shiny e costas shiny. Cada imagem pode ser **PNG estático** (um quadro) ou **animação GIF/PNG spritesheet**. Isso evita exigir GIF para Fakémon estáticos.

Ao escolher um registro em `pokemon.txt` ou `pokemon_forms.txt`, use **Importar imagem** em cada variante. O servidor valida tipo e tamanho, cria backup e grava diretamente na pasta local `game/Graphics/Pokemon/`. PNG em faixa é tratado como animado pelo plugin do Decades quando sua largura ultrapassa duas vezes a altura. Formas `[CHARIZARD,1]` usam `CHARIZARD_1.png`.

**Limite atual:** 5 MB por imagem; backups em `.blue-backups/sprites/`. Não são publicados no GitHub, pois o jogo original está ignorado em `.gitignore`. O carregamento in-game em Windows ainda exige teste integrado. O editor **não é 100% funcional**: não compila PBS automaticamente nem oferece edição de pivot e métricas de batalha.

Confira a [auditoria técnica e próximos passos](docs/AUDITORIA_EDITOR_POKEMON.md).

## Aba exclusiva: ⚔️ Golpes dos Pokémon (v0.4)

No menu **Editor de ROM**, a aba **Golpes dos Pokémon** permite selecionar qualquer espécie ou forma cadastrada no Decades — inclusive seus novos Fakémon — e editar **`Moves` (nível), `TutorMoves` (tutor/TM) e `EggMoves` (ovo)**. Há pesquisa, sugestão de IDs e nomes, herança de movesets para formas alternativas, adição e remoção de linhas e salvamento exclusivo dos campos de golpes.

A gravação valida os golpes contra o catálogo `moves*.txt`, cria backup e preserva os outros campos da espécie. A compilação dentro do Pokémon Essentials ainda precisa ser feita pelo modo Debug.

**[Manual da aba de golpes](docs/EDITOR_GOLPES_POKEMON.md)**.

## Adicionar Pokémon novos sem substituir nenhum (v0.3)

O Blue Studio **não utiliza slots ou IDs numéricos fixos do GBA**. As espécies novas têm identificadores simbólicos exclusivos, como `CAVEFANG` ou `ABYSSMON`, e são acrescentadas a `PBS/pokemon.txt`, com entrada própria em `PBS/pokemon_metrics.txt`. O cadastro confere duplicidade nos arquivos `pokemon*.txt` do Decades, incluindo outros pacotes de gerações, e preserva os registros anteriores.

**Fluxo de uso:** rode `RUN.bat` → **Editor de ROM → Pokédex** → **＋ Adicionar Pokémon**. Preencha ID, nome, tipo(s), habilidades, golpes e atributos; clique **Criar nova espécie sem substituir**. A tela abrirá o novo registro, com **Ficha Pokémon** (edição de campos e validação de referências), editor de sprites normal/shiny e ajustes reais de posição/escala em batalha (PBS Metrics). Antes de salvar alterações na ficha, clique **Validar dados**; depois clique **Salvar alterações**. As métricas possuem botão **Salvar posição/escala no jogo** separado.

**Compilação para o jogo:** depois de modificar os PBS, clique **Abrir Debug / Compilar PBS**. O Blue Studio tenta iniciar o atalho oficial `Game.exe - Debug Mode.lnk` do Decades. No jogo, use **Debug → Files → Compile data**, ou o procedimento de compilação do Pokémon Essentials 21.1. A interface mostra uma checagem de timestamps de `Data/species.dat` e `Data/species_metrics.dat`, **mas isso não prova que a compilação foi concluída**. A confirmação real precisa vir do runtime do Essentials. O editor não tenta executar um compilador de ROM GBA em um jogo RPG Maker XP.

**Limitações atuais:** espécies recém-criadas precisam ser incluídas nos encontros/treinadores e, se desejado, nas Pokédex regionais; a compatibilidade final de GIF e animações dentro de uma batalha deve ser testada no Windows. O teste automatizado roda com dados sintéticos e não modifica os arquivos do jogo real.

Detalhes e pendências: [auditoria técnica](docs/AUDITORIA_EDITOR_POKEMON.md).

## O que já funciona

- **Blue Studio** no navegador, com Python 3 e sem dependências externas.
- Identificação de arquivos `.txt` de `game/PBS/`, inclusive os pacotes personalizados do Decades.
- Busca de Pokémon, formas, habilidades, golpes, itens, encontros e treinadores por ID/nome.
- Formulário de edição de campos PBS e editor avançado do texto original (incluindo campos repetidos).
- Inclusão de novos registros com modelos básicos editáveis.
- Salvamento diretamente nos arquivos locais do projeto; não mexe no repositório do Decades original.
- Backups automáticos na pasta `.blue-backups/`, com histórico de até 20 cópias por arquivo e restauração.
- Detecção de alterações simultâneas (hash SHA-256) para evitar sobrescrever edição de outra ferramenta.
- Prévia de sprites front/back quando presentes nos caminhos padrão do Essentials.
- Botão **Testar jogo**, que executa `game/Game.exe` no Windows.

**Ainda não disponível:** edição visual dos mapas, importação/conversão de sprite sheet 64×64, compilação automática dos PBS no jogo, gerenciamento visual complexo de encontros e equipes, sprites editor, criação automática da campanha, sistema de Paradoxos ou novas Mega Evoluções. Para essas tarefas ainda é necessário usar o RPG Maker XP e/ou desenvolver novos scripts/plugins.

## Requisitos no Windows

- Windows 10/11 e **Python 3.10+** instalado (`py` ou `python` no PATH).
- **Git** para baixar a base original.
- **RPG Maker XP** para editar mapas, eventos e scripts da engine (software comercial).
- **GitHub CLI (`gh`)** se quiser publicar este editor em um novo repositório da sua conta pelo script fornecido.
- Espaço em disco e internet suficientes: o repositório do Decades tem perto de 936 MiB de tamanho reportado pelo GitHub, podendo exigir mais espaço durante download e uso.

## Primeira execução

1. Extraia o ZIP em uma pasta, por exemplo `C:\Projetos\Pokemon-Blue-Dessastre-Paradoxal`.
2. Execute **`BAIXAR_BASE_DECADES.bat`** para baixar o Decades para `game/` (cópia local, ignorada pelo Git).
3. O instalador ajusta o título da janela do jogo para **Pokémon Blue: Dessastre Paradoxal** (arquivos locais `Game.ini` e `mkxp.json`); execute **`RUN.bat`**. O navegador abrirá o endereço `http://127.0.0.1:8765`.
4. Escolha `pokemon.txt` para editar espécies; `pokemon_forms.txt` para formas; `trainers_story_mode.txt` para treinadores; `encounters.txt` para encontros.
5. Clique em um registro, modifique e salve. É criado um backup local antes de escrever.
6. Para o jogo aplicar dados PBS alterados, abra o projeto em modo **debug** pelo RPG Maker XP ou pelo procedimento de compilação do Pokémon Essentials v21.1. O botão **Testar jogo** só inicia o executável: **não recompila o PBS automaticamente**.

Se você já baixou Pokémon Decades, copie os arquivos para `game/` mantendo `Game.exe`, `Game.rxproj`, `Data/`, `PBS/`, `Graphics/` e `Plugins/`, sem precisar baixar novamente.

> Alternativa: definir a variável de ambiente `BLUE_GAME_DIR` com o caminho da sua cópia local do jogo e executar `RUN.bat`. Arquivos originais não precisam ficar dentro desta pasta.

## Abrir e atualizar automaticamente (RUN.bat)

O **RUN.bat** agora verifica o GitHub e tenta atualizar o editor pela branch `main` antes de abrir o Blue Studio no navegador. **Nao exige GitHub CLI (`gh`)**: basta **Git for Windows** com acesso a este repositorio privado e **Python 3.10+**.

- **Pasta clonada por Git:** clique duas vezes em `RUN.bat`. Ele executa `git pull --ff-only origin main`, depois inicia o servidor Python em `http://127.0.0.1:8765` (o navegador abre automaticamente).
- **Pasta antiga extraida de ZIP (sem `.git`):** coloque nela o novo `RUN.bat`. Na primeira execucao, ele cria um clone em uma pasta irma chamada `Pokemon-Blue-Dessastre-Paradoxal-Git` e inicia a copia atualizada. Se existir `game/PBS` na pasta antiga, o editor continua usando essa copia local do jogo via `BLUE_GAME_DIR`.
- **Sem Git, sem acesso a rede ou com conflito:** o editor local ainda pode abrir, mas a atualizacao sera pulada e aparecerá um aviso. Para projeto privado, o Git pode solicitar autenticacao no navegador por meio do Git Credential Manager.
- **Alteracoes locais:** a atualizacao nao usa `git reset --hard`, `git clean` ou `--force`. Se um arquivo modificado impedir o pull, corrija o conflito manualmente; **nao** sera apagado.
- **Jogo e dados locais:** `game/` e `.blue-backups/` sao ignorados pelo Git e nao recebem atualizacoes do Decades automaticamente. O script atualiza **o codigo deste repositorio**, nao os arquivos da base original.

Se o script antigo ainda estiver no computador, voce pode atualizar uma vez pelo terminal, dentro de uma pasta clonada:

```powershell
git pull --ff-only origin main
```

Se nao tiver clone e quiser criar um manualmente (requer autorizacao no repositorio privado):

```powershell
git clone https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git
```

Depois execute `RUN.bat` da pasta clonada.

### Se o RUN.bat disser "A branch atual nao e main"

Essa mensagem vinha da versão antiga do iniciador. **Corrigido na branch main.** O novo `RUN.bat` verifica a branch atual; se a área de trabalho estiver limpa, muda para `main` sem descartar arquivos e sincroniza a versão atual. Se houver alterações locais ou conflitos, utiliza um clone seguro em pasta irmã (`Pokemon-Blue-Dessastre-Paradoxal-Git`) e preserva o conteúdo original. `game/` e backups não são sincronizados nem apagados.

Para quem ainda usa o `RUN.bat` antigo, a correção inicial precisa ser aplicada **uma vez**. Substitua `RUN.bat` pelo arquivo atualizado do repositório ou execute o pacote `CORRIGIR_ATUALIZACAO_BLUE.bat` entregue na conversa de suporte, dentro da pasta do projeto. O reparador busca a versão atual no GitHub, migra para `main` quando possível e inicia o editor.

CI: `.github/workflows/regression.yml` também executa um teste real do iniciador em `windows-latest`, simulando uma branch antiga, verificando `main` e repetindo o RUN em modo de teste (`BLUE_STUDIO_NO_SERVER=1`).

## Criar o repositório GitHub

Execute **`PUBLICAR_GITHUB.bat`** depois de instalar `git` e `gh` e fazer login com `gh auth login` (o script pode iniciar esse login).

O script cria `Pokemon-Blue-Dessastre-Paradoxal` **privado** na sua conta e publica apenas o editor, a documentação e os scripts originais. A pasta `game/`, os saves, backups e outros dados locais são excluídos pelo `.gitignore`.

> Não é possível criar um repositório novo usando a conexão GitHub disponível nesta conversa. O script funciona **na sua máquina autenticada**, com permissão para criar repositórios na sua própria conta.

## Estrutura

```text
Pokemon-Blue-Dessastre-Paradoxal/
├── RUN.bat                    # Sincroniza o GitHub e abre Blue Studio no navegador
├── BAIXAR_BASE_DECADES.bat    # Baixa Decades SOMENTE para uso local
├── JOGAR.bat                  # Inicia Game.exe, se instalado
├── PERSONALIZAR_JOGO.bat      # Ajusta o titulo local da janela do fangame
├── ABRIR_RPG_MAKER.bat        # Abre Game.rxproj
├── PUBLICAR_GITHUB.bat        # Cria repo privado com GitHub CLI
├── server/main.py             # Servidor HTTP local e API PBS
├── web/                       # Interface visual do Blue Studio
├── tests/                     # Testes automatizados
├── examples/                  # Modelo de espécie ORIGINAL, não aplicado
├── docs/                      # Próximas etapas e notas de distribuição
├── game/                      # Não versionada: cópia local do Decades
└── .blue-backups/             # Não versionada: histórico de alterações
```

## Testes

```powershell
py -3 -m unittest discover -s tests -v
```

Para abrir o editor manualmente:

```powershell
py -3 server\main.py --port 8765
```

## Licenciamento, créditos e distribuição

**Créditos obrigatórios:** HazyCrazy / Pokémon Decades, Pokémon Essentials e cada criador de plugins, músicas, sprites e outros recursos conforme `game/Credits.txt` e respectivas licenças. O projeto original está em <https://github.com/HazyCrazy/Pokemon-Decades>.

O repositório público original do Decades **não apresenta uma licença explícita no diretório raiz consultado em 31/10/2026**. Ser público no GitHub **não equivale a autorização ampla** para republicar ou adaptar comercialmente o conteúdo de terceiros. **Peça permissão ao autor e revise os créditos/licenças** antes de disponibilizar cópias modificadas do jogo, sprites, músicas, scripts ou qualquer distribuição pública. Os direitos da franquia Pokémon e dos personagens pertencem aos respectivos titulares. Este projeto independente não tem afiliação oficial.

O Blue Studio aqui fornecido é código original. Você pode utilizá-lo, modificá-lo e publicá-lo conforme o arquivo `LICENSE` (MIT), sem estender essa licença ao Decades ou ao Pokémon Essentials.

## Referências

- [Pokémon Decades — repositório do criador](https://github.com/HazyCrazy/Pokemon-Decades)
- [Pokémon Decades — fórum oficial do fangame](https://eeveeexpo.com/threads/9341/)
- [Pokémon Essentials Wiki](https://essentialsdocs.fandom.com/wiki/Essentials_Docs_Wiki)
- [RPG Maker XP](https://store.rpgmakerofficial.com/products/rpg-maker-xp)
