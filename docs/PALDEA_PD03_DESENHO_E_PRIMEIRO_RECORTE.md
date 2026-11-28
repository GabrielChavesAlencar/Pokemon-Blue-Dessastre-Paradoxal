# PD03 — desenho 2D e primeiro recorte de Paldea

Proposta de construção futura. Cruze o
[atlas PD05](PALDEA_PD05_ATLAS_VISUAL_E_TILES_KANTO.md),
[inventário PD02](PALDEA_PD02_INVENTARIO_E_PROGRESSAO.md) e
[percurso de Scarlet/Violet](https://bulbapedia.bulbagarden.net/wiki/Appendix:Scarlet_and_Violet_walkthrough).
O recorte começa em Cabo Poco até a academia e a primeira entrega
sugere o oeste até Katy, sem impor uma ordem de ginásios à campanha.

| Módulo | Trecho a provar | Limite |
|---|---|---|
| D01 | Casa e vila de Cabo Poco ↔ Poco Path; ramais da praia/farol e Inlet Grotto; retorno aos trechos abertos. | Novo jogo escolhe inicial uma vez; visitante usa a equipe. O encontro de história da montaria não concede a espécie para a party nem habilidades de Titã. |
| D02 | South Province Area One ↔ Los Platos ↔ portão sul de Mesagoza ↔ praça ↔ academia; apresentar Treasure Hunt e três caminhos. | Não duplicar academia Naranja/Uva como cidades. Separar início do passeio e estado da aula/abertura. Manter acessos físicos e respawn válido. |
| D03 | Saída oeste de Mesagoza ↔ South Province Area Two ↔ Grand Olive Orchard ↔ Cortondo; teste da azeitona e Katy, com retorno. | Não tornar Katy obrigatória para sair pelo leste quando o setor correspondente for entregue. Mostrar fronteiras de setores ainda não instalados sem fingir passagem. Não liberar habilidade de montaria por vitória de ginásio. |

Os três módulos qualificam um único recorte jogável futuro. O mundo
aberto completo não cabe nessa primeira entrega, mas este piloto já
deve evitar ligações falsas e requisitos que virariam regra global.

## Do mundo aberto para mapas em tiles

1. Começar pelo grafo da superfície: bordas de província e de cidade,
   entradas, cruzamentos, marcos visíveis, métrica relativa e caminhos
   alternativos. Não redesenhar as quatro províncias como uma fila de
   corredores. Uma zona pode ser vários mapas; identificar cada saída
   pareada e manter o retorno a pé quando a origem o permite.
2. Usar vistas de chegada, de saída e altas/baixas para preservar o
   terreno. Converter altura com camadas, degraus, rampas, passagens
   curtas e bordas próprias. A academia, as portas leste/oeste de
   Mesagoza e a entrada da cratera não devem virar o mesmo teleporte.
3. Quando não houver mapa aprovado, compor com tiles de Kanto em uso:
   costa e falésia em Cabo Poco; terra, capim e cercas em Poco Path;
   fachada, escadaria e praça na cidade; árvores e paredes baixas no
   olival. Identificar equivalência e diferença em cada ficha, não
   substituir globalmente os tilesets de Kanto. Não anexar mídia de
   terceiros ao jogo.
4. Para cada aresta do grafo, registrar método de ida e volta, estado do
   portão, desnível, colisão e habilidade de campo necessária. Distinguir
   Dash, Surf, High Jump, Glide e Climb; não deixar Surf de Kanto ou
   outra montaria remover o bloqueio local. Verificar costas e bordas
   sem pontos onde o jogador fica preso. Voar até ponto visitado não
   substitui o caminho original nem libera setor ainda fechado.
5. No motor, comparar reconstrução e referências lado a lado, percorrer
   rotas antes/depois de cada desbloqueio, salvar, reabrir e repetir.
   Reservar os IDs apenas após auditoria de main e instalação real.

## Estado e saves

Separar início da Treasure Hunt, eventos opcionais, vitórias de
ginásio, Titan/ride, Equipe Star e três encerramentos. Nas oito vagas
de ginásio, vitória e primeira esmeralda são uma gravação única.
Titãs entregam a capacidade local correspondente, não uma esmeralda
de ginásio. Área Zero exige encerramentos em vez de contar 18 marcas
em acúmulo. A visita entre regiões segue o [NPC do Blue](VIAGEM_REGIONAL_LIVRE_NPC.md).
Preservar party, Boxes, saves antigos e respawn; marcar lacunas de
serviço ou engine em vez de dar vitória simulada.

Prova no motor e em aparelho: `NOT_RUN`.
