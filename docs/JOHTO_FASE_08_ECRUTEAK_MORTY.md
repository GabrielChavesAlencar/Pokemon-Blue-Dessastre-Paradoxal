# Johto — Etapa 08/16: Routes 35–37, National Park, Ecruteak, Burned Tower e Morty

**Estado: PARCIAL — núcleo Ruby e contrato de mapas simbólicos preparados; ainda não jogável.**  
**Data:** 12/11/2026  
**Plano:** [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)  
**Progresso:** [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md)  
**Dependência anterior:** [Etapa 07 — Goldenrod e Whitney](JOHTO_FASE_07_ILEX_GOLDENROD_WHITNEY.md).

## Arquivos publicados

| Arquivo | Entrega |
|---|---|
| [scripts/regions/JohtoEcruteak.rb](../scripts/regions/JohtoEcruteak.rb) | Módulo de eventos isolados: Route 35, National Park, Route 36/Sudowoodo, Route 37, Ecruteak, Burned Tower, rival, despertar, Rocket do Dance Theater, Surf e Morty |
| [tests/johto_ecruteak_runtime.rb](../tests/johto_ecruteak_runtime.rb) | Testes de progressão, derrota/vitória, prêmio único, Cut/Surf indiretos, regiões isoladas e save/reload |
| [tests/test_johto_ecruteak_runtime.py](../tests/test_johto_ecruteak_runtime.py) | Integra a regressão Ruby ao conjunto Python executado no CI |
| [data/regions/johto-phase08.json](../data/regions/johto-phase08.json) | Grafo simbólico da rota Goldenrod → Ecruteak, interiores, equipes PBS futuras, pré-condições e todos os gates de integração como `false` |
| [tests/test_johto_phase08_contract.py](../tests/test_johto_phase08_contract.py) | Confirma ligação com Goldenrod, FOG/SURF regional, IDs de treinador, bloqueio de MapIDs não auditados e ausência de falso aceite |

As fontes do Map Pack e da instalação real `game/` **não estão disponíveis neste repositório**; esses arquivos são código, testes e documentação. **Nenhum MapXXX.rxdata, música, Game.exe, salva ou Scripts.rxdata de Kanto/Decades foi alterado.**

## Caminho e pré-requisitos implementados em Ruby

1. `route35` exige **PLAIN Badge local** e a passagem por Ilex concluída; a visita é registrada só uma vez.
2. `national_park` registra a visita. **Não implementa Bug-Catching Contest**, premiação ou calendários, portanto não deve ser usado para afirmar que o National Park está integralmente pronto.
3. `route36` exige PLAIN, visita à Rota 35, `goldenrod_squirtbottle_received` e `route36_sudowoodo_cleared`. O confronto anterior com Sudowoodo depende do módulo da Etapa 07. **Os eventos físicos, a posição da árvore, captura/derrota, colisão e transição real ainda não foram conectados**.
4. `route37` só avança após Rota 36; `ecruteak_arrive` só ocorre após a Rota 37.
5. `burned_tower` registra entrada depois da chegada à cidade; a batalha `tower_rival` só chama o tipo PBS próprio de Johto quando o conjunto real estiver compilado e um marcador do piloto tiver sido autorizado.
6. `legendary_awakening` marca o despertar dos três Pokémon **apenas após vitória do rival**, uma única vez. Não cria sprites, roaming, lendários na party ou acesso à captura. Esses aspectos continuam pendentes para a fase de lendários.
7. `dance_theater_rocket` prepara um combate isolado contra Rocket. O prêmio `surf_reward` só é possível depois da vitória e com o item real de Surf cadastrado/validado no piloto. Ele não grava HM falso.
8. `morty` só abre depois da entrada em Ecruteak, evento da Burned Tower, despertar e cadastro dos treinadores PBS do piloto. Perda não concede nada. Vitória válida chama `BlueRegions.award(state, "JOHTO", "FOG")` exatamente uma vez.
9. `surf_allowed?(tool_ready)` chama `BlueRegions.field_access(state, "JOHTO", "SURF", tool_ready)`. **Apenas FOG de Johto e ferramenta válida** permitem Surf; o total mundial de esmeraldas e badges de Kanto não substituem a FOG.

A FOG contabiliza **uma** conquista no cartão da região e uma esmeralda no cartão mundial graças ao sistema global existente. O evento não duplica o cálculo, nem modifica o balanço dos níveis dos adversários.

## Integridade dos treinadores, itens e batalha

**Três tipos PBS novos reservados, ainda não compilados:**

