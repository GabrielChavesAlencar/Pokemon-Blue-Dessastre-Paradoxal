# Johto — Etapa 06/16: Route 32, Union Cave, Azalea, Slowpoke Well e Bugsy

**Estado:** PARCIAL — eventos Ruby, testes e contrato de mapas simbólicos publicados. Nenhum mapa verdadeiro ou treinador PBS da fase foi instalado ou validado em Game.exe.  
**Referências:** [plano de 16 fases](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) · [status](JOHTO_ETAPAS.md) · [fase 05](JOHTO_FASE_05_VIOLET_FALKNER.md).

## Arquivos implementados

| Arquivo | Função |
|---|---|
| [scripts/regions/JohtoAzalea.rb](../scripts/regions/JohtoAzalea.rb) | Módulo Ruby de eventos: chegada a Azalea, Kurt, poço, dois Rockets, Proton, Bugsy, rival e CUT regional |
| [tests/johto_azalea_runtime.rb](../tests/johto_azalea_runtime.rb) | Testes Ruby sem assets: condições prévias, vitória, derrota, ordem dos Rockets, Hive idempotente, Cut, persistência e isolamento entre regiões |
| [tests/test_johto_azalea_runtime.py](../tests/test_johto_azalea_runtime.py) | Integra o teste de eventos no conjunto de regressões Python |
| [data/regions/johto-phase06.json](../data/regions/johto-phase06.json) | Contrato simbólico Route 32 → Union Cave → Route 33 → Azalea, interiores, trainers PBS a criar e critérios de aceitação |
| [tests/test_johto_phase06_contract.py](../tests/test_johto_phase06_contract.py) | Comprova as ligações simbólicas, registros de HIVE/CUT, versões de treinadores e bloqueio de liberação antes de validar os mapas |

## Sequência de eventos planejada

1. **Sair de Violet** para a Rota 32. O desafio de Azalea exige **ZEPHYR de Johto**, nunca uma insígnia de Kanto ou o número global de esmeraldas.
2. Passar pela **Route 32**, Centro Pokémon da rota, **Union Cave (1F, B1F)** e Route 33; garantir passabilidade e volta de todos os mapas.
3. **Chegar a Azalea:** `BlueJohtoAzalea.arrive` registra a primeira visita uma única vez no subestado `blue_regions["johto_pilot"]`.
4. **Casa de Kurt:** `BlueJohtoAzalea.kurt` registra o pedido de ajuda. Só a partir daí `well_entrance` inicia o capítulo do poço. Depois da libertação, Kurt agradece uma única vez. Nenhum item é concedido prematuramente.
5. **Slowpoke Well:** `rocket_grunt(0)` e `rocket_grunt(1)` exigem vitória e ordem correta; `rocket_executive` luta com Proton, e somente a vitória registra `slowpoke_well_cleared=true`. Perder não avança eventos; os Rockets derrotados não retornam ao recarregar o save.
6. **Ginásio de Azalea:** `BlueJohtoAzalea.bugsy` exige Zephyr, libertação do poço e treinadores instalados. A vitória contra Bugsy concede **HIVE** via `BlueRegions.award(state, "JOHTO", "HIVE")`; derrota, replay ou reload não concedem insígnia nem esmeralda extra.
7. **Saída para Ilex Forest:** `azalea_rival` usa o rival contraposto ao inicial escolhido na Etapa 04, com três versões PBS próprias; o encontro só é concluído depois de vitória.
8. **Cut:** `cut_allowed?(tool_ready)` chama `BlueRegions.field_access(state, "JOHTO", "CUT", tool_ready)`. A HIVE local e a ferramenta/HM de fato disponível são requisitos simultâneos. O módulo não distribui um HM fictício.

## Contrato com treinadores compilados

Os scripts **não** importam equipes de terceiros nem abrem batalhas só porque o usuário entrou no mapa. Depois que os dados oficiais do piloto forem compilados e revisados, o instalador isolado poderá criar o marcador:

