# Aplicar eventos de Pokémon FireRed no Pokémon Blue: Dessastre Paradoxal

**Data:** 12/11/2026 · **Alvo:** RPG Maker XP + Pokémon Essentials v21.1 / Pokémon Decades · **Natureza desta entrega:** documentação e auditoria; nenhum evento é instalado no jogo por este documento.

## 0. Referências obrigatórias e estado atual

- [Estudo técnico completo dos 425 mapas do FireRed](ESTUDO_EVENTOS_MAPA_POKEMON_FIRERED_RPG_MAKER_XP.md).
- [Extrator Python do catálogo](../scripts/regions/extrair_eventos_firered.py).
- [Plano funcional das regiões v2](PLANO_REGIOES_DESSASTRE_V2.md), prioritário para regras de história, HMs, especiais, liga, viagem e balanceamento.
- [Estado das 16 etapas de Kanto](KANTO_ETAPAS.md), [Fase 09](KANTO_FASE_09.md), [feedback dos testes](KANTO_FEEDBACK_TESTES_MANUAIS_2026-11-12.md), [testes do piloto](KANTO_TESTE_EXPERIMENTAL.md).

**Foto da main em 12/11/2026:** 40 mapas nas fases anteriores e 11 cenários adicionais, total 51 mapas no piloto. **Os 11 mapas da fase 09 estão intencionalmente sem qualquer evento**, inclusive portas, NPCs, insígnias e cura. O progresso funcional permanece **08/16 (50%)**, e o aceite **01/16 (6,25%)**. Documentar como implementar **não significa** que a implementação ocorreu nem que está autorizada para a fase 09.

## 1. O que está sendo importado e o que não está

Há **duas fontes diferentes**, que não devem ser misturadas:

1. **`pret/pokefirered`** é a decompilação GBA para estudar o comportamento canônico de cada evento. Tem índice de 425 mapas, estruturas `map.json` e scripts `.inc`. **Não** é a base de mapas `.rxdata` usada pelo jogo instalado.
2. **Essentials FRLG 21.1 / 1.1**, definido em [`data/regions/kanto-source.json`](../data/regions/kanto-source.json), é a fonte local de mapas RPG Maker do piloto. O manifesto registra hash e créditos. O instalador e a auditoria atuais trabalham com **IDs dessa fonte**, não os IDs `MAP_*` do GBA.

Não distribuir ROM, arquivos de jogo de terceiros ou saves em commits. Criar apenas scripts, documentação, tabelas derivadas e testes permitidos. Uma cena original precisa ser **traduzida** para o engine correto, não colada como assembly do GBA no Ruby.

## 2. Preparação em uma cópia isolada

1. Atualize sua cópia de `main` e feche o Game.exe. Faça backup dos saves e de `game/` antes de qualquer teste; não versionar esses dados no Git.
2. Instale o jogo pelo fluxo documentado em [INSTALACAO.md](INSTALACAO.md). Não modifique os dados originais do Decades.
3. Pelo menu do jogo principal use **Testar Kanto** (se disponível), ou na raiz do repositório execute `KANTO_JOGAR_EXPERIMENTAL.bat`. Para recriar a cópia experimental, execute `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`. Alternativamente, execute `python scripts/regions/pilot.py --launch`.
4. Verifique `.blue-work/kanto-pilot/` e o perfil de save **Kanto Piloto**. O piloto usa uma cópia separada; não presumir que o save do Decades foi alterado.
5. Confirme que `data/regions/kanto-source.json` ainda possui os **11 IDs `preview_only`**; o verificador deve barrar qualquer evento nesses IDs até a decisão explícita de avançar a fase 09.

## 3. Gerar inventário dos eventos do FireRed

O extrator é **somente leitura** da árvore decompilada; a saída não inclui uma ROM, não cria RXDATA, não executa scripts e não concede flags.

