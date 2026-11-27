# Johto — Roadmap Codex para 100% jogável no Windows e Android

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data-base:** 27/11/2026  
**Alvo:** campanha HeartGold/SoulSilver adaptada ao Blue/Decades, no mesmo Game.exe, com novo jogo, exploração integral, oito ginásios, Liga, pós-jogo, viagem regional, saves e publicação Windows + Android. Crystal é complemento somente quando compatível.  
**Natureza:** plano de execução, não certificado de gameplay nem recibo de instalação. J00–J23 são novos lotes verticais, distintos das antigas fases 01–16 e da barra offline 12/12.

## 0. Instrução permanente ao Codex

Você é o executor: leia AGENTS.md se existir, este roadmap, a main atual e os PRs em andamento. Implemente funcionalidades reais no repositório; não entregue apenas planos, manifestos vazios, mocks ou novas barras. Retome o primeiro lote incompleto com evidência; não reinicie o trabalho já aprovado. Priorize PR pequeno por fluxo funcional (porta + NPC + PBS + teste + migração + publicação), reutilize código existente, faça commits rastreáveis. Não altere Kanto, Gary, Decades, Hoenn, Sinnoh, Unova, regras globais ou saves para facilitar Johto.

- Não sobrescreva PR alheio, force-push main, desative testes, ignore falha de workflow nem invente logs. Confira HEAD completo e base antes de cada merge.
- Não use o ZIP doador como jogo, nem copie Scripts.rxdata, MapInfos.rxdata, Tilesets.rxdata ou System.rxdata inteiros de outro jogo. Integre somente dados auditados, scripts próprios e recursos com autorização.
- Trabalhe em staging isolado, com runner Windows descartável autorizado para Game.exe. Nunca execute no computador pessoal nem leia saves reais sem autorização; use saves de teste descartáveis.
- Se faltar fonte, permissão ou dispositivo, registre BLOCKED_SOURCE / BLOCKED_RIGHTS / BLOCKED_ENV / QA_PENDING com insumo e teste exatos. Continue trabalho independente que não contorne o gate, sem marcar falso aceite. Não solicite token no chat.
- Cada lote perceptível aprovado exige um par Windows + Android na mesma revisão funcional, antes de começar o próximo lote perceptível. Aplique [regra de Kanto](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md). Se hardware físico for adiado expressamente, separe DELIVERED_WITH_QA_PENDING de ACCEPTED e não emita VERIFIED_PLAYABLE final.
- Mantenha texto de acompanhamento mínimo: lote, HEAD, PR, checks, mapas/IDs, marcadores comprovados, builds/hashes, bloqueio e próximo passo. Oculte barras já concluídas no relatório de execução, preserve histórico no manifesto.

## 1. Baseline confirmado e divergências a resolver em J00

