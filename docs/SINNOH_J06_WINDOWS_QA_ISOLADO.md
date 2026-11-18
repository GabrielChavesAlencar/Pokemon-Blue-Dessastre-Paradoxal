# J06 — Windows QA isolada: instalador, launcher e rollback

Data: 18/11/2026. Base J05 PR #231 integrada; J06 issue #230.

## Entrega de código, não de jogabilidade

A ferramenta scripts/regions/prepare_sinnoh_playable_j06.py implementa:
- Pré-voo somente leitura que reusa o instalador privado install_sinnoh_qa_copy.py e o launcher launch_sinnoh_qa.py, sem copiar saves para a área QA.
- Exigência de nove mapas privados auditados, 16 portais, 5 NPCs, 3 Poké Bolas e três PBS Barry originais. Compara hashes SHA-256 de todos os arquivos do overlay, Game.exe e MapInfos da base, cada mapa do intervalo 442–517 e os IDs protegidos de outras regiões.
- Revisão explícita e **local** de direitos para CADA arquivo; não confundir atestado do usuário com licença ou verificação independente. Nenhuma permissão é inventada. Sem autorização R08 e R07, a instalação fica bloqueada.
- Cópia exclusivamente dentro de .blue-work/game-sinnoh-qa-XXXXXXXXXXXX com título, identificador e namespace de saves próprios. Nenhum overwrite em game/, Decades/Kanto/Johto/Hoenn. Sem fallback para instalar Game.exe.
- Recibo com inventário SHA-256 de todos os arquivos copiados e operação de rollback SOMENTE para cópia intacta, ainda sem testes nem saves. Se a pasta tiver save novo, conteúdo alterado ou extra, o rollback recusa e preserva os arquivos.
- Compilação e lançamento separados por comandos explícitos; o launcher anterior exige relatório do motor, perfil isolado e marcadores assinados por hashes antes de abrir a cópia QA. Nenhum Game.exe é executado no CI desta fase.

**Situação real: 0/9 mapas Sinnoh instalados, 0/24 eventos instalados e 0/44 QA G12 executados.** Os cinco mapas de origem ausentes continuam sendo: quarto, térreo da casa, casa Barry, Lago Verity e laboratório Rowan. R07/R08/R09 não estão aprovados.

## Fontes obrigatórias — não publicar no Git

O usuário deve montar localmente e com autorização um overlay privado por prepare_sinnoh_pilot_bundle.py contendo nove mapas de verdade, coordenadas e tilesets auditados, eventos Blue originais, PBS Barry, SinnohPilot.rb, e o arquivo sinnoh-qa-overlay-report.json SHA. Staging J03 de quatro terrenos ou template CH06 com null não bastam.

Crie também na pasta ignorada .blue-work os três arquivos JSON locais:

### j06-events.json
Espelho da especificação de eventos usada no overlay, contendo os nove MapIDs reais, as posições e 24 comandos reais verificados. Não preencher coordenadas fictícias.

### j06-rights.json
Campos EXATOS:
- schema = 1, region = SINNOH, stage = J06
- mode = LOCAL_RIGHTS_REVIEW_NOT_REDISTRIBUTABLE
- reviewed_locally = true somente após aprovação humana real
- redistribution_authorized = false
- overlay_report_sha256 = hash dos bytes do relatório de overlay
- source_game_exe_sha256 = hash do Game.exe local
- source_mapinfos_sha256 = hash de game/Data/MapInfos.rxdata
- spec_sha256 = hash dos bytes de j06-events.json
- reviewer_reference = referência privada e identificável ao registro humano, sem enviar arquivos protegidos
- files = objeto com EXATAMENTE cada caminho do campo files_sha256 do overlay. Valor de cada arquivo: sha256 (igual ao overlay), basis (OWNED_ORIGINAL, EXPLICIT_PERMISSION ou REUSABLE_LICENSE), permission_evidence (referência comprovável) e private_qa_permitted = true somente para uso realmente permitido.

Uma simples escrita de reviewed_locally = true não comprova direitos. A ferramenta exige correspondência dos hashes e documenta que autorização jurídica continua sendo responsabilidade de quem fornece o conteúdo. Não redistribuir.

### j06-reservations.json
Campos EXATOS:
- schema = 1, region = SINNOH, stage = J06
- mode = PRIVATE_REGIONAL_MAPID_REVIEW
- reviewed_locally = true e r07_global_reservations_approved = true SOMENTE após revisão concreta das reservas existentes e futuras
- source_mapinfos_sha256 = hash real do MapInfos da instalação
- candidate_map_ids = lista crescente de TODOS os IDs do overlay, incluindo terrenos extras além dos nove primeiros quando existirem
- protected_map_ids = lista sem duplicatas dos IDs de outras regiões e reservas futuras
- reviewer_reference = identificação local do registro real de aprovação.

A ferramenta relê o MapInfos, mapas e PBS do Blue, e bloqueia colisões mesmo se o registro local parecer válido.

## Como usar no Windows — sem PowerShell

Execute a partir do CMD da pasta do repositório, usando SINNOH_J06_QA_WINDOWS.bat.

Pré-voo SEM escrever ou executar Game.exe:

    SINNOH_J06_QA_WINDOWS.bat --overlay ".blue-work\sinnoh-qa-overlay" --spec ".blue-work\j06-events.json" --rights ".blue-work\j06-rights.json" --reservations ".blue-work\j06-reservations.json"

Depois de todas as revisões e somente no Windows, acrescente --install ao mesmo comando. Isso cria uma pasta privada NOVA; a saída inclui qa_directory e receipt_sha256 reais.

Verificar a cópia antes de qualquer execução:

    SINNOH_J06_QA_WINDOWS.bat --verify ".blue-work\game-sinnoh-qa-TOKEN" --receipt-sha SHA_DO_RECIBO

Iniciar a compilação NATIVE apenas na cópia QA previamente revisada (ação explícita):

    SINNOH_J06_QA_WINDOWS.bat --compile ".blue-work\game-sinnoh-qa-TOKEN" --receipt-sha SHA_DO_RECIBO

Abrir somente a cópia QA após a compilação/relatório estrutural válido:

    SINNOH_J06_QA_WINDOWS.bat --launch ".blue-work\game-sinnoh-qa-TOKEN" --receipt-sha SHA_DO_RECIBO

Rollback apenas de uma cópia QA ainda intacta (NUNCA de um jogo que gerou saves):

    SINNOH_J06_QA_WINDOWS.bat --rollback ".blue-work\game-sinnoh-qa-TOKEN" --receipt-sha SHA_DO_RECIBO --confirm-rollback

O duplo clique no BAT sem os JSON locais NÃO instala nada e retorna um bloqueio.

## Regressões e próxima etapa

- tests/test_sinnoh_j06_qa_windows.py: 40 cenários com arquivos, mapas, sprites, PBS e Game.exe SINTÉTICOS. Não reproduz/redistribui uma ROM nem confirma Game.exe real.
- Workflow J06 com testes Linux e Windows em runners descartáveis; regressões do instalador S11/CH10, J04/J05 e portal.
- Jogos reais, saves reais, direitos e Joiplay permanecem pendentes mesmo após o CI verde.

Próxima fase J07: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/232.
