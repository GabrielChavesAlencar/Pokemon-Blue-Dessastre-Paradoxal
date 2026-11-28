# AD03 — desenho 2D de Alola e primeiro recorte: Melemele

Proposta sem implementação. Use [inventário AD02](ALOLA_AD02_INVENTARIO_E_PROGRESSAO.md),
[atlas AD05](ALOLA_AD05_ATLAS_VISUAL_E_TILES_KANTO.md) e [matriz AD01](ALOLA_AD01_FONTES_E_DIREITOS.md).

| Módulo | Trecho e evidência de saída | Não pode acontecer |
|---|---|---|
| D01 | Casa/Hau’oli Outskirts ↔ R01 ↔ Iki Town ↔ Mahalo Trail; inicial no percurso de USUM, ocorrência da ponte, festival e procura do laboratório. | Dar dois iniciais, remover o grupo do visitante, repetir evento de ponte, ou deslocar o personagem para uma saída que ele não percorreu. |
| D02 | R01: laboratório/centro/escola com retorno ↔ Hau’oli City (escolher setores separados para zona comercial, praia e marina) ↔ R02 ↔ Verdant Cavern. | Transformar escola ou prova em menu; atravessar gate antes da prova; renderizar marinas/praias como portais sem retorno. |
| D03 | Prova de Ilima, R03 e Melemele Meadow, ida a Iki Town para Grande Prova de Hala; habilitar Tauros em obstáculos verificáveis. | Tratar Hala como segunda esmeralda, deixar quebra de pedra retroagir para outra região, pular a entrada/saída de R03, ou vender a travessia a Akala antes de seu lote. |

Ordem e áreas cruzadas com o
[percurso registrado de USUM](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Ultra_Sun_and_Ultra_Moon).
D01–D03 são três recortes de construção que formam **uma entrega futura**.
A primeira passagem e o retorno às áreas abertas são jogáveis; desvios
não incluídos exibem fronteira clara. Não liberar o barco ou Mantine
Surf para um destino que ainda não existe. R02 não precisa ter todos
os interiores opcionais ativos para provar o caminho, mas as lacunas
precisam constar no relatório.

## Da referência para a malha 2D

1. Desenhar o grafo com bordas, ordem das saídas, posição relativa dos
   marcos, caminho jogável e áreas altas/baixas. Para R01 separar seus
   setores, sem encurtar o retorno casa–Iki. Nas passarelas testadas,
   alinhar entrada, saída e direção do personagem nas duas pontas.
2. Usar só a família de tiles/autotiles de Kanto já disponível e auditada
   no Blue como padrão para mapas sem versão RPG Maker aproveitável.
   Costa: areia, água e borda. Vilas: terreno, cercas, casas e escadas.
   Cavernas: rocha, vegetação e entradas. Em falta de peça idêntica,
   montar a silhueta com o acervo e registrar a adaptação. Não alterar
   tilesets globais nem mapas existentes de Kanto.
3. Ler pelo menos uma vista do terreno e um percurso que confirme
   entradas/retorno; buscar mais ângulos onde a câmera esconde trecho.
   Anotar edição, minuto/recorte, marco a preservar, referência
   conflitante e resolução. Dar prioridade a USUM.
4. Comparar o croqui com as vistas sem sobrepor ou importar pixels,
   malhas ou eventos. Em revisão futura, abrir o mapa no motor, percorrer
   portas e curvaturas e repetir depois de salvar/reabrir. Tile visual
   não deve prometer uma passagem inexistente.

## Estado e critérios para o futuro

- Entrada inicial e visita em save existente são cenários separados.
  Usar a party existente do visitante, checar capacidade e deixar a oferta
  narrativa transacional e não repetível. [Viagem por NPC](VIAGEM_REGIONAL_LIVRE_NPC.md)
  só entre regiões instaladas; sem atalho para uma ilha bloqueada.
- A prova `ILIMA` grava resultado e primeira esmeralda juntos, com retorno
  válido após derrota, cancelamento e recarga. A grande prova é outro
  estado e libera Tauros uma vez. Não usar o contador global como fonte
  da habilidade de campo.
- O primeiro Centro válido atualiza o respawn apenas quando ativado;
  fallback inicial em ponto seguro junto à casa. Reusar
  [RegionalRespawn](../scripts/battle_polish/RegionalRespawn.rb).
- Antes de construir, conferir MapInfos, mapas instalados, reservas
  e destinos de eventos inclusive expressões dinâmicas. Se a faixa não
  couber, provar limite em editor, runtime Windows e JoiPlay antes de
  propor extensão. Não renumerar saves nem mapas publicados.
- As regras da prova do Totem devem ser distintas do visual da caverna;
  validar comportamento de aliados, novos turnos, saída em derrota e
  novo desafio sem duplicar recompensa. Não copiar scripts de doador.

Todos os testes acima estão `NOT_RUN`.
