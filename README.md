# Pokémon Blue: Dessastre Paradoxal

> Fangame **em planejamento**, derivado para uso local de **Pokémon Decades** (HazyCrazy), feito com RPG Maker XP e Pokémon Essentials v21.1. Este repositório contém o **Blue Studio**, o editor próprio. **A ROM/arquivos do jogo original não estão neste repositório**; o desenvolvimento do fangame ainda não substituiu os mapas, a história ou os assets do Decades.

![Prévia do Blue Studio usando registros de teste](docs/blue-studio-preview.png)

*Prévia com dados demonstrativos: o jogo original não faz parte do download.*

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

## Criar o repositório GitHub

Execute **`PUBLICAR_GITHUB.bat`** depois de instalar `git` e `gh` e fazer login com `gh auth login` (o script pode iniciar esse login).

O script cria `Pokemon-Blue-Dessastre-Paradoxal` **privado** na sua conta e publica apenas o editor, a documentação e os scripts originais. A pasta `game/`, os saves, backups e outros dados locais são excluídos pelo `.gitignore`.

> Não é possível criar um repositório novo usando a conexão GitHub disponível nesta conversa. O script funciona **na sua máquina autenticada**, com permissão para criar repositórios na sua própria conta.

## Estrutura

```text
Pokemon-Blue-Dessastre-Paradoxal/
├── RUN.bat                    # Abre Blue Studio no navegador
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
