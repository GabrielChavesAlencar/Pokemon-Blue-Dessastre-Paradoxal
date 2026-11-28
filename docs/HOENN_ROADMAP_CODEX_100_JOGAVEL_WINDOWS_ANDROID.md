# Hoenn 100% jogável — roadmap executável pelo Codex (Windows + Android)

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Auditoria de referência:** 27/11/2026 · **Linha de execução:** H00–H24  
**Alvo:** Pokémon Emerald como campanha principal, no Game.exe compartilhado do Blue/Decades; exploração integral, oito insígnias, Liga, pós-jogo, Battle Frontier, serviços, viagens e saves preservados em Windows e Android/JoiPlay. Ruby/Sapphire e ORAS são variantes separadas, não pré-requisitos da campanha Emerald.

> Este documento é um plano de execução, não uma certificação de gameplay. Nenhum mapa, evento, executável, pacote ou save foi alterado para produzi-lo. Os números abaixo são de fontes de código/catalogação e de registros históricos; H00 deve reconfirmar a instalação, as releases e a HEAD atual. Leia AGENTS.md antes de qualquer alteração.

## 0. Contrato de execução para o Codex

- Trabalhe por unidades verticais pequenas. Primeiro descubra o estado real, depois reutilize a implementação existente, corrija lacunas comprovadas, teste e entregue. Não recrie tudo.
- Execute uma fase/subfase por PR (agrupe apenas mudanças inseparáveis). Leia o diff contra main atual; não interfira em PRs paralelos de Kanto/Johto/Sinnoh/Unova. Faça merge somente após aprovação integral dos checks exigidos e relevantes da HEAD e base atuais. Não desative, afrouxe ou substitua testes reais por mocks que aprovam qualquer resultado.
- Cada lote perceptível exige **Windows Blue-Story.exe e Android multiregion publicados na mesma revisão funcional S**, assets e patches conferidos, antes da próxima feature. Documentação pura não exige novo par. Se faltar permissão/ambiente, marque BLOCKED_ENV e registre próximo comando; não simule execução nem deixe uma release pela metade sem informar.
- Use runner Windows autorizado, descartável, cópia local QA, saves descartáveis e perfis distintos. Não acessar PC/saves pessoais, não apagar game/, não sobrescrever System/Scripts/MapInfos/Tilesets completos, não copiar scripts do doador. Preserve todos os MapIDs já distribuídos e as chaves de flags existentes; migrações aditivas e transacionais.
- Não publique ZIP, ROM, OST, Game.exe ou assets de terceiros sem direitos comprovados. Fonte pública não equivale a licença. Se necessário, autoria própria de terreno/sprites/músicas e eventos, sem inventar coordenadas de referência. Não introduza dados externos em scripts de build executáveis.
- Não use teleportes QA, flags forçadas, teleporte entre cidades desconectadas ou encontros de teste como prova de campanha. QA teleporte é ferramenta independente; progressão real usa portas/bordas/HMs/transporte narrativo legítimo.
- Preserve motor Blue/Decades, IA, níveis e BST, Normal 70% / Master 90% do maior Pokémon do jogador quando aplicável, evolução dinâmica vigente (+5 por nível, pedra >=30, troca >=40, felicidade >=45 conforme regra existente), equipes-base dos líderes e chefes autorais, Gary/Kanto, XP party e Dynamax desativado conforme configuração atual. Não reimplemente regras globais dentro de Hoenn.
- 1 insígnia inédita local = 1 esmeralda global; derrota/revanche/reload não duplicam. HMs requerem item/recibo regional, insígnia local e Pokémon compatível de acordo com a API vigente; itens-chave e HMs não cruzam regiões. Viagem usa serviço global atual entre regiões instaladas; não restaurar restrição pós-Liga de documentos históricos. NPC em Littleroot, guardar equipe atual no PC pelo fluxo real, não entregar segundo inicial ao viajar, preservar times/boxes, dinheiro, itens e checkpoint. Blackout retorna ao Centro mais recente da região, fallback cidade inicial. Respeitar restrição vigente para Pokémon especiais e pós-jogo global.
- Gates de QA física não podem ser declarados aprovados sem recibos. Se proprietário adiar QA física explicitamente, registre DELIVERED_WITH_QA_PENDING para permitir próximo lote técnico somente sob essa autorização; nunca promover para 100% por CI.

### 0.1. Estado comprovável da base

