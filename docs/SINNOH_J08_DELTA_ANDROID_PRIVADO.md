# Sinnoh J08 — pacote incremental privado Android/JoiPlay

Base: J07 PR #235 integrado, J08 issue #234. Próximo J09: issue #236.

## Estado real e limites

J08 implementa **código executável** que gera somente um ZIP candidato de diferenças entre snapshots Android de uma QA privada. Não existe release Android Sinnoh real neste PR. Faltam cinco mapas físicos e R07/R08/R09. 0/9 mapas instalados, 0/44 testes nativos, Game.exe e JoiPlay não executados nesta entrega. A engenharia 8/8 não é jogabilidade 8/8.

O código está em scripts/regions/prepare_sinnoh_playable_j08.py. Não instala ZIP, não procura celulares, não executa Game.exe/JoiPlay, não acessa saves pessoais, não faz backup total nem publica releases. Nunca altera a instalação principal game/, o Android original ou Kanto/Johto/Hoenn/Decades.

O script reutiliza a política safe_path existente em scripts/android/update_client.py, mas não cria um canal global Sinnoh, não publica assets públicos e não modifica o atualizador do Android.

## Pré-requisitos privados e humanos

É obrigatório fornecer as fontes reais aprovadas da J06/J07, sem subir recursos/contratos/saves no GitHub:
- Cópia Windows QA privada J06 com recibo SHA-256, nove mapas reais, 16 portais, cinco handlers originais, três Poké Bolas, três variantes PBS Barry, profile de save separado, compilação e prova estrutural do motor.
- Source overlay privado, specification de nove MapIDs, revisão individual de direitos R08 e reservas globais R07; todos os hashes devem corresponder à J06.
- Sessão J07 privada com os **43/43 registros de casos Windows** e revisão humana independente real dos 43 casos, preservando saves. Mesmo uma revisão escrita em JSON é um atestado humano, não prova independente para o ChatGPT nem direito de redistribuir.
- Dois snapshots Android privados na pasta .blue-work: sinnoh-j08-android-base-TOKEN e sinnoh-j08-android-qa-TOKEN, com o MESMO token aleatório de 12 caracteres hexadecimais. Cada snapshot usa Game.ini com Title=Sinnoh Android QA TOKEN e mkxp.json com dataPathApp=Sinnoh-QA-Android-TOKEN, dataPathOrg=Dessastre-Sinnoh-Android-QA-TOKEN e windowTitle=Sinnoh Android QA TOKEN. É um perfil de **teste de isolamento de diretório**, não prova de que o JoiPlay de uma instalação real irá respeitar essas configurações. Base inclui Data/MapInfos.rxdata, Data/System.rxdata, Data/PluginScripts.rxdata, mas não pode ocupar nenhum dos nove novos MapIDs Sinnoh. Alvo inclui toda a base sem remoções mais as nove áreas, 24 eventos, os arquivos PBS Barry, SinnohPilot.rb e sprites PNG. O cache PluginScripts do Android deve ter sido compilado e revisado separadamente. O script não compila nem afirma compatibilidade JoiPlay.

Dois recibos locais sob .blue-work (jamais publicar credenciais, saves, ROMs ou comprovantes privados):
1. j08-windows-review.json: chaves schema=1, region=SINNOH, stage=J08, mode=INDEPENDENT_WINDOWS_HUMAN_REVIEW_LOCAL_ONLY, session_sha256, j06_receipt_sha256, independent_human_reviewed=true somente após revisão física, reviewer_reference e cases. Este último mapeia EXATAMENTE os 43 IDs G12 Windows para record_sha256, evidence_checked=true e native_windows_run_observed=true (somente com observações realmente vistas). A integridade é verificada contra os registros J07.
2. j08-android-review.json: chaves schema=1, region=SINNOH, stage=J08, mode=LOCAL_ANDROID_QA_RIGHTS_REVIEW_NOT_REDISTRIBUTABLE, reviewed_locally=true somente depois de revisar, redistribution_authorized=false, j06_receipt_sha256, j07_session_sha256, windows_review_sha256, android_stage_profile_sha256, android_plugin_cache_sha256, android_mapinfos_sha256, reviewer_reference e files. O objeto files contém exatamente todos os arquivos alterados, com sha256, permission_evidence e private_qa_permitted=true SOMENTE se realmente permitido no QA privado.

Atestados falsos ou sintéticos **nunca** autorizam uma distribuição real. O CI só gera documentos sintéticos para detectar regressões.

## CLI Windows sem PowerShell

Atalho SINNOH_J08_QA_ANDROID.bat ou Python 3 diretamente. Exemplo de estrutura com caminhos e hashes ILUSTRATIVOS, que devem ser substituídos por valores reais confirmados localmente:

    SINNOH_J08_QA_ANDROID.bat --qa ".blue-work\game-sinnoh-qa-TOKEN" --receipt-sha SHA_J06 --overlay ".blue-work\sinnoh-qa-overlay" --spec ".blue-work\j06-events.json" --rights ".blue-work\j06-rights.json" --reservations ".blue-work\j06-reservations.json" --session ".blue-work\sinnoh-j07-sessions\game-sinnoh-qa-TOKEN-SESSION" --session-sha SHA_J07 --windows-review ".blue-work\j08-windows-review.json" --android-stage ".blue-work\sinnoh-j08-android-qa-TOKEN" --android-baseline ".blue-work\sinnoh-j08-android-base-TOKEN" --android-review ".blue-work\j08-android-review.json"

Sem opções de ação, o pré-voo é **somente leitura** e deve falhar se qualquer entrada autorizada estiver faltando. Com a opção --package e todos os gates aprovados, cria exclusivamente um novo ZIP em .blue-work/sinnoh-j08-candidates/SINNOH-J08-TOKEN-ID.delta.zip.

O ZIP contém SOMENTE arquivos modificados/adicionados, com hash SHA-256 e tamanho no J08-delta.json. Sem remoções, saves, backups, mkxp.json, Game.ini, Game.exe, .dll, .so ou instaladores; arquivo de perfil sempre preservado. O script revalida cada mapa, PNG, PBS Barry e plugin SinnohPilot.rb comparando SHA contra a cópia J06, e impede sobrescrita de MapIDs já presentes na base Android. Não modifica a base. Não possui comando para aplicar o patch.

Para conferir ZIP candidato existente:

    SINNOH_J08_QA_ANDROID.bat --verify ".blue-work\sinnoh-j08-candidates\ARQUIVO.delta.zip" --zip-sha SHA_REAL

Para descartar apenas ZIP ainda não aplicado, usar --discard no lugar de --verify e acrescentar --confirm-discard. O descarte nunca remove snapshots, Android instalado, backups nem saves. Se outro processo externo aplicou um patch, não é possível desfazer isso com --discard.

## Gate Android independente

O caso android-joi-play (1/44) só poderá ser contabilizado após teste JoiPlay real num ambiente autorizado, validando profile de saves verdadeiramente independente, inicial, warp, recarregamento de save, encontros selvagens, músicas e integridade Kanto/Johto/Hoenn/Decades. Evidência Windows, fixture, hash de ZIP e declaração genérica não contam. J08 não executou Android e não promove Sinnoh de planned.

**Próximo J09, desbloqueio real:** https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/236
