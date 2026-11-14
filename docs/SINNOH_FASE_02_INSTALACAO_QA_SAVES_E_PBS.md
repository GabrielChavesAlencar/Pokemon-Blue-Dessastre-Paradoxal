# Sinnoh — Fase 02: instalador experimental com saves isolados e compilação PBS

**Atualização:** 13/11/2026.  
**Status:** o código está implementado e coberto por testes sintéticos. **Não foi instalado no Game.exe real; mapas/posições/direitos da Sinnoh definitiva e QA Windows/Android seguem não confirmados.** A preparação do piloto é parcial. Não subir Game.exe, saves ou assets privados para o GitHub.

## Entrega do código

- [install_sinnoh_qa_copy.py](../scripts/regions/install_sinnoh_qa_copy.py): reúne uma **instalação Blue original** e um **overlay privado de Sinnoh** já validado por [prepare_sinnoh_pilot_bundle.py](../scripts/regions/prepare_sinnoh_pilot_bundle.py). A montagem final é **somente em nova pasta sob `.blue-work`**; o programa não modifica `game/` nem migra seus saves.
- [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb): somente para a cópia QA, inicializa o novo jogo **dentro do quarto do jogador** e prepara `BlueRegions.new_state("SINNOH")` após prova local da primeira compilação. Se o comprovante estiver ausente, o início é **bloqueado**, em vez de carregar Decades por engano.
- [test_sinnoh_qa_install.py](../tests/test_sinnoh_qa_install.py): testes sintéticos de cópia, hashes, mapa inicial, perfil de saves, colisões, compilação pendente, rollback por não sobrescrita e nenhuma modificação no jogo nativo.
- [sinnoh_qa_start_runtime.rb](../tests/sinnoh_qa_start_runtime.rb): testes Ruby puros para confirmar que a falta do comprovante bloqueia o início, que um mapa ou PBS alterado invalida o início e que carregar um save existente não reinicializa a região.
- [regression.yml](../.github/workflows/regression.yml): executa os testes Python e Ruby isolados.

## Segurança da cópia e dos saves

A base original deve ser a pasta **`game/` do projeto**. O instalador recusa iniciar a partir de Kanto/Johto/Sinnoh já montados, colidir com arquivos existentes, aceitar symlinks, copiar saves atuais para a QA ou sobrescrever a pasta de destino.

Em cada montagem é criado um **identificador aleatório novo**, aplicado aos três controles: `mkxp.json > dataPathApp`, `mkxp.json > dataPathOrg` e `Game.ini > Title`. São diferentes do Blue original e de outras montagens de Sinnoh, seguindo o padrão usado no piloto Johto. Não se reutiliza o perfil dos saves de Decades/Kanto/Johto/Hoenn.

A cópia preserva todos os arquivos válidos do jogo de referência e os substitui **apenas na cópia**, incluindo `MapInfos.rxdata`, `Tilesets.rxdata`, `System.rxdata` (mapa/posição inicial) e `Scripts.rxdata` (bootstrap compilador). Os originais substituídos ficam dentro da cópia em `_sinnoh_qa_originals/`. Saves, `.bak`, logs, temporários, symlinks e diretórios de backup não são copiados. A base com um piloto legado de Sinnoh já instalado também é recusada. Os 24 nomes e coordenadas de evento são reconferidos contra o overlay antes de montar a cópia.

**Importante:** a exclusividade efetiva do diretório do save depende do comportamento do `Game.exe`/mkxp na máquina. O teste de código garante que os identificadores sejam distintos; ainda é necessário verificar no Windows/Android os caminhos reais de armazenamento antes de declarar o isolamento nativo aprovado.

## Compilação dos três PBS de Barry

O instalador prepara um bootstrap nativo, apenas dentro da cópia. Ele reconhece `Sinnoh qa.json` e `Data/blue-sinnoh-qa-compile-request.txt` e, na **primeira abertura** do `Game.exe` da QA:

1. Habilita a compilação do Essentials com debug na cópia separada, após descartar somente os dados compilados antigos da cópia.
2. Deixa `Compiler.main` compilar o PBS e carrega `GameData::Trainer` no runtime local.
3. Exige as três versões `BLUE_SINNOH_RIVAL,Barry,0/1/2`. Se faltarem, cria `Data/blue-sinnoh-qa-compile-error.txt` e falha de maneira explícita.
4. Apenas quando essas versões estiverem presentes, grava `Data/blue-sinnoh-qa-compiled.txt` com o token do pedido, remove o pedido e encerra o processo **sem iniciar um jogo**.
5. Na próxima abertura, o plugin `SinnohQAStart.rb` confere o token e o SHA-256 dos arquivos protegidos (MapInfos, System, mapa do quarto e dois PBS) antes de permitir a inicialização regional de Sinnoh.

