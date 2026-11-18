# Unova G07.3 — transação incremental, CAS e rollback sintéticos

**Escopo:** somente memória Python; nenhum instalador real ou arquivo nativo de Unova foi modificado. Status `planned`, Barra A `0/8` e Unova jogável `0/32`.

## Pré-requisito G07.2 — fail-closed

A G07.3 chama o validador existente [G07.2](../scripts/regions/audit_unova_g07_incremental_manifest.py) **antes** de gerar staging ou cópias. A verificação inclui o schema 2020-12, versão, identificador do pacote, revisões Git de origem/destino, manifesto de origem com SHA-256 canônico, bytes reais das duas versões, direitos obrigatórios `FIXTURE_ONLY_NOT_DISTRIBUTABLE`, caminhos permitidos e proibição absoluta de mapas `.rxdata`, saves, executáveis, scripts e release nativa.

Os identificadores `FIXTURE_*` e arquivos `docs/unova-package-fixtures/*.txt|*.md|*.json` são **artificiais e existem só em dicionários Python**. Não há código que grave esses arquivos no disco, nem que baixe ou abra ZIP, `Game.exe`, Blue-Story, JoiPlay ou a pasta real de saves.

## Pipeline da transação

1. **Preflight:** o contrato de origem G07.2 valida hashes, direitos e compatibilidade documental. O estado sintético deve indicar `UNOVA`, canal `blue-story-unova-documentation`, revisão de origem, manifesto de origem e versão de fixture `0.0.0` coerentes.
2. **CAS inicial:** o chamador fornece obrigatoriamente `expected_generation` e `expected_snapshot_sha256`. O digest do snapshot abrange **todos** os bytes documentais, revisão, geração, metadados e conjuntos protegidos. Geração/revisão desatualizada gera conflito sem escrever nada.
3. **Staging:** cópias dos bytes de destino são preparadas apenas em memória e seus hashes e tamanhos são novamente conferidos contra o manifesto já validado.
4. **Backup sintético:** são capturados os bytes antigos dos arquivos documentais a substituir. O relatório registra SHA-256, tamanho e `memory_only=true`. Não é backup físico e não dá permissão para extrair qualquer asset licenciado.
5. **CAS pré-commit:** um segundo estado observado (`observed_after_staging`) representa mudanças concorrentes. Se arquivo, geração, checkpoint ou qualquer dado protegido mudou, a operação é bloqueada.
6. **Commit em memória:** constrói um **novo dicionário** a partir de uma cópia profunda do estado original, com os novos bytes e atualização de revisão/versão/geração. O estado original não é modificado e nenhum estado parcialmente aplicado é publicado.
7. **CAS pré-publicação:** uma observação independente (`observed_before_publish`) precisa continuar igual ao etag inicial. A transação só devolve o novo snapshot se todos os invariantes forem aprovados.

O resultado aprovado é `SIMULATED_ATOMIC_COMMIT_NOT_INSTALLED`. “Commit” significa **retornar um novo valor Python**, não fazer commit Git, `os.replace`, gravação de arquivos ou transação segura em filesystem real. O resultado contém `native_files_written=0`, `bytes_written=0`, `can_install=false` e `release_allowed=false`.

## Conflitos que bloqueiam integralmente

- Revisão de origem errada, manifesto local adulterado, cadeia além da versão sintética `0.0.0` ou diferença entre bytes locais e o snapshot de origem.
- `expected_generation` ou SHA-256 do snapshot desatualizados; hashes válidos do pacote **não** substituem uma confirmação de estado local.
- Edição concorrente entre staging e CAS, ou entre CAS e publicação, inclusive em **arquivos não listados no patch**.
- Mudança de qualquer namespace protegido: `decades`, `kanto`, `johto`, `hoenn`, `sinnoh`, `unova_uninstalled`, `global_files`, `saves`, `checkpoints`, `key_items`, `boxes`, `progress`, `mechanics`.

Cada conjunto contém **somente tokens sintéticos**. Nenhum dado privado do usuário é lido. Em conflito, o resultado volta com o snapshot original e a categoria `CONFLICT_*`, sem sobrescrever silenciosamente a alteração concorrente.

## Injeção de falhas e rollback

São sete pontos controlados:

| Etapa | Falha simulada |
| --- | --- |
| `after_preflight` | Após G07.2 e CAS inicial |
| `after_staging` | Após staging e verificação de hashes |
| `after_backup` | Após capturar os bytes antigos |
| `after_cas` | Após observar a geração/etag atual |
| `after_first_candidate_write` | Após trocar **somente o primeiro arquivo no candidato privado** |
| `after_candidate_commit` | Após montar o candidato completo, antes de publicá-lo |
| `before_publish` | Após CAS e checagens finais, antes de devolver o candidato |

Todos os pontos retornam `SIMULATED_ROLLBACK_COMPLETE` com **o estado de entrada integral**, não apenas a lista de arquivos: arquivos documentais originais, metadados, geração, revisão, snapshots de saves, checkpoints, Boxes, itens-chave, mecânicas e dados de outras regiões. Nenhum estado parcialmente editado é exposto ao chamador.

O teste de transação usa **dois arquivos documentais** sintéticos para identificar regressões de aplicação parcial. A suíte inclui casos positivos e negativos de versões, bytes adulterados, origens conflitantes, hashes falsos, direitos ausentes, path traversal, snapshots atrasados e concorrência em cada namespace protegido.

## Executar localmente

~~~bash
python scripts/regions/audit_unova_g07_transaction.py --check
python scripts/regions/audit_unova_g07_transaction.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g07_transaction.py' -v
~~~

O CI de Unova valida o contrato e executa o simulador no Linux; roda os testes G07.3 na suíte Python Linux e no job Windows, enquanto o portal valida build e Barra G. A publicação da barra para **29/32 (91%)**, frente G07 **3/4**, ocorre **somente após** CI Linux/Windows/portal aprovado e merge na `main`.

## Limitações reais — não é instalador

- **Sem transação de filesystem real.** Não existem operações de rename atômico, locks, backups persistentes, teste em Windows real de instalação, migração de save ou retentativa após queda de energia.
- **Sem assinatura de origem ou licença conferida.** SHA-256 é integridade, não autenticação nem autorização para distribuir assets de terceiros.
- **Sem cadeia incremental real.** G07.2 aceita apenas baseline sintético `0.0.0`; evoluir de um pacote anterior exige novo protocolo e novos testes. O controle de CAS G07.3 não corrige automaticamente esse limite.
- **Sem natividade.** Nenhum MapID de Unova foi instalado; não há comprovante de execução da nova região no Game.exe ou JoiPlay.
- **Sem persistência do estado retornado.** O “snapshot publicado” existe só na memória de quem chamou a função.

A próxima etapa **G07.4** prepara os contratos **Windows e Android/JoiPlay** sem transformar o pacote G07.3 em instalador e sem promover Unova a jogável.