| Indicador | Evidência disponível | Interpretação |
|---|---|---|
| Fonte v1 | [PR #31](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/31): 74 mapas RMXP, IDs origem 79–152; 42 conexões, Mt. Silver 102/103 | Terreno auditado, sem campanha completa |
| Offline 12/12 | [PR #45](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/45): 82 mapas 600–681, 32 eventos (16 transferências + 16 ações), 44 conexões, 21 equipes PBS e 6 tabelas de encontros | Pacote privado anterior; não é total da instalação atual |
| Prévia compartilhada | [johto_main_preview.py](../scripts/regions/johto_main_preview.py): 100 IDs 600–699, EXPERIMENTAL_PRIVATE_UNVERIFIED, fully_playable=false, android_verified=false | Existe instalação experimental transacional; não provar que a máquina do usuário ou Android atual possui esses bytes |
| Progresso | [johto-progress.json](../data/regions/johto-progress.json): 12/12 offline, 0/13 jogáveis, 0/13 testadas; 16/16 cobertura de código | Contadores antigos; atualizar só com evidência |
| Portal | [johto-preview.json](../site/public/data/johto-preview.json): mapas/treinadores/encontros/áudio certificados = 0 | Catálogo simbólico desatualizado versus prévia; reconciliar sem promover ficticiamente |
| Runtime integrado | Prévia concatena JohtoPilot.rb, JohtoRouteTrainers.rb, JohtoViolet.rb, JohtoMainCompile.rb; há classes de fases seguintes | Conferir código real, eventos RXDATA e PBS carregados; falta vínculo físico das etapas posteriores |
| MapIDs globais | [PR #111](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/111): snapshot de 100 IDs Johto 600–699, Hoenn 700–898, reservas 700–999 | Snapshot histórico, não prova de IDs livres hoje |
| Áudio | [johto-music.json](../data/johto-music.json): 42 BGM + 11 ME planejados; 0 certificados; [johto_opening.py](../scripts/regions/johto_opening.py) associa e copia OGG locais quando disponíveis | Inventariar o que de fato toca e direitos; não declarar zero áudio instalado em todos os clientes |

Origens pinadas no código/documentos:

- Remastered Kanto Johto Map Packv1.zip — SHA-256 5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715.
- Bundle privado OFFLINE12 — SHA-256 74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49.
- johto-pilot-inputs.zip — SHA-256 f34b13b56fd42f089c6df525c54e11ad0f5b64acef9027911867efc4be89fee4; exportação histórica de insumos, sem executável.

Revalidar os hashes do arquivo local, não do nome. Não baixar ZIP privado por URL inventada. O Map Pack v3 atual não equivale ao v1 auditado; não substituir a fonte pinada silenciosamente. IDs atuais: 600–673 terreno remapeado; 674 quarto, 675 casa, 676 Elm; 677 ginásio, 678–680 Sprout Tower, 681 Centro; 682–699 adicionais. Spawn da prévia: Map674 (6,7), chegada Map600 (10,26), agente Map600 (10,25), conforme contrato existente; confirmar passabilidade e assinatura nativa antes de preservar/aplicar. Auditar candidatos extras em johto_visual.NEW_MAPS/REGIONAL_INTERIORS versus PREVIEW_IDS; não presumir que cada candidato seja instalado ou que 700+ pertença a Johto.

## 2. Fontes de download, referência e testes

| Recurso | Link | Como usar |
|---|---|---|
| Código e atualizações Blue | [GitHub](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal) · [ZIP main](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/archive/refs/heads/main.zip) | Git clone/fetch para desenvolvimento; fixar SHA e preservar cópia existente |
| Terreno RMXP Johto | [Map Pack AenaonDogsky](https://eeveeexpo.com/resources/828/) · [Histórico de versões](https://eeveeexpo.com/resources/828/history) · [Discussão](https://eeveeexpo.com/threads/4434/) | Botão de download do autor; obter v1 exato via pacote privado autorizado já utilizado, ou auditar nova versão separadamente; v3 não é fallback silencioso |
| Interiores e tiles candidatos | [Recursos Akizakura](https://eeveeexpo.com/resources/15/) · [Catálogo de recursos Eevee Expo](https://eeveeexpo.com/resources/) | Inspecionar compatibilidade RMXP e termos individuais, criar interiores próprios se necessário; não copiar todos os assets |
| Fangame Johto | [Pokémon Grueling Gold](https://eeveeexpo.com/threads/7771/) | Referência visual/funcional e página do autor; engine diferente, não doador automático de scripts, ROM, dados ou binários |
| Base do Blue | [Pokémon Decades](https://github.com/HazyCrazy/Pokemon-Decades) · [Instalação Blue](INSTALACAO.md) | Usar aquisição pinada do projeto, não atualizar Decades/engine durante o lote |
| Engine | [Pokémon Essentials](https://github.com/Maruno17/pokemon-essentials) · [Wiki Essentials](https://essentialsdocs.fandom.com/wiki/Essentials_Docs_Wiki) | Consultar APIs v21.1 do runtime real; não substituir engine nem importar combate de HGSS |
| Editor | [RPG Maker XP](https://www.rpgmakerweb.com/products/rpg-maker-xp) · [Johto Map Studio](JOHTO_MAP_STUDIO.md) | Autoria/revisão manual quando necessária, licença válida, exportação RXDATA em cópia isolada |
| Narrativa e geografia | [Pokémon Mythology HGSS](https://www.pokemythology.net/detonados/detonado-heartgold-soulsilver/) · [Bulbapedia Johto](https://bulbapedia.bulbagarden.net/wiki/Johto) · [Serebii Pokéarth Johto](https://www.serebii.net/pokearth/johto/) · [detonado interno](JOHTO_DETONADO_HEARTGOLD_SOULSILVER_REFERENCIA_ORGANIZADA.md) | Inventário de locais, pré-condições, itens, equipes e encontros; escrever diálogos PT-BR próprios; não reproduzir artigos/textos oficiais integralmente |
| Áudio | [Catálogo HGSS MusicBrainz](https://musicbrainz.org/release/216a467d-ccdb-4568-93db-b4ff13af8263) · [seleção interna](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) | Referência de títulos, não download licenciado da OST; usar música própria/autorizada e hash individual |
| Windows | [Releases Blue](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases) · [Canal Blue-Story Windows](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/blue-story-windows) | Baixar Blue-Story.exe da revisão pareada validada, não assumir latest |
| Android | [JoiPlay e RPG Maker Plugin](https://joiplay.net/) · [Termux](https://termux.dev/en/) · [Releases Blue](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases) | Versões reais compatíveis registradas; canal multiregion e delta incremental |
| CI e ferramentas | [Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions) · [GitHub CLI](https://cli.github.com/) | Logs, jobs, artifacts e publicação rastreáveis por SHA |

Os links são pontos de aquisição/referência, não concessão de direitos. A página pública do Map Pack, do Grueling Gold e do JoiPlay foi localizada nesta análise; nenhum arquivo externo foi baixado ou executado. Outros links são referências do projeto/upstream; conferir acesso, versão, licenças e bytes ao executar. Sem autorização de redistribuição, manter fonte privada/local (fora do Git, logs e artifacts públicos), usar recursos próprios ou autorizados e bloquear release que depender de material não redistribuível. Creditar AenaonDusky/AenaonDogsky, Earthescape/Orbitender, demais autores conforme o pacote; crédito não substitui autorização.

## 3. Arquivos existentes a reaproveitar

| Grupo | Caminhos |
|---|---|
| Documentação | [JOHTO_ETAPAS](JOHTO_ETAPAS.md), [guia integral](JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md), [plano](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md), [E2E](JOHTO_TESTES_E2E.md), [fase 16](JOHTO_FASE_16_INTEGRACAO_E_ACEITE.md) |
| Fonte/staging | scripts/regions/{prepare_johto_source,audit_johto,plan_johto,stage_johto,verify_johto,compile_johto_connections,package_johto_offline12}.py |
| Prévia real e correções | scripts/regions/{johto_main_preview,auto_integrate_johto,johto_qa,johto_visual,johto_opening,johto_hgss_assets,johto_map_patches,johto_map_editor}.py |
| Eventos atuais | scripts/regions/{JohtoPilot,JohtoRouteTrainers,JohtoViolet,JohtoMainCompile}.rb; build_johto_events.py, build_johto_warps_v1.py, build_johto_story_v1.py |
| Fases posteriores | scripts/regions/{JohtoAzalea,JohtoGoldenrod,JohtoEcruteak,JohtoOlivineCianwood,JohtoJasmine,JohtoMahogany,JohtoBlackthorn,JohtoLeague,JohtoLegendaries}.rb; data/regions/johto-phase05.json ... johto-phase16.json conforme inventário real |
| Runtime compartilhado | scripts/battle_polish/{Regions,RegionalPolicy,RegionalCards,RegionStart,RegionTravel,TitleKanto}.rb |
| Instalador definitivo | [install_johto.py](../scripts/regions/install_johto.py) e [schema 13 gates](../data/regions/johto-release-proof.schema.json); --apply final ainda bloqueado |
| Windows | [Bootstrap.cs](../scripts/windows/Bootstrap.cs), [blue-story-windows.yml](../.github/workflows/blue-story-windows.yml), [battle-hub-release.yml](../.github/workflows/battle-hub-release.yml) |
| Android | [package.py](../scripts/android/package.py), [publish_updates.py](../scripts/android/publish_updates.py), [update_client.py](../scripts/android/update_client.py), [android-multiregion.yml](../.github/workflows/android-multiregion.yml), [android-updater-regression.yml](../.github/workflows/android-updater-regression.yml) |
| Padrões de referência | [PR #340](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/340) migração Kanto; [PR #334](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/334) conexão física/quest Sinnoh; [Kanto native](../.github/workflows/kanto-pilot-check.yml) |

Documentos antigos que citam viagem bloqueada pela Liga, fonte sem SHA ou ausência absoluta de instalação foram superados por código/contratos posteriores. A [regra atual de viagem](VIAGEM_REGIONAL_LIVRE_NPC.md) prevalece; confirme política vigente diretamente na main, sem reintroduzir gates de Liga para viagem. Não assumir que todos os caminhos históricos continuam iguais: git ls-files e --help antes de executar. Não criar versão duplicada de uma ferramenta existente.

## 4. Método de execução eficiente (cada lote)

1. Inventariar main e versão publicada. Se PR corrente de Johto existir, retomar sua HEAD e falhas; não abrir PR concorrente para a mesma tarefa.
2. Extrair somente o subconjunto de mapas/tilesets/PBS necessário. Cache por SHA em .blue-work/johto/, sem subir fonte privada. Gerar plano read-only do delta, mapa de dependências, propriedade regional e baseline.
3. Implementar conteúdo físico + compilação PBS + runtime + regressão na mesma unidade vertical. Reutilizar parser Ruby Marshal inerte e builders do Blue; não copiar scripts de origem.
4. Rodar testes focados primeiro; depois regressão integral e prova nativa no runner autorizado. Se falhar, analisar logs completos e corrigir a causa. Marcador só depois de asserts; não imprimir OK incondicional.
5. Conferir PR checks atuais contra main, fazer merge só com todos os gates técnicos obrigatórios verdes. Após merge fixar revisão funcional S, publicar Windows e Android; validar assets/patches e registrar QA física separadamente.
6. Só então iniciar próximo lote perceptível. Se falha de release, corrigir e gerar par sincronizado. Não cancelar publicação por feature nova.

Comandos iniciais (na raiz, ajustar ambiente/paths reais; não executar git reset/clean destrutivo):

    git fetch origin
    git status --short
    git rev-parse origin/main
    git ls-files 'docs/JOHTO*' 'data/regions/johto*' 'scripts/regions/*johto*' 'scripts/regions/Johto*' '.github/workflows/*'
    gh pr list --state open
    gh run list --branch main --limit 30
    gh release list --limit 30
    python scripts/regions/install_johto.py --dry-run
    python -m unittest discover -s tests -p "test_johto*.py" -v
    python scripts/regions/johto_main_preview.py --help
    python scripts/regions/johto_qa.py --help

Para SHA de arquivos, usar Get-FileHash -Algorithm SHA256 no PowerShell ou sha256sum em Linux/Termux. Comandos dependem de clone, GH autenticado e Python/engine autorizados. Não declarar executados por estarem neste documento.

## 5. Contratos técnicos transversais

### 5.1 MapIDs e instalação

- Congelar identidade de 600–699: nunca reutilizar um ID para outro mapa, nem deslocar o player por renumeração. Validar MapInfos, todos Map*.rxdata, PBS, System, regiões, reservas e eventos de origem; mapear MapID antigo para mesmo ID em migrações.
- Não usar 700–999 (Hoenn). Auditar reservas e limites atuais, incluindo Kanto dinâmico, Sinnoh e Unova. Só alocar IDs adicionais comprovadamente livres, globalmente aprovados e suportados pelo motor; não presumir >=1000 seguro. Se expansão exigir IDs não contíguos, migrar consumidores de range fixo para registro explícito de propriedade, sem relaxar verificação.
- Pontos que precisam evoluir conjuntamente: PREVIEW_IDS/contagem em johto_main_preview.py, RegionStart.johto_preview_proof, guard de sinnoh_map_id_guard, instaladores e auto_integrate_johto, metadata de mapas, portal e atualizador. Preservar suporte à prévia legada enquanto migração for testada.
- Importação de tilesets/autotiles com append e remap de referências; preservar prefixo nativo, flags de passagem/prioridade/terrain, gráficos, áudio e dependências. Não apagar mapa divergente sem identidade e recibo de propriedade comprovados.
- Construir grafo de componentes caminháveis considerando direção, ledges, eventos e HMs; separar conexão PBS (borda) de warp (porta/escada) e viagem QA. Testar ida/volta real; entrada e destino livres, sem loop, tile preto indevido ou porta falsa.
- Migração transacional N→N/N+k: preflight SHA, validação de mudança concorrente, staging, backup apenas arquivos modificados, replace atômico, rollback de novos/alterados, verificação SHA final. Não tocar saves reais. Preservar mapas externos e dados de outras regiões byte a byte sempre que aplicável; alterações compartilhadas de MapInfos/Tilesets verificadas semanticamente.

### 5.2 História e runtime

- Cada evento tem ID/chave estável, MapID, coordenada, sprite, trigger/páginas, precondições, pós-condições, itens consumidos/concedidos, resultado cancelado/derrota/fuga/retry, persistência e fonte. Reutilizar self-switches corretamente; não marcar vencedor antes do retorno real da batalha.
- Usar API nativa de GameData, pbTrainerBattle, inventário, cura, captura e Hall of Fame compatíveis com v21.1 conforme assinatura encontrada no Blue. Não criar engine paralela. IDs de treinadores BLUE_JOHTO_*; não colidir com Gary, rival de outra região ou Full Power Decades.
- Preservar escala global Normal 70% / Master 90% do maior Pokémon, selvagens conforme regra vigente (histórico 45%), level cap/esmeraldas, evolução dinâmica nível +5, pedra >=30, troca >=40, felicidade >=45; chefes autorais e líderes/Elite/Campeões conforme exceções atuais. XP party ligada, Dynamax off. Não hardcodar níveis HGSS em runtime.
- Cada badge local única vale uma esmeralda global; HMs exigem item regional + insígnia local + Pokémon elegível conforme política vigente. Johto: Rock Smash/ZEPHYR, Cut/HIVE, Strength/PLAIN, Surf/FOG, Fly/STORM, Whirlpool/GLACIER, Waterfall/RISING. Rock Climb pós-jogo exige decisão explícita sem reaproveitar badge Kanto por engano.
- Novo Jogo Johto: quarto Map674 após validação, Ethan/Lyra e nome, uma única escolha inicial. Visita por agente: rua de New Bark, sem repetir seletor/autorun indevido. Viagem livre entre regiões instaladas por NPC da cidade inicial, sem gate de Liga; equipe depositada/Boxes de acordo com política vigente, checar espaço, HMs/itens-chave isolados também no PC de itens, preservar dinheiro/itens comuns/Pokédex/histórico. Conferir divergência entre regra desejada de depósito de toda a equipe e código que reserva especiais; se não corresponder, corrigir com testes regionais e não alterar outras regras silenciosamente.
- Blackout no último Centro Pokémon local validado, fallback cidade inicial Johto. Sem fallback para outra região. Derrota/retry, save/reload, viagem e rollback são testes mandatórios de cada arco.
- Todas as falas novas PT-BR, placas legíveis, sprites e tamanhos consistentes. BGM/ME de Johto com fallback seguro; transições não interferem na música de Kanto/Decades.

### 5.3 Registro único proposto (reutilizar se já existir)

Criar/extender data/regions/johto-map-registry.json, johto-content-ledger.json e johto-roadmap-progress.json (nomes propostos; não duplicar schemas equivalentes). Cada mapa: key, source SHA/ID, target ID estável, dimensões, tileset, conexões, cobertura de NPC/evento/item/treinador/encontro/música, estado e evidências. Cada entrada de conteúdo referencia mapa físico, fonte/versão, autorização, ID persistente e casos de teste. Portal e progresso gerados dos recibos, não preenchidos à mão como 100%.

Estados distintos: PENDING, IN_PROGRESS, BLOCKED_SOURCE, BLOCKED_RIGHTS, BLOCKED_ENV, CI_PASS, MERGED, BLOCKED_RELEASE, PUBLISHED_BOTH, QA_PENDING, QA_FAIL, ACCEPTED. Não contar área simbólica como mapa instalado. Distinguir fonte, instalado, alcançável, conteúdo completo, prova nativa, QA física.

## 6. Roadmap J00–J23 (ordem de execução)

Todos os marcadores abaixo são **propostos**, não existentes nem emitidos nesta documentação. Cada fase exige adicionalmente regressão global, save/reload e recibo de publicação se houver mudança perceptível. Use os testes específicos existentes e amplie-os; não gerar um workflow por NPC.

### J00 — Inventário real e reconciliação 82 → 100
- Ler Data/blue-johto-main-preview.json, blue-johto-preview-ready.txt, eventual manifesto final, MapInfos/Tilesets, 100 mapas, PBS e Boot.rb em cópia autorizada do build atual. Comparar com fonte pinada, OFFLINE12, prévia atual, publicação Windows/Android e recibos históricos; incluir maps 682–699 e candidatos não instalados.
- Produzir inventário por mapa de dimensões, eventos/páginas, conexões, warp, scripts, itens, encounter, gráfico/áudio, component graph, SHA. Conferir divergências de hashes por alterações legítimas da engine e migração do quarto, sem liberar arquivos desconhecidos.
- Listar portas sem destino, mapas órfãos, scripts não carregados, PBS ausentes, fases incompletas, direitos e baselines. Não subir binário privado. Atualizar status de portal somente quando provado.
- Gate: 100/100 IDs da prévia reconciliados ou lista exata dos ausentes; nenhum ID estrangeiro alterado; fonte/instalação/QA separados.
- Marcador: JOHTO_J00_BASELINE_100_MAP_AUDIT_OK.

### J01 — Espaço adicional de mapas e propriedade global
- Reconciliar reservas atuais de todas as regiões, inclusive mapas futuros, origens remapeadas, usos de IDs em scripts/PBS/save/warps e limites reais RMXP/JoiPlay. Nunca reservar por intervalo vazio inferido de snapshot antigo.
- Fixar registro explícito dos 100 existentes; escolher IDs adicionais apenas com prova livre; adaptar validadores e manifesto versionado, mantendo leitura legada. Testar conflito com Hoenn e Sinnoh, número inválido, duplicata, tentativa de sobrescrever Decades, regressão dos 100 IDs.
- Gate: alocação não contígua se necessária, 100→100 migração-base sem alteração de identidade; publicação se mudar runtime.
- Marcador: JOHTO_J01_MAPID_OWNERSHIP_AND_MIGRATION_OK.

### J02 — Fontes e catálogo físico de interiores/dungeons
- Cruzar inventário de terreno v1 e detonado completo; incluir dez cidades, rotas 29–48, 26–28, todos os andares, portões, casas, lojas, ginásios, torres, Safari Zone, Ruins of Alph, Liga e pós-jogo. Separar beta/custom (Whiteport, minas etc.) do escopo HGSS; não incluir automaticamente como caminho canônico.
- Localizar recursos autorizados de interiores/sprites; usar Johto Map Studio/RMXP ou autoria própria para lacunas. Reaproveitar salas 674–681 e correções visuais, preservando identidade; diferenciar casa provisória de layout final. Conferir todos os tiles e sprites realmente referenciados.
- Produzir catálogo fechado de destinos obrigatórios/opcionais com IDs de destino aprovados; não inventar coordenadas, map count final, NPCs ou direitos.
- Gate: todo destino obrigatório possui fonte/autoria, plano, acesso e dependências ou bloqueio explícito; validar um novo interior de ponta a ponta como piloto.
- Marcador: JOHTO_J02_SOURCE_AND_INTERIOR_REGISTRY_OK.

### J03 — Pipeline compartilhado e migração transacional
- Evoluir johto_main_preview/auto_integrate_johto e install_johto sem duplicar instalador; separar EARLY_ACCESS/VERIFIED_PLAYABLE. Conservar prova antiga, dry-run, migração 100→100/100+k, preflight e rollback. Adaptar Boot.rb/JohtoMainCompile sem recriar loop prepend/alias Compiler.main já corrigido.
- Compilar PBS e eventos em Windows isolado, validar GameData, sprites e início/continuação. Preparar equivalente Android via pipeline multiregion; não depender de Ruby JSON indisponível em JoiPlay.
- Garantir menu Testar Johto somente QA e Novo Jogo Johto no Game.exe compartilhado para build instalada; não abrir executável/pasta de campanha separada como solução final.
- Gate: instalação limpa, atualização de prévia antiga, falha injetada e rollback, mesma revisão, prova de compilação real; final --apply protegido por 13 gates.
- Marcadores: JOHTO_J03_NATIVE_COMPILE_OK, JOHTO_J03_REAL_100_TO_100_MIGRATION_OK.

### J04 — New Bark: novo jogo e inicial
- Reusar Map600, 674, 675, 676; verificar quarto fiel/adaptado, escadas, portas, casa da mãe, Elm, assistente, Silver na janela, casas vizinhas e agente regional. Introdução Ethan/Lyra/nome uma vez; câmera/escala/sprite corretos.
- Três Poké Bolas físicas Chikorita/Cyndaquil/Totodile; concessão atômica de uma, remover/ocultar bolas após escolha, obter PokéGear e instruções; bloqueio físico de saída/grama antes de inicial. Não repetir início ao viajar para Johto.
- Testar 3 iniciais, escolha cancelada/duplicada, inventário/party, saída e retorno, save em cada cômodo, black out inicial, agente sem regressão.
- Marcador: JOHTO_J04_NEW_BARK_STARTERS_SAVE_RELOAD_OK.

### J05 — Cherrygrove, Sr. Pokémon, Silver, Rotas 29–31
- Validar conexões Map625↔601↔626↔627↔602 e as duas ligações derivadas offline; gates/portões não podem esconder borda bloqueada. Completar guia, Running Shoes conforme regra do Blue, Center/Mart/casas, Mr. Pokémon, Oak/Pokédex, Mystery Egg, telefonema Elm, tutorial captura e itens.
- Silver em ponto coerente da história após Mystery Egg; 3 versões PBS de acordo com inicial, batalha nativa, derrota/retry, não alterar Gary. Auditar seis tabelas existentes e cinco treinadores/dez variantes; substituir design apenas se fonte/regra aprovada, adicionar métodos/horários/itens faltantes e passabilidade.
- Gate: percurso ida/volta físico, todos os estabelecimentos acessíveis, captura real, Silver três iniciais, save/reload, sem Pokémon extra gratuito ou duplicação.
- Marcador: JOHTO_J05_CHERRYGROVE_SILVER_NATIVE_CORRIDOR_OK.

### J06 — Violet, Sprout Tower, Falkner
- Completar Map602/677–681, 3 andares, ancião Li, sages, puzzles/escadas, centro cura de verdade, Mart e casas. Entregar Mystery Egg/Togepi conforme história adotada; Rock Smash no evento local; ligar Routes 31/32/36 e Ruins of Alph sem atravessar trava indevida.
- Falkner e treinadores reais em PBS; sprites e BGM corretos; gate Sprout Tower, Zephyr + uma esmeralda + TM apropriada; bloquear recompensa após derrota e duplicação.
- Gate: jornada contínua New Bark→Falkner em Game.exe, Normal/Master, derrota/retorno, Rock Smash local, save/reload, acesso às saídas.
- Marcador: JOHTO_J06_FALKNER_ZEPHYR_NATIVE_OK.

### J07 — Route 32, Union Cave, Route 33, Azalea
- Instalar/ligar todos os andares relevantes, encontros grama/caverna/pesca/Surf condicionado, pescadores, itens e acessos Ruins/Union Cave. Completar Azalea Center/Mart, Kurt, Apricorns, Slowpoke Well (andares), bloqueio Rocket, grunts e Proton.
- Integrar JohtoAzalea.rb às páginas reais e PBS; Bugsy com puzzle de plataformas compatível, Hive única e TM; Silver recorrente distinto do evento inicial. Cut só após requisitos locais, desbloqueio Ilex.
- Gate: sem entrar gym antes da missão, derrota/retry Rocket e Bugsy, Slowpoke resgatados persistentes, retorno por Union Cave, itens e NPCs únicos.
- Marcador: JOHTO_J07_SLOWPOKE_BUGSY_HIVE_OK.

### J08 — Ilex Forest, Farfetch'd, Cut, Headbutt, Route 34
- Ligar Azalea→Ilex→R34; puzzle físico dos dois Farfetch'd, orientação/galhos, trabalhador e HM Cut entregue uma vez. Verificar remoção de árvore, bloqueio sem HM/badge/Pokémon e reload. Kimono Girl, tutor Headbutt, árvores com encontros.
- Creche: reaproveitar serviço nativo, depósito/retirada, experiência, ovos, compatibilidade de espécies, custo e espaço, save/reload, sem perder Pokémon; NPCs da Route 34 e encontros diurno/noturno.
- Gate: puzzle ambos, Cut físico, retorno, Day Care depósito/ovo/retirada persistentes; sem softlock com party cheia.
- Marcador: JOHTO_J08_ILEX_CUT_DAYCARE_OK.

### J09 — Goldenrod e Whitney
- Construir/validar interiores cidade: Center/Mart, Department Store andares, Bike Shop, Radio Tower, Underground, floricultura, estação, Game Corner e serviços. Mapear portas reais e transições, NPCs, trocas, itens e preços. PokéGear rádio/quiz, bicicleta única.
- Whitney e puzzle, derrota, comportamento após vitória, Plain + esmeralda uma vez, SquirtBottle/Floricultura com requisitos; Strength local disponível conforme história. Separar estado normal da futura ocupação Rocket.
- Gate: todas as portas do lote funcionam, rádio/quiz persistentes, badge/TM/item sem repetição, saída para R35, save/reload.
- Marcador: JOHTO_J09_GOLDENROD_WHITNEY_PLAIN_OK.

### J10 — Routes 35–37, National Park, Sudowoodo
- Construir portões/conexões, National Park, treinador/encontros/itens e entrada do Pokéathlon; preparar acesso à competição sem alegar minigame pronto. Sudowoodo visível e obstáculo real, SquirtBottle local, batalha/captura/derrota/fuga conforme regra escolhida.
- Testar bloqueio antes de Plain/item, retirada persistente, corredor aberto de volta, prevenção de duplicação e ligação Ecruteak; validar percurso alternativo Violet↔R36.
- Gate: travessia física bidirecional e item/estado comprovados.
- Marcador: JOHTO_J10_SUDOWOODO_NATIONAL_PARK_OK.

### J11 — Ecruteak, Morty, Burned Tower
- Ligar R37/R38/R42 e interiores, Dance Theater, Rocket e Surf; Burned Tower andares, Silver, Eusine, Raikou/Entei/Suicune, flags roaming sem duplicação. Bell Tower geografia e acesso condicionado.
- Integrar JohtoEcruteak.rb, puzzle de piso do gym, treinadores, Morty, Fog e TM; Surf por travessia real, embarque/desembarque, água e terreno. Não aceitar teleporte no lugar de Surf.
- Gate: evento lendário persiste, Fog única, derrotas e retorno, Surf bloqueado sem três requisitos e funcionando com eles.
- Marcador: JOHTO_J11_MORTY_FOG_SURF_ROAMERS_OK.

### J12 — Olivine, Lighthouse, Cianwood, Chuck
- Routes 38/39, Moomoo Farm, Olivine porto/serviços e Lighthouse seis andares com portas/escadas; Jasmine solicita medicina para Ampharos. Routes 40/41 com Surf real, nadadores e encontros. Cianwood farmácia, SecretPotion, ginásio Chuck e Fly.
- Integrar JohtoOlivineCianwood.rb, recepção de medicina somente após pedido, Storm + uma esmeralda, Fly limitado a destinos realmente descobertos, volta física e opcional Fly conforme requisitos.
- Gate: pedido→travessia→farmácia→Chuck→retorno, derrota/retry, medicina não consumida prematuramente, save no farol e mar.
- Marcador: JOHTO_J12_LIGHTHOUSE_CHUCK_STORM_MEDICINE_OK.

### J13 — Ampharos, Jasmine e Whirl Islands
- Consumo atômico da SecretPotion somente na cena válida; cura Ampharos, retorno de Jasmine ao gym, batalha nativa, Mineral + esmeralda/TM únicos. Reconciliar estado após save antes/depois da cura; não deixar missão incompleta com item perdido.
- Auditar quatro entradas/saídas e andares Whirl Islands, ligações aquáticas e Whirlpool bloqueado até badge adequada. Preparar Lugia para J17, não liberar lendário antes da narrativa.
- Gate: item consumido uma vez, cura e badge persistentes, Whirlpool e acesso condicional corretos.
- Marcador: JOHTO_J13_JASMINE_MINERAL_AMPHAROS_OK.

### J14 — Mahogany, Lake of Rage, Rocket HQ, Pryce
- Ligar R42/Mt. Mortar/R43 e Lake of Rage com terreno Surf. Gyarados vermelho único, captura/fuga/derrota com estados válidos, Red Scale e Lance. Esconderijo Rocket completo, senhas, portões, armadilhas, NPCs, Petrel/Ariana conforme adaptação, três Electrode com batalhas e persistência.
- Integrar JohtoMahogany.rb, liberar gym após missão, Pryce/Glacier + esmeralda/TM, Whirlpool. Rádio/telefonema Elm dispara ocupação Goldenrod uma vez.
- Gate: captura/fuga/retry, três Electrode distintos, derrota e reentrada HQ, badge sem duplicação, Whirlpool nativo, retorno Goldenrod.
- Marcador: JOHTO_J14_LAKE_ROCKET_HQ_PRYCE_GLACIER_OK.

### J15 — Goldenrod Radio Tower e Underground (Rocket)
- Fases de ocupação com NPCs/páginas/sprites distintos; uniforme Rocket e desmascaramento, torre e subterrâneo com portas/interruptores, executivo disfarçado, Director, Basement Key/Card Key e resgate. Petrel, Proton, Ariana, Archer e Silver conforme fonte de referência e composição PBS.
- Missão termina somente após batalha/cena e estado final, entrega de prêmio/itens-chave e rádio restaurado. Bloquear R44/Blackthorn antes do término conforme cronologia.
- Gate: entrada antes/durante/depois, chaves locais, derrota/retry, nenhum autorun infinito, retorno de NPCs e save/reload.
- Marcador: JOHTO_J15_RADIO_TOWER_ROCKET_LIBERATION_OK.

### J16 — Ice Path, Blackthorn, Clair
- R44→Ice Path todos os andares, gelo escorregadio, Strength com rochas e buracos, Waterfall adquirido no mapa de referência; teste de retorno e reset apropriado do puzzle. R45/46 e Dark Cave conectadas.
- Blackthorn serviços e gym com puzzle, Clair, Dragon's Den e Dragon Master. Rising só após prova final, esmeralda/TM uma vez; Waterfall em terreno real. Integrar JohtoBlackthorn.rb e impedir bypass por teleporte comum.
- Gate: derrotas/retry, oito badges locais, passagem de gelo/rochas, Waterfall sem/ com requisitos, save antes/depois da prova.
- Marcador: JOHTO_J16_CLAIR_RISING_ICE_PATH_WATERFALL_OK.

### J17 — Kimono Girls e guardião da versão
- Resolver escolha HG/SS/Crystal conforme design existente, sem missões contraditórias, registrar regra para saves antigos. Dança e batalhas das Kimono Girls, itens/Sinos, Rainbow/Silver Wing, caminho Bell Tower/Whirl Islands e Ho-Oh/Lugia.
- Integrar JohtoLegendaries.rb: captura, derrota, fuga, respawn permitido, forma/shiny/registro, roaming Raikou/Entei e Suicune/Eusine conforme cronologia escolhida. Não dar item ou lendário fictício para avançar. Especiais e oito badges locais continuam vigentes.
- Gate: duas variantes separadas de save ou variante combinada formalmente definida, caminho físico, batalha real, persistência e sem duplicação.
- Marcador: JOHTO_J17_KIMONO_LEGENDARY_VERSION_OK.

### J18 — Tohjo Falls, Victory Road, Liga e Hall of Fame
- New Bark→R27→Tohjo Falls→R26→Victory Road, portões por oito badges locais, Surf/Waterfall, Silver, treinadores, salas Elite e saída. Will→Koga→Bruno→Karen→Lance em ordem, equipes PBS nativas, sem confundir Kanto/Blue.
- Integrar JohtoLeague.rb: derrota reinicia tentativa sem conquista, Hall of Fame nativo gravado uma vez; progresso regional de campeão e pós-jogo, sem gate de Liga para viagem normal.
- Gate: jornada completa com save/reload, derrotas intermediárias e vitória, Hall of Fame real após callback/gravação, Kanto/Decades inalterados.
- Marcador: JOHTO_J18_EIGHT_BADGES_LEAGUE_HALL_OF_FAME_OK.

### J19 — Cobertura física opcional e rotas/dungeons
- Fechar todos os destinos restantes do catálogo J02: Ruins of Alph/Unown (puzzles, inscrições, salas), Union Cave níveis/condições, Dark Cave duas entradas, Mt. Mortar, Whirl Islands, Bell Tower, R45–48, Cliff Edge Gate/Cliff Cave, Safari Zone, R28/Mt. Silver, áreas extras autorizadas.
- Verificar todas as portas de todas as cidades, Center/Mart/casas, NPCs de serviço, placas, hidden items, HMs e música. Grafo completo de ida/volta, sem mapa órfão exceto área intencional e documentada, sem buraco preto/colisão inconsistente.
- Teleporte QA opcional para cada mapa instalado com ponto seguro e sem alterar flags; não é prova de acesso normal, não substituir NPC regional nem liberar cheat em build normal.
- Gate: 100% do catálogo físico aprovado, contagem derivada do registro e não inventada, cobertura de conectividade e recibos nativos.
- Marcador: JOHTO_J19_ALL_MAPS_DOORS_PHYSICAL_ACCESS_OK.

### J20 — Sistemas exclusivos e pós-jogo completo
- PokéGear mapa/telefone/rádio, rematches, Apricorns/Kurt, Headbutt, Bug-Catching Contest, Pokéathlon, Voltorb Flip, Safari Zone/Baoba, Moomoo Farm, bicicleta, Day Care/ovos, dia/noite/swarm, Pokémon acompanhante se previsto, S.S. Aqua, Battle Frontier (Tower/Factory/Arcade/Castle/Hall conforme escopo).
- Mt. Silver/Red com requisitos explicitados para o Blue, Red e equipes finais, rematches líderes/Elite, Suicune, Embedded Tower (Groudon/Kyogre/Rayquaza), National Dex, presentes de iniciais e eventos especiais compatíveis/autorizados (Celebi, Arceus/Sinjoh) sem distribuição indevida.
- Pós-jogo HGSS em Kanto deve usar região Kanto existente; implementar diferença temporal como estado de Johto ou desafio próprio, sem duplicar mapa/insígnia ou substituir campanha FRLG/Gary. Rock Climb e requisitos Red a homologar; não exigir conquista inexistente.
- Dividir em sublotes verticais J20A... por sistema, cada qual com publicação se perceptível. Para recursos DS incompatíveis, equivalente aprovado e testado ou BLOCKED_FEATURE explícito; não declarar 100% de escopo integral com sistema omitido.
- Gate: atividades acessíveis e reproduzíveis, recompensas/cooldowns persistentes, sem softlocks ou duplicações.
- Marcador agregado após todos os sublotes: JOHTO_J20_POSTGAME_SYSTEMS_AND_RED_OK.

### J21 — Auditoria de conteúdo, áudio, visual e portal
- Derivar lista final por mapa: NPCs e eventos, todos treinadores e versões PBS, itens/lojas, encontros (Land/morning/night/cave/water/rod/headbutt/smash/swarm/Safari/estáticos), pesos/métodos/condições com fonte e regra Blue. Distinguir tabelas autorais de extração canônica. Testar somas válidas por método e espécies/learnsets existentes.
- Integrar 42 BGM + 11 ME planejados ou equivalentes autorizados; mapear cidade/rota/interior/dungeon, batalhas/vitórias/cenas, loop, fade, fallback e reprodução; não copiar OST sem direitos. Auditar sprites, escala do protagonista/ Silver, títulos, placas, animações, bordas, diálogos PT-BR.
- Gerar portal de dados nativos: MapIDs, habitats, treinadores, badges, progresso e links de evidência. Atualizar johto-progress.json/JOHTO_ETAPAS sem apagar histórico.
- Gate: cobertura 100% das entradas aprovadas do ledger, sem referência ausente, nenhuma taxa inventada como canônica, áudio ouvido em QA físico separado.
- Marcador: JOHTO_J21_CONTENT_PBS_ENCOUNTERS_AUDIO_COVERAGE_OK.

### J22 — QA integral, viagens e migração de saves
- Executar matriz da seção 9 em Windows e Android; novos jogos, saves antigos da prévia de 100 mapas, saves da revisão imediatamente anterior e de outras regiões, updates sucessivos. Testar jogador dentro de interior/caverna, durante missão, após badge, com PC cheio, item-chave em Bolsa/PC e falha de viagem; preservar slots, posição e inventário. Testar retorno de Johto↔Decades/Kanto/Hoenn/Sinnoh e Unova só se instalada.
- Preservar IDs e save namespace do principal; criar fixtures por geração de save e checar byte/semântica antes/depois. Validar blackout regional e fallback, versão in-game, rollback, atualização interrompida, ausência de perda de Pokémon.
- Gate: provas nativas e QA físico Windows/JoiPlay (sem assumir CI Windows prova Android), 13 checks reais, zero falha crítica pendente, direitos revisados. Se QA físico for adiado, registrar pendência e manter certificação final bloqueada.
- Marcadores: JOHTO_J22_NATIVE_SAVE_MIGRATION_TRAVEL_OK, JOHTO_J22_WINDOWS_GAMEPLAY_OK, JOHTO_J22_JOIPLAY_GAMEPLAY_OK (somente emitidos pelo teste aplicável).

### J23 — Release final Windows/Android e aceite
- Aplicar instalação definitiva transacional após gates; promover status VERIFIED_PLAYABLE e marcadores finais somente com provas verificáveis; validar schema e hashes. Corrigir link do README, portal, documentação de instalação e histórico.
- Publicar par na mesma revisão S, baixar assets, verificar SHA-256, manifests, delta compatível, instalação limpa e upgrade incremental. Confirmar pós-merge e links versionados; manter releases antigas rastreáveis.
- Gate: 13/13 fases de gameplay do tracker antigo somente se evidências cobrem todas; 24/24 lotes J00–J23 aceitos (sub-lotes J20 inclusos), mapa/evento/QA 100% do escopo definido, par de releases válido e 13 checks do schema. Nenhuma reivindicação de fidelidade integral HGSS se recurso omitido.
- Marcador: JOHTO_J23_FINAL_SHARED_WINDOWS_ANDROID_RELEASE_OK.

## 7. Windows — integração automática no Blue-Story.exe

1. Usar Bootstrap.cs e auto_integrate_johto.py existentes. O launcher já prepara pacote privado OFFLINE12 pinado, pode encontrar ZIP ao lado do EXE e chama integração automática. Reutilizar fluxo; não exigir abertura manual de BAT para cada atualização. Não embutir arquivo de terceiros em release pública sem autorização.
2. Transformar prévia em instalador incremental versionado: detectar manifestos antigos, validar origem, plano e propriedade, atualizar apenas arquivos necessários, compilar PBS/runtime no mesmo Game.exe e preservar saves. Prévia existente com SHA divergente legítimo exige migração específica, não apagar pasta ou aceitar tudo.
3. Executar pipeline autorizado de johto_qa.py e probes de compilação, sem hook recursivo de Compiler.main. Validar Data, PBS, Plugins, Graphics, Audio e System local; menu Novo Jogo/Continuar, agente e título/versão com revisão/data UTC e equivalente local. Tratar erro claro com caminho de log.
4. Usar os workflows existentes battle-hub-release.yml (release versionada battle-hub-N-SHA) e blue-story-windows.yml (canal independente quando aplicável). Conferir triggers e SHA. O EXE é launcher; build dele ou runtime-test do Hub não equivale a instalar/andar em Johto.
5. Baixar asset Blue-Story.exe da tag versionada aprovada, conferir estado uploaded, tamanho e SHA-256 calculado. Caso canal estável também seja divulgado, verificar mesma revisão funcional; não indicar latest de outro canal.

Diagnóstico local autorizado (cópia QA, não pasta do usuário):

    python scripts/regions/johto_main_preview.py --help
    python scripts/regions/johto_main_preview.py --game CAMINHO_COPIA_QA --bundle CAMINHO_ZIP_OFFLINE12
    python scripts/regions/johto_main_preview.py --game CAMINHO_COPIA_QA --bundle CAMINHO_ZIP_OFFLINE12 --apply
    python scripts/regions/johto_main_preview.py --game CAMINHO_COPIA_QA --bundle CAMINHO_ZIP_OFFLINE12 --verify-installed

Substituir placeholders por caminhos reais e conferir argumentos na HEAD; --apply acima é apenas prévia, não aceite definitivo. Executar somente em cópia descartável e depois validar nativamente. Não confundir com install_johto.py --apply, ainda bloqueado na baseline. Testar execução Windows de Game.exe apenas no runner autorizado.

## 8. Android — JoiPlay, Termux e atualizador incremental

1. Estender android-multiregion.yml e package.py para instalar/compilar o mesmo conteúdo Johto autorizado da revisão S, com GameData/cache necessário para JoiPlay. Confirmar se prévia local Johto está ausente no pacote atual; não alegar presença a partir do nome. Preservar Decades/Kanto/Hoenn/Sinnoh e futura Unova.
2. Manter canal multiregion e contrato atual do cliente: Blue-Android-Decades-Kanto-Hoenn.zip, .zip.sha256, .update.json e patches por baseline/alias conforme workflow. O nome histórico do ZIP não prova conteúdo; só renomear com migração de cliente retrocompatível, sem trocar canal para resolver bug.
3. Estender publish_updates.py/update_client.py: comparar manifestos da instalação anterior e nova, incluir somente arquivos modificados/novos, removals estritamente pertencentes ao jogo, SHA de entrada/saída, versão de base, ZIP seguro, staging e rollback limitado aos arquivos alterados. Não fazer backup da pasta inteira. Nunca empacotar ou remover save, configuração pessoal, screenshots ou dados de outra instalação; rejeitar paths traversal, symlink, colisão de case, arquivo estrangeiro ou tamper.
4. Testar delta a partir da última versão publicada e baselines antigas suportadas; testar cliente antigo, paginação de releases, patch interrompido, falta de espaço, hash incorreto, falha parcial, retry e atualização idempotente. Não cair silenciosamente em download completo; fallback explícito/autorizado se delta não compatível.
5. No aparelho autorizado, baixar JoiPlay/RPG Maker Plugin das páginas oficiais, registrar versão, Android e dispositivo. Fechar JoiPlay durante update, abrir Game.exe da mesma pasta após patch, validar controle virtual, música/efeitos, movimento, batalhas, saves, viagens e versão.
6. Termux: usar pasta real do jogo e arquivo atualizador incluído na distribuição; descobrir nome com ls, ler --help. Exemplo se o pacote contiver update_client.py na raiz:

       cd "CAMINHO_REAL_DO_JOGO"
       python update_client.py --help
       python update_client.py --game-dir . --update

   Se a distribuição usa outro nome/wrapper, usar o nome real do manifesto e instruções. Não inventar caminho /sdcard nem fornecer comando destrutivo; conceder acesso ao armazenamento pelo fluxo normal Termux se necessário. Não usar --full como padrão.

## 9. QA, CI e provas

### 9.1 Testes rápidos e workflows

Reutilizar os testes Ruby/Python e .github/workflows/regression.yml, kanto-pilot-check.yml, android-updater-regression.yml, android-multiregion.yml, blue-story-windows.yml, battle-hub-release.yml e workflows Johto existentes encontrados via git ls-files. Criar johto-native-check.yml **somente se não houver equivalente**, com Linux contratos/remap/testes negativos, Windows runtime autorizado e build/patch Android. Não duplicar toda CI por fase, agrupar por fluxo. Não expor segredos em PR não confiável.

    python -m unittest discover -s tests -p "test_johto*.py" -v
    python -m unittest discover -s tests -p "test_regions.py" -v
    python -m unittest discover -s tests -p "test_android_multiregion.py" -v
    python -m unittest discover -s tests -p "test_multiregion_release_pagination.py" -v
    python -m py_compile scripts/regions/johto_main_preview.py scripts/android/update_client.py scripts/android/publish_updates.py
    ruby -c scripts/regions/JohtoPilot.rb
    ruby -c scripts/regions/JohtoViolet.rb
    ruby -c scripts/battle_polish/RegionStart.rb
    ruby -c scripts/battle_polish/RegionTravel.rb
    gh pr checks NUMERO --watch
    gh run view RUN_ID --log-failed

Verificar dependências e descoberta dos testes (zero casos não é aprovação). Usar suite da HEAD, incluir sintaxe dos novos arquivos, portal/Chromium, regressões Kanto/Decades/Hoenn/Sinnoh, verificação de installer e pacote. Não ignorar falha pré-existente; registrar baseline e corrigir/isolar com aprovação.

### 9.2 Matriz mínima de QA real

| Grupo | Ações positivas e negativas | Evidência |
|---|---|---|
| Boot e introdução | Ethan/Lyra, nome, 3 iniciais, sem Pokémon/duplicação, continue antigo | MapID/posição, espécie/party, estado persistente |
| Mundo físico | Cada cidade/rota/dungeon/porta/escada ida+volta; HMs e puzzles; sem teleporte QA como substituto | Grafo, componentes, coordenadas, colisão, log nativo |
| Combate | Treinador comum, Silver versões, Rocket, 8 líderes, Elite/Lance, Red; Normal/Master; vitória/derrota/retry | GameData IDs, níveis runtime, resultado de batalha, flags/badge |
| Itens e encontros | Itens únicos/hidden, bolsas cheias, quest consume/grant, captura e métodos/hábitat/horário | inventário antes/depois, encontro real e persistência |
| Saves e blackout | Salvar/carregar em cada arco; retorno Centro local, fallback, atualização 100→N e N→N | snapshot sintético, MapID/posição, party/PC/flags e versões |
| Viagem | Cada par instalado a partir de New Bark; sem Liga, Box cheia, falha no warp, HMs de outra região, volta | transação e rollback de estado, nunca perda de Pokémon |
| Áudio/visual | BGM/ME, sprite, escala, texto, bordas, touch/controller | screenshots/logs reais e reprodução observada em Windows e JoiPlay |
| Instalação/patch | fresh, upgrade, hash errado, falta de espaço, queda de rede, rollback, reexecução | manifests e SHA por arquivo, nenhum save alterado |
| Pós-jogo | Hall of Fame, lendários, Red, rematches, sistemas J20 | ledger completo, recompensas e flags persistentes |

Headless Windows prova apenas asserts executados no motor; batalha com resultado forçado, captura simulada ou warp substituído deve ser rotulada como simulação. Não declarar batalha jogada, áudio ouvido, vídeo/screenshot ou QA física sem execução/observação. Teste em emulador identificado não substitui aparelho real se gate exigir dispositivo. Se falta hardware, QA_PENDING.

### 9.3 Treze gates finais do schema existente

source_rights, maps_and_warps, sprites_and_tilesets, story_events, trainers_pbs, battles_and_encounters, native_save_reload, hms_and_badges, region_travel_and_box, audio_rights_and_playback, kanto_decades_regression, windows_gameplay, joiplay_gameplay.

Só emitir Data/blue-johto-install.json (schema/region/status VERIFIED_PLAYABLE), Data/blue-johto-start.txt e prova final após evidências dos 13 critérios, com hashes de MapInfos/Tilesets e todos os arquivos exigidos, start/travel_point/npc_point validados. Se evoluir schema para registro não contíguo, manter leitor da prévia e teste de migração; booleans não substituem autorização/QA. Preservar manifesto experimental separado.

## 10. Release pareada e recibo obrigatório por lote

Conferir YAML dos workflows antes de despachar, usar inputs reais. Se só aceitam main, confirmar que main é revisão funcional S. Quando os filtros não acionarem a publicação, despacho explícito autorizado:

    gh workflow view battle-hub-release.yml --yaml
    gh workflow view blue-story-windows.yml --yaml
    gh workflow view android-multiregion.yml --yaml
    gh workflow run battle-hub-release.yml --ref main
    gh workflow run android-multiregion.yml --ref main
    gh run list --workflow battle-hub-release.yml --limit 10
    gh run list --workflow android-multiregion.yml --limit 10
    gh run view RUN_ID --json headSha,status,conclusion,url,jobs
    gh release view TAG --json tagName,targetCommitish,assets,url
    gh release download TAG --pattern 'Blue-Story.exe' --dir .blue-work/johto/release-check

Se necessário, publicar também canal Windows dedicado conforme workflow e verificar equivalência funcional. Confirmar headSha, revisão dentro do manifesto, commit resolvido da tag (targetCommitish pode ser branch), tamanho/estado uploaded, SHA-256 local e digest da release quando disponível. Baixar ZIP/manifest/sha/patches Android por tag correta e testar delta contra baseline verdadeira. Não misturar release latest do Hub com multiregion. Se só um publicado ou SHA divergir, BLOCKED_RELEASE; corrigir e publicar novo par rastreável, sem apagar versões do usuário. Não iniciar outro lote perceptível até resolver.

Formato de recibo (exemplo de campos, não prova):

    lote: Jxx
    estado: PENDING
    pr: null
    head_sha: null
    base_sha: null
    merge_sha: null
    source_hashes: []
    map_ids_before: []
    map_ids_after: []
    map_migration: null
    workflow_runs: []
    native_markers_verified: []
    synthetic_tests: []
    windows_native: null
    windows_physical_qa: null
    android_build: null
    joiplay_physical_qa: null
    windows_release: {tag: null, url: null, asset: null, sha256: null}
    android_release: {tag: null, url: null, asset: null, sha256: null, patches: []}
    blockers: []
    next: null

Salvar recibos sanitizados no registro de progresso, manter issue rastreadora Johto existente (se não houver, criar uma única issue com link a este MD; não reutilizar issue de Kanto/Sinnoh), anexar URLs dos runs/jobs/PRs. Sem saves pessoais, logs com segredos, arquivos proprietários ou SHA fictício.

## 11. Definição de 100% e painel

- **Exploração:** todos os mapas físicos do catálogo J02 instalados, portas/warps e conexões caminháveis com requisitos legítimos; zero ID em conflito.
- **Campanha:** percurso completo New Bark→8 insígnias→Lance→Hall of Fame, todos os eventos essenciais, itens, derrotas e retornos, sem softlock.
- **Conteúdo integral:** todos os NPCs/treinadores/encontros/itens/músicas do ledger, puzzles, opcionais, Red e pós-jogo J19/J20. Exclusões ou equivalentes explicitamente aprovados; não mascarar fidelidade incompleta.
- **Integração:** mesmo Game.exe/save, viagem livre por agente, política regional, migração de saves anteriores, Kanto/Gary/Decades/Hoenn/Sinnoh intactos.
- **QA:** 13 checks finais, QA Windows e JoiPlay real, CI e regressão integral, recibos rastreáveis.
- **Entrega:** par Windows+Android mesma revisão funcional, Blue-Story.exe e pacote/patch incremental verificados, README/portal atualizados.

Barras separadas: mapa físico/acessível, história, conteúdo opcional, QA Windows, QA Android; denominadores provenientes do registro, e antigas 13 fases acompanhadas sem contar preparação offline. Não estimar porcentagem por quantidade de arquivos. Todos J00–J23 iniciam como pendentes de revalidação nessa nova linha; reaproveitar evidências anteriores válidas sem refazer implementação.

## 12. Prompt de início/retomada (copiar no Codex)

> Leia docs/JOHTO_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md, main e PRs em aberto. Inicie/retome J00: audite a prévia compartilhada de 100 MapIDs 600–699 e o OFFLINE12 de 82 mapas, compare manifestos e runtime real Windows/Android, inventarie mapas, portais, eventos, PBS, encontros, áudio e direitos, preserve saves, Gary, MapIDs e balanceamento. Reuse johto_main_preview.py, auto_integrate_johto.py, johto_qa.py e os workflows nativos existentes. Implemente as correções comprovadas e avance J01–J23 na ordem do roadmap, em lotes verticais. Faça merge somente após CI integral da HEAD e base atual; publique Windows e Android na mesma revisão funcional para cada lote perceptível, valide assets, SHA e patches incrementais. Não invente fonte, mapa, teste físico, marcador ou release. Atualize o registro e issue Johto, entregue link versionado de Blue-Story.exe quando publicado e próxima tarefa objetiva. Se faltar fonte/hardware, registre o bloqueio exato e não declare 100%.

**Primeiro objetivo jogável:** New Bark → Cherrygrove → Violet → Falkner com todas as portas, Silver, encontros, insígnia, HMs locais e save/reload, dentro do jogo principal. Depois expansão contínua por arco até Liga, Red e pós-jogo.
