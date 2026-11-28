# Kalos — pesquisa e planejamento, sem implementação

Escopo autorizado: pesquisa, documentação e planejamento da campanha X/Y em
2D para o Dessastre Paradoxal. Nenhum código do jogo, mapa, asset, reserva de
MapIDs, save, instalador, catálogo público ou versão jogável muda nesta
entrega. O [roadmap KA00–KA31](KALOS_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md)
é referência para planejar, não autorização para executar seus lotes de jogo.
O único YAML novo valida a documentação no GitHub Actions.

## Etapas documentais

| Fase | Evidência de saída | Estado neste documento |
|---|---|---|
| KD00 | Baseline estática, fronteiras e critério de validação | [Validada no Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/46150162315) |
| KD01 | [Matriz de fontes, direitos e contingência](KALOS_KD01_FONTES_E_DIREITOS.md) | [Validada no Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/46150810468) |
| KD02 | [Inventário e progressão](KALOS_KD02_INVENTARIO_E_PROGRESSAO.md) | Submetida à validação |
| KD03 | Desenho 2D, dados, save, riscos de ID e preparação do primeiro corte | A fazer |
| KD04 | Roteiro Windows/Android pela fonte, testes e handoff implementável | A fazer |

Um lote por vez nesta frente documental: conferir o commit, o resultado do
workflow e sua evidência. Se falhar, corrigir e validar a mesma fase antes
da seguinte. Nada aqui é um marco de implementação KA00–KA31, nem altera o
ritmo de Celadon. Registrar a revisão, os links dos runs e as lacunas no
handoff; uma CI documental verde não é um teste no Game.exe ou no JoiPlay.

## KD00 — baseline estática verificada

Snapshot remoto da main: `7903ae94fb18f47e36fecd4c07b6673ef6ea8b70`,
árvore `c4501d7c7755e8a7ed77c844a1a2e634cdb766dd`, 2.281 arquivos
rastreáveis na listagem recursiva de Git. Isso não é uma inspeção de uma
instalação pessoal. A auditoria foi por árvore e leitura de contratos.

| Componente | Observado no snapshot | Implicação |
|---|---|---|
| [Catálogo regional](../site/public/data/regions.json) | KALOS está `planned`, X/Y, com oito chaves: BUG, CLIFF, RUMBLE, PLANT, VOLTAGE, FAIRY, PSYCHIC, ICEBERG. | Não publicar destino, status ativo ou progresso. |
| [Novo jogo](NOVO_JOGO_SELECAO_REGIONAL.md) e [viagem](VIAGEM_REGIONAL_LIVRE_NPC.md) | Referência compartilhada para seleção regional, entrada normal e retorno. | Contrato a confrontar com o runtime em futuro lote autorizado. |
| Arquivos específicos | Entre os nomes rastreados com Kalos, só o roadmap existente. Não há receita, workflow nativo, mapa nem piloto identificado pelo nome. | Isto não prova ausência em dados privados ou indiretos; nenhuma instalação testada. |
| [MapIDs](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md) | Relatório histórico, não inventário atual das instalações. | Sem ID reservado, sem faixa declarada livre e sem presumir suporte acima de 999. |
| [Windows](INSTALACAO.md) e [Android pela fonte](ANDROID_INSTALACAO_PELAS_FONTES.md) | Há fluxos multirregionais existentes. | Planejar paridade numa revisão e receita de origem, sem novo ZIP do jogo; instalação existente não troca de canal por conveniência. |

Sem fontes de Kalos baixadas, permissões verificadas, builds, QA física ou
assets de gameplay publicados. A próxima fase verifica páginas de autores,
distingue pesquisa de licença e escolhe apenas referências ou material
expressamente habilitado para reutilização.
