# Unova A13 — cópia QA privada REAL do Decades, sem instalar Unova

Data: 17/11/2026. Esta etapa evolui a A12, que havia criado apenas um plano em memória. A13 pode criar uma **cópia privada verificada** dos arquivos da instalação local do Decades em Windows, sem executar Game.exe, instalar mapas de Unova ou alterar a instalação original. É uma preparação física da QA, **não um teste jogável concluído**.

## Evidência que a A13 exige
- A04, A06–A12 auditadas na mesma instalação e com hashes coerentes.
- A12 com status A12_SOURCE_REVIEW_DONE_ISOLATED_QA_NOT_CREATED, sem autorizações forjadas de reserva ou instalação.
- MapInfos.rxdata e Map001.rxdata ainda correspondem aos hashes de A04; arquivos requeridos: Game.exe, Game.ini, mkxp.json, Data/Scripts.rxdata e Data/System.rxdata.
- Nenhum MapID 518–599 é atribuído nesta fase. Mesmo com 82 IDs candidatos desocupados, os dados Unova de origem, os manifests futuros e as referências dinâmicas estão pendentes.

## O que o BAT A13 faz com um duplo clique
1. Repete os diagnósticos A04–A12 na instalação atual.
2. Quando há baseline e configuração compatíveis, inventaria os arquivos locais, rejeita symlinks/junctions/reparse points, verifica limites de arquivos e capacidade de disco e confere hashes durante a cópia.
3. **Exclui pastas e arquivos típicos de saves e dados privados**, inclusive Saves, Savedata, FileN.rxdata, SaveN.rxdata, .blue-work e backups. Os saves normalmente armazenados em AppData não são lidos ou tocados.
4. Copia o Decades para uma nova pasta privada dentro de %LOCALAPPDATA%\PokemonBlueUnovaMapids\qa-copies\qa-unova-a13-IDENTIFICADOR. Nunca escreve na pasta original. Não copia arquivos para o repositório/GitHub.
5. **Somente na cópia**, redefine windowTitle, dataPathApp e dataPathOrg em mkxp.json e o Title de Game.ini para um perfil diferente do jogo original. Configurações com chaves personalizadas de save são rejeitadas.
6. Cria a cópia numa pasta temporária privada e só publica o diretório final após hashes verificados. Uma falha remove apenas o estágio temporário criado por esta execução, preservando qualquer QA existente ou arquivo da instalação original.
7. Em reexecuções, verifica a QA existente; se houver adulteração, bloqueia sem substituir nem apagar.
8. Escreve a13-private-qa-HASH.json no cache de auditoria e, dentro da QA, unova-a13-copy-evidence.json e UNOVA_A13_NAO_ABRIR_ANTES_DOS_TESTES.txt.

## Limitações cruciais
- **O Game.exe NÃO é aberto**, e a cópia pode **não ser segura para jogar ainda**: o namespace de saves é alterado apenas nas configurações conhecidas; scripts Ruby, plugins e caminhos efetivos de save exigem inspeção/teste de execução em ambiente controlado.
- **NÃO** são instalados mapas Unova, reserva 518–599, manifestos de Unova, scripts de inicialização ou dados de origem.
- Um backup de saves do usuário ou uma migração de saves não ocorre, nem deve ser inferido.
- O uso do BAT pode exigir **vários GB de espaço adicional**; a ferramenta aborta se o espaço estimado for insuficiente.
- Se Game.ini ou mkxp.json faltar, contiver opções de save personalizadas ou houver pastas inseguras, A13 fica BLOCKED_A13_QA_COPY_NOT_CREATED. **Isso é bloqueio legítimo**, não uma aprovação tácita.

## Como executar e enviar evidências
Baixar e extrair RUN_UNOVA_MAPIDS_A13.zip. Executar RUN_UNOVA_MAPIDS.bat com dois cliques e Python 3.11+ no Windows. Depois enviar LEIA_AQUI_UNOVA_MAPIDS.txt e a13-private-qa-HASH.json referenciado no resumo; **não enviar Game.exe ou saves pessoais**. Se a QA foi criada, apenas informar o caminho e o status, sem iniciar o executável.

## Próxima etapa provável — A14
Confirmar em ambiente estritamente isolado a compatibilidade de saves e o bootstrap real do Game.exe. Somente após isso, e após a obtenção e auditoria de fonte Unova autorizada, iniciar experimentos de remap e instalação em cópia QA com rollback real. **Barra A 0/8 e Unova jogável 0/32** enquanto esses critérios não forem cumpridos.