`Data/blue-johto-azalea-ready.txt` com conteúdo `BLUE_JOHTO_AZALEA_V1_READY`.

O marcador **não existe ainda e não deve ser criado no `game/` principal**. Os tipos PBS reservados são:

| Treinador | Tipo PBS | Versões previstas |
|---|---|---|
| Rocket Grunt | `BLUE_JOHTO_ROCKET_GRUNT` | 0, 1 |
| Executivo Proton | `BLUE_JOHTO_ROCKET_PROTON` | 0 |
| Bugsy | `BLUE_JOHTO_BUGSY` | 0 |
| Rival de Azalea | `BLUE_JOHTO_AZALEA_RIVAL` | 0, 1, 2 (escolha do inicial) |

As equipes, níveis, recompensa de vitória e dificuldade **não estão definidos ou compilados ainda**. Devem reutilizar o balanceamento real de Decades/Blue, inclusive as regras configuradas de Master Mode, sem duplicar processamento de níveis nos eventos. Nenhuma habilidade, forma regional ou item é inventado pelo módulo.

## Dependências dos mapas reais

O [contrato de mapas da Fase 06](../data/regions/johto-phase06.json) define **somente nomes simbólicos**, não MapIDs ou coordenadas confirmadas.

**Caminho principal:** Violet City → Route 32 → Union Cave (1F) → Route 33 → Azalea Town.

**Interiores/saídas a validar:** Union Cave B1F, Centro Pokémon na Rota 32, Slowpoke Well e B1F, casa de Kurt, Ginásio de Azalea, Centro Pokémon e Mart de Azalea e portaria para Ilex Forest (ligação definitiva na Fase 07). Também auditar escadas, portas, encounters de caverna, encontros noturnos, Rocket grunts, passagem sob a chuva e retorno sem travamento.

Como o Map Pack real não foi fornecido nem auditado, nenhum desses locais tem ID de origem ou destino aprovado. O mapa da região continua bloqueado. As fotos, música, scripts externos e eventos estrangeiros não foram importados.

## Comandos de testes automatizados

```powershell
python -m unittest discover -s tests -p "test_johto_azalea_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase06_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
```

**Os testes são sintéticos**, sem `Game.exe`; uma CI verde demonstra regras de evento e regressão de módulos, não prova que o jogador atravessou Union Cave ou enfrentou Bugsy dentro do jogo.

## Critérios para aceitar integralmente a Etapa 06/16

- [ ] Obter fonte real, conferir direitos de tiles/gráficos e SHA-256, mapear IDs de origem e atribuir IDs livres estáveis da região.
- [ ] Instalar o trecho Violet → Azalea em `.blue-work/johto-pilot/`, com retorno e caves/escadas/interiores reais, sem sobrescrever Kanto/Decades.
- [ ] Criar e ligar encontros, sprites e NPCs por eventos locais, **sem executar Ruby de fonte externa**.
- [ ] Compilar Rocket Grunts, Proton, Bugsy e rival no PBS com as equipes e balanceamento vigentes.
- [ ] Testar no Game.exe o arco de Kurt, derrota e vitória na equipe Rocket, Slowpoke libertos, batalha de Bugsy, HIVE única, Ilex rival e uso de Cut somente após insígnia local + ferramenta.
- [ ] Confirmar registros das **duas páginas de treinador**: Johto atual e somatório global com esmeraldas de todas as regiões.
- [ ] Validar save/reload real, não duplicação de prêmio, volta a Violet, travessia segura e, quando possível, JoiPlay/Android.
- [ ] Conferir Blue Studio, piloto nativo de Kanto e saves Decades/Kanto antes/depois de cada integração; não ativar Johto no menu até prova real.

**Barras:** implementação integral **0/16**; aceite em gameplay **0/16**. A Etapa 06 está **parcial**, já que a integração e os testes dentro do jogo estão pendentes.