```powershell
git clone https://github.com/pret/pokefirered.git .blue-work/pokefirered-reference
python scripts/regions/extrair_eventos_firered.py .blue-work/pokefirered-reference --out .blue-work/kanto-event-audit
```

Ele gera:

| Saída | Para que usar |
|---|---|
| `eventos_detalhados.csv` | Revisar linhas por mapa e tipo, importar em planilhas |
| `eventos_detalhados.json` | Automatizar conferência de objetos, posições, warps e triggers |
| `mapas_resumo.json` | Obter quantidades, metadados, flags e scripts por mapa |
| `INVENTARIO_COMPLETO_FIRERED.md` | Ler checklist por mapa + referência de todos os registros explícitos |

Se o repositório `pret` mudar, registrar o **commit de origem** para que a auditoria seja reproduzível. A contagem 425 é dos mapas **cadastrados** no índice; não é contagem de eventos nem garantia de que todos foram revisados semanticamente. O extrator ignora a interpretação semântica de scripts globais, tabelas de encontros e efeitos do engine, que precisam de revisão manual.

## 4. Mapear IDs sem sobrescrever Decades

1. Ler `data/regions/kanto-source.json` (`maps` e `preview_only`).
2. Ler `.blue-work/kanto-pilot/Kanto pilot.json` após gerar o piloto: `maps` associa os IDs **da fonte Essentials FRLG** aos MapIDs reais da cópia.
3. Conferir cada `Data/MapXXX.rxdata` e `MapInfos.rxdata` da **cópia**, nunca editar a fonte nem o `game/` principal inicialmente.
4. Para eventos extraídos do GBA, criar uma tabela intermediária: `fire_red_map,fire_red_script,fire_red_flag,essentials_source_map_id,blue_map_id,blue_event_id,trigger,priority,condicoes,teste,status`.
5. Não presumir que `dest_warp_id` de FireRed é um MapID: é o índice do warp de destino no mapa GBA. Resolver a coordenada e o ID do mapa RMXP separadamente.
6. Reservar namespace `KANTO_*` para flags, estados e chaves de prêmio. Não reutilizar automaticamente switches/variáveis do Decades. Conferir saves antigos e migração.
7. Não escrever nos 11 mapas marcados `preview_only` enquanto a restrição da Fase 09 estiver ativa.

## 5. Converter um evento: receita que deve ser repetida por registro

1. Localizar no inventário o objeto, trigger, warp ou placa e seu mapa de origem.
2. Abrir o `scripts.inc` do mesmo mapa e seguir labels, branches, flags e variáveis até o resultado final. Conferir também scripts globais chamados.
3. Identificar **quando dispara**: Action Button, Player Touch, Event Touch, Autorun, Parallel Process ou line-of-sight do Essentials.
4. Identificar página(s), prioridade, movimento, gráfico, direção, colisão, distância de visão e condições de visibilidade; o FireRed pode usar flags invertidas de esconder NPC.
5. Construir **uma matriz de estados**: antes, durante, vitória, derrota, fuga, inventário cheio, repetição, save/reload e após troca de região. Qualquer flag de vitória só muda após sucesso.
6. Implementar em `scripts/regions/` se for comportamento reutilizável, ou em eventos RXDATA **na cópia isolada** se for simples. Manter funções com retorno claro e sem mudar estado global em caso de falha.
7. Compilar PBS apenas quando forem alterados dados PBS, usando o modo Debug do Essentials; não confundir isso com validação de eventos.
8. Estender a verificação estrutural (`scripts/regions/verify_pilot.py`) e um teste nativo para provar existência de evento, scripts/condições, resolução de transferências e ausência de colisões.
9. Fazer teste **gráfico no Windows** e salvar/reabrir; a CI estrutural não prova caminhada, linha de visão nem UI real.
10. Registrar numa tabela de aceitação o commit, MapID, EventID, origem, teste, status e evidência. Somente então promover do piloto isolado para instalação opcional.

## 6. Ordem recomendada, eventos concretos e critérios

