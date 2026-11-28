# KA02 — censo de IDs e referências, sem alocação

Auditoria em duas etapas. Esta primeira prova revisita a instalação
histórica Android 247 do [KA00](KA00_BASELINE_EXECUCAO.md), compara
arquivos físicos, índice, contratos de destino e referências de
transferência e não é autorização para ocupar IDs. O recorte
[KA01](KA01_FONTES_EXECUCAO.md) tem 11 símbolos ainda sem números.

## Evidência verificável nesta execução

- O ZIP público histórico é usado exclusivamente em um runner
  descartável, com tamanho e SHA-256 fixados. Não extrair o ZIP,
  executar eventos, guardar saves ou fazer upload do jogo.
- Ler comandos 201 diretos, contar 201 dinâmicos e scripts de evento
  355/655 sem executá-los. Conferir as duas pontas das linhas em
  `PBS/map_connections.txt` e juntar destinos a MapInfos, arquivos
  físicos e às faixas conservadoras. Um destino referenciado mas
  ausente é evidência de risco, não um slot disponível.
- Conservar IDs publicados K05, candidatos Celadon 276–279, Johto
  600–699, Hoenn 700–999, hold administrativo de Sinnoh 442–517,
  mapeamentos atuais de Sinnoh e janela candidata Unova 518–599.
  Faixas de cobertura podem se sobrepor sem implicar dupla
  ocupação de fato. Não renumerar mapas, eventos nem saves.

O censo também faz triagem inerte nos comandos de script dos mapas, em CommonEvents e no índice compilado Scripts quando observados. ID literal analisável entra no conjunto conservador; expressão dinâmica continua sem resolução. Plugins não são interpretados por esse scanner.

O relatório publica só agregados e IDs que requerem verificação, sem
arquivos do jogo. `KALOS_KA02_HISTORICAL_MAPID_GUARD_OK` significa que
a auditoria histórica funcionou; **não** equivale à aprovação
`KALOS_KA02_MAPIDS_NO_COLLISION_OK`.

## Gate ainda em aberto

Para promover KA02, repetir na instalação atual que será o alvo das
receitas Windows e Android. Confrontar as revisões publicadas e
pendentes, vínculos do runtime/manifestos, eventos comuns, plugins,
scripts compilados e variáveis com destinos reais. Conferir também
direções, limites de ID e persistência no editor, Game.exe e caminho
Android. Lista velha, prova sintética ou ausência de um marcador não
provam que um slot é livre. Não presumir suporte acima de 999.

Se não houver como obter a base atual sem misturar fontes privadas,
preservar trabalho independente de inspeção e não reservar, instalar
ou publicar Kalos. Esta etapa não toca os branches Kanto/Hoenn, saves,
tilesets globais, runtime, instalador ou catálogo regional.
