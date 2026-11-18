# Unova G07.4 — contratos Windows Blue-Story e Android/JoiPlay

**Entrega documental e offline apenas. Não instala mapas de Unova.** A Barra A continua **0/8**, Unova jogável **0/32** e o estado segue `planned`. A etapa G07.4 fecha os contratos de compatibilidade do desenvolvimento, **não** implementa um atualizador nativo.

## Fontes reais auditadas

| Plataforma | Comportamento existente (na fonte) | Lacuna que impede afirmar compatibilidade nativa de Unova |
| --- | --- | --- |
| Windows **Blue-Story** | `scripts/windows/Bootstrap.cs` consulta a revisão da `main`, baixa o ZIP de código-fonte de GitHub, faz staging e cópias dos arquivos existentes em `.blue-backups`; possui `SafePath`, `Protected` e SHA-256 opcional na rotina de download | O ZIP de **código-fonte** é baixado com `expected=null` e o processo de cópia por arquivo não é uma transação atômica certificada; instalação de mapa não é aprovada por esse fluxo |
| Android/Termux + **JoiPlay** | `scripts/android/update_client.py` possui os canais `decades`, `kanto` e `multiregion`. As atualizações incrementais verificam versões, entradas de ZIP, SHA-256 e certos arquivos imutáveis; os caminhos de saves são protegidos | **Não existe canal Unova**; `apply_patch` é incremental, recuperável por repetição, mas **sem backup** e sem rollback atômico; preservar arquivos não comprova funcionamento do jogo |
| Origem G07.2 | `data/regions/unova-g07-incremental.schema.json` e `scripts/regions/audit_unova_g07_incremental_manifest.py` exigem identidade, versão, hashes reais, manifesto de origem, direitos declarados e caminhos restritos | O conteúdo aceito é um **fixture documental não redistribuível**, não um pacote nativo |
| Transação G07.3 | `scripts/regions/audit_unova_g07_transaction.py` simula staging, CAS do estado completo, cópia em memória dos bytes anteriores, novo snapshot e rollback em sete falhas | Nenhuma escrita real, nenhum backup físico e nenhuma garantia contra queda de energia |

Os contratos **não** alteram `Bootstrap.cs`, `install_game.py`, `update_client.py`, Game.exe, JoiPlay, RXDATA, mapas ou saves.

## Protocolo G07.4

Os artefatos são:

- `data/regions/unova-g07-platform-compatibility-contract.json` — versões e políticas do contrato, canais existentes, requisitos documentais, provas ainda ausentes, limitações de backup e release;
- `scripts/regions/audit_unova_g07_platform_compat.py` — auditor estático de fontes reais mais pré-validação de pedido e simulação offline para os perfis `windows` e `android`;
- `tests/test_unova_g07_platform_compat.py` — casos positivos e negativos para ambos os perfis, CAS, rollback, caminhos proibidos, saves e arquivos de outras regiões.

Todo pedido possui *campos obrigatórios*, entre eles: `platform_id`, `mode`, `channel`, `package_id`, `package_version`, `package_sha256`, `source_manifest_sha256`, `source_revision`, `target_revision`, `requested_paths`, `expected_generation`, `expected_snapshot_sha256`, `rights_status`, `redistribution_approved`, `native_install_requested`, `download_requested`, `save_write_requested`, `game_exe_write_requested`, `runtime_qa`, `source_archive_sha256`, `approved_native_mapids`, `unova_release_channel` e `dry_run_only`.

**Campos estritos:** nenhum campo desconhecido, omissão, mudança de tipo ou alteração de canal é aceita. Os campos de evidência nativa precisam ser `null`; não se pode falsificar QA, MapIDs ou um release. A G07.2 valida *bytes de origem e destino*, manifesto e rights, e a G07.3 valida o snapshot integral e aplica a transação **apenas a um novo dicionário Python**. A G07.4 bloqueia quaisquer pedidos de download, instalação nativa, alteração de Game.exe ou saves.

### Canal e compatibilidade

O único canal de *fixture* permitido é `blue-story-unova-documentation`, em `docs/unova-package-fixtures/` com `.txt`, `.md` ou `.json`. O Windows continua possuindo a sua operação real `github-main-source-zip`, e o Android mantém `decades/kanto/multiregion`; tais canais **não são intercambiáveis** nem permitem instalar pacotes documentais de Unova.

Os números de versão sintéticos seguem o G07.2 (`0.0.N-planned`, origem `0.0.0`). Rejeitam-se downgrade, origem divergente, SHA-256 inválido, manifesto diferente, canal errado, alteração de direitos, perfis de runtime falsamente aprovados e source ZIP sem autenticidade. SHA-256 prova apenas integridade dos bytes, não assinatura, licença ou proveniência legal.

### Pré-condições, proteção e fallback

- O pacote/documentação deve passar no **fail-closed G07.2**, inclusive direitos `FIXTURE_ONLY_NOT_DISTRIBUTABLE` e `redistribution_approved=false`.
- O estado de fixture deve passar nas validações **G07.3**, incluindo revisão, geração e SHA-256 de snapshot completo que cobre arquivos documentais e dados regionais/globais, Saves, Boxes, checkpoints, HMs, itens-chave, mecânicas e progresso.
- As solicitações **não** podem incluir `Game.exe`, `Data/Map*.rxdata`, `MapInfos.rxdata`, save profile JoiPlay, executáveis, scripts ou qualquer caminho fora do diretório documental.
- Erros e conflitos preservam o snapshot original e resultam no fallback lógico `KEEP_EXISTING_INSTALLATION_UNCHANGED`. **Isso descreve o simulador; não é um mecanismo implementado no jogo ou nos atualizadores reais.**
- Falhas em qualquer dos sete pontos de G07.3, inclusive após a primeira alteração de candidato privado, devem reverter **todo** o estado do fixture sem publicar parcialmente dados.
- Mesmo quando a simulação é válida, o resultado é `PLATFORM_DOCS_PREVIEW_NOT_INSTALLABLE`; `install_allowed=false`, `release_allowed=false`, `native_files_written=0`, `bytes_written=0`.

## Direitos, QA e lacunas

Para habilitar Unova nativa no futuro serão necessárias **separadamente**: fontes e direitos de redistribuição auditados, manifesto confiável/assinado, hashes de artefato de release, MapIDs com propriedade verificada, pontos de entrada/saída e Centros Pokémon seguros, cadeia de revisões reais, testes no Game.exe Windows, QA JoiPlay e estratégia de backup/rollback robusta para cada plataforma. **Nenhuma dessas provas é fabricada pela G07.4.**

## Validação

~~~bash
python scripts/regions/audit_unova_g07_platform_compat.py --check
python scripts/regions/audit_unova_g07_platform_compat.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g07_platform_compat.py' -v
npm run build --prefix site
npm test --prefix site
~~~

O workflow `.github/workflows/unova-documentation.yml` executa `--check` e `--simulate-demo` no Linux e as regressões Python G07.4 em **Linux e Windows**; o workflow do portal valida o build e o progresso. Após CI aprovado e merge, a Barra G pode avançar de **29/32 para 30/32 (94%)**, frente G07 **4/4**; Barra A **0/8** e Unova jogável **0/32** não mudam.

**Próximo marco:** G08.2 — definir critérios e documentação de verificação de evidências sem confundir o progresso GitHub com jogabilidade.
