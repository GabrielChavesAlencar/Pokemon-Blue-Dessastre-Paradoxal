# Unova A12 — propriedade regional dos MapIDs e preparação de QA isolado

**17/11/2026 · Somente leitura.** A12 não instala Unova, não cria um jogo de teste, não reserva 518–599, não abre Game.exe, não executa scripts Ruby/Python de instaladores e não altera saves.

## Dados observados no PC (A11)
Fonte: LEIA_AQUI_UNOVA_MAPIDS(5).txt fornecido pelo usuário:
- 648/648 mapas inventariados; MapInfos SHA-256 8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420;
- 82/82 IDs 518–599 desocupados no snapshot, com 0 colisões nos manifestos locais reconhecidos e 0 referências estáticas no bloco;
- 2 referências ao MapID 3 nas introduções, sem teste do caminho real no Game.exe;
- 20 expressões computadas: INDEXED_VARIABLE=10, VARIABLE_OR_SYMBOL=7 e UNCLASSIFIED_EXPRESSION=3, sem resolução em runtime;
- Sinnoh/Unova sem manifesto local; Kanto/Johto/Hoenn apenas com esquemas parcialmente reconhecidos;
- Barra A 0/8; Unova jogável 0/32.

O usuário não forneceu o JSON detalhado A11. A A12 o regenera na instalação local via BAT e o usa no relatório.

## Evidência de código-fonte — sintaxe inerte

Os oito arquivos fonte são carregados do repositório ou embutidos no BAT. Um analisador AST inspeciona funções e intervalos literais, registra SHA-256 por arquivo e jamais importa ou executa o código de instalação.

- scripts/install_game.py: ponto de entrada de integração Blue-Story; não é um inventário exaustivo de destinos.
- scripts/regions/install_kanto.py e scripts/regions/pilot.py: Kanto depende do mapeamento gerado no piloto e manifesto; não assumir faixa fixa.
- scripts/regions/johto_main_preview.py e scripts/regions/auto_integrate_johto.py: lote 600–681 e intervalo preventivo de preview 600–699.
- scripts/regions/pilot_hoenn.py e scripts/regions/install_hoenn.py: pool dinâmico 700–999; pool não significa propriedade de todos esses IDs.
- scripts/regions/install_sinnoh_qa_copy.py: preparador de cópia QA; não constitui autorização de reserva Sinnoh.

Estes intervalos literais não invadem o candidato Unova 518–599. Isso NÃO prova ausência de outras reivindicações dinâmicas nem futuras versões do instalador, e NÃO aprova os 82 MapIDs.

## Entrega A12

1. Confronta fases A04–A11 com mesmo MapInfos SHA-256 e confere os arquivos físicos MapInfos.rxdata e Map001.rxdata; alteração intercalada bloqueia o diagnóstico.
2. Faz inventário de oito fontes Python de instaladores com AST e hash, sem executá-las.
3. Consolida reivindicações observadas em manifestos e faixas literais, sem inferir mapeamentos ocultos.
4. Prioriza as expressões computadas de A11; não executa Ruby nem resolve variáveis.
5. Produz matriz de 82 destinos hipotéticos de Data/Map518.rxdata a Data/Map599.rxdata. Cada entrada fica com write_allowed=false, reservation_approved=false e source_map_confirmed=false.
6. Simula em memória três cenários sintéticos negativos: claim de manifesto no 518, MapInfos desatualizado, fonte não autorizada. Não cria cópia QA nem executa uma instalação de teste. Documenta pré-requisitos de saves isolados, SHA de pré-instalação, rollback, Game.exe.
7. Emite a12-installer-ownership-HASH.json e uma seção A12 no LEIA_AQUI_UNOVA_MAPIDS.txt do BAT.

## Bloqueios futuros

- Mapas reais Unova com direito de uso e hashes de origem;
- revisão completa de manifestos regionais e das rotas efetivas do Blue-Story;
- destino correto MapID 3, condições e execução real no Game.exe;
- cópia QA isolada, com backup transacional e rollback efetivamente testado;
- validação de viagens entre regiões no Windows e depois Android/JoiPlay.

**Estado:** A12 é validação estática e ensaio de bloqueios em memória, não reserva. Barra A 0/8, Unova jogável 0/32. Enviar LEIA_AQUI_UNOVA_MAPIDS.txt e o JSON detalhado A12.