| Evidência | O que significa | O que NÃO significa |
|---|---|---|
| [Catálogo](../site/public/data/hoenn-pilot.json) | 199 localizações, 194 registros de equipes, oito líderes, 25 entradas com encontros listados; etapa técnica 10/10 | Não prova completude de encontros do runtime nem 199 mapas funcionando em cada cliente |
| [QA12](../scripts/regions/hoenn_qa_phase12.py) e [TESTAR_HOENN.bat](../TESTAR_HOENN.bat) | Ferramentas 12/12, 11 relatórios técnicos prévios, matriz 15 categorias x 2 plataformas | Não prova 30 casos nativos aprovados; catálogo native_gameplay_verified=false |
| [Instalador](../scripts/regions/install_hoenn.py), [RegionStart](../scripts/battle_polish/RegionStart.rb), [RegionTravel](../scripts/battle_polish/RegionTravel.rb) | Integração principal, marcador de 199, spawn na casa (fonte 8, 25,6) e agente em Littleroot | Não é certificação de campanha integral |
| [Snapshot #107](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/107) | Registro histórico de 199 IDs Hoenn ocupados em 700–999, 100 Johto em 600–699 | Não presume que IDs restantes estão livres hoje |
| [Fonte](../data/regions/hoenn-source.json) | 373 mapas de referência, 100 tilesets, revisão pinada; direitos de redistribuição não confirmados no manifesto | Não significa 373 mapas obrigatórios ou 174 faltantes |
| [Registro regional](../site/public/data/regions.json) | HOENN planned, oito conquistas e HMs | Não promover sem evidências |
| [Stage 10 #59](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/59) | História até Juan, Elite, Wallace e Hall, 199 mapas técnicos | Não comprova puzzles, cenas ou pós-jogo nativo |

Lacunas confirmadas no código: daycare_info (apenas mensagem), contest_stage8 (apenas mensagem), harbor_stage8 (texto provisório; verificar se está alcançável), stage8_future_gate (Safari Zone/Scorched Slab e outros gates antigos; verificar reachability), norman_intro (captura Wally por texto/flag), sootopolis_crisis e rayquaza_stage10 (efeitos e mensagens simplificados), qa10_postgame_status (informação, não pós-jogo completo). QA12 registra candidatos de NPC/treinador/placa, obstáculos e sprites provisórios; contagens detalhadas dependem de relatórios privados. QA11 declara fallback musical, não OST completa. O instalador retorna verify_installed se já instalado e recusa parcial: não possui migração geral de 199 para N. Android package e workflow também têm gate fixo 199. Corrigir esses contratos antes de ampliar mapas.

O catálogo lista nominalmente 29 das 34 rotas 101–134; ausentes 105, 107, 108, 115, 123. Confirmar com MapInfos e aliases reais antes de alocar. Não inferir que ID de origem 108 seja Rota 108: nomes e IDs de fonte diferem.

## 1. Links de aquisição, consulta e distribuição

| Recurso | Link e uso |
|---|---|
| Blue | [GitHub](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal) · [ZIP main](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/archive/refs/heads/main.zip) · [AGENTS](../AGENTS.md) |
| Mapas RMXP | [The Pokémon World Project](https://github.com/SocomSeal/The-PMon-World-Project) · [árvore fixada](https://github.com/SocomSeal/The-PMon-World-Project/tree/c59233bdbaac4fbfeca6aa01c7f05be628da2a92) · [arquivo da revisão](https://github.com/SocomSeal/The-PMon-World-Project/archive/c59233bdbaac4fbfeca6aa01c7f05be628da2a92.zip). O arquivo de árvore inteira não equivale ao ZIP local específico; usar ensure_hoenn_source.py e validar hashes/estrutura, não renomear um pacote arbitrário. |
| Referência de mundo | [Eternal Emerald](https://eeveeexpo.com/threads/4871/) (consultar e solicitar autorização para uso de mapas) · [Eevee Expo recursos](https://eeveeexpo.com/resources/) |
| Jornada | [Detonado Emerald Pokémon Mythology](https://www.pokemythology.net/detonados/detonado-emerald/) · [detonado interno](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md) · [plano original](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) · [seleção de fontes](HOENN_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) · [preparação ZIP](HOENN_PREPARACAO_ZIP_E_RECURSOS.md) |
| Base e motor | [Pokémon Decades](https://github.com/HazyCrazy/Pokemon-Decades) · [Pokémon Essentials](https://github.com/Maruno17/pokemon-essentials) · [documentação Essentials](https://essentialsdocs.fandom.com/wiki/Essentials_Docs_Wiki) · [RPG Maker XP](https://www.rpgmakerweb.com/products/rpg-maker-xp). Referência APIs v21.1; não atualizar a engine como parte do lote. |
| Instalação Windows | [Manual](INSTALACAO.md) · [Downloads Blue](https://pokemondessastreparadosal.vercel.app/downloads) · [Releases versionadas](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases). Baixar Blue-Story.exe da tag comprovada, não latest arbitrário. |
| Android | [JoiPlay e RPG Maker Plugin](https://www.joiplay.net/) · [Termux](https://termux.dev/en/) · [Releases](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases) — canal android-multiregion, ZIP e patches verificados. |
| CI | [Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions) · [GitHub CLI](https://cli.github.com/) · [regra publicação Kanto](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md) |
| Auditorias de referência | [#49 treinadores/habitats](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/49) · [#61 portas](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/61) · [#62 encontros](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/62) · [#63 HMs](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/63) · [#64 Magma/Aqua](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/64) · [#340 migração Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/340) · [#334 conexão física Sinnoh](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/334) |

Fonte técnica inicial: revisão c59233bdbaac4fbfeca6aa01c7f05be628da2a92; MapInfos SHA256 7a69152de41a8b70df3199182e09d04e2f1be2db73a2ab509137571e4d8ade15; Tilesets SHA256 6812832c71da1b6b27585f45212135afcd74bd578e5127caa4d5296ee1126a9b. ZIP privado esperado: The Pokémon World Project - Hoenn.zip; SHA integral não confirmado no manifesto consultado. Fixar SHA antes de consumir. Inventário por arquivo com licença/autor/atribuição; áudio apenas próprio/autorizado. Não distribuir ROMs/OSTs; consultas de guias não autorizam copiar diálogos ou imagens.

## 2. Arquivos existentes e pontos de alteração

| Camada | Caminhos |
|---|---|
| Origem | [ensure_hoenn_source.py](../scripts/regions/ensure_hoenn_source.py), [prepare_hoenn_source.py](../scripts/regions/prepare_hoenn_source.py), [hoenn-source.json](../data/regions/hoenn-source.json), audit_hoenn_baseline.py |
| Mundo | [pilot_hoenn.py](../scripts/regions/pilot_hoenn.py), hoenn_stage10.py, [HoennPilot.rb](../scripts/regions/HoennPilot.rb), módulos hoenn_qa_phase1.py a hoenn_qa_phase12.py |
| Instalação | [install_hoenn.py](../scripts/regions/install_hoenn.py), [auto_integrate_hoenn.py](../scripts/regions/auto_integrate_hoenn.py), [install_game.py](../scripts/install_game.py), [Bootstrap.cs](../scripts/windows/Bootstrap.cs) |
| Região e menu | [RegionStart.rb](../scripts/battle_polish/RegionStart.rb), [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb), [Regions.rb](../scripts/battle_polish/Regions.rb), RegionalPolicy.rb, RegionalCards.rb, Balance.rb, Campaign.rb, TitleKanto.rb |
| Android | [package.py](../scripts/android/package.py), [publish_updates.py](../scripts/android/publish_updates.py), [update_client.py](../scripts/android/update_client.py), [android-multiregion.yml](../.github/workflows/android-multiregion.yml), [android-updater-regression.yml](../.github/workflows/android-updater-regression.yml) |
| Windows/CI | [battle-hub-release.yml](../.github/workflows/battle-hub-release.yml), [blue-story-windows.yml](../.github/workflows/blue-story-windows.yml), [regression.yml](../.github/workflows/regression.yml), [TESTAR_HOENN.bat](../TESTAR_HOENN.bat) |
| Catálogos | [hoenn-pilot.json](../site/public/data/hoenn-pilot.json), [regions.json](../site/public/data/regions.json), scripts/music/BlueMusic.rb, hoenn_audio.py (localizar caminho real) |

Descubra nomes atuais antes de criar novos arquivos. Proposta: data/regions/hoenn-content-inventory.json (inventário público sanitizado, sem assets), hoenn-roadmap-status.json (fase, gates e links), docs/HOENN_EVIDENCIAS.md (recibos). Relatórios brutos, fontes e fixtures privadas em .blue-work/hoenn-*/. Não criar segundo motor de mapas, batalha, viagem ou atualizador. Reutilize utilitários, contratos e fixtures do projeto.

## 3. H00: preflight reproduzível e inventário global

Comandos iniciais (terminal com git, Python 3.11+, Ruby, GH autenticado; executar a partir do clone de trabalho autorizado):

    git clone https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git
    cd Pokemon-Blue-Dessastre-Paradoxal
    git fetch origin main
    git status --short
    git rev-parse origin/main
    git ls-files 'docs/HOENN*' 'data/regions/hoenn*' 'scripts/regions/*hoenn*' 'scripts/regions/Hoenn*' '.github/workflows/*' 'tests/*hoenn*'
    gh pr list --state open
    gh release list --limit 40
    gh workflow list
    python scripts/regions/ensure_hoenn_source.py --help
    python scripts/regions/prepare_hoenn_source.py --help
    python scripts/regions/install_hoenn.py --help
    python -m unittest discover -s tests -p 'test_hoenn*.py' -v
    ruby -c scripts/regions/HoennPilot.rb

Em clone já existente não repetir git clone; não dar reset em trabalho alheio. Verificar --help antes de comandos dependentes de versão. Usar worktree/branch limpa a partir de origin/main. Para hashes: PowerShell Get-FileHash -Algorithm SHA256, Linux/Termux sha256sum. Nunca escrever fora da cópia QA.

- Identificar SHA da main, versão Windows, versão Android, release tags, manifesto de atualização, plataforma e contagens; recuperar logs de jobs recentes da própria revisão. Não presumir versão pelo número maior nem pelo README.
- Ler em modo inerte MapInfos, MapXXX, Tilesets, passabilidade/prioridade/terrain tags, metadados, conexões PBS, eventos/páginas/switches, sprites, áudio, tabelas de encontros/treinadores, itens e flags. Separar fonte histórica, 199 instalados de referência, instalados efetivos em cada build, e diferenças. Inspecionar MapIDs globalmente (Decades, Kanto, Johto, Sinnoh, futuras regiões). Listar IDs ocupados, reservas, lacunas, colisões, capacidade real de IDs >999 e leitores %03d/regex de três dígitos.
- Inventariar 373 mapas fonte por tipo: Emerald obrigatório, secundário, pós-Liga, variante, duplicata, hierarquia sem terreno, externo. Comparar com catálogo, não declarar 373 alvo automaticamente. Incluir interiores por sala/andar; nomes agregados não comprovam cada porta.
- Por MapKey: source_revision, source_id, hash, autorização, destino estável, dimensões, tileset, mapa físico, pontos de entrada/saída, grafo de conexão, eventos/NPC/treinador/item/habitat/música esperados vs reais, status e testes. Por evento: ID/nome, coordenadas, gatilho/páginas, dependências, switch/flag, recompensas, derrota/retry, localização/PT-BR, evidência. Desconhecido = BLOCKED_INVENTORY, nunca zero.
- Obter manifestos de instalação, saves de teste em vários checkpoints, 11 relatórios QA, backlog QA03/04/10, arte provisória e todos os casos de QA12. Não copiar dados pessoais.
- Executar TESTAR_HOENN.bat apenas no ambiente Windows descartável autorizado. Preflight deve ter base game/Game.exe, ZIP ou cache auditado; BAT gera .blue-work/hoenn-qa-fase12, relatório por fase e fluxo de teste. Não confundir auditoria estática com jogo aberto.
- Instalação atual pode ser verificada em cópia existente: python scripts/regions/install_hoenn.py --game game --verify-installed. O instalador só aplica em game/ principal daquele clone; portanto use clone/ambiente descartável, não instalação pessoal.
- Saída: relatório baseline, grafo, mapa de propriedade global, inventário e fila ordenada por fase. Gate proposto HOENN_H00_BASELINE_INVENTORY_OK. Se assets/ambiente faltarem, isole o bloqueio, avance apenas trabalho demonstrável.

### Recibo de H00 em 28/11/2026

| Verificação | Resultado |
|---|---|
| Revisão | Main `f3d5809a`. Desde a revisão funcional `02732eadaedf49f3728755edb2bd2654ceae3897`, o diff da main estava restrito ao histórico do portal. |
| Windows | Build 1632, executável baixado e self-test aprovado. SHA-256 `613786df97908f55417f3d169831b6b1d7534c61a224423467c63bd8fac2f4fe`. [Release](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/battle-hub-1632-02732ea) |
| Android | Build 247, ZIP completo de 1.401.504.567 bytes conferido pelo SHA-256 `0469d877818490a31f6e0a080d8f2d942f954dc65568d5aec38ef3235606f87b` e pelo manifesto interno. Patch 234 → 247 com 27 arquivos alterados e zero removidos, validado pelos hashes dos membros. [Release](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/android-multiregion-247-02732ea) |
| MapIDs instalados | 199 pares origem/destino idênticos em Windows e Android, faixa observada 700–898. Os dois conjuntos têm 81 mapas com tabelas PBS de encontros. |
| Game.exe compartilhado | Em cópia Windows descartável, Novo Jogo abriu o quarto de Littleroot em `701,25,6` e o save de QA reabriu na mesma posição. A inspeção nativa encontrou um agente no mapa exterior `700` em `9,10`. Travessia e campanha integral seguem pendentes. |
| Fonte | 373 arquivos RXDATA conferidos contra os Git blobs da revisão fixada, 100 tilesets e 5.181 eventos inventariados. A fonte tem 25 mapas sem terreno e sem eventos. Entre os 373, a classificação de escopo de 235 entradas ainda precisa de revisão. |
| QA técnica | QA01 e QA03–QA11 emitiram relatórios estáticos. QA02 reprovou as conexões abaixo e QA12 permaneceu `BLOCKED_STATIC`. O backlog do gerador tem 2.035 candidatos de NPC/treinador/placa, 26 obstáculos a revisar e arte provisória da Elite Four. |
| Estado | `BLOCKED_INVENTORY` pelas cinco bordas. `BLOCKED_RIGHTS` para nova distribuição de recursos de terceiros. `BLOCKED_ENV` para executar a campanha e o atualizador no JoiPlay. A Barra de aceite nativo segue em 0/12. |

As 34 rotas foram identificadas pelo nome físico original. As cinco fora do catálogo são **105 → fonte 107**, **107 → 109**, **108 → 110**, **115 → 129** e **123 → 142**. Os IDs da fonte permanecem separados dos IDs do jogo compartilhado.

| Conexão sem faixa de travessia geométrica | IDs no Blue |
|---|---|
| Rota 126 e Mossdeep | 857 ↔ 810 |
| Rota 127 e Rota 124 | 858 ↔ 818 |
| Rota 128 e Rota 124 | 859 ↔ 818 |
| Rota 129 e Ever Grande Sul | 860 ↔ 846 |
| Rota 131 e Rota 126 | 862 ↔ 857 |

Os registros originais dessas cinco bordas já contêm os mesmos deslocamentos. A correção precisa de uma âncora de terreno verificável e de teste de travessia de ida e volta. Além disso, Kanto já usa os IDs 600–608 nesta revisão, e o instalador recusou a prévia de Johto para preservar os arquivos existentes. Resolver propriedade global integra o gate de H01. As vagas observadas em 899–999 ainda não constituem reserva aprovada.

O auditor `scripts/regions/audit_hoenn_h00.py` salva o inventário por mapa, o grafo observado, os marcadores compactos, os IDs ocupados e os erros em `.blue-work/hoenn-h00/h00-report.json`. Ele retorna código 2 enquanto a geometria ou o mapeamento tiver falhas. O relatório bruto e os dados de origem ficam no workspace descartável. O `TESTAR_HOENN.bat` também passou a usar o diretório do repositório em `PYTHONPATH` para carregar os módulos das auditorias. [CI da integração da revisão de referência](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/46102703628).

### Correção das travessias marítimas em 28/11/2026

As cinco bordas da tabela histórica foram removidas. Três conexões resgatadas do PBS da revisão fixada c59233bd recompõem os trajetos por bordas de água compartilhadas.

| Nova conexão | MapIDs no Blue | Pares de tiles navegáveis observados no motor |
|---|---|---:|
| Rota 127 ↔ Rota 126 | 858 ↔ 857 | 42 |
| Rota 128 ↔ Rota 129 | 859 ↔ 860 | 67 |
| Rota 131 ↔ Rota 130 | 862 ↔ 861 | 68 |

Mossdeep fica acessível pela Rota 127, a Rota 124 pela Rota 126 e Ever Grande Sul pela Rota 128. A Rota 131 volta ao corredor pelas rotas 130, 129, 128 e 127. O Game.exe compartilhado, em perfil Windows descartável, compilou o PBS revisado e confirmou nove cruzamentos individuais nos dois sentidos com o estado de Surf ativo. A obtenção de Surf e a campanha completa ainda aguardam teste.

A atualização de Hoenn já instalado reconhece o conjunto de bordas anterior, cria backup local e solicita a recompilação no próximo lançamento. A migração exercitada preservou os 199 pares de MapIDs, o ponto inicial, os RXDATA de mapa e um arquivo de save de teste. A segunda execução reconheceu a instalação atualizada. A auditoria privada do conteúdo do Android 247 com o PBS revisado confirmou os mesmos 199 MapIDs e 44 bordas de Hoenn com sobreposição. QA02 passou. A consolidação QA01–QA12 passou na verificação estática e mantém a aceitação nativa integral pendente.

O bloqueio geométrico de H00 foi corrigido. O teste físico de abertura, travessia e atualização no JoiPlay segue pendente, assim como a autorização de redistribuição e a publicação pareada. As rotas 105, 107, 108, 115 e 123 continuam no backlog. H01 depende também da confirmação de propriedade dos IDs em conflito com Johto.

### Classificação e conferência do catálogo H00

A conferência de 28/11/2026 verificou byte a byte os 373 RXDATA da fonte pelo hash de cada blob e classificou todos com base na hierarquia, no terreno e nos eventos. O catálogo compartilhado cobre 199 MapKeys. A auditoria mantém a decisão de incluir um mapa separada de sua classificação.

| Grupo de referência | Mapas |
|---|---:|
| Rotas com numeração confirmada | 34 |
| Locais de história e dungeons da campanha | 100 |
| Interiores, serviços urbanos e anexos de rota | 76 |
| Locais opcionais e referências subaquáticas | 47 |
| Áreas de pós-Liga candidatas | 35 |
| Áreas de eventos externos | 5 |
| Variantes e filler da fonte | 41 |
| Hierarquia vazia, cenas e apoio à integração | 35 |

Sete entradas não vazias têm RXDATA idêntico ao do MapID fonte 271. O inventário preserva suas identidades para revisão. A instalação compartilhada recompilada no Windows apresentou 44 bordas de Hoenn com sobreposição, 81 mapas de encontros e 199 MapIDs de Hoenn sem sobreposição com os 178 de Kanto. O auditor também verifica os registros compartilhados de Johto e Sinnoh quando presentes.

## 4. H01: migração aditiva 199 → N, antes de qualquer expansão

P0: retirar dependência de igualdade rígida com 199 **sem reduzir garantia de conteúdo**. N é derivado do conjunto completo de MapKeys aprovado para aquela revisão, não um mínimo permissivo.

1. Localizar todas as constantes/gates (incluindo workflow e arquivos Android):
   
       git grep -n -E 'BLUE_HOENN_READY_V1|BLUE_HOENN_PILOT_V1|199|700\.\.999' -- scripts/regions scripts/battle_polish scripts/android .github/workflows

2. Inventário canônico versionado, mapping origem/destino, schema e hashes. Preservar todos os pares V1 existentes, inclusive home 8 e town 7, flags, eventos e links de save. Atribuir só IDs livres comprovados pelo registro global. Não supor 100 IDs adicionais disponíveis. Se necessário estender faixa e suporte a quatro dígitos, com testes de leitura, regex, filenames, PBS, cache, mapa e Android antes de usar.
3. Migrador com detecção de V1 íntegro, V1 parcial, arquivo ausente, divergência legitimamente conhecida, arquivo estrangeiro, conflito, instalação nova, V2 atual e versão futura. Validar identidade e hashes antes de restaurar arquivo legado conhecido; rejeitar qualquer situação desconhecida sem sobrescrever. Mesclar MapInfos/Tilesets/PBS e eventos por propriedade; preservar IDs de outras regiões e referência de evento usada no save. Comparar e revalidar todos os 199 anteriores.
4. Atualizar em conjunto install_hoenn, auto_integrate, ensure_source, pilot_hoenn, HoennPilot.metadata, RegionStart.hoenn_manifest/compact_manifest/integrated?, RegionTravel, gate de menu, auditorias 01–12, Android package/verify, workflow android-multiregion, cache/compilação e portal. Compatibilidade JoiPlay sem JSON Ruby: formato compacto validado, vinculado ao manifesto e hashes; não liberar destino pela mera existência de marcador.
5. Dry-run padrão, staging, CAS de arquivos antes de gravar, atomic replace, rollback só arquivos afetados, marcador final após verificação e compilação conforme contrato; falha não perde save. Android sem backup integral. Reexecução idempotente. Testar migração 199→199 (schema sem mapas novos), 199→N, N→N, primeira instalação, interrupção, disco cheio, hash divergente, symlink, colisão de case, destino ocupado, mapa ausente, marcador forjado, sem JSON, recompilação, saves em mapa antigo.
6. Só publicar expansão quando migração comprovada. Gatilhos de CI devem incluir mapas, música, scripts, catálogos, instaladores e plugins que afetam gameplay. Preservar hashes/regressões das demais regiões.
7. Gates propostos: HOENN_H01_LEGACY_199_PRESERVED_OK, HOENN_H01_REAL_199_TO_N_MIGRATION_OK, HOENN_H01_INSTALL_ROLLBACK_OK, HOENN_H01_JOIPLAY_NO_JSON_OK. Em H01 sem mapas novos, N=199; repetir migração real em todo lote de expansão. Não imprimir marcadores manualmente.

### Catálogo de instalação e migração

O manifesto compartilhado V2 usa o catálogo versionado em `data/regions/hoenn-map-catalog.json`. A revisão 1 aprova os mesmos 199 MapKeys legados. A instalação registra os pares antigos separadamente e bloqueia remapeamentos, MapKeys ausentes e revisões desconhecidas. Um catálogo de expansão precisa listar explicitamente os MapKeys aprovados e vir acompanhado dos mapas e conexões auditados.

Uma instalação compartilhada V1 conserva seus mapas e saves. O instalador valida as reservas globais e os registros de Hoenn, guarda os arquivos afetados, atualiza o manifesto e os marcadores compactos e solicita recompilação. Se a gravação for interrompida, a próxima preparação restaura o estado anterior com base nos hashes registrados antes de tentar outra vez. A leitura V1 continua disponível para instalações anteriores e para a cópia isolada de QA.

Em 28/11/2026, uma cópia descartável da instalação compartilhada anterior foi migrada de V1 para V2 no Windows. O ensaio conservou os 199 pares de MapIDs, reparou as conexões marítimas do H00 e preservou o save de teste byte a byte. O Game.exe recompilou os plugins e o PBS. A segunda execução conservou o manifesto já migrado. Os testes de alocação cobrem conjuntos maiores em ambiente isolado. A revisão 1 continua instalando os mesmos 199 mapas.

O atualizador Android pela fonte usa a contagem do catálogo ativo. A validação em aparelho com JoiPlay permanece adiada a pedido do proprietário.

## 5. Fases H02–H17: campanha jogável ponta a ponta

Para cada subfase use inventário H00, fonte autorizada e geometria nativa. Reutilize handlers existentes; teste caso positivo e todos os pré-requisitos negativos, derrota/retry, recompensa única, save/reload, retorno físico, blackout, escala e regressão. Cada marcador abaixo é proposto, não emitido nesta análise; gerado somente por assertions reais. Lote sem feature comprovada não promove status. A partir do primeiro lote, validar em versão principal e não só cópia piloto.

### H02 — Littleroot, perfil e início
- Inventariar caminhão/abertura, casa/quarto, relógio, mãe, casa do rival, laboratório Birch, vila e R101. Spawn existente na casa: preservar saves e adaptar a chegada de caminhão somente se adotada sem quebrar checkpoint. Seleção de personagem, nome, sprites e escala compatíveis com Blue.
- Reusar choose_profile, clock, mother, route_birch, choose_starter/choose_birch_ball. Antes de inicial, bloquear grama/saída indevida; resgate Birch com batalha de Zigzagoon, escolha Treecko/Torchic/Mudkip única, remover as bolas após escolha, não repetir ao falar ou recarregar. Testar derrota conforme roteiro e time/PC cheio. Diferenciar novo jogo de chegada regional.
- Gate HOENN_H02_STARTERS_BIRCH_SAVE_OK: três iniciais x dois perfis, jogo novo/reload, saída física casa→Littleroot→R101, nenhum segundo inicial.

### H03 — Oldale, R102/R103, Wally
- Rival_103 e Birch: May/Brendan e equipe conforme perfil e inicial; derrota/retry sem avanço indevido, Pokédex/Poké Balls/Running Shoes uma vez. Reusar cura e Mart reais; entrar/sair de todas as casas, placas e portas. Preservar tabela R102 (Poochyena, Zigzagoon, Wurmple, Lotad, Seedot, Ralts, Surskit); conferir taxas da fonte.
- Petalburg: trocar norman_intro textual por cena autoral real de tutorial de captura do Wally com Ralts, sem alterar party do jogador; flags independentes, bloquear Norman até quatro badges. Testar R102→Petalburg e retorno.
- Gate HOENN_H03_RIVAL_POKEDEX_WALLY_OK.
- O catálogo compartilhado revisão 2 incorpora as casas de Oldale (MapKey 15) e mantém os 199 pares instalados. As duas portas retornam a pontos distintos de Oldale. O Centro, o Mart e as três placas usam os serviços e o diálogo da campanha. O único recurso novo de instalação é a geometria baixada do commit de origem já fixado.
- Em Petalburg, o jogador orienta Wally pelo menu da cena de batalha. O tutorial usa a animação e a resolução de captura do motor. Cancelar permite nova tentativa. A captura altera somente a flag regional e Norman exige as quatro primeiras insígnias locais.
- Ensaio Windows automatizado com Game.exe: ida e volta pelas duas casas, Centro e Mart, travessia da Rota 102 até Petalburg e de volta, cancelamento e captura concluída com party, Bolsa, PC e estatísticas intactos. As escolhas do tutorial foram fornecidas pelo ensaio e a animação foi executada pelo motor.

### H04 — Rustboro, R104, Petalburg Woods, R116 e Devon
- Floresta: recruta Aqua, empregado, item e bloqueio, treinadores, itens visíveis/ocultos, saídas norte/sul e floricultura/Wailmer Pail. Rustboro: todas as casas, escola, Devon e ginásio; Roxanne e puzzle, STONE/TM/uma esmeralda, aquisição de Cut na casa correta. Não confundir desbloqueio por badge com aquisição do HM.
- R116/Rusturf Tunnel: roubo de Devon Goods, resgate de Peeko, retorno ao funcionário e Mr. Stone, Letter/PokéNav, entrega única e acesso ao barco Briney. Conectar passagens com coordenadas auditadas; leste do túnel continua bloqueado até Rock Smash quando exigido.
- Gate HOENN_H04_ROXANNE_CUT_DEVON_OK.
- O desafio de Roxanne registra a solução em Hoenn e permite revanche sem repetir as perguntas. Cut exige o recibo do especialista, uma insígnia local e um Pokémon que conheça o golpe. Mr. Stone libera o PokéNav de destinos após a entrega da Devon e o recebimento da carta, incluindo saves anteriores elegíveis.
- Cut, PokéNav e o desafio de Roxanne passaram em ensaio no Game.exe Windows com save e reload. A migração acrescenta as três escadas das casas de Rustboro e mantém os destinos instalados. Rusturf exige o registro regional de Rock Smash, a Insígnia do Dínamo e um Pokémon com o golpe. Em instalações que ensinam Rock Smash pela TM98 consumível, o registro continua válido depois do ensino.
- O ensaio Windows atravessou as três escadas nos dois sentidos e confirmou o bloqueio do atalho de Rusturf nos dois portais antes de Rock Smash. Após quebrar uma pedra, foi possível atravessar e retornar. O save reabriu no túnel com a passagem habilitada. A campanha integral ainda precisa de um ensaio contínuo.

### H05 — Dewford e Granite Cave
- Casa de Briney, embarque real, destino Dewford e retorno, sem bypass de missão. Old Rod, NPCs/interiores, Brawly e ginásio escuro, KNUCKLE/TM. Flash obtido na entrada da caverna conforme referência; visibilidade e passagem corretas, entregar Letter a Steven, Steel Wing se válido no PBS.
- Validar Granite Cave todos os andares, pesca, itens, entradas e saída; preparar conexão R105–109 (ver H14, adicionar trechos necessários antecipadamente sem liberar Surf antes de hora).
- Gate HOENN_H05_BRINEY_BRAWLY_STEVEN_OK.
- A migração preserva os 200 MapIDs e instala o pescador da Vara Velha, moradores nas três casas de Dewford e cinco itens nos andares inferiores. O ginásio começa com a luz reduzida e ganha iluminação conforme as vitórias. Flash em Granite Cave exige a Insígnia do Punho, o recibo regional do montanhista e um Pokémon apto que saiba o golpe. A TM70 consumida ao ensinar Flash fica registrada pelo recibo; o movimento não é usado no ginásio. Briney exige resgate e carta, só embarca nos respectivos portos e reserva a ida a Slateport para depois da insígnia e da entrega a Steven.

#### Preparação das rotas marítimas

O catálogo compartilhado revisão 3 acrescenta os MapKeys 107, 109 e 110, totalizando 203 mapas. O instalador baixa as três geometrias da fonte fixada e compila os encontros de água e pesca no jogo. As quatro bordas têm células de água em comum e nenhuma dupla de células caminháveis em terra. A faixa R106–R107 usa o deslocamento 7 para criar uma faixa de água onde o deslocamento 20 da fonte deixava as bordas separadas. A Insígnia do Equilíbrio continua sendo exigida pelo motor para Surf. As entradas opcionais da costa ficam para os lotes que implementam seus interiores.

| Rotas | Conexão entre os MapKeys | Uma dupla de células de água |
|---|---|---|
| R105–R106 | 107 Sul 0 → 108 Norte 0 | (1, 79) → (1, 0) |
| R106–R107 | 108 Leste 0 → 109 Oeste 7 | (189, 1) → (0, 8) |
| R107–R108 | 109 Leste 0 → 110 Oeste 0 | (59, 3) → (0, 3) |
| R108–R109 | 110 Leste 0 → 111 Oeste 40 | (59, 3) → (0, 43) |

O `Game.exe` no Windows compilou e abriu o catálogo de 203 mapas. Em cenários isolados, foram percorridas as 28 transferências de portas e escadas de Dewford e Granite Cave e as oito travessias costeiras em ambos os sentidos. O ensaio confirmou o embarque e o retorno de Briney, a pesca, a iluminação do ginásio, Flash após consumir a TM70, a entrega a Steven e o carregamento de saves na caverna e na costa. Os resultados das batalhas desse ensaio isolado foram simulados.

No percurso contínuo em Windows, uma parede isolava o corredor de Steven. A migração abre a célula (14, 14) do MapKey 159, preserva os 203 MapIDs e mantém o acesso ao corredor pela saída alta de B1F. O ensaio partiu de um checkpoint pós-H04 na Rota 104. Percorreu 706 passos com os controles automatizados, sete vitórias decididas pelo motor, pesca, ensino e uso de Flash, itens de B1F e B2F e entrega a Steven. Depois de voltar por Granite Cave, o mesmo save foi reaberto na praia de Slateport. Recibo Windows `HOENN_H05_BRINEY_BRAWLY_STEVEN_OK`.

### H06 — Slateport e Capitão Stern
- Embarque a Slateport, R109 e casa de praia, mercado, Fan Club, centro/mart, estaleiro, porto, Battle Tent (sistema opcional H19). Museu Oceanic: entrada/taxa conforme referência, grunts Aqua em ordem, entrega Devon Goods, flags e retorno.
- R110 acessível por percurso físico após missão. Todos os estabelecimentos devem ter porta e saída funcionais. Não manter texto provisório em evento alcançável.
- Gate HOENN_H06_STERN_MUSEUM_ACCESS_OK.
- O segundo recruta Aqua só batalha depois da primeira vitória. Toda a borda norte de Slateport fica fechada até Stern registrar a entrega. O retorno à Rota 109 continua disponível.
- O ensaio Windows partiu do save do H05 na Rota 109. Em 556 passos foram verificadas as portas da praia e da cidade, a taxa única de ₽50, as duas vitórias Aqua, a entrega a Stern e a travessia de ida e volta na Rota 110. O save reabriu na rota com a entrega registrada. Recibo Windows `HOENN_H06_STERN_MUSEUM_ACCESS_OK`.
- Restam os serviços do mercado e do porto. As regras da Battle Tent seguem no H19.

### H07 — Mauville, rival e Wattson
- R110, Cycling Road e portarias, rival_110 variantes, Itemfinder, acesso normal e de bicicleta. Rydel: Mach/Acro, troca sem duplicar itens, controles no Android, queda/obstáculos. Wally no ginásio, batalha/retry, tio.
- Wattson: interruptores, barreiras, treinadores, DYNAMO/TM, Rock Smash recebido do NPC, uso nativo. Game Corner e serviços passam por H19 se ausentes; New Mauville H18/H19.
- Gate HOENN_H07_WATTSON_ROCK_SMASH_BIKES_OK.

### H08 — R117, Verdanturf, creche e Rusturf
- R117 treinadores, itens, conexão; substituir daycare_info por serviço real usando API existente de daycare/ovos, depósito/retirada de dois Pokémon, taxa, experiência, compatibilidade, ovo único, party cheia/sem dinheiro, cancelamento e persistência. Reusar padrão da creche Kanto validado, com escopo regional conforme regra global.
- Rusturf: pedras nativas que exigem HM+insígnia, libertar casal e dar Strength uma vez, corredor bidirecional para Rustboro; acesso à saída sem softlock. Battle Tent e interiores.
- Gate HOENN_H08_DAYCARE_TUNNEL_STRENGTH_OK.

### H09 — Fallarbor, Meteor Falls e Mt. Chimney
- R111/112/113/114, Fiery Path, cinzas/Soot Sack, casa Winstrate, oficina, NPCs, Fossil Maniac e Lanette. Auditar R115 norte (ausente no catálogo), acessos e Meteor Falls interiores; adicionar rota segura sem sobrescrever IDs. Deserto bloqueado antes de Go-Goggles.
- Magma/Aqua em Meteor Falls, Cozmo, teleférico e estados, batalha de Maxie e Tabitha, Meteorite, máquina e retorno; abrir Jagged Pass somente após progressão. Testar bloqueios, derrota e subida/descida.
- Gate HOENN_H09_METEORITE_CABLE_CAR_OK.

### H10 — Lavaridge, Flannery, Norman
- Jagged Pass, Lavaridge, loja de ervas, interiores, ovo/presentes, puzzle de vapor e andares; Flannery HEAT/TM e Go-Goggles; liberar deserto e Strength. Auditoria Mirage Tower e fósseis H18.
- Retorno Petalburg sem teleporte; Norman só após quatro badges locais, salas dos desafios e batalha; BALANCE/TM, Surf via família de Wally; negar uso anterior e com item estrangeiro, travessia física da primeira margem e retorno.
- Gate HOENN_H10_FLANNERY_NORMAN_SURF_OK.

### H11 — R118/R119, Weather Institute, Fortree
- Surf para R118, pesca, R119 chuva/ponte, Instituto Meteorológico Aqua e Shelly, Castform com party cheia/Box, rival e Fly. Reconstruir entradas do instituto, escadas e descanso.
- Fortree: casas suspensas, ponte, Kecleon invisível, Devon Scope de Steven em R120, remover/reativar obstáculos apenas por estado correto; Winona com portas giratórias, FEATHER/TM, Fly local para cidades visitadas. R120/121 e Scorched Slab.
- Gate HOENN_H11_CASTFORM_SCOPE_WINONA_OK.

### H12 — Lilycove, Mt. Pyre e Magma
- R121/122 e R123 (adicionar se ausente), acesso Safari Zone (serviço H19), Lilycove departamento/andares, rival, museu, motel, porto e Contest Hall. Corrigir gate/harbor provisórios no caminho real.
- Mt. Pyre todos os andares, exterior/cume, túmulos, grunts, Archie e orbes; Magma Emblem, Jagged Pass entrada base, grunts/Tabitha/Maxie, despertar Groudon, retorno. A ordem de flags não deve prender jogador após derrota/reload.
- Gate HOENN_H12_MT_PYRE_MAGMA_EMBLEM_OK.

### H13 — Aqua Hideout, Mossdeep e Centro Espacial
- Notícia/roubo de submarino em Slateport, entrada Aqua Hideout, warp panels, grunts, Matt, Master Ball/itens quando referência válida, fuga submarino e rota para Mossdeep. Sem acesso prematuro ou salto de sequência.
- Mossdeep: interiores, Super Rod, ginásio Tate & Liza em dupla com party adequada, switches/puzzle, MIND/TM; invasão do Centro Espacial, dupla com Steven quando prevista e casa de Steven com Dive. Proteger flags e derrotas; validar BGM/arte.
- Gate HOENN_H13_AQUA_TATE_LIZA_DIVE_OK.

### H14 — Malha marítima, cinco rotas ausentes e Dive
- Inventário 101–134: 105,107,108,115,123 não listadas nominalmente; auditar fonte e instalar as realmente ausentes. Não interpretar números de rotas como source IDs. H05/H09/H12 podem adiantar segmentos indispensáveis mantendo o mesmo inventário.
- R105–109, R115, R123–134, Pacifidlog, Sootopolis, Ever Grande, áreas subaquáticas e Abandoned Ship. Conferir offset/direção e tile de borda; não substituir passagem por warp arbitrário. Adicionar portais apenas quando a fonte/roteiro prevê porta, navio, mergulho etc.
- Para cada ponto Surf: margem de embarque, água passável, trajeto e desembarque; cada par Dive superfície/submerso, mapeamento de coordenadas, saída correta, terreno, visibilidade e retorno; correntes R132–134 com destinos/retorno alcançáveis, pesca e encontros, treinador aquático; Waterfall Ever Grande (liberar H16). Testar sem badge, HM, Pokémon compatível e item de outra região. Verificar mapa sem conexão/porta de ida sem volta; provar por caminhada real, não teleporte QA.
- Gate HOENN_H14_ALL_34_ROUTES_CATALOG_OK, HOENN_H14_NATIVE_SURF_DIVE_ROUNDTRIP_OK, HOENN_H14_MAP_GRAPH_NO_ORPHANS_OK. Se mapa submerso não tiver correspondência, bloquear lançamento do segmento, não inventar coordenada.

### H15 — Seafloor Cavern e crise climática
- Entrada física exige sequência Magma/submarino/Centro Espacial, MIND e Dive; não bloquear saída de save legado preso. Todos os andares, pedras Rock Smash/Strength, correntes, puzzles e resets, Archie e despertar Kyogre no mapa correto.
- Sootopolis: clima, NPCs, bloqueios, Groudon/Kyogre e Wallace/Cave of Origin. Substituir simplificação por cenas autorais com sprites, movimentos, som/efeitos e recuperação em reload. Não depender apenas de flash/mensagem para declarar fidelidade.
- Gate HOENN_H15_SEAFLOOR_ARCHIE_CRISIS_OK.

### H16 — Sky Pillar e Juan
- Acesso Sky Pillar com Wallace e condição de história, escadas/andares, piso quebrável e Mach Bike conforme fase narrativa; queda e retorno sem softlock. Rayquaza convocado, crise termina de forma consistente e NPCs/clima atualizam; captura separada no pós-jogo.
- Sootopolis: puzzle de gelo do ginásio, rachadura, queda e reset, treinadores e Juan, RAIN/TM, Waterfall e acesso real Ever Grande. Verificar Surf/Dive para chegar e sair.
- Gate HOENN_H16_RAYQUAZA_JUAN_WATERFALL_OK.

### H17 — Victory Road, Liga, Hall da Fama
- Ever Grande sul/norte, cachoeira, centro, Victory Road 1F/B1F/B2F, Flash/Strength/Rock Smash/Surf e travessia real, Wally conforme progressão. Entrada da Liga exige oito badges locais, não global.
- Elite: Sidney→Phoebe→Glacia→Drake→Wallace, portas sequenciais, derrota e novo desafio, itens/curas conforme regra, escala, sprites, música, transições. Hall da Fama registra vitória uma vez, equipe/registro regional, créditos, retorno e reload sem alterar Hall de Decades. Johto/Sinnoh disponíveis conforme serviço regional atual; não entregar nova equipe automaticamente. Confirmar primeira vitória e revanche.
- Gate HOENN_H17_NATIVE_LITTLEROOT_TO_WALLACE_OK, HOENN_H17_HALL_SAVE_RELOAD_OK. Playthrough contínuo novo save sem teleportes/flags artificiais, em Normal e Master conforme matriz. Considerar MAIN_STORY_ACCEPTED somente após evidência nas duas plataformas; não significa pós-jogo completo.

## 6. H18–H22: conteúdo integral de Emerald

### H18 — Pós-Liga, lendários, fósseis
- Steven em Meteor Falls, casa de Steven/Beldum, revanches, Weather Institute indica Terra Cave/Marine Cave e capturas Groudon/Kyogre; Sky Pillar/Rayquaza pós-crise conforme Emerald. Diferenciar cena de batalha/captura real. Tratar KO/fuga/captura, respawn conforme regra, party/Box cheia, save/reload e política de especiais local.
- Sealed Chamber: mapa, acesso por Dive e enigma de Braille (texto autoral/acessível), ordem e espécies necessárias conforme referência, desbloquear Island Cave/Desert Ruins/Ancient Tomb, três Regis, persistência e retorno. Latios/Latias: escolha, roaming, encontros e flags, não duplicar. Eventos de distribuição externos ficam opt-in conforme autorização, não fingir presentes.
- Mirage Tower/Desert Underpass: Mach Bike, Rock Smash, Root/Claw Fossil, escolha exclusiva inicial, segundo pós-Liga, reviver na Devon com slot, item e confirmação transacionais. New Mauville missão Wattson, Basement Key, gerador/recompensa. S.S. Tidal ticket e rota pós-Liga para Battle Frontier, embarque/retorno.
- Gate HOENN_H18_POSTGAME_LEGENDARIES_FOSSILS_OK.

### H19 — Mundo opcional, serviços e interiores
- Safari Zone: acesso físico R121, taxa/tempo/passos, setores Mach/Acro, encontros e captura próprias, itens, expansão após Liga, saída segura, sem consumir recursos duas vezes. Shoal Cave: maré com relógio local e casos offline/Android, salas e itens, Shell Bell e retorno. Abandoned Ship: R108, porões, portas/chaves, Dive, itens únicos. Scorched Slab: acesso/itens; Mirage Island: condição Emerald e relógio, não forçar spawn. Trick House: sequência de puzzles e recompensas.
- Battle Tents (Slateport/Verdanturf/Fallarbor) com regras específicas, Game Corner conforme política do projeto e sem monetização real, serviços de loja/fan club, trocas NPC, presentes, Move Tutor/Deleter/Reminder, berry master, PokéNav, rematches, Itemfinder. Se mecânica global já existe, reutilizar em vez de duplicar.
- Auditar cada porta de cada cidade: Littleroot, Oldale, Petalburg, Rustboro, Dewford, Slateport, Mauville, Verdanturf, Fallarbor, Lavaridge, Fortree, Lilycove, Mossdeep, Sootopolis, Pacifidlog, Ever Grande. Incluir interiores múltiplos, escadas, elevador, retornos, hospitais e lojas. As localizações agrupadas no catálogo precisam ser desdobradas por porta.
- Gate HOENN_H19_OPTIONAL_MAPS_SERVICES_OK.

### H20 — Concursos, Pokéblocks e Secret Bases
- Substituir contest_stage8 por concurso real: categorias Cool/Beauty/Cute/Smart/Tough, ranks e condições conforme Emerald, inscrição, validação de Pokémon, exibição/pontuação, movimentos, vitória/derrota, ribbons, prêmios, persistência. Reusar sistemas da engine quando disponíveis, sem copiar scripts do doador.
- Pokéblock Case, berries, receitas/mistura e efeitos, limites, evolução por beleza conforme balanceamento autorizado. Secret Power e pontos de base, decoração, guardar/remover itens, visita e persistência; não permitir escrever mapa global por save.
- Testar plantio/colheita por tempo, relógio offline, save/reload, party/bolsa cheia, cancelamento. QA de interface no Android e PC.
- Gate HOENN_H20_CONTESTS_POKEBLOCKS_BASES_OK.

### H21 — Battle Frontier e Trainer Hill
- Obter mapas autorizados da ilha, porto, instalações, Artisan Cave, serviços, acessos, NPCs, sete instalações. Reusar motor de batalha Blue com regras de cada facility isoladas do level cap/story, sem alterar campanha: Battle Tower (Anabel, streak), Dome (Tucker, torneio), Palace (Spenser, comportamento autônomo), Arena (Greta, julgamento), Factory (Noland, rental), Pike (Lucy, salas/condições), Pyramid (Brandon, exploração e recursos).
- Implementar regras de elegibilidade, equipe/itens temporários e restauração atômica, cancelamento, derrotas, sequência, pontos, símbolos prata/ouro, recompensa idempotente, save/resume. Não marcar por existir mapa ou menu. Testes de RNG determinístico para CI, sessões reais para aceite.
- Trainer Hill: cronômetro, andares, batalhas, pontuação/recompensas; relógio/pausa e Android. Artisan Cave encontros e itens. Testar S.S. Tidal e retorno à campanha sem perder time.
- Gate HOENN_H21_SEVEN_FRONTIER_FACILITIES_OK, HOENN_H21_TRAINER_HILL_OK.

### H22 — Auditoria transversal de conteúdo, arte e som
- Completar todas as 34 rotas, localidades e interiores esperados do inventário H00; nenhum mapa sem retorno; sem placeholders vazios. Separar variantes Ruby/Sapphire e ORAS, não duplicar ginásios ou história. Substituir sprites provisórios de chefes, rival e NPC; escala do protagonista consistente com outras regiões, bordas pretas preenchidas por arte adequada, colisão e tile visual correspondentes, água/lava/areia/chuva/sol/cinzas.
- Para cada mapa, comparar eventos de fonte: NPCs, placas, treinadores, visibilidade, duplas, itens no chão/ocultos, presentes, lojas, diálogos, obstáculos. Processar backlog QA03/04 e boss_graphics da QA12; cada item classificado IMPLEMENTED, INTENTIONAL_VARIANT com justificativa ou BLOCKED (não omitir). Reconciliar 194 equipes existentes, versões PBS, IA, rematches, regras de escala e líderes. Não inventar porcentagens.
- Encontros: Land/Cave/Surf/OldRod/GoodRod/SuperRod/RockSmash/Dive/Safari e métodos realmente suportados; verificar pesos/níveis/espécies e soma por método quando a tabela é percentual, sem confundir encounter rate com peso. Separar encontros fixos, presentes, roaming, swarms e métodos especiais. Preservar R102 existente e outras tabelas corretas; corrigir por prova de origem. Compilar e testar GameData::Encounter/Trainer/MapMetadata.
- BlueMusic: BGM por cidade, rota, cavernas, oceano, Dive, clima, Centro, ginásio, batalha rival/Magma/Aqua/Elite/lendário, Hall, fanfarras/SE; loops/fade e retomada após batalha; usar somente assets com direitos, manter fallback claro se faltar trilha. Conferir áudio realmente tocando em Windows e JoiPlay; QA11 não é prova auditiva. PT-BR autoral, revisão de texto, menus, Trainer Card local/global e atlas. Atlas e teleporte QA devem ler o manifesto inteiro e permitir busca de qualquer mapa com spawn seguro, sem liberar conteúdo na campanha normal.
- Gate HOENN_H22_FULL_INVENTORY_RECONCILED_OK, HOENN_H22_AUDIO_VISUAL_PTBR_OK.

## 7. H23 — viagens, saves e isolamento regional

- Reusar BlueRegions/BlueRegionTravel/BlueRegionStart, agente em Littleroot e menu Novo Jogo no jogo principal. Confirmar regra atual de viagem livre entre regiões instaladas; docs antigas pós-Liga não são autoridade. Destino não instalado aparece como indisponível, sem warp inválido.
- Exercitar Hoenn↔Decades/Kanto/Johto/Sinnoh conforme instalações e conexões efetivas. Salvar antes/depois, time depositado sem perda, equipe regional recuperada, Box cheia cancela antes de commit, rollback, Pokémon especiais bloqueados segundo oito badges locais, itens-chave/HMs isolados e contagem global de esmeraldas intacta. Novo jogo/chegada por viagem não compartilham flags de início indevidas. Blackout em cidade inicial e em Centro mais recente, sem retorno a outra região.
- Migrar saves de testes de builds antigas em Littleroot, rotas, ginásios, cavernas, Elite/Hall e fora de Hoenn; preservar MapID, posição alcançável, eventos, party/PC e demais regiões. Não testar com save pessoal. Validar um save novo e um legado em cada atualização. Conferir mapa atual ao atualizar, recuperação de cenário removido apenas por migração explícita (preferir não remover IDs).
- Gate HOENN_H23_REAL_REGIONAL_TRAVEL_SAVE_OK, HOENN_H23_NO_FOREIGN_STATE_CHANGE_OK.

## 8. H24 — integração e publicação principal (procedimento de todo lote perceptível)

### 8.1 Windows Blue-Story.exe
1. Usar auto_integrate_hoenn.py → ensure_hoenn_source.py → install_hoenn.py, chamados pelo fluxo install_game.py/Bootstrap.cs real. Corrigir migração H01, não criar launcher de campanha separado. TESTAR_HOENN.bat e Testar Hoenn continuam como QA isolado, nunca substituem Novo Jogo Hoenn compartilhado. Verificar mensagens e .blue-work/hoenn-main-install-status.json + .log. Nenhum download doador de executável.
2. Em clone/runner descartável com game/ autorizado, executar simulação padrão e só depois --apply; no estado atual --apply pode recusar parcial ou retornar verificação se já instalado, H01 deve tornar migração segura.
   
       python scripts/regions/install_hoenn.py --game game
       python scripts/regions/install_hoenn.py --game game --apply
       python scripts/regions/install_hoenn.py --game game --verify-installed

   Comandos acima são reais na baseline; verificar --help se alterados. Testar também caminho automático pelo Blue-Story.exe, incluindo download ausente/cache válido, atualização 199→N e compilação, fechamento/reabertura, menu e versão visível (SHA + data/hora), game/Data/PBS/Plugins/Graphics/Audio. Não criar marcador manualmente.
3. Rodar Game.exe com janela/renderização e controles reais quando ambiente autorizado; guardar screenshots/logs sanitizados, revisão e hash da cópia. Regressão das demais regiões e do Hub.
4. Publicar workflow battle-hub-release.yml (tag battle-hub-N-SHA) e blue-story-windows.yml quando canal dedicado aplicável. Build do Hub não comprova conteúdo de Hoenn; conferir instalação final no game/. O EXE é launcher, não prova de gameplay. Baixar Blue-Story.exe versionado, validar estado uploaded, tamanho e SHA-256 calculado ou deixar explícito quando só metadados conferidos. Canal estável deve apontar à mesma revisão funcional.

### 8.2 Android/JoiPlay — mesma revisão S, atualização incremental
1. android-multiregion.yml já integra Kanto e Hoenn, verifica install_hoenn, compila e empacota. Atualizar todos os gates fixos 199 com inventário validado, conferir package.py também no verify de ZIP. Preservar canal multiregion e nomes legados Blue-Android-Decades-Kanto-Hoenn.zip, .zip.sha256, .update.json e *.patch.zip. Nome histórico não prova conteúdo. Não renomear sem migração do cliente.
2. Reproduzir empacotamento em ambiente autorizado (substituir SHA_REAL pelo SHA real após merge):

       python scripts/android/package.py --game-dir game --revision SHA_REAL --channel multiregion --output dist/Blue-Android-Decades-Kanto-Hoenn.zip
       python scripts/android/package.py --verify --revision SHA_REAL --channel multiregion --output dist/Blue-Android-Decades-Kanto-Hoenn.zip

   Verificar scripts e inputs reais da HEAD antes de rodar. Usar publish_updates.py com manifesto completo e --previous-manifest de cada baseline publicada ainda suportada (obter pelo GitHub Release, não inventar). Testar updater-regression e recuperação real de baseline N-1 e antiga de uso do jogador.
3. Delta somente arquivos novos/alterados/removals estritamente pertencentes ao jogo, hashes SHA-256 de entrada e saída, canal/base/result revision, ZIP seguro, staging e rollback limitado aos arquivos afetados. Sem backup completo automático, sem download integral automático, sem tocar saves, configs pessoais ou dados de outra instalação. Verificar falta de espaço, rede interrompida, patch errado, hash ruim, path traversal, symlink, colisão de nomes, repetição e cadeia incremental. Fallback integral somente com autorização explícita.
4. JoiPlay sem JSON Ruby: testar manifesto compacto e caches de compilação; imagens, áudio e paths com espaços/acento/case, teclas virtuais, toque, menus, batalha dupla, Surf/Dive, save/reload, blackout e viagem. Registro do aparelho/Android/JoiPlay/plugin e versão real. Compilar em Windows não equivale a teste de JoiPlay.
5. Instalação nova: baixar JoiPlay + RPG Maker Plugin oficiais, ZIP multiregion da tag pareada, conferir SHA, extrair e adicionar Game.exe da pasta real. Atualização existente: fechar JoiPlay, abrir Termux e entrar na pasta real que o JoiPlay usa (não inventar /sdcard). Se arquivo distribuído for ATUALIZAR-ANDROID.py:

       python ATUALIZAR-ANDROID.py --help
       python ATUALIZAR-ANDROID.py
       python ATUALIZAR-ANDROID.py --update

   Se wrapper mudou, ler manifesto/instruções e --help; não executar comandos destrutivos. Conferir Data/blue-update.json, canal, revisão e título do jogo, não editar marcador para forçar aceitação.
6. Baixar/verificar assets, manifesto e patch da tag android-multiregion-N-SHA. Conferir tamanho/hash, saída do pacote, lista de arquivos e sentinelas de regiões. Não afirmar aparelho atualizado só porque release saiu.

### 8.3 CI, merge e publicação pareada

Reusar regression.yml, android-updater-regression.yml, android-multiregion.yml, battle-hub-release.yml, blue-story-windows.yml e workflows regionais existentes. Descobrir workflow Hoenn real; adicionar um workflow Hoenn nativo apenas se não existir equivalente. Agrupar por tipo de teste, não criar um workflow por NPC. Linux testes Python/Ruby/contratos/negativos; Windows runtime autorizado/compilação/fixtures/instalação; Android empacotamento/patch e verificação sem JSON; portal e regressões globais. Não expor credenciais em PR não confiável.

    python -m unittest discover -s tests -p 'test_hoenn*.py' -v
    python -m unittest discover -s tests -p 'test_android_updates.py' -v
    python -m unittest discover -s tests -p 'test_android_multiregion.py' -v
    python -m unittest discover -s tests -p 'test_regions.py' -v
    python -m py_compile scripts/regions/install_hoenn.py scripts/regions/pilot_hoenn.py scripts/android/package.py scripts/android/publish_updates.py scripts/android/update_client.py
    ruby -c scripts/regions/HoennPilot.rb
    git diff --check
    gh pr checks NUMERO_PR
    gh run list --commit SHA_REAL
    gh run view RUN_ID --json headSha,status,conclusion,jobs
    gh run view RUN_ID --log-failed

Descobrir nomes existentes com git ls-files e garantir que cada unittest executou casos reais (0 tests não é sucesso). Executar suites completas exigidas e testes novos. Conferir conclusão, todos jobs relevantes e marcadores de cada fase, investigar logs exatos, corrigir causas. Skipped só aceitável se opcional e justificado; não cancelar CI verde de outra fase. Não fixar número de workflows por PR.

Após merge autorizado, registrar S funcional, verificar main e inputs dos YAML. Se filtros não dispararam builds, operador GH autorizado pode executar:

    gh workflow view battle-hub-release.yml --yaml
    gh workflow view blue-story-windows.yml --yaml
    gh workflow view android-multiregion.yml --yaml
    gh workflow run battle-hub-release.yml --ref main
    gh workflow run android-multiregion.yml --ref main

Usar canal dedicado Windows quando aplicável; confirmar headSha dos runs e que ambas as releases correspondem ao S, não disparar main se avançou funcionalmente. Se main avançou por docs, demonstrar equivalência funcional por diff ou revalidar revisão comum. Não criar tags/assets manualmente para simular workflow. Aguardar/conferir resultado no GitHub, ou registrar bloqueio com run IDs e retomar na próxima sessão; sem trabalho assíncrono prometido.

    gh release view TAG_WINDOWS --json tagName,targetCommitish,assets,url
    gh release view TAG_ANDROID --json tagName,targetCommitish,assets,url
    gh release download TAG_WINDOWS --pattern 'Blue-Story.exe' --dir dist/windows
    gh release download TAG_ANDROID --pattern 'Blue-Android-Decades-Kanto-Hoenn.update.json' --dir dist/android

Verificar tag resolvida para commit real (targetCommitish sozinho pode ser branch). Baixar hashes/patches e ZIP conforme necessidade e ambiente; calcular SHA-256 e conferir manifestos. Guardar URLs versionadas, não latest. H24 gates propostos HOENN_H24_WINDOWS_INSTALL_UPDATE_OK, HOENN_H24_ANDROID_INCREMENTAL_OK, HOENN_H24_RELEASE_PAIR_SAME_REVISION_OK, HOENN_H24_NATIVE_ACCEPTANCE_OK.

## 9. Matriz de aceite real e definition of done

O QA12 atual define 15 cenários por plataforma; ampliar em subcasos, sem contar casos planejados como aprovados:

| Grupo | Prova mínima Windows e Android |
|---|---|
| Início | três iniciais, dois perfis, primeira batalha rival, Pokédex, save/reload |
| Mapas | 34 rotas, todas cidades/salas, portas e bordas, ida/volta, passagem física |
| Encontros | tabelas por método, NPC/itens/treinadores, duplas, vitória/retry |
| Movimentos | Cut, Fly, Surf, Strength, Flash, Rock Smash, Waterfall, Dive; positivo/negativo e retorno |
| Magma/Aqua | toda sequência, derrota/reload e recompensas únicas |
| Clima | cenas, clima e Sky Pillar, Rayquaza e retorno |
| Ginásios | oito, puzzles, badges locais, oito esmeraldas únicas e balanceamento |
| Wally/Victory Road | tutorial, rivais, travessia, batalha/retry |
| Elite | quatro chefes e Wallace, derrota/retry e ordem |
| Hall | registro regional único, créditos, retorno, pós-Liga |
| Localização | PT-BR, NPCs/placas, atlas, Trainer Card |
| Áudio | BGM/ME/SE, loop, fade, restauração e audição |
| Saves | antigo/novo, checkpoints, migração, PC, reload e blackout |
| Regiões | viagens reais e isolamento, regressão Decades/Kanto/Johto/Sinnoh |
| Travamentos | controles, bordas, colisão, cache, crash e recuperação |
| Ampliação H18–H22 | lendários, pós-Liga, Safari, concursos, Frontier, serviços, itens, mapas opcionais |

Matriz de badges: Roxanne/Rustboro STONE→Cut; Brawly/Dewford KNUCKLE→Flash; Wattson/Mauville DYNAMO→Rock Smash; Flannery/Lavaridge HEAT→Strength; Norman/Petalburg BALANCE→Surf; Winona/Fortree FEATHER→Fly; Tate & Liza/Mossdeep MIND→Dive; Juan/Sootopolis RAIN→Waterfall. HM01–08 Emerald: Cut/Fly/Surf/Strength/Flash/Rock Smash/Waterfall/Dive; validar IDs por move no PBS Blue, não confiar em nome TM histórico.

Recibo mínimo por fase/caso (proposta; dados brutos privados):

    phase: Hxx
    status: PENDING | IN_PROGRESS | BLOCKED_SOURCE | BLOCKED_RIGHTS | BLOCKED_ENV | CI_PASSED | PUBLISHED_BOTH | DELIVERED_WITH_QA_PENDING | NATIVE_ACCEPTED
    source_sha: null
    main_baseline: null
    pr_url: null
    head_sha: null
    functional_sha: null
    maps_expected: null
    maps_installed: null
    preserved_legacy_map_ids: null
    event_inventory: {expected: null, implemented: null, pending: null}
    ci: {workflows: [], jobs: [], markers: [], failures: []}
    native_windows: {build: null, case_ids: [], receipts: [], result: NOT_TESTED}
    native_android: {build: null, case_ids: [], receipts: [], result: NOT_TESTED}
    releases: {windows: null, android: null, assets: [], hashes: [], patches: []}
    blockers: []
    next_action: null

Guardar SHA da fonte e build, MapID/posição, flag antes/depois, caso, saída de assertions, log/screenshot real sanitizado, versão da plataforma, hash de fixture de save quando apropriado. Fixtures/headless provam lógica/compilação, não renderização, áudio ou controle físico. Prints sem identidade de versão não bastam. Nenhum marcador em echo ou relatório manual substitui assert de runtime.

**Dois níveis de entrega:** MAIN_STORY_ACCEPTED = início→Hall de forma contínua em ambas plataformas, todas dependências obrigatórias e saves/viagem; HOENN_100_PERCENT_ACCEPTED = adicionalmente inventário Emerald inteiro (todos locais, eventos, serviços, pós-jogo e sete Frontier), todas pendências de direitos resolvidas por uso autorizado ou autoria própria, matrizes nativas completas, releases pareadas, zero falha crítica/alta não resolvida e nenhuma lacuna obrigatória desconhecida. Variantes ORAS/eventos externos ficam separados e declarados. Não promover por estimativa.

## 10. Otimização do Codex, retomada e documentação

1. Ler AGENTS.md, este roadmap, status e PR atual. Usar git grep/ls-files e ler apenas funções/relatórios relevantes à fase; não reabrir 373 arquivos em toda iteração. Cache da fonte por SHA, inventário e grafo reutilizáveis; invalidar por hash. Não baixar ROM/ZIP completo repetidamente. Testes rápidos direcionados primeiro, depois regressões completas; paralelizar auditorias independentes e builds, não gravar arquivos globais em paralelo.
2. Prioridade H00→H01→H02–H17→H18–H22→H23→H24; gates de instalação/saves/viagem e publicação valem em toda fase. Subdividir por corredor, mapa e dependência (H04-A, H04-B...), com commits pequenos. Evitar um PR com região inteira, ou refatoração sem ganho demonstrável.
3. Se PR já existe, continue nele; recuperar HEAD, runs, jobs e marcador ausente. Corrigir primeiro falhas comprovadas. Se main avançou, atualizar branch com segurança e revalidar. Não marcar fase concluída até resultados da HEAD; não iniciar próxima implementação se publicação pareada falhou.
4. Atualizar status público sanitizado, catálogo, roadmap e issue de acompanhamento Hoenn (pesquisar existente antes de criar uma nova). Vincular PRs, tags, SHA, jobs, testes, bloqueios, próximas tarefas. Manter barras separadas: inventário/engenharia, campanha nativa, conteúdo integral, publicação pareada. Contagem derivada de recibos; ocultar concluídas somente na apresentação, manter histórico. Não alterar status de outras regiões.
5. Após H24, atualizar README, docs de instalação e circuito, portal/região, notas de releases, links Windows e Android e instrução Termux. Verificar link do documento no README, não adicionar código/asset alheio. Nunca declarar 100% antes de todos os gates.

### Prompt inicial pronto para Codex

> Leia docs/HOENN_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md e AGENTS.md. Execute exclusivamente H00 na main atual em branch própria, reusando ferramentas existentes. Reconfirme releases Windows/Android, manifestos reais, 199 MapIDs preservados, contagem de equipes, todas as rotas 101–134, inventário fonte, backlog QA12, bloqueios e direitos. Não invente mapas ou QA. Gere relatório sanitizado e testes necessários; confirme todos os workflows pertinentes. Se H00 aprovado, abra/continue PR H01 para migração aditiva 199→N; não implemente mapa novo antes do gate. Preserve saves, MapIDs, Gary, balanceamento e demais regiões. Publique mudanças perceptíveis no Blue-Story.exe e Android multiregion da mesma revisão funcional, valide hashes e patches, atualize issue e roadmap. Minimize texto, priorize código e evidência GitHub.

### Prompt de retomada (preencher com IDs reais)

> Continue diretamente no PR atual de Hoenn, HEAD e base reais. Recupere workflows/jobs e marcadores da fase Hxx pendente, corrija todas as falhas comprovadas sem afrouxar testes. Valide inventário, caminho físico, vitória/derrota/retry, save/reload, migração dos 199 MapIDs anteriores, regressões, Windows e Android sem JSON quando aplicável. Merge apenas após CI integral aprovada; publique ambas as plataformas na mesma revisão funcional, confira assets/hashes e deltas. Atualize issue e roadmap com evidências, informe bloqueios e só avance conforme gates. Não invente QA física.

## 11. Checklist inicial de execução (nenhuma caixa equivale a aceite)

- [ ] H00: inventário e baseline atuais, evidências e direitos.
- [ ] H01: migrador 199→N, todos os consumidores compatíveis.
- [ ] H02: início e Birch.
- [ ] H03: Oldale/Petalburg/Wally.
- [ ] H04: Rustboro/Roxanne/Devon.
- [ ] H05: Dewford/Brawly/Granite Cave.
- [ ] H06: Slateport/Stern.
- [ ] H07: Mauville/Wattson.
- [ ] H08: Verdanturf/creche/túnel.
- [ ] H09: Fallarbor/Meteor Falls/Mt. Chimney.
- [ ] H10: Flannery/Norman.
- [ ] H11: Weather Institute/Fortree.
- [ ] H12: Lilycove/Mt. Pyre/Magma.
- [ ] H13: Aqua/Mossdeep/Centro Espacial.
- [ ] H14: todas 34 rotas/Surf/Dive.
- [ ] H15: Seafloor/crise.
- [ ] H16: Rayquaza/Juan.
- [ ] H17: Victory Road/Liga/Hall.
- [ ] H18: lendários/fósseis/pós-Liga.
- [ ] H19: mapas opcionais/serviços.
- [ ] H20: concursos/Pokéblocks/Secret Bases.
- [ ] H21: Frontier/Trainer Hill.
- [ ] H22: inventário final/arte/áudio/PT-BR.
- [ ] H23: viagens/saves/regressões.
- [ ] H24: homologação, releases pareadas e documentação final.

**Estado atual** — H00 teve as cinco bordas inválidas corrigidas e verificadas no Game.exe Windows. O início e o save/reload em Littleroot foram confirmados em cópia descartável no baseline. H01, a publicação pareada, a verificação física no JoiPlay e o aceite da campanha integral continuam pendentes.
