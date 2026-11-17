# Sinnoh G01 — auditor de recibos de recuperação B09 (somente GitHub)

**Escopo:** confirmar que os *metadados* do recibo B09 são coerentes com o contrato do repositório e, opcionalmente, com o dry-run de origem. O script **não acessa o jogo, não percorre o clone, não copia saves e não inicia Game.exe**. Sem artefatos de terceiros no GitHub.

## Entradas

- Um JSON local de recuperação B09 com exatamente 20 campos, status \`PRIVATE_NATIVE_QA_CLONE_CREATED_NOT_RUNNABLE_YET\`, contagens e indicadores de segurança.
- Opcionalmente o JSON do dry-run B09 com SHA-256 do plano.
- Contrato existente em \`data/regions/sinnoh-b09-native-qa.json\` (público, não contém saves).

Execute localmente **somente quando quiser auditar um relatório**; esta etapa de engenharia no GitHub foi testada com fixtures próprias:

~~~bash
python scripts/regions/audit_sinnoh_g01_b09_receipt.py --receipt CAMINHO/RELATORIO_RECUPERACAO.json --dry-run CAMINHO/B09_DRYRUN.json
python -m unittest discover -s tests -p 'test_sinnoh_g01_b09_receipt.py' -v
~~~

Saída: JSON sanitizado no stdout, **sem caminhos do usuário, hashes de arquivos individuais, dados do jogo, PNGs ou saves**. Um JSON inválido, arquivo ausente, link simbólico, esquema desconhecido, contador incoerente ou marcador de \`safe_to_launch=true\` provoca \`SINNOH_G01_BLOCKED\` (exit code 2).

## Verificações

1. Exige exatamente o status de clone privado não executável e caminho relativo no padrão \`.blue-work/sinnoh-b09-native-qa/native-<16 hex>\`. Bloqueia caminho absoluto, traversal e destinos fora do workspace.
2. Confere 648 mapas nativos + 54 geometrias = 702 declarados; B08 declara 54 mapas, 14 PNGs e 484.722 células, com total de overlay 70 entradas.
3. Reconcilia \`files_reused + files_copied + files_repaired\` com \`native_file_count + sinnoh_overlay_files - 2\`. A subtração decorre **somente** das tabelas \`Data/MapInfos.rxdata\` e \`Data/Tilesets.rxdata\` substituídas pelo overlay. Isso **não prova** que as duas tabelas físicas foram realmente substituídas: só verifica a política contábil da B09.
4. Com \`--dry-run\`, exige SHA-256 no formato correto e prefixo coerente com a pasta do clone, mesmas quantidades declaradas, mesmo escopo B08 e garantias de não execução; continua sem autenticar arquivos físicos.
5. Recusa \`saves_copied\`, \`game_exe_executed\`, \`native_game_tested\`, \`joiplay_tested\`, \`safe_to_launch\`, \`can_install_live_game\`, \`r07_complete\`, \`future_reservations_verified\` ou \`phase_b_approved\` falsamente verdadeiros.

## Diagnóstico do relato recebido, verificado fora do GitHub

Os **valores numéricos sanitizados** enviados no diálogo: 25.918 reutilizados + 2.755 copiados + 1 reparado = **28.674 operações**; 28.606 entradas originais + 70 do overlay = **28.676 entradas lógicas**. A diferença **2** é consistente com as duas tabelas de overlay que substituem tabelas nativas. Também houve correspondência do prefixo do SHA-256 com o dry-run fornecido.

O resultado da validação de metadados é \`B09_RECEIPT_METADATA_CONSISTENT_NOT_PLAYABLE\`, com:
- \`linked_to_supplied_dry_run=true\`, apenas ligação declarativa entre os JSONs;
- \`private_clone_independently_audited=false\` e \`receipt_authenticity_proven=false\`;
- \`game_exe_tested=false\`, \`joiplay_tested=false\`, \`safe_to_launch=false\`;
- Barra B/C/D = **0/13**, R07 pendente.

**NÃO publicar os JSONs de recuperação do usuário no repositório.** Os 14 testes usam dados sintéticos e verificam esquema, SHA/pasta, contagens, indicadores falsos, privacidade e entradas malformadas.

## O que ainda depende do ambiente local

B10 precisa criar e validar Windows Sandbox com o clone isolado; B11 precisa comparar escopos de saves reais antes/depois; R07 precisa de reservas futuras revisadas e R08 de direitos de uso. Nenhuma execução ou CI da G01 libera o Game.exe, inventa caminhos ou aprova fases jogáveis.