| Lote | Áreas | Eventos a implementar depois de auditados | Critério mínimo |
|---|---|---|---|
| A | Pallet, Oak Lab, Rota 1 | Oak impede saída; três iniciais; rival; portas de casas/lab; Potion do funcionário do Mart | Oak dispara uma vez, duas posições de entrada, starter e batalha persistem |
| B | Viridian, Rota 2, Viridian Forest, Pewter | Parcel, Centro e Mart, treinadores com visão, Brock, Boulder Badge, itens ocultos | Todas as portas ida/volta, nenhum treinador obrigatório é atravessado, badge única |
| C | Rotas 3–4, Mt. Moon | Treinadores, Rockets, fósseis, andares, escadas e itens | Sem softlock, sem itens duplicados e todos os andares retornáveis |
| D | Cerulean, 24–25, Bill | Rival e Rocket, Nugget Bridge, Bill e S.S. Ticket, Misty | Estados corretos, passagem e itens sem duplicação |
| E | Rotas 5–6, Vermilion, S.S. Anne | Portarias, navio, capitão e Cut, Surge e puzzles | Ticket/embarque/saída + trava das lixeiras + HM e badge no estado correto |
| F | Lavender, Celadon, Saffron | Game Corner e esconderijo Rocket, Silph Scope, fantasma Marowak, Poké Flute, Snorlax, Silph Co., Erika e Sabrina | Triggers, teletransportes, Master Ball e progressão irreversível correta |
| G | Fuchsia, Safari, Seafoam, Cinnabar, Viridian | Safari e Surf, Gold Teeth e Strength, Koga, blocos/correntes de Seafoam, Mansion, Blaine, Giovanni | Puzzles resolúveis e oito badges distintas |
| H | Rotas 22–23, Victory Road, Indigo Plateau | Rival, bloqueio individual das 8 badges, boulders, Elite Four e campeão | Percurso completo, Hall of Fame e liga única |
| I | Pós-jogo e Ilhas Sevii | Bill/Celio, Ruby e Sapphire, Rocket Warehouse, passagens, lendários, Tanoby e especiais | Pós-jogo sem duplicar flags; viagens reversíveis |

**A fase 09 de Celadon permanece somente como prévia de cenário:** o lote F é um **roteiro futuro**, e não uma instrução para ativar eventos nessa fase agora.

## 7. Resolver primeiro os três problemas já relatados

### MAN-01: interiores/portas

- Auditar todos os `warp_events` do FireRed, os `Transfer Player` já existentes no `RXDATA` de origem e o mapeamento da cópia.
- Criar/instalar o mapa interior **antes** de criar a porta. Se não existe no manifesto, registrar pendência; não transformar porta em ligação incorreta com Decades.
- Testar ida/volta e direção/posição de chegada para casas, Centro, Mart, laboratório, ginásio e portarias.
- Fazer verificador de `target_map_id` e coordenadas dentro do mapa, além de checagem de retorno; passagem visível exige teste manual.

### MAN-02: treinadores

- A auditoria atual constatou que o piloto tem NPCs criados com `trigger=0` (interação), logo isso **não prova** detecção automática; adaptar os eventos de visão usando os mecanismos existentes do Essentials e a distância correta, verificando obstáculos.
- Manter `KANTO_<mapa>_<evento>` como chave estável da vitória; não deixar derrota/fuga registrar sucesso ou repetir dinheiro/item.
- Somente lutar como **bloqueio de história** se a fonte e a progressão exigirem. Treinadores normais não devem virar barreiras artificiais.
- Testar se o NPC vê o jogador na direção correta, se não vê através de parede, se não dispara duas vezes e se persiste após save.

### MAN-03: dois painéis de conquistas

- Painel A: oito insígnias e respectivos líderes de Kanto.
- Painel B: conquistas por região, mantendo marcadores próprios para Alola, Hisui e Decades.
- Ler do estado único `BlueRegions`, sem conceder badges pela UI; conferir contador após save/reload e regras HMs da região atual.
- Não aumentar o contador de etapas só por criar layout sem teste gráfico.