| Treinador | Identificador | Versões |
|---|---|---|
| Rival na Burned Tower | `BLUE_JOHTO_BURNED_TOWER_RIVAL` | 0, 1 e 2, conforme o inicial |
| Rocket do Dance Theater | `BLUE_JOHTO_DANCE_ROCKET` | 0 |
| Morty | `BLUE_JOHTO_MORTY` | 0 |

Os demais treinadores do ginásio precisam de entradas reais no PBS, com versões normal/master e os mesmos hooks de balanceamento de Decades, sem sobrescrever Kanto.

As batalhas ficam **inativas** sem `Data/blue-johto-ecruteak-ready.txt` contendo `BLUE_JOHTO_ECRUTEAK_V1_READY`. O item de Surf exige, adicionalmente, `Data/blue-johto-ecruteak-surf-ready.txt` contendo `BLUE_JOHTO_ECRUTEAK_SURF_V1_READY` e uma entrada verdadeira para `HM03` (ou ajuste do código para a chave real auditada). **Nenhum marcador foi instalado agora**; os scripts apenas reconhecem esses arquivos futuramente em uma cópia isolada, e a existência de marcador por si só não comprova que os treinadores estão corretos.

O evento de Morty não implementa o puzzle visual de pisos invisíveis, iluminação ou o comportamento real dos treinadores do ginásio: isso requer mapas e testes em execução.

## Mapas exigidos e integrações futuras

O [contrato da fase 08](../data/regions/johto-phase08.json) descreve:

**Goldenrod → Route 35 → Route 36 → Route 37 → Ecruteak**, com National Park como percurso opcional e duas portarias. Em Ecruteak, relaciona o Centro Pokémon, Mart, Dance Theater, Burned Tower (1F e B1F), Ginásio, entrada da Bell Tower e saída oeste para Route 38 (próxima fase).

**Não são MapIDs reais.** O mapa HGSS/Crystal, casas, NPCs, imagens, efeitos, passabilidade, portas, escadas e warps ida/volta devem ser extraídos/produzidos em uma cópia temporária e auditados antes de qualquer instalação. Nenhum novo destino foi colocado no menu `Testar Johto` como se fosse jogável.

**Opcional/não implementado:** Ruins of Alph, Mt. Mortar, Bug-Catching Contest, sprites e roaming de Raikou/Entei/Suicune e eventos de Bell Tower. Não declarar esses recursos prontos com base apenas no diálogo da torre. A seleção de temporadas e as versões HGSS/Crystal precisam de uma decisão posterior no piloto real.

## Testes

```powershell
python -m unittest discover -s tests -p "test_johto_ecruteak_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase08_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
```

Os testes Ruby simulam estados de Decades, Kanto e Johto; garantem que Rota 35 depende de Plain/Ilex, Rota 36 exige Sudowoodo liberado, a Burned Tower depende do rival, o prêmio Surf não duplica nem registra entrega falha, Morty só dá FOG por vitória, Surf exige ferramenta e badge, e os estados persistem após save/reload. **São testes sintéticos, não testes visuais ou de mapa no Game.exe.**

## Critérios pendentes para concluir a Etapa 08

- [ ] Importar e auditar os mapas reais e os tilesets autorizados sem substituir Decades/Kanto.
- [ ] Auditar o fim físico da Rota 36/Sudowoodo, inclusive derrotar, capturar, fugir, salvar, recarregar e retornar da Rota 37.
- [ ] Conectar portarias do National Park, entradas/saídas e todos os andares das torres com passabilidade e coordenadas reais verificadas.
- [ ] Implementar a localização, os NPCs, os sprites e a sequência real de despertar/roaming dos lendários (sem ativar a captura precocemente).
- [ ] Compilar times de rival, Rocket, Morty e treinadores do ginásio com balanceamento atual de Decades e Master Mode.
- [ ] Verificar o **item real** de Surf e se o retorno de cada batalha da API Essentials condiz com vitória/derrota antes de liberar a premiação.
- [ ] Validar FOG, Surf com ferramenta, saves separados, as **duas páginas de treinador** e ausência de duplicação de esmeraldas.
- [ ] Testar sequência Goldenrod → Ecruteak → Burned Tower → Morty no Game.exe Windows e JoiPlay, com regressões Blue Studio e Kanto aprovadas.

**Duas barras: 0/16 integralmente aprovadas e 0/16 gameplay integralmente aprovado.** A fase 08 **permanece PARCIAL**, pois os mapas e a execução real ainda faltam.
