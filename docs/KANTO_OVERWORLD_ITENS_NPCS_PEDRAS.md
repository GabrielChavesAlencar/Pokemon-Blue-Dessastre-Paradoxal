# Kanto — Recuperação de itens, NPCs e pedras dos mapas

## Diagnóstico confirmado

O importador de Kanto (`scripts/regions/pilot.py`) copia o terreno da fonte **Essentials FRLG**, mas monta uma nova tabela de eventos. Até esta fase, só preservava principalmente transferências, equipes de treinadores e poucos scripts de progresso. Assim, a maioria das **Poké Bolas de itens**, dos **NPCs comuns** e das **pedras de campo** não era importada. O detonado de Kanto em [KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md), especialmente as seções 2, 4 e 6, lista os conteúdos que precisam existir.

## Primeira fase implementada — objetos simples com fonte verificável

O módulo `scripts/regions/kanto_overworld.py` recupera eventos dos mapas **ativos** da fonte, preservando exatamente os respectivos **MapID de origem, EventID, X/Y e gráfico**. O importador executa somente callbacks seguros, sem copiar scripts, recompensas, switches ou variáveis estrangeiras:

1. **Itens no chão:** identifica a convenção original `Item:ITEM` ou o evento compilado `pbItemBall(:ITEM, quantidade)`. Somente importa IDs existentes no PBS do Blue. Ao recolher, confere espaço na Bolsa, entrega a quantidade original, registra `pilot_items` da campanha Kanto e liga o self-switch A para que desapareça de forma persistente. Se a Bolsa estiver cheia, permanece no chão. A coleta anterior de saves antigos é reconhecida e não premia novamente.
2. **NPCs de ambientação:** recupera apenas NPCs visíveis com diálogo *literal*, sem efeitos colaterais ou opções. Mantém o diálogo original da fonte, que pode estar em inglês — tradução e eventos de missão precisam de auditoria separada. Não transforma treinadores, líderes ou NPCs especiais em personagens genéricos.
3. **Rock Smash:** reconhece apenas eventos com o marcador nativo `SmashRock`. Preserva o gráfico da rocha e chama `pbRockSmash`, `pbSmashThisEvent` e `pbRockSmashRandomEncounter`, usando o sistema existente do Essentials 21.1.
4. **Strength:** reconhece `StrengthBoulder` e cria um evento sólido de `Player Touch` com `pbPushThisBoulder`. A engine só o empurra quando o HM estiver efetivamente disponível/ativado conforme suas regras.
5. **Auditoria:** cada compilação grava `Data/blue-kanto-field-events.json` no **piloto gerado**, com os eventos realmente importados, posições, categorias, itens ignorados por não existirem no catálogo **e a lista `pending_review` de NPCs/objetos originais ainda omitidos**. `scripts/regions/verify_pilot.py` valida os callbacks e as coordenadas. O relatório não fica no repositório porque depende dos mapas reais da fonte FRLG instalada localmente.

O núcleo da história já implementado continua prioritário. Itens, pedras e NPCs não podem substituir eventos adaptados de Oak, rival, centros Pokémon, lojas, líderes, Elite Four e Liga.

## Restrições importantes e o que ainda falta

**Isto ainda não equivale a Kanto integral.** Há **142 mapas previstos no piloto, dos quais 45 são prévias sem eventos**, como documentado em [KANTO_FASE_14.md](KANTO_FASE_14.md). O importador não deve inserir eventos nessas prévias ou reabrir locais com regras de história ainda ausentes. Além disso, mapas que já usam listas fechadas de eventos (partes de Celadon, Fuchsia, Saffron, Cinnabar e Victory Road) continuam com suas listas protegidas. Portanto, itens ou NPCs de tais locais podem continuar ausentes até a aprovação de cada etapa.

### Pendências por conteúdo do detonado

| Local ou sistema | O que falta além desta importação | Dependência |
|---|---|---|
| Pallet, Rotas 1/2/3, Viridian Forest e Mt. Moon | Auditar o inventário gerado; NPCs de item especial, tutores, itens ocultos e diálogos de missão | Original `MapXXX.rxdata` |
| Cerulean, Bill e Rotas 24/25 | Eventos de missão, Nugget Bridge, presentes e confrontos especiais | Auditoria de estados e treinadores |
| Route 11, Diglett's Cave e Rock Tunnel | Liberar mapas ainda não implementados, Flash, Rock Smash e respectivos bloqueios | HMs e importação de mapas |
| Celadon, Hideout, Tower e dois Snorlax | Completar zonas de prévia, scripts condicionados, itens, NPCs e obstáculos | Eventos de história |
| Fuchsia, Safari e casa do Warden | Gold Teeth, HM04 Strength e HM03 Surf com condições corretas | Safari e Warden ainda não jogáveis integralmente |
| Seafoam e Power Plant | Rochas Strength, correntes de água e entradas | Mapas de prévia e puzzles |
| Victory Road | **Substituir o mecanismo experimental que abre barreiras diretamente** por pedras que são empurradas até posições reais; liberar puzzle somente com as permissões e HM corretos | Estudo de coordenadas e switches da fonte |
| One Island / Ember Spa | Obter HM06 Rock Smash no lugar original | Implementação de Sevii |

