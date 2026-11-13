# Johto — etapa OFFLINE 07/12: portas, escadas e spawn de New Bark

**Data:** 13/11/2026. **Implementação de dados de evento RMXP realizada em prévia isolada, sem executar Game.exe.** A instalação automática pelo `Blue-Story.exe` ainda não existe; não marcar Johto jogável.

## Entregas

- `scripts/regions/build_johto_warps_v1.py` lê a prévia aprovada da etapa 06 em `.blue-work/johto-staging-elm-lab-v1`; valida o manifesto dos 77 mapas, seus símbolos e os tilesets nativos, além do PBS de conexões.
- `data/regions/johto-stage07-warps.json` fixa seis transições **propostas**, reversíveis, e a posição inicial, com `verified_in_engine=false`.
- O gerador compila **RPG::Event + RPG::Event::Page** com apenas comando **201** (transferência) e terminador **0**, reutilizando `build_johto_events.event_page`. Não inclui scripts Ruby `355` nem eventos de origem desconhecida.
- Grava **uma CÓPIA NOVA**, `.blue-work/johto-staging-warps-v1`, com status `BLUE_WARP_PREVIEW_ONLY_NOT_PLAYABLE`. O manifesto de entrada da etapa 06 permanece intacto. A saída não pode ser confundida com a prévia inicial de geometria sem eventos.
- Um dos destinos da escada/portas não pode coincidir com a posição-gatilho da volta. Os testes exigem que todos os gatilhos/chegadas de cada mapa sejam alcançáveis usando a tabela estática dos tiles, sem afirmar passabilidade no motor.
- Mantém `Game.exe`, `game/`, Kanto, Decades, Hoenn e saves fora do fluxo de escrita.

## Seis warps preparados

| Evento | Origem (mapa e x,y) | Destino (mapa e x,y) | Verificação |
|---|---|---|---|
| `JH_HOME2F_TO_1F` | Quarto 2F **674** (9,8) | Casa 1F **675** (11,8) | Par com retorno |
| `JH_HOME1F_TO_2F` | Casa 1F **675** (11,9) | Quarto 2F **674** (9,7) | Par com retorno |
| `JH_HOME1F_TO_TOWN` | Casa 1F **675** (7,9) | New Bark **600** (13,34) | Par com retorno |
| `JH_TOWN_TO_HOME1F` | New Bark **600** (13,33) | Casa 1F **675** (7,8) | Par com retorno |
| `JH_TOWN_TO_ELM_LAB` | New Bark **600** (5,21) | Elm Lab **676** (10,11) | Par com retorno |
| `JH_LAB_TO_TOWN` | Elm Lab **676** (9,12) | New Bark **600** (5,22) | Par com retorno |

**Spawn inicial proposto:** quarto 2F Map674 **(6,7)**. O gatilho da escada está em outra célula, sem volta imediata.

As fachadas escolhidas na captura auditada de New Bark eram **(5,21), “Lab?”**, e **(13,33), “Casa jogador?”**. As posições **(14,23) e (4,31)** pertencem a casas ainda não classificadas e não foram conectadas. A identidade visual dessas duas entradas é candidata; o teste no `Game.exe` ainda precisa confirmá-la.

### Borda de New Bark ↔ Rota 29

A ligação real do pacote de origem continua sendo uma linha de `map_connections.txt`:

```text
600,West,13,625,East,0
```

O gerador **verifica que essa linha ocorre uma única vez** no PBS da prévia. **Não cria um warp adicional na borda**, evitando teletransporte duplicado ou conflito com o deslocamento contínuo esperado da engine.

## Verificações offline

Usando os `Map600/674/675/676.rxdata` reais do estágio privado:

- Todos os seis pontos de evento, seis pontos de chegada e spawn possuem **flags estáticas de passagem livres** e ficam dentro dos limites do mapa.
- Os âncoras de cada mapa pertencem à **mesma região caminhável**, conforme busca ortogonal estática: New Bark **228** tiles, quarto **81**, casa **106**, laboratório **198**.
- **Seis eventos** com código RMXP **201** inseridos em **quatro mapas**, reabertos com Ruby Marshal, parâmetros de destino conferidos.
- Comparação dos 77 mapas: **somente** `Map600.rxdata`, `Map674.rxdata`, `Map675.rxdata` e `Map676.rxdata` mudaram. Os outros **73** permaneceram byte a byte iguais.
- `Data/MapInfos.rxdata` e `Data/Tilesets.rxdata` são **idênticos** à etapa 06.
- `tests/test_johto_warps_v1.py` contém **12 testes unitários**: seis conexões e PBS, bloqueio de passabilidade, coordenadas duplicadas, ida/volta obrigatória, spawn, chegada em gatilho, conexão PBS ausente/duplicada, limites e afirmações indevidas de QA, desconexão estática, serialização do evento.

**Limite da prova:** nenhum teste automatizado offline substitui `Game.exe`. A interpretação do evento de toque/porta, orientação do jogador, colisão das fachadas, alcance visual e retorno após salvar ainda precisam da engine. `gameplay_playable=false`, `tested_in_game=false`, `can_install=false`.

## Executar sem abrir o jogo

Com os estágios privados anteriores e a base instalada:

```powershell
python scripts/regions/build_johto_warps_v1.py
python -m unittest discover -s tests -p "test_johto_warps_v1.py" -v
```

`build_johto_warps_v1.py` escreve apenas em **novo** `.blue-work/johto-staging-warps-v1`; recusa saída já existente. A prévia RXDATA de 77 mapas também foi entregue em ZIP privado no chat, **não publicada no GitHub**.

## Próximos passos e requisito do instalador

1. **08/12:** inserir mãe, Elm, rival e **três Poké Bolas interativas individuais**. O laboratório do estágio 06 usa bolas estáticas em tiles; a etapa 08 deve substituir o desenho estático no mesmo local para não gerar sprites duplicados. Os novos eventos de história deverão **coexistir** com os seis warps já preparados, não criar um conjunto novo que os apague.
2. Depois preparar PBS e encontros (09–11).
3. Integração automática do `Blue-Story.exe`: obter os recursos legalmente distribuíveis, gerar/reconciliar o estágio, fazer backups e aplicar idempotentemente os mapas com testes de integridade. **Ainda pendente**; não declarar instalação pronta só porque o código Python chegou à `main`.

**Barras:** **OFFLINE 7/12 (58,3%) · JOGÁVEIS 0/13 · TESTADAS NO EXE 0/13.**
