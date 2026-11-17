# Sinnoh S10 — lançador experimental Windows seguro

**Escopo da Barra A:** entregar o lançador `SINNOH_JOGAR_EXPERIMENTAL.bat` e sua validação de segurança. **Não instala mapas nem declara Sinnoh jogável.** A aceitação desta S10 é do software de inicialização e seus testes offline, não de execução visual do `Game.exe`.

## Duplo clique no Windows

1. Atualize/cloque o repositório na pasta do projeto.
2. Clique duas vezes em **`SINNOH_JOGAR_EXPERIMENTAL.bat`**. Não requer PowerShell, GitHub CLI, nem abertura manual de terminal.
3. O BAT usa `py -3` ou `python` **3.10+** disponível na máquina e chama somente `scripts/regions/launch_sinnoh_qa.py --auto --start`.
4. Se a pasta `.blue-work/` não possuir **uma única** instalação no formato `game-sinnoh-qa-<12 hex>`, o lançador **bloqueia com mensagem**, sem iniciar Decades, Johto, Kanto, Hoenn ou outra região.
5. Se a cópia QA tem um **pedido de compilação pendente**, o Python relê os hashes, perfil de save e provas do instalador, e só então inicia o **`Game.exe` privado** para compilar. Quando a compilação terminar, clique no BAT novamente: ele **somente abrirá para teste manual** se existir um relatório estrutural real da engine consistente e um token de compilação válido. **Não cria marcador de sucesso jogável.**
6. O argumento opcional `--check` do BAT faz apenas a auditoria e devolve o status, **sem executar jogo nenhum**.

Caso haja **várias cópias QA**, o BAT recusa decidir sozinho. O Python permite selecionar uma explicitamente com `--qa CAMINHO`, desde que esteja dentro de `.blue-work` e cumpra todas as condições de `verify`. O instalador **S12** é separado: S10 não fabrica assets, não baixa mapas, não cria cópia QA nem move arquivos do jogo principal.

## Proteções implementadas

- [BAT](../SINNOH_JOGAR_EXPERIMENTAL.bat) usa o diretório do projeto e **não executa diretamente `game/Game.exe`**, não instala dependências, não atualiza Git nem altera arquivos.
- [Selecionador Python](../scripts/regions/launch_sinnoh_qa.py) aceita somente nomes `game-sinnoh-qa-[a-f0-9]{12}` e uma única pasta real; bloqueia symlinks, origens ambíguas e ausência de instalação. Não busca executável em nenhuma outra pasta.
- [Preflight QA](../scripts/regions/install_sinnoh_qa_copy.py) exige SHA-256 dos arquivos relevantes, `Sinnoh qa.json`, transação do instalador, `mkxp.json`/Game.ini com perfil privado, assets mínimos, ausência de saves herdados e validação de token de compilação/eventos. Qualquer falha impede `subprocess.Popen`.
- `subprocess.Popen` recebe exclusivamente o **caminho absoluto do `Game.exe` QA**, `cwd` QA e `shell=False`; nenhum fallback para a cópia principal.
- O resultado sempre informa `gameplay_approved=false`, `is_main_game=false` e `fallback_to_other_region=false`; um processo ser iniciado **não prova batalha/colisão/saves**.

## Testes e aceite

[15 testes S10](../tests/test_sinnoh_s10_launcher.py) verificam descoberta segura, ausência/duplicidade de cópias, symlink, preflight somente leitura, escolha de compilação/abertura, bloqueio sem comprovantes, inexistência de fallback, interface CLI e estrutura do BAT. Os processos de teste são **mockados**; o Game.exe real nunca é aberto no CI.

A [suíte S30](../scripts/regions/audit_sinnoh_s30_suite.py) também exige a presença do BAT e dos testes S10. O aceite de código pede **CI de Sinnoh Python, matriz S30 e regressões aprovados**, commits publicados na `main` e o ledger atualizado.

Com CI verificado e merge, a S10 pode ser contada como `done` **apenas para o lançador entregue**, elevando a **Barra A a 13/32 (40%)** (6 parciais, 13 pendentes). **B/C/D seguem 0/13**, a Barra E 20/20, e **44 testes nativos** seguem pendentes.

## Restrições reais

No GitHub, **não há os assets originais de Sinnoh nem `Game.exe` real** para executar. O código de instalação S12 e a criação de uma cópia com dados legítimos precisam de fonte autorizada e auditoria local. O BAT instalado sozinho não torna Sinnoh jogável. Não executar QA Android/JoiPlay a partir deste arquivo Windows.
