# Sinnoh S12 — instalador isolado do piloto experimental

**Escopo da entrega de desenvolvimento:** instalador Windows com fluxo seguro de duplo clique e script Python para preparar/instalar **apenas uma cópia QA privada**, sem tocar no `game/` original e sem utilizar saves de Decades, Kanto, Johto ou Hoenn. **Este documento não certifica que os mapas de Sinnoh estão disponíveis ou que o Game.exe foi testado.**

## Como funciona

- [`SINNOH_INSTALAR_EXPERIMENTAL.bat`](../SINNOH_INSTALAR_EXPERIMENTAL.bat) é o acesso de duplo clique. Usa Python 3.10+ instalado no Windows, sem PowerShell. Tenta a instalação **somente após verificar as duas entradas privadas**. Argumento `--check` executa exclusivamente uma simulação, sem criar instalação.
- [`scripts/regions/sinnoh_s12_installer.py`](../scripts/regions/sinnoh_s12_installer.py) faz uma simulação **por padrão**; a criação da cópia precisa de `--install`. Usa o instalador transacional já existente `install_sinnoh_qa_copy.py`, sem criar MapIDs nem conteúdo ausente.
- O modo `--auto` exige **exatamente um** diretório dentro de `.blue-work/` contendo `sinnoh-qa-overlay-report.json` auditado, além do arquivo local `.blue-work/sinnoh-qa-spec.json` com as coordenadas e eventos auditados. Uma especificação arbitrária fora do espaço privado, dois overlays, links simbólicos ou arquivos adulterados são bloqueados.
- **Preparar os dados:** o [montador de overlay](../scripts/regions/prepare_sinnoh_pilot_bundle.py) recebe a geometria autorizada, os eventos de Twinleaf, a especificação real e o draft de PBS Barry. Após `--publish`, produz o overlay privado com hashes em `.blue-work`. Uma cópia da **mesma especificação local auditada** deve ser disponibilizada como `.blue-work/sinnoh-qa-spec.json`. A S12 não baixa dados protegidos nem fabrica mapas, sprites, eventos ou permissão de redistribuição.
- Quando todos os insumos passam na validação, `--install` cria uma nova pasta `.blue-work/game-sinnoh-qa-<12 hex>`, copia apenas a base auditada **excluindo saves**, sobrepõe os arquivos exclusivos do overlay nessa cópia, registra hashes/transação, gera `Sinnoh qa.json` e um **pedido de compilação pendente**. A operação usa diretório temporário e rename atômico; se falhar durante a cópia, remove apenas os arquivos temporários criados naquele processo.
- Depois de instalar, o usuário poderá usar [`SINNOH_JOGAR_EXPERIMENTAL.bat`](../SINNOH_JOGAR_EXPERIMENTAL.bat) (S10) para executar **somente a compilação privada pendente**. Um segundo clique só permite abrir a cópia para teste manual após o relatório estrutural nativo passar. Isso **não cria** marcadores de batalha aprovada, mapa jogável nem compatibilidade Android.

## Executar com argumentos explícitos (opcional)

```bash
python scripts/regions/sinnoh_s12_installer.py --auto
python scripts/regions/sinnoh_s12_installer.py --auto --install
```

O primeiro comando é **dry-run sem gravação**; o segundo só instala se o overlay/specificação realmente existirem e forem íntegros. Para caminhos locais diferentes, use `--overlay` e `--spec`, ambos obrigatoriamente em `.blue-work`. Não existe `--game` ou `--output`: a base sempre é o `game/` do projeto e o destino é sempre uma nova pasta de QA privada.

## Segurança e testes automatizados

Os [16 testes S12](../tests/test_sinnoh_s12_installer.py) usam somente mapas, `Game.exe` e saves **sintéticos**. Cobrem simulação sem efeitos, seleção automática/duplicidades, instalação QA em pasta nova, hashes da base preservados, perfil de save isolado, bloqueio de uma segunda instalação, especificações adulteradas ou de outra região, conteúdo de overlay ausente ou adulterado, symlinks, rollback de falha durante cópia, CLI sem argumentos e segurança do BAT.

A [matriz S30](../scripts/regions/audit_sinnoh_s30_suite.py) exige tanto o instalador e seu BAT quanto os testes S12. Os workflows CH19 Python/Ruby, S30, portal e CH20 devem aprovar a entrega.

## Aceite de desenvolvimento e impedimentos nativos

Após CI e merge na `main`, **S12 é `done` no escopo do instalador de código/fixtures** e a Barra A passa a **15/32 (46%)** (6 parciais, 11 pendentes). A Barra E fica **20/20 (100%)**; B/C/D **0/13**; permanecem **44 casos Windows/JoiPlay sem execução real**.

A instalação física de Sinnoh ainda requer a fonte original autorizada de mapas, direitos, coordenadas/mapas reais, PBS e validação no Game.exe Windows e JoiPlay. Não afirmar que o BAT sozinho instala um piloto jogável. O instalador não possui código para baixar assets automaticamente de fontes externas nem altera a instalação principal em caso de bloqueio.
