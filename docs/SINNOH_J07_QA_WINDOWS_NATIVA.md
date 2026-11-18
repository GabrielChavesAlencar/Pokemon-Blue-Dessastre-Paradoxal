# Sinnoh J07 — Harness Windows QA nativa com evidência SHA

**Base:** J06 PR #233 integrada, issue #232. **Próxima J08:** issue #234.

## Engenharia executável, não jogo aprovado

O script scripts/regions/prepare_sinnoh_playable_j07.py é um harness de preflight, abertura de sessão privada, conferência de observações e lançamento apenas explícito da cópia QA. Reutiliza o launcher J06 e o validador audit_sinnoh_playtest.py; não cria um instalador concorrente.

**Realidade:** 0/9 mapas físicos Sinnoh instalados, 0/24 eventos executados no jogo e 0/44 casos QA nativos. Game.exe/JoiPlay não foram executados nesta etapa. R07/R08/R09 pendentes, cinco mapas ainda faltando. O CI usa exclusivamente mapas, sprites, equipes PBS, Game.exe e permissões **sintéticas**. Isso não é fonte licenciada nem prova de uma sessão nativa.

## Pré-requisitos exigidos

1. Uma cópia J06 QA **privada e real** em .blue-work/game-sinnoh-qa-TOKEN (não a instalação principal). Exige seu recibo SHA-256 e verifica Game.exe, MapInfos, hashes do conteúdo autorizado e isolamento do perfil de saves mkxp/Game.ini. Não migra saves nem cria marcador de Barry.
2. Revalida todos os arquivos originais de staging, os 9 mapas com 16 warps, 5 handlers, 3 bolas e sprites, revisão R08 por arquivo e reserva R07 de **todos** os MapIDs, com hashes iguais aos usados na instalação J06. Um atestado manual não equivale a licença de redistribuição.
3. Exige que o **Game.exe da cópia QA** já tenha compilado as três versões PBS Barry e produzido o relatório de inspeção nativa estrutural com nove mapas, 24 eventos e 16 warps. Um relatório estrutural NÃO prova batalhas, save/reload ou jogabilidade.
4. Vincula a sessão ao catálogo G12 versionado com 43 casos Windows e 1 Android; rejeita matriz alterada, falso status concluído, região ausente, modo Master 70% em vez de 90%, evento inexistente, perfil diferente ou prova adulterada.

### Uso futuro no Windows (sem PowerShell)

Executar a partir do CMD no repositório usando SINNOH_J07_QA_WINDOWS.bat e as fontes reais no workspace privado.

Pré-voo sem iniciar Game.exe:

    SINNOH_J07_QA_WINDOWS.bat --qa ".blue-work\game-sinnoh-qa-TOKEN" --receipt-sha SHA_J06 --overlay ".blue-work\sinnoh-qa-overlay" --spec ".blue-work\j06-events.json" --rights ".blue-work\j06-rights.json" --reservations ".blue-work\j06-reservations.json"

Para criar sessão de QA sem executar o jogo, repetir esse comando com o parâmetro --init. Será criada pasta NOVA e sem overwrite .blue-work/sinnoh-j07-sessions/game-sinnoh-qa-TOKEN-SESSIONID, com arquivo j07-session.json, duas subpastas evidence/ e records/, e session_sha256. Não escreve em game/ nem em Saves/.

Para abrir a cópia QA apenas com autorização explícita, repetir os parâmetros obrigatórios e adicionar:

    --launch --session ".blue-work\sinnoh-j07-sessions\game-sinnoh-qa-TOKEN-SESSIONID" --session-sha SHA_SESSAO

Essa ação chama o launcher QA existente, verifica o hash e a configuração de save e **nunca** abre o Game.exe principal. Se os pré-requisitos não existirem, ela bloqueia antes da execução.

Para cada caso realmente observado, colocar em evidence/ um JSON nomeado pelo caso G12 (ex.: ball-TURTWIG.json) com os campos medidos pelo testador e um segundo arquivo PNG/TXT/LOG com evidência local. Informar os SHA-256 dos dois arquivos no comando:

    --record ball-TURTWIG --observed "<sessao>\evidence\ball-TURTWIG.json" --observed-sha SHA_JSON --attachment "<sessao>\evidence\ball-TURTWIG.txt" --attachment-sha SHA_LOG --session "<sessao>" --session-sha SHA_SESSAO

O auditor valida as medições contra regras do Blue (70% Normal / 90% Master, espécie e time de Barry, três iniciais únicos, localização dos 16 portais, cinco handlers, save/reload e saves intocados nas quatro regiões). A evidência permanece **local**, sem subir capturas, saves, EXE ou assets ao repositório público.

Para auditar sem modificar arquivos: adicionar --audit --session "<sessao>" --session-sha SHA_SESSAO ao comando completo original. A saída conta apenas a quantidade de documentos enviados para revisão; **não** converte alegações do testador em prova independente de execução real. Mesmo 43 documentos corretos mostram native_windows_cases_independently_verified=0 até revisão de verdade. O caso Android permanece para J08.

### Matriz de testes G12

- 3 escolhas físicas: Turtwig, Chimchar, Piplup, sempre impedindo a segunda Poké Bola.
- 12 batalhas Barry: cada inicial x Normal/Master x vitória/derrota, com contra-inicial correto, níveis 70%/90% e time compatível.
- 3 verificações save/reload em perfil Sinnoh independente e preservação de equipe/Pokédex.
- 16 portais, conferindo MapID e coordenadas de chegada.
- 5 NPCs: mãe, Barry, Rowan, com handlers originais.
- 4 regressões: Decades, Kanto, Johto e Hoenn, com saves não alterados.
- 1 Android JoiPlay: exclusivamente J08.

### Regressões e promoção

O workflow roda 50 cenários sintéticos em Windows/Linux descartáveis, regressões de J06/J05/J04, e valida o portal. CI verde conta somente como código pronto. Esta J07 muda a barra de engenharia para **7/8 (87,5%)**, mantendo nativo **0/8**, 0/44 G12 e Sinnoh planned/não jogável. Nunca cria marcador Barry, abre Game.exe no CI público, toca saves pessoais ou marca direitos como aprovados. Próxima J08: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/234.