## 8. Estados especiais que exigem cuidado

- **Snorlax Rotas 12 e 16:** exige Poké Flute; resolver captura/derrota/fuga conforme script canônico; não ocultar NPC prematuramente.
- **Tower 6F:** Marowak/fantasma e Silph Scope dependem dos marcos da campanha; não transformar encontro obrigatório em batalha comum sem revisar pré-condições.
- **Rocket Hideout B4F / Silph Co 11F:** portas, card key, bosses e recompensas dependem da sequência; Giovanni e presidente não concedem prêmios antes do confronto.
- **Victory Road:** pedras, botões, layout e passabilidade; salvar estado conforme comportamento auditado, sem deixar mapa impossível de resolver.
- **Seafoam B4F:** correnteza só para com pedras nas posições certas; validar Articuno, fuga e persistência.
- **Power Plant:** Zapdos e Electrode são encontros estáticos distintos; não confundir seus estados.
- **Ilhas Sevii:** Celio/Ruby/Sapphire e Rocket Warehouse têm dependências de pós-jogo separadas. Não desbloquear antes da Liga por causa de item copiado.

## 9. Como testar, promover e reverter

Primeiro gerar a cópia e rodar a auditoria estrutural:

```powershell
python scripts/regions/pilot.py
python scripts/regions/verify_pilot.py --help
python scripts/regions/install_kanto.py --help
```

Use `--help` para confirmar os argumentos atuais antes de executar importação. O instalador `install_kanto.py` opera inicialmente como **dry run**, com checagens de integridade e recusa de sobrescrita suspeita; só executar aplicação efetiva após revisar o diff, confirmar backup, conferir hashes e testar a cópia. Não fazer force-push.

Checklist mínimo por evento:

- [ ] Script de origem e suas dependências documentados
- [ ] MapID/EventID resolvidos na fonte Essentials e no destino
- [ ] Prioridade, trigger, line-of-sight, colisão e movimento corretos
- [ ] Flags e prêmios idempotentes; derrota/fuga não concluem vitória
- [ ] Portas e escadas com ida e volta verificadas
- [ ] Save novo, save antigo, reload e troca de região preservados
- [ ] Regras regionais de HMs, especiais e balanceamento mantidas
- [ ] Testes estruturais e testes nativos concluídos
- [ ] Caminhada e batalha reais no Game.exe Windows verificadas
- [ ] JoiPlay verificado somente após aprovação no Windows
- [ ] Rollback de uma instalação testado antes de promovê-la
- [ ] Resultado, commit e evidências registrados no checklist

**Duas barras independentes:** *construção* = implementado/planejado e *validação* = aprovado/planejado. Nenhum sucesso de teste simulado pode ser contabilizado como aceitação manual.

## 10. Próxima execução segura no projeto

1. Rodar o extrator e congelar o commit da referência pret.
2. Cruzar seus registros com os 51 MapIDs da cópia piloto; excluir os 11 `preview_only` de qualquer plano de escrita.
3. Corrigir primeiro o **MAN-01** na parcela Pallet–Pewter; documentar cada porta bidirecional.
4. Depois corrigir **MAN-02**, registrando a line-of-sight e os estados de derrota/vitória.
5. Preparar o **MAN-03** sem mudar flags de concessão.
6. Repetir o caminho manual e testes de save/reload para avaliar os itens 02/03/07/08 do roteiro de 16 etapas.
7. Só quando autorizado retomar eventos de Celadon/Fase 09 e adicionar os grandes blocos históricos.

**Documentação adicionada ao GitHub não muda o jogo nem transfere automaticamente eventos para o executável.** O objetivo deste guia é transformar o estudo em tickets reproduzíveis sem perder nenhuma referência de mapa e sem corromper a campanha Decades.
