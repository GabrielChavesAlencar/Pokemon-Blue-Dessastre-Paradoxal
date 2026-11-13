# RELATÓRIO DEFINITIVO — Johto Fase 04: por que 1/13 ainda não foi liberado

**Data da verificação:** 13/11/2026  
**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**PR de implementação:** [#36](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/36)  
**Conclusão comprovada:** **0/13 fases jogáveis e 0/13 fases testadas**. **O trecho New Bark (quarto 2F → casa 1F → Elm → Rota 29) NÃO foi executado com êxito no Game.exe real.** Marcar 1/13 agora seria falso.

## A. A causa-raiz (não é a barra de progresso)

São duas dependências distintas, ambas ainda abertas:

1. **Fonte de mapas incompleta para o roteiro inicial:** a fonte `Remastered Kanto Johto Map Packv1.zip` contém 74 mapas **externos de Johto** (MapIDs originais 79–152), **42 conexões publicadas**, mas **zero eventos no conjunto Johto**, **nenhum interior New Bark necessário**, e nenhum script NPC importável. O exterior de New Bark existe, mas o quarto, a casa e o laboratório ainda precisam de **mapas RMXP reais (geometria, tileset, passabilidade, entrada/saída)**.
2. **Sem uma execução nativa de Johto comprovada:** o repositório ignora `game/` para evitar redistribuir a base Decades. O ambiente de desenvolvimento usado nesta entrega não dispõe de uma instalação jogável nativa Blue/Decades + `Game.exe` e seus gráficos, PBS e plugins. Os scripts de montagem foram exercitados com dados sintéticos, não com o mundo Johto em runtime real.

**Consequência:** compilador de eventos + mapas externos + testes Python/Ruby não equivalem a uma região jogável. Para o primeiro marco é necessária uma cópia **completa e funcional** da instalação nativa que possa iniciar, caminhar, conversar, escolher Pokémon e salvar/recarregar.

## B. Evidências materiais auditadas

- ZIP original: SHA-256 `5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715`; arquivo `Map079.rxdata` de New Bark: SHA-256 `e5ffa3a8831101eca319b2567ebc3f6cff22ac673072776a31bf69fceaefc9c9`.
- Exterior `Map079`: **22 × 48 tiles**, três camadas, tileset original 23; quatro fachadas candidatas: laboratório noroeste (5,21), casa nordeste (14,23), casa sudoeste (4,31) e casa sudeste (13,33). São **candidatas visuais**, não portas aprovadas, nem identidade confirmada da casa do jogador. Ver `docs/JOHTO_FASE_04_ENTRADAS_REAIS_V1.md`.
- New Bark ↔ Rota 29: conexão `79,West,13,104,East,0` na PBS de origem; o montador isolado elimina os dois warps artificiais correspondentes para não duplicar a transição.
- **Rota 29 ↔ Cherrygrove está ausente na fonte**, mas isso **não impede**, por si só, o primeiro marco até Rota 29; afeta a sequência para Violet/etapa seguinte.
- O contrato `data/regions/johto-new-bark-events.json` ainda traz `map_id=null`, `map_sha256=null`, coordenadas/sprites nulos e `verified_position=false`. É proposital para não inventar entradas. `data/regions/johto-interior-templates.json` também tem IDs/hashes nulos e nenhum interior aprovado.
- `scripts/regions/build_johto_interiors.py` atualmente **clona geometria de três salas nativas auditadas**, não cria automaticamente interiores HGSS fiéis. A presença dessas três cópias, por si só, não confirma colisões ou passagens.
- `scripts/regions/JohtoPilot.rb` implementa mãe, Elm, escolha de inicial e rival. **Batalha do rival permanece intencionalmente bloqueada** sem confirmação das três variantes PBS no jogo e marcador privado `Data/blue-johto-rival-ready.txt`.
- O montador `scripts/regions/pilot_johto.py` escreve na pasta isolada `.blue-work/johto-pilot`, define perfil de save próprio e emite `EXPERIMENTAL_UNTESTED`, nunca `VERIFIED_PLAYABLE`.
- Menu `Testar Johto` continua protegido até existir build real auditado. Não alterar para fingir que funciona.

## C. Auditoria da CI / regressão de Kanto

Em **13/11/2026**, a execução nativa de Kanto **já falhava na `main`**, no run [43443180745](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43443180745). O log termina em **`Kanto native test timed out` após `WaitForExit(150000)`** no passo `Compilar e testar Kanto na engine`. No PR #36 a falha também ocorreu (run [43444917488](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43444917488)), sem prova de uma regressão de Johto. **Não atribuir a causa ao novo código sem diagnóstico.**

No mesmo PR, o workflow **Blue Studio - testes e regressão** passou, bem como **Portal Blue - validar site**. Esses resultados abrangem código/contratos/sintéticos e **não validam New Bark rodando**. A CI de Kanto deve diagnosticar logs/prints após o timeout ou ter prova de saída do `Game.exe`, sem desativar o gate para forçar merge.

**Status do PR #36:** aberto, sem merge na main. Este relatório e os novos testes ficam na branch do PR até regressões serem esclarecidas.

## D. Inventário de implementação — necessário para 1/13

| Requisito observável | Fonte/código preparado | Prova real | Estado |
|---|---|---|---|
| Exterior New Bark no RMXP | Map079 e auditoria SHA | Visual da origem, sem gameplay | PARCIAL |
| Transição New Bark ↔ Route 29 | Conexão PBS remapeada | Game.exe ainda não percorreu a borda | PARCIAL |
| Quarto do jogador 2F | Layout simbólico + clonador nativo | Sem mapa/colisões autenticados | BLOQUEADO |
| Casa do jogador 1F | Template + evento da mãe | Sem interior/escada validados | BLOQUEADO |
| Laboratório de Elm | Template + Ruby handlers | Sem interior/porta/NPC no jogo | BLOQUEADO |
| Identidade da casa do jogador | Quatro candidatos de fachada | Falta conferir qual casa é correta | BLOQUEADO |
| Spawn dentro do quarto | Validador de coordenadas | `start.x/y=null`, sem passabilidade nativa | BLOQUEADO |
| Warps 2F↔1F↔Town↔Lab | Compilador e checklist | Eventos sem x/y/arrival reais | BLOQUEADO |
| Falas mãe/Elm | `JohtoPilot.rb` | Sem interação de NPC real | PARCIAL |
| Seleção Chikorita/Cyndaquil/Totodile | `choose_starter` | Sem GameData/PBS runtime comprovado | PARCIAL |
| Rival | Três rascunhos PBS, handler protegido | Sem batalha real, pronto=false | BLOQUEADO |
| Caminhar, voltar, salvar/recarregar | Cópia experimental projetada | Sem Game.exe Johto executado | BLOQUEADO |
| Preservar Kanto/Decades/saves | Diretório separado, hashes, guards | Testes sintéticos passam; regressão nativa Kanto com timeout | PARCIAL |

## E. Arquivos já existentes no PR #36

- `JOHTO_EXPORTAR_BASE_PILOTO.bat` e `scripts/regions/export_johto_pilot_inputs.py`: exportam somente dados nativos em ZIP **privado**, excluindo executáveis, scripts, plugins, saves e segredos; `sprites` inclui personagens/treinadores.
- `JOHTO_VERIFICAR_PRIMEIRO_PILOTO.bat` / `scripts/regions/inspect_johto_pilot_readiness.py`: conferem a topologia dos **12 eventos**, 5 mapas simbólicos, hashes, sprites, destinos, spawn e borda PBS; produzem lista explícita de pendências. "Pronto para montar" **não** significa "jogável".
- `JOHTO_MONTAR_PRIMEIRO_PILOTO.bat` / `scripts/regions/assemble_johto_first_playable.py`: só montam `.blue-work/johto-pilot` quando a verificação dos arquivos locais passar.
- `tests/test_johto_first_playable_readiness.py`: 5 testes sintéticos passaram na CI do Blue Studio, incluindo prevenção de colisões, erro de sprite/posição, topologia trocada e conexão PBS única.
- Documentos `docs/JOHTO_FASE_04_ENTRADAS_REAIS_V1.md`, `docs/JOHTO_FASE_04_ENVIAR_BASE_NATIVA.md` e `docs/JOHTO_ETAPAS.md`.

Nenhuma dessas entregas alterou `game/` original ou constituiu evidência de jogabilidade real.

## F. Procedimento exato para desbloquear 1/13 no Windows

**Todo conteúdo da fonte deve permanecer no PC e em `.blue-work/`; verificar direitos dos assets antes de distribuir jogo ou qualquer ZIP público.** Caso ainda não exista instalação Blue/Decades local, primeiro usar o instalador do projeto e confirmar `game/Game.exe`, `game/Data`, `game/Graphics`, `game/PBS` e plugins.

1. Atualizar branch do PR #36 ou aplicar arquivos nela; ao executar pela main, verificar antes se PR foi integrado. **Não fazer merge ignorando testes.**
2. Copiar o mesmo ZIP original do Map Pack v1 para `.blue-work/johto-source/original.zip` (preservar hash). Não subir para o GitHub público.
3. Executar `JOHTO_PREPARAR_PRIMEIRA_FASE.bat` → auditar 74 mapas, remapear 42 conexões em IDs locais livres, gerar `.blue-work/johto-staging` sem tocar `game/`.
4. Executar `JOHTO_PREPARAR_NEW_BARK.bat auditar` → gerar candidatas de salas nativas. Abrir `.blue-work/johto-native-room-candidates.json` e **inspecionar visualmente as três salas**. Preencher somente após revisão `.blue-work/johto-interior-templates-review.json` com **três MapIDs nativos distintos**, hashes exatos, três IDs livres e os dois flags de revisão verdadeiros. Não inventar dimensões/IDs.
5. Executar `JOHTO_PREPARAR_NEW_BARK.bat montar` → criar três rascunhos em `.blue-work/johto-staging-interiors` e o manifesto de eventos ligado em `.blue-work/johto-new-bark-bound.json`.
6. **Editar e validar a geometria dos rascunhos**, garantindo quarto/casa/Elm distintos e utilizáveis. Identificar qual fachada exterior corresponde à casa do jogador; registrar posições reais das portas, chegada de cada warp, sprite de cada NPC, local de Elm/iniciais e spawn no quarto. No manifesto ligado, preencher `x/y`, `arrival_x/y`, `sprite`, `verified_position=true` **apenas após inspecionar mapas e passagens**. O `start.passability_verified=true` exige inspeção coerente de passabilidade (e confirmação final no runtime).
7. Executar `JOHTO_VERIFICAR_PRIMEIRO_PILOTO.bat`. Corrigir todas as entradas de `.blue-work/johto-phase04-acceptance.json`. Bordas New Bark–Rota 29 devem ser geridas apenas pela conexão PBS real.
8. Executar `JOHTO_MONTAR_PRIMEIRO_PILOTO.bat`. Se o montador bloquear ou reclamar de hashes antigos, reavaliar os dados; **nunca alterar checks/flags só para passar**.
9. Abrir **somente** `.blue-work/johto-pilot/Game.exe` no Windows. Registrar logs e capturas de spawn, quatro transições internas, Elm, escolha de inicial, travessia de fronteira, retorno e save/reload. Conferir separação de perfil de save da instalação principal.
10. Validar/compilar as **três versões PBS do rival** na cópia, executar batalha via engine e só então liberar marcador local do rival. Validar derrota/vitória, não duplicação de inicial e save após eventos.
11. Repetir regressões do Decades/Kanto e identificar a causa do timeout nativo atual. Corrigir a falha se reproduzível, sem desabilitar gates.
12. **Só com evidência observável de gameplay completo em Game.exe isolado:** marcar `gameplay_playable=true` na fase 04, atualizar barra para **1/13 jogáveis** e anexar prova no GitHub. **Barra TESTADAS** só vira 1/13 após QA nativo integral aprovado.

**Não há requisito de concluir Rota 29 → Cherrygrove para o trecho New Bark → Rota 29**, mas a ligação será obrigatória na etapa subsequente.

## G. Critérios objetivos de aprovação

| Teste de aceite em Game.exe (cópia) | Resultado atual |
|---|---|
| Novo jogo abre **dentro** do quarto 2F | NÃO EXECUTADO |
| Descer escada para 1F e voltar | NÃO EXECUTADO |
| Falar com mãe e manter flag de história | NÃO EXECUTADO |
| Sair da casa, voltar e manter coordenadas corretas | NÃO EXECUTADO |
| Entrar/sair do laboratório de Elm | NÃO EXECUTADO |
| Escolher exatamente 1 entre 3 iniciais e persistir | NÃO EXECUTADO |
| Encontrar rival, batalhar com motor Blue e persistir | NÃO EXECUTADO |
| Atravessar e voltar na borda New Bark–Rota 29 | NÃO EXECUTADO |
| Salvar, fechar, reabrir, carregar sem corromper | NÃO EXECUTADO |
| Kanto/Decades e saves anteriores intactos | SINTÉTICO OK; CI NATIVA KANTO PENDENTE |

Se um desses testes essenciais falhar, o marco continua **0/13**. Nunca publicar prova fabricada, teletransporte falso nem substituição do jogo original.

## H. Riscos ainda não resolvidos

1. Licença/autorização da arte externa, tilesets e músicas do Map Pack — não inferir direito de redistribuição apenas porque o recurso é público.
2. Fidelidade visual dos três interiores: clonagem de salas nativas é somente scaffolding; requer criação ou edição autoral de layout.
3. Passagem e colisões RMXP: bits de tileset não equivalem a passo real em Pokémon Essentials com personagens e eventos.
4. Coordenadas de exterior podem ser fachadas, não tile acionável; não colocar `verified_position=true` sem inspeção.
5. Compilação PBS de treinador/escolha de inicial pode revelar incompatibilidade entre plugins e versão Essentials local.
6. Um pipeline que só prepara JSON, PNG e mapas em staging não pode validar início, batalha e persistência de save.
7. A falha anterior de Kanto é **timeout nativo**, não erro de pytest; requer logs/artefatos de Windows.

## I. Conclusão e insumo mínimo

**A Fase 04 não foi concluída.** Trabalho de infraestrutura foi feito, mas **não existe evidência legítima para elevar a barra a 1/13**. O insumo mínimo que falta para finalizar com testes é uma instalação local legítima, íntegra e verificável do Blue/Decades — dados, gráficos, PBS, plugins e runtime `Game.exe` — e auditoria/montagem real dos três interiores.

Se for necessário compartilhar dados para análise privada, executar `JOHTO_EXPORTAR_BASE_PILOTO.bat sprites` no próprio PC e anexar **`.blue-work/johto-pilot-inputs.zip` apenas em conversa privada**. Esse pacote não inclui `Game.exe` nem saves, portanto permite auditoria de geometria, **não** execução nativa nesta sessão. O jogo real deve ser testado em Windows ou em uma CI Windows configurada com sua própria base legítima.

**Status final confiável:** `Fases JOGÁVEIS 0/13` · `Fases TESTADAS 0/13` · `Fase 04 PARCIAL/BLOQUEADA`.
