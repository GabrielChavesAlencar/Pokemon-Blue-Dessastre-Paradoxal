# Johto — Etapa 04/16: base segura para iniciar em New Bark Town

**Situação:** implementação parcial da seleção de nova partida. A região **não está jogável**: a fonte de mapas ainda não foi auditada, o interior da casa do jogador não existe na instalação e o launcher experimental de Johto não foi criado.

## Código novo e protegido

O módulo [RegionStart.rb](../scripts/battle_polish/RegionStart.rb) conserva a seleção nativa Decades e o spawn de Kanto. Foram acrescentados:

- Marcador dedicado `Data/blue-johto-start.txt`, com assinatura `BLUE_JOHTO_START_V1,JOHTO,MapID,x,y`.
- Registro de instalação separado `Data/blue-johto-install.json`. **É exigido junto com o marcador de início** para permitir Johto na seleção.
- Validação de valores inteiros, coordenadas não negativas, MapID no intervalo reservado 600–999 e existência real do arquivo `Data/MapNNN.rxdata`.
- Regra de seleção inicial retrocompatível: Decades continua padrão quando não há mapa regional válido; Kanto continua funcionando; Johto aparece como opção selecionável **somente** quando satisfaz seus pré-requisitos.
- Preparação de Story Mode e save regional usando as mesmas bases já utilizadas em Kanto, sem substituir o objeto de save ou o começo nativo de Decades.
- Reconhecimento futuro de `Johto pilot.json` **somente** se o mapa de origem e seus marcadores estiverem válidos na cópia de teste.

Os dois arquivos de ativação de Johto **não existem ainda** em `game/`; o código novo permanece inativo na instalação atual. Um mapa de Johto sintético usado em testes Ruby não é publicado como mapa verdadeiro.

## Provas estruturais

O teste [tests/region_start_runtime.rb](../tests/region_start_runtime.rb) verifica:

1. Ausência de marcadores → novo jogo mantém Decades e não exibe diálogo extra.
2. Kanto instalado → início em Pallet e todos os estados existentes preservados.
3. Arquivo de mapa Johto isolado, sem registro de instalação → Johto fica bloqueado.
4. Marcadores e mapa sintéticos válidos → o adaptador consegue configurar New Bark, salvar a região JOHTO e restaurar as coordenadas globais originais de Decades.
5. Coordenada inválida → marcador recusado.
6. Piloto isolado de Johto → seleção direta só no contexto de teste; piloto de Kanto continua abrindo em Kanto.
7. Carregamento de saves antigos → não altera a escolha de região nem reinicia o jogo.

**Isso valida apenas o comportamento Ruby em simulação.** Não prova que a casa, escada, laboratório de Elm, cenas ou batalhas existam no mapa real.

## Pré-requisitos que faltam para concluir a etapa

- [ ] Auditar o arquivo verdadeiro de mapas HGSS/RMXP e confirmar se contém o interior da casa do protagonista e o laboratório.
- [ ] Adicionar as partes ausentes de New Bark Town por desenho original ou fonte com direitos de uso confirmados.
- [ ] Criar transições bidirecionais casa/quarto/escadas/rua/laboratório em **MapIDs finais estáveis**, sem copiar scripts estrangeiros.
- [ ] Implementar o evento do Professor Elm, os três iniciais e a primeira batalha do rival, com flags únicas e save/reload.
- [ ] Construir um piloto executável separado com `Johto pilot.json`, `Data/blue-johto-install.json` e `Data/blue-johto-start.txt`, só após prova de mapa funcional. O lançador `JOHTO_JOGAR_EXPERIMENTAL.bat` ainda **não** existe.
- [ ] Validar visualmente início, colisões, portas, caminhada, menus e save com Windows, sem substituir Kanto/Decades.
- [ ] Repetir CI nativa de Kanto e testes do Blue Studio; rejeitar regressões.

**O botão `Testar Johto` do menu principal permanece em modo de preparação** até que o lançador e o piloto reais sejam instalados e auditados.

## Contrato do instalador futuro

Não gerar os marcadores de Johto com antecedência. Somente o instalador transacional da região, depois de conferir a fonte e os MapIDs, poderá gravar o marcador de início e o registro de instalação no destino autorizado, com backup/rollback. Para uma cópia de teste isolada, criar marcadores **somente dentro da cópia**, nunca no `game/` mestre.

**Barra 1: 0/16; Barra 2: 0/16.** A Etapa 04 está **PARCIAL**, não concluída. Os dois pilotos permanecem independentes.
