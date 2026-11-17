# Sinnoh L00 — Auditoria documental segura antes da QA física

**17/11/2026 · continuação da esteira G01–G12, issue #165.** Esta entrega **não examina o computador**, não instala a região, não executa `Game.exe`, Windows Sandbox ou JoiPlay e não processa saves, PNGs, ZIPs ou arquivos privados. Somente *contratos públicos versionados* do GitHub e **resumos JSON estritamente sanitizados** podem alimentar o auditor.

## Entradas e estados

- [Modelo seguro de entrada L00](../data/regions/sinnoh-l00-public-reports.json): `B09`, `B10`, `B11`, `R07`, `R08` começam como `null`, pois **nenhum relatório local novo foi entregue nesta tarefa**. O modelo não contém paths de sistema nem identificadores de saves.
- [Auditor fail-closed L00](../scripts/regions/audit_sinnoh_l00_readiness.py): verifica a lista de campos e valores esperados para cada etapa, hashes de vínculo, limites de contagem, estados de segurança, relatórios G12 e contratos públicos B09/B10/B11/R07/R08.
- O relatório do CI classifica cada origem como **`MISSING_REPORT`** ou **`RECEIVED_SANITIZED_REPORT_UNVERIFIED`**. Nenhum desses valores significa prova física independentemente aceita.

| Origem | Campos sanitizados permitidos | O que continua não provado |
| --- | --- | --- |
| **B09** | SHA do plano/cópia, SHA de inventário **público**, 702 mapas esperados, 54 terrenos, 14 PNGs de referência, nenhum save ou execução | Que os bytes do clone foram verificados remotamente, executável ou mapas funcionais |
| **B10** | SHA do plano B09, 648/54/702 mapas, configuração WSB com montagem somente leitura, rede/clipboard desabilitados e autostart falso | **Que a VM iniciou, o convidado foi isolado ou qualquer jogo foi executado** |
| **B11** | Contagem de diretórios e arquivos monitorados, estado de alteração antes/depois, `watch_unchanged` e escopo parcial | Cobertura completa dos caminhos de save da engine, isolamento global ou execução independente na VM |
| **R07** | Inventário agregado, checksum público MapInfos, quantidade de regiões cadastradas, colisões e `candidate_safety_reviewable` | Titularidade e reserva de **todos** os MapIDs futuros, mesmo sem colisões observadas |
| **R08** | Contagem de análises de licenças, 14 PNGs esperados, status de revisão pendente | Direitos legais por recurso, assets instalados, eventos, mapas, PBS de Barry compilados |

**Atenção ao R08:** não existe um recibo público de aprovação física R08 no GitHub. O JSON L00 para R08 é um **formato novo e intencionalmente restrito de relatório de progresso documental**, sempre com `RIGHTS_REVIEW_PENDING`, `r08_complete=false` e `can_install=false`. Mesmo a contagem máxima de análises documentais não confirma licença ou redistribuição autorizada.

## Uso em CI e sem acesso ao computador

O modo padrão:

~~~bash
python scripts/regions/audit_sinnoh_l00_readiness.py
~~~

Lê exclusivamente o modelo versionado com **cinco relatórios ausentes**. O CI grava um JSON apenas em `.blue-work/sinnoh-l00/public-readiness.json` dentro do runner do GitHub e publica esse **único artefato de metadados**. Nenhum arquivo da VM, recibo privado ou jogo entra nos artifacts.

**Opção futura e totalmente explícita:** `--workspace-reports` só aceita a localização **fixa** `.blue-work/sinnoh-l00-input/public-reports.json`, no checkout em que o auditor for executado voluntariamente. Não há argumento de caminho arbitrário nem varredura de máquina. O JSON deve ter exatamente o mesmo envelope do modelo, e cada relatório recebido só pode ter os campos especificados no auditor; qualquer nome, path, snapshot, campo extra ou tentativa de indicar aprovação causa erro. Esse modo **não é acionado pelo GitHub Actions** e sua simples existência não significa que o PC foi inspecionado.

## Regras de segurança implementadas

1. **B09 → B10:** exigir o mesmo `plan_sha256` em recibos sanitizados e comparação com o inventário B09 versionado; SHA não comprova por si só origem nem integridade física verificada independentemente.
2. **B10:** exige `mapped_folders_read_only=true`, `internet_networking_enabled=false`, `clipboard_enabled=false`, `game_exe_started=false` e `sandbox_session_started=false`. A configuração preparada nunca é promovida à sessão executada.
3. **B11:** verifica coerência de `files_added`, `files_removed`, `files_changed` e `watch_unchanged`; mesmo com **zero alterações**, exige `coverage_is_partial=true`, `host_saves_globally_isolated_proven=false` e `complete_host_save_coverage_verified=false`. Relatório que esconde alterações é recusado.
4. **R07:** os manifestos futuros Kanto/Johto/Hoenn são necessários para declarar um candidato apto à **revisão**, nunca para completar R07. A L00 não inventa reservas de Unova ou interpreta ocupação como propriedade.
5. **R08:** rejeita qualquer afirmação de direitos verificados, mapas físicos aprovados ou PBS compilado. A revisão real por ativo continua fora do GitHub.
6. **G12:** exige **44 casos nativos pendentes (43 Windows + 1 Android)**, gates L01–L05 pendentes, R07/R08/R09 falsos, barras B/C/D em **0/13**, sem alterações no jogo ou nos saves.

## Testes automatizados

[24 testes L00](../tests/test_sinnoh_l00_readiness.py) cobrem:
- modelo sem relatórios; exemplos inteiramente sintéticos válidos que permanecem não aprovados;
- incompatibilidade de SHA B09/B10, mapas esperados e stage;
- rede/clipboard/autostart inseguros em B10;
- falsificação de `watch_unchanged`, escopos, contagens e salvamentos em B11;
- R07 com futuras reservas omitidas, MapInfos divergentes ou `r07_complete=true`;
- R08 com direitos aprovados sem prova, contagem de PNGs alterada e falsa compilação;
- rejeição de paths/nomes/saves/snapshot/HMAC como campos extras, links simbólicos e arquivos de entrada grandes;
- retificação falsa dos 44 casos G12, permissões de jogo e barra B/C/D.

O [workflow L00](../.github/workflows/sinnoh-l00-readiness.yml) reexecuta G12, G11, B10, B11 e R07, além do novo CI específico. **Sucesso no CI apenas confirma auditoria e fixtures, não o jogo.**

## O que falta depois da L00

Ainda é necessário coletar e revisar **fora do GitHub** evidências locais sanitizadas B09/B10/B11, MapIDs de todas as regiões e direitos por ativo. Após essa revisão humana, será possível decidir se há condições de **agendar** uma QA Windows Sandbox com isolamento demonstrado — jamais no Windows principal como fallback — e, depois, QA em Android/JoiPlay. Não há autorização para iniciar qualquer sessão nesta entrega.

**Próxima etapa segura sugerida: L01 — preparação de um exportador local opcional de relatórios sanitizados e revisão de cobertura**, a ser desenvolvida no GitHub sem executar nem abrir o jogo. O operador local decidirá se deseja rodá-lo; nenhuma coleta automática do PC será realizada pelo chat.