O detonado estabelece que **HM04 Strength** é obtido com o Warden em Fuchsia e **HM06 Rock Smash** em Ember Spa, One Island. Sem esses eventos no jogo, aparecerem pedras nos mapas não significa que os HMs já estejam disponíveis legitimamente. **Não** conceder um HM de graça, liberar obstáculos pelo menu de teste ou substituir o puzzle por um botão falso.

### Critérios de aceite

- [x] Importador isolado reconhece categorias seguras por comandos e nomes originais e não inventa objetos/posições
- [x] Pickups têm flags locais e página de desaparecimento; proteção contra Bolsa cheia e repetição
- [x] Rochas padrões usam callbacks físicos da engine; NPC simples mantém texto original sem executar script não auditado
- [x] Relatório JSON de itens, NPCs e obstáculos realmente gerados
- [ ] Conferir quantidades por mapa no `Data/blue-kanto-field-events.json` gerado da fonte original
- [ ] Caminhar e coletar objetos no `Game.exe`, salvar e recarregar no Windows
- [ ] Testar Rock Smash, Strength e colisões, primeiro com os HMs legítimos
- [ ] Auditar eventos especiais das áreas em prévia; traduzir NPCs; liberar as fases de história
- [ ] Reproduzir testes no Android/JoiPlay e verificar regressão regional

## Correção de inicialização — gráficos opcionais ausentes (14/11/2026)

O erro real reportado na abertura do Testar Kanto foi `ValueError: Missing actor graphic: NPC_Hiker`. Ao restaurar NPCs comuns, o importador começou a exigir sprites de personagens que a fonte FRLG extraída pode não fornecer, interrompendo a criação de toda a cópia antes do `Game.exe` abrir.

O importador agora:

- Verifica primeiramente o sprite do pacote FRLG original; se ele não estiver lá, reutiliza **somente um PNG de mesmo nome já existente na pasta de personagens da instalação do Blue**, nunca um substituto arbitrário.
- Se um evento **opcional** ainda não possuir gráfico, registra o MapID/EventID/nome/posição em `Data/blue-kanto-field-events.json → missing_graphics`, mostra aviso e deixa esse evento pendente, **sem bloquear a geração do restante de Kanto**.
- Se faltar sprite de evento de história, treinador obrigatório ou porta, o erro continua explícito; não se mascara falha em fluxo crítico.
- Testes simulam especificamente o NPC `NPC_Hiker` ausente e garantem que outros erros não sejam engolidos. `verify_pilot.py` rejeita qualquer evento registrado como ausente mas importado como obstáculo invisível.

**Para aplicar o reparo:** atualize a `main` local, feche o piloto e execute `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`. O piloto antigo é preservado, e a nova cópia terá sua própria pasta `kanto-pilot-revisao-...`. Em caso de falha, consulte o log e o nome exato do próximo sprite ausente.

**Limitação:** não há garantia de que o NPC `NPC_Hiker` aparecerá até existir um PNG válido de mesmo nome; a correção primeiro recupera a abertura do piloto sem inventar sprites.

## Como testar

1. Usar a **fonte editável FRLG com SHA-256 fixado** em `data/regions/kanto-source.json`, sem substituí-la por outro Map Pack.
2. Reconstruir o piloto isolado por `KANTO_JOGAR_EXPERIMENTAL.bat`. O `Game.exe` instalado anteriormente **não é atualizado** apenas com um commit GitHub.
3. Rodar `python -m unittest tests.test_kanto_overworld -v`, `python -m unittest discover -s tests -v`, `python scripts/regions/verify_pilot.py --game .blue-work/kanto-pilot` e o teste nativo previsto na CI.
4. Abrir `.blue-work/kanto-pilot/Data/blue-kanto-field-events.json`: verificar quais objetos existem por `source_map`, `event` e `x/y`, e quais itens foram pulados por ID ausente.
5. Verificar persistência, mapa ativo, item na Bolsa, estados dos HMs, NPCs visíveis e retorno entre mapas.

**Observação de CI:** a verificação nativa depende do arquivo de origem FRLG auditado. Caso o download diverja do SHA pinado, isso é bloqueio de construção, e não prova de aprovação dos novos eventos.
