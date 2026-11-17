# Sinnoh G04 — endurecimento do isolamento B10 (GitHub-only)

**17/11/2026.** Esta entrega altera somente scripts, testes e CI versionados. **Não executa** Windows Sandbox ou `Game.exe`, não lê o PC, não manipula saves, não copia arquivos de terceiros e **não** libera os 702 MapIDs como jogáveis.

## Diagnóstico do código B10 anterior

A B10 já validava SHA de cada arquivo privado do clone B09, MapInfos/Tilesets, 648 mapas nativos + 54 terrenos e as evidências B07/B08. O XML `.wsb` já solicitava dois mapeamentos somente leitura, sem rede, clipboard, impressora ou início automático. Entretanto, alguns pontos ainda admitiam erros de preparação:

1. O CMD de cópia **avisava** para ser executado na VM, mas não tinha guarda contra execução acidental no Windows principal.
2. `safe_rel` usava `PurePosixPath` após receber o caminho: a normalização poderia esconder `/` duplicado ou `/./`, além de nomes inválidos do Windows.
3. O criador do XML não reabria o próprio resultado para verificar regressões futuras (por exemplo, `ReadOnly=false` ou `LogonCommand` inserido por engano).
4. A função de preparação podia ser invocada diretamente com outro diretório e metadados parciais; o caminho e o SHA do clone devem ser restritos ao plano B09.
5. O plano contém duas entradas lógicas para cada tabela global substituída pelo overlay: a auditoria passa a permitir **somente** `Data/MapInfos.rxdata` e `Data/Tilesets.rxdata` com origens NATIVE/OVERLAY.

## Correções entregues

| Controle | Proteção nova | Limite |
| --- | --- | --- |
| **Guarda do convidado** | O CMD recusa `USERNAME` e `USERPROFILE` diferentes do padrão `WDAGUtilityAccount` e exige a ferramenta no mapeamento do convidado antes da cópia | É uma prevenção de uso acidental; variáveis de ambiente **não autenticam VM** |
| **Robocopy** | Uso de `/XJ /SL`: não percorre junctions e não segue destinos de links simbólicos | Ainda depende da integridade prévia do clone e de uma VM real |
| **Caminhos Windows** | Bloqueio de dot segments, `//`, caracteres de controle, curingas, caracteres especiais, ADS e nomes reservados | Protege manifesto e destinos do clone, não executa conteúdo |
| **Origem B09** | Pasta exatamente em `.blue-work/sinnoh-b09-native-qa/native-<SHA>`, hash de plano coincidente, evidência 648+54=702 | Não gera SHA/autenticidade a partir do relatório privado do usuário |
| **Duas substituições** | Apenas MapInfos/Tilesets podem surgir nas duas origens do plano; colisões de case/path bloqueadas | Não muda os arquivos `.rxdata` |
| **Política WSB** | `check_wsb_policy` exige **exatamente dois HostFolder**, ambos `ReadOnly=true`, rede/clipboard/áudio/vídeo/vGPU/impressora desabilitados, ProtectedClient habilitado, sem LogonCommand nem tags inesperadas | Revisão estática de XML; não demonstra execução da VM |

## Testes e evidência de CI

- [Preparador B10](../scripts/regions/prepare_sinnoh_b10_save_isolation.py) — endurecimento do código original.
- [27 testes B10](../tests/test_sinnoh_b10_save_isolation.py) — 20 anteriores + 7 negativos da G04 (WSB adulterado, paths Windows, guarda do guest, fonte fora da pasta esperada, prova B09 falsa, arquivo com dupla origem não autorizada e symlink no clone).
- [GitHub Actions G04](../.github/workflows/sinnoh-g04-sandbox.yml) — executa a suíte sintética e gera somente um JSON com estado **`WSB_POLICY_STATIC_CHECK_PASSED_NO_NATIVE_EXECUTION`**.
- Os testes completos de Sinnoh via CH19/S30 também são executados quando o PR altera `scripts/regions` ou `tests/test_sinnoh_*.py`.
- Nenhum artifact da G04 deve conter `Game.exe`, saves, PNGs de terceiros, caminhos pessoais ou binários de jogo.

## Portões pendentes

**B10 local:** só o relatório gerado na máquina do usuário, em Windows Pro/Enterprise/Education com Windows Sandbox e virtualização habilitados, pode mostrar a criação real da sessão. O CMD do guest continua precisando de confirmação visual da janela Windows Sandbox.

**B11 local:** comparar os arquivos de save observados no host antes/depois de uma sessão; mesmo um relatório de hashes sem alterações não prova cobertura de todos os caminhos possíveis de save.

**Sinnoh jogável:** ainda requer R07 (reservas futuras), R08 (direitos por asset), R09 (Game.exe/JoiPlay) e os casos nativos. As barras B/C/D permanecem **0/13**.

Esta G04 não atualiza automaticamente a Central Sinnoh ZIP que já foi extraída no PC. Para obter as novas proteções em uso real será necessário atualizar os arquivos do instalador/central a partir da versão publicada do GitHub e verificar a equivalência dos scripts.