**O arquivo `Data/blue-sinnoh-rival-ready.txt` NÃO é produzido automaticamente.** Compilar PBS não prova que o combate, level cap, o sprite ou saves funcionem. O encontro de Barry permanece bloqueado até a auditoria manual no jogo. Não habilitar o marcador na instalação principal.

## Instruções para Codex no Windows

Pré-requisitos: uma **fonte Sinnoh real e com direitos**, mapas e posições auditados, um `sinnoh-qa-overlay` privado criado via [roteiro anterior](SINNOH_FASE_02_PACOTE_INTEGRACAO_QA.md), e especificação local de Twinleaf contendo o MapID inicial, posição e os flags de passabilidade realmente verificados.

**1. Prévia em dry-run, sem escrever nada:**

```powershell
python scripts/regions/install_sinnoh_qa_copy.py --game game --overlay .blue-work/sinnoh-qa-overlay-v1 --spec .blue-work/sinnoh/twinleaf-events-local.json
```

A saída deve informar `ISOLATED_QA_INSTALL_PLAN`, `copy_only:true`, ``native_compile_required:true`, a identidade do perfil privado e o spawn verificado. Se houver MapIDs 600–999 ou conflito de IDs, a instalação é bloqueada. **Não preencher as coordenadas com valores fictícios para fazer esse comando passar.**

**2. Criar a cópia experimental sem tocar no jogo principal:**

```powershell
python scripts/regions/install_sinnoh_qa_copy.py --game game --overlay .blue-work/sinnoh-qa-overlay-v1 --spec .blue-work/sinnoh/twinleaf-events-local.json --install
```

O resultado traz `qa_directory`: uma pasta nova `.blue-work/game-sinnoh-qa-<perfil>/`. O `Game.exe` é **copiado**, nunca executado automaticamente. Não passar `--output game` nem destino já existente.

**3. Verificar antes de abrir:**

```powershell
python scripts/regions/install_sinnoh_qa_copy.py --verify ".blue-work/game-sinnoh-qa-PERFIL_REAL"
```

Espera-se inicialmente `compiled_marker_present:false` e `compile_request_pending:true`. O código Python não afirma que o Essentials foi executado.

**4. Primeira execução local:** abrir **somente** o `Game.exe` da cópia QA. O bootstrap tenta compilar os PBS, faz as três verificações de Barry, grava o comprovante local se concluir e fecha a janela. Se houver erro, examinar o arquivo de compilação dentro dessa mesma cópia, **sem alterar `game/`**.

**5. Segunda verificação:**

```powershell
python scripts/regions/install_sinnoh_qa_copy.py --verify ".blue-work/game-sinnoh-qa-PERFIL_REAL"
```

`compiled_marker_present:true` e `compile_request_pending:false` significam apenas que o token da compilação foi verificado. **Não** significam que o piloto já esteja jogável.

**6. Segunda execução:** abrir novamente o `Game.exe` da mesma cópia. O plugin deve iniciar com estado `SINNOH`, na posição auditada dentro do quarto, com as três Poké Bolas físicas e os eventos Blue. Testar cada inicial num save novo e independente; inspecionar sprites, portais, Barry, Pokédex, ida/volta e save/load.

**7. QA obrigatório:** conferir os níveis reais conforme as regras Blue (70% normal, 90% Master), os três PBS no motor e o sprite do rival, a compatibilidade com as outras regiões e o Android/JoiPlay. Guardar os logs privados do QA e não publicar fontes/assets não autorizados.

## Os bloqueios permanecem

- `Johto 600–999`: o piloto antigo Sinnoh usa IDs 800–805, reservados para Johto na instalação multi-regiões; **não são reutilizados**.
- Sem os nove mapas de origem reais, com eventos, coordenadas, sprites e permissões verificadas, o montador não pode preparar uma cópia legítima.
- O bootstrap nativo e o gate de novo jogo só foram testados **com arquivos sintéticos**. Precisam de execução no Game.exe Windows e verificação dos saves e JoiPlay.
- O instalador não copia saves, não ativa Barry, não altera o Game.exe principal, não autoriza redistribuição, não gera sprites do doador e não certifica todas as fases.

Acompanhamento: [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md), [sinnoh-progress.json](../data/regions/sinnoh-progress.json), [SINNOH_CODEX_PENDENCIAS.md](SINNOH_CODEX_PENDENCIAS.md).
