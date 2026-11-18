# Unova G07.2 — contrato de pacote incremental (sem instalador nativo)

**STATUS:** `PLANNED_INCREMENTAL_SCHEMA_ONLY` · nenhuma instalação, download, ZIP real ou alteração de saves.

Esta entrega define uma camada auditável de **identidade, compatibilidade, SHA-256, proveniência, direitos e caminhos de pacote**, para que G07.3 possa exercitar transações offline. Ela **não** cria um canal utilizável pelo Blue-Story e **não** habilita Unova no Game.exe ou JoiPlay.

## Fonte de verdade e integração com Blue-Story

O auditor confere assinaturas de fonte dos arquivos atuais:

- `scripts/windows/Bootstrap.cs`: Blue-Story valida SHA-256 quando o hash esperado é informado para uma dependência e possui rotinas de proteção de caminhos de ZIP. Entretanto, no download do ZIP do *source* de GitHub, o argumento de checksum é `null`; **isso não constitui autenticação de pacote regional**.
- `scripts/install_game.py`: possui caminhos nativos de Kanto, Hoenn e Johto, mas **nenhuma integração física de Unova** foi feita por G07.2.
- `scripts/android/update_client.py`: possui canais `decades`, `kanto` e `multiregion`, nenhum canal G07.2 para Unova. A compatibilidade do pacote abaixo declara Android/JoiPlay `not_supported`.
- `scripts/regions/audit_unova_a12_ownership.py`: auditoria AST estática que não certifica propriedade física de MapIDs, Game.exe, licenças ou instalações.
- `site/public/data/regions.json` e `site/public/data/unova-github-progress.json`: Unova tem de continuar `planned`, Barra A **0/8** e jogável **0/32**.

## Arquivos

| Arquivo | Finalidade |
| --- | --- |
| `data/regions/unova-g07-incremental.schema.json` | JSON Schema draft 2020-12, com `additionalProperties: false`, tipos, constantes, limites e padrões |
| `data/regions/unova-g07-incremental-contract.json` | Política bloqueada, fontes de verdade, lista de extensões e limites |
| `scripts/regions/audit_unova_g07_incremental_manifest.py` | Validador fail-closed e demo inteiramente em memória |
| `tests/test_unova_g07_incremental_manifest.py` | Testes positivos e ataques negativos (direitos, hash, origem, versão, caminho) |

## Formato de pacote (G07.2)

O manifesto exige **todos** os campos:

- `schema_version=1`, `region=UNOVA`, `campaign=WHITE_BW`, `package_id` e `package_version` no formato `0.0.N-planned`, com N positivo.
- `channel=blue-story-unova-documentation` e `mode=fixture_only`. `release_allowed=false`, `native_payload_approved=false`, `game_exe_tested=false` e `saves_modified=false` são constantes do contrato.
- `source.repository` corresponde ao repositório conhecido; `origin_revision` e `target_revision` são SHAs completos de 40 dígitos, diferentes. Nenhum deles prova, sozinho, que uma instalação real suporta Unova.
- `source.manifest_path` é somente o marcador `docs/unova-package-fixtures/origin-manifest.json`, junto com seu SHA-256 e tamanho. O validador recebe os **bytes reais do fixture** e compara o inventário, o Git SHA de origem, a identidade do canal e a versão anterior `0.0.0`.
- `compatibility` declara o Blue-Story e o protocolo **1**, mas `windows=schema_only`, `installer_adapter_implemented=false`, `android=not_supported` e `joiplay=not_supported`. Não representa um instalador capaz de aplicar Unova.
- `rights`, tanto no pacote quanto em **cada arquivo**, possui os campos `status=FIXTURE_ONLY_NOT_DISTRIBUTABLE`, `license_id=null`, `evidence_path=null` e `redistribution_approved=false`. É obrigatório **declarar a falta de licença**; omitir provas ou fingir que direitos foram aprovados é erro bloqueante.
- `files[]` contém apenas `kind=documentation_fixture`, `path`, hashes SHA-256 e tamanhos do conteúdo de origem e destino, além da declaração de direitos. O auditor compara os **bytes efetivos** em memória, não somente a string de hash fornecida.
- `package_sha256` confere integridade de todos os metadados serializados de maneira canônica, excluindo esse próprio campo. **Não é uma assinatura criptográfica** e não autentica quem publicou o pacote.

### Política de caminho

A única raiz permitida é `docs/unova-package-fixtures/`, com arquivos artificiais `.txt`, `.md` ou `.json`. O validador recusa `..`, barras invertidas, caminho absoluto, letras de unidade Windows, separadores percent-encoded, segmentos ocultos, duplicações (inclusive variações de maiúsculas), nomes não ASCII, arquivos de script, executáveis e arquivos `.rxdata`.

O source manifest é somente uma **referência de inventário** e não pode ser ele próprio o arquivo a atualizar. Qualquer arquivo no diretório `game/`, `saves/`, `Data/`, `Graphics/`, `PBS/`, no instalador, nas Boxes, scripts Ruby ou pastas do Blue-Story é bloqueado.

Cada arquivo tem limite **64 KiB**; até **16 arquivos**; total sintético limitado a **512 KiB**. Nenhum desses limites equivale a autorização de escrever na pasta do usuário.

## Segurança, validação e limitações

O validador trabalha com `dict`, `bytes` e JSON canônico, sem extrair ZIP ou acessar arquivos de jogo. Falha se algum campo não estiver presente, se houver direitos ausentes, versão/revisão incompatível, SHA incorreto, tamanho divergente, manifesto não canônico, chave JSON duplicada, caminho suspeito ou inventário de origem/destino inconsistente. Para um cenário aceito, o único resultado é `SYNTHETIC_DOCS_UPDATE_VALIDATED_NOT_INSTALLABLE`, com `native_files_written=0` e `bytes_written=0`.

Comandos de validação:

~~~bash
python scripts/regions/audit_unova_g07_incremental_manifest.py --check
python scripts/regions/audit_unova_g07_incremental_manifest.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g07_incremental_manifest.py' -v
~~~

O workflow `.github/workflows/unova-documentation.yml` executa checks e demonstração no Linux e testa o auditor no Windows. O portal usa `npm run build --prefix site` e `npm test --prefix site` para validar Barra G e situação não jogável. Publicar G07.2 só após CI completo Linux, Windows e portal.

**Limite essencial:** G07.2 não aprova publicação/distribuição de nenhuma obra protegida, não faz verificação real de licenças, não implementa CAS, backups ou rollback e não autoriza patches no executável ou nos saves. A implementação e simulação dessas transações ficam para **G07.3**, também em fixtures offline. Android/JoiPlay e Windows nativos serão tratados na **G07.4**, dependendo de provas verificadas e sem presumir aprovação.

**Indicadores após CI e merge:** Barra G **28/32 (88%)**, G07 **2/4**, Barra A **0/8**, Unova jogável **0/32**.
