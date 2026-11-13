# Johto — Etapa 09/16: Olivine, Lighthouse, Cianwood e Chuck

**Estado: PARCIAL.** O fluxo Ruby, o contrato simbólico de mapas e a regressão de lógica estão publicados no GitHub. **Não há mapas reais/MapIDs auditados, NPCs associados a eventos RMXP, PBS compilados ou piloto executável validado.**

**Data:** 12/11/2026  
**Dependências:** [Etapa 08 — Ecruteak/Morty](JOHTO_FASE_08_ECRUTEAK_MORTY.md) · [Plano geral](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) · [Acompanhamento](JOHTO_ETAPAS.md)

## Entregas publicadas

| Arquivo | O que foi criado |
|---|---|
| [scripts/regions/JohtoOlivineCianwood.rb](../scripts/regions/JohtoOlivineCianwood.rb) | Eventos regionais isolados Route 38/39, Olivine, Lighthouse, Jasmine, Route 40/41, Cianwood, farmácia, Chuck, Fly e retorno |
| [tests/johto_olivine_cianwood_runtime.rb](../tests/johto_olivine_cianwood_runtime.rb) | Teste Ruby puro: travas regionais, floors, travessia marítima, vitória/derrota, itens únicos, STORM, save/reload e falta de efeitos em Kanto/Decades |
| [tests/test_johto_olivine_cianwood_runtime.py](../tests/test_johto_olivine_cianwood_runtime.py) | Executa a regressão Ruby na suíte Python do Blue Studio |
| [data/regions/johto-phase09.json](../data/regions/johto-phase09.json) | Percurso e interiores simbólicos, checkpoints de história, equipes PBS previstas, validações pendentes |
| [tests/test_johto_phase09_contract.py](../tests/test_johto_phase09_contract.py) | Valida continuidade com Ecruteak, FOG/STORM/SURF/FLY, Lighthouse, itens provisórios e que não há liberação fictícia |

## Sequência de eventos preparada

### 1. Ecruteak → Olivine

1. `route38`: exige **FOG Badge de Johto** e Ecruteak já visitada. Registra a rota uma vez.
2. `route39`: exige Rota 38 e libera chegada a Olivine. Moomoo Farm está no contrato de mapa, mas sua cura e recompensas não foram implementadas nesta fase.
3. `olivine_arrive`: registra a chegada e orienta o jogador para o farol.
4. `lighthouse_entrance` e `lighthouse_floor(1..6)`: marcam os checkpoints lógicos dos andares em ordem. A estrutura real do farol, elevador, escadas, portas, saltos e atalhos **não está implementada**. O instalador deve substituir a dependência de ordem estrita dos checkpoints se o layout real permitir rotas alternativas.
5. `jasmine_request`: depois da chegada ao 6º andar, Jasmine pede medicina para Ampharos. A interação pode ser repetida sem abrir outro pedido.

### 2. Travessia das Rotas 40 e 41

- `route40(tool_ready)`: exige chegada a Olivine, recebimento validado do Surf no piloto de Ecruteak (`ecruteak_surf_rewarded`) e `BlueRegions.field_access(..., "SURF", tool_ready) == :allowed`. Nem uma badge de Kanto nem a soma mundial de esmeraldas substituem a FOG e o uso real da ferramenta.
- `route41(tool_ready)`: exige a Rota 40 iniciada e autorização atual de Surf. O mar e as Whirl Islands **não estão fisicamente instalados**.
- `cianwood_arrive`: registra chegada depois da Rota 41. O conteúdo de treinadores, encontros aquáticos, pescaria e maré depende dos mapas reais e PBS compilados.

### 3. Farmácia e medicina de Ampharos

- `pharmacy`: só permite buscar medicina em Cianwood **se Jasmine já a solicitou**. O provável identificador `:SECRETPOTION` só é usado se estiver no catálogo `GameData::Item`, e se existir um marcador do instalador independente, exclusivo do piloto de Johto.
- O marcador previsto é `Data/blue-johto-medicine-ready.txt` contendo `BLUE_JOHTO_MEDICINE_V1_READY`; **não foi criado**.
- `pbReceiveItem` deve retornar sucesso para marcar `cianwood_medicine_received`. Falha não altera o save, entrega bem-sucedida não se repete.
- `return_to_olivine(tool_ready)` registra a volta com a medicina apenas quando Surf está permitido e a medicina já foi recebida. **Não remove a SecretPotion, não cura Ampharos e não libera Jasmine**.

**Separação obrigatória:** a **Etapa 10** deve implementar a entrega física de `:SECRETPOTION` a Jasmine, validação e consumo no inventário real, recuperação de Ampharos, Ginásio de Olivine e MINERAL Badge. A fase 09 não pode antecipar esse progresso, nem permitir duplicação do item após recarregar o save.

### 4. Ginásio de Cianwood — Chuck

1. `chuck_waterfall`: evento lógico para desligar a cascata do ginásio, acessível apenas depois de Cianwood. A colisão, animação e o gatilho no mapa real ainda são pendentes.
2. `chuck`: exige FOG, chegada a Cianwood, queda d'água interrompida e um treinador `BLUE_JOHTO_CHUCK` versão 0 **realmente compilado**. Derrota não concede insígnia.
3. Vitória confirmada chama `BlueRegions.award(state, "JOHTO", "STORM")`; a API controla unicidade da conquista. O evento **não incrementa manualmente** esmeraldas.
4. `chuck_wife_fly_reward`: após STORM, verifica `:HM02` no catálogo real, recompensa validada e `pbReceiveItem` concluído. A concessão só ocorre uma vez.
5. `fly_allowed?(tool_ready)`: verifica a **STORM local e a ferramenta efetiva**, conforme o registro regional. Nenhuma insígnia de Kanto serve como autorização em Johto.

**Treinador ainda pendente:** o marcador `Data/blue-johto-cianwood-ready.txt` com `BLUE_JOHTO_CIANWOOD_V1_READY` poderá ser escrito **somente após revisar e compilar o PBS real**, incluindo os treinadores auxiliares. Não instalar o marcador no jogo principal. As equipes, níveis, variações e Master Mode devem usar o balanceamento de Decades já presente no projeto, incluindo a escala e cobertura de fraquezas configuradas, sem definir times fictícios nesta fase.

**HM Fly:** `:HM02` é um candidato, não confirmação de ID. Antes da instalação, conferir em `GameData::Item`; o segundo marcador local previsto é `Data/blue-johto-fly-ready.txt` com `BLUE_JOHTO_FLY_V1_READY`. O script não cria um item inexistente.

## Contrato de mapas (não instalados)

O arquivo [johto-phase09.json](../data/regions/johto-phase09.json) define o percurso:

**Ecruteak → Portaria Route 38 → Route 38 → Route 39 → Olivine → Route 40 → Route 41 → Cianwood.**

**Interiores previstos:** Moomoo Farm, Olivine Poke Center/Mart/Cafe/Port/Gym, **Lighthouse 1F–6F**, Cianwood Centro Pokémon, farmácia, ginásio, casa/interação da esposa de Chuck, estúdio fotográfico e portaria das Whirl Islands (sem liberar Lugia ou cavernas). A entrada de Jasmine em Olivine deve permanecer indisponível até os eventos de cura da Etapa 10.

Todos os nós são **símbolos de planejamento**, sem IDs, warps, escadas ou coordenadas verdadeiras. O pacote original Johto não está no repositório; não inventar topologia, encontros Land/Water/Fishing nem grafo de ilhas para liberar o piloto.

## Regressões locais e CI

```powershell
python -m unittest discover -s tests -p "test_johto_olivine_cianwood_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase09_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
```

A suíte inclui tentativas de visitar Cianwood sem Surf, travessia com e sem FOG/ferramenta, farmácia sem o pedido de Jasmine, entregas de item mal sucedidas, andares fora de ordem, Chuck bloqueado por cascata, derrota sem STORM, vitória com STORM única, Fly com/sem ferramenta, retorno com medicamento e save/reload sem repetição. **São testes sintéticos de lógica**, não uma prova de gameplay em `Game.exe`.

## Aceite integral da Etapa 09: pendências

- [ ] Fonte RMXP legítima auditada, hashes, artes/tilesets licenciados, MapIDs remapeados e cópia isolada em `.blue-work/johto-pilot`.
- [ ] Mapas reais das Rotas 38–41, Olivine, Lighthouse (escadas/elevador/andares) e Cianwood com portas e conexões bidirecionais.
- [ ] Encontros terrestres, aquáticos, pescaria, treinadores nadadores e mecanismos de Surf/Whirlpool na costa, sem tornar Lugia capturável.
- [ ] Farmácia e SecretPotion com item/key verdadeiro, não duplicação e integração futura à recuperação de Ampharos.
- [ ] Chuck com puzzle da cascata e equipe PBS completa; normal e Master Mode compatíveis com Decades.
- [ ] Esposa de Chuck com Fly realmente fornecido, teste de ida/volta de Olivine e Cianwood e restrição de STORM por região.
- [ ] Validar as duas páginas do cartão do treinador: insígnias da região atual e soma de todas as regiões.
- [ ] Game.exe em Windows e, quando disponível, JoiPlay com save/reload, portas, animações, encontros e regressão Kanto/Decades.
- [ ] Testes CI concluídos com sucesso no commit de integração final; resultados de regressões sintéticas não substituem gameplay.

**Estado oficial:** Etapas 01–09 possuem trabalho parcial, mas nenhuma aprovação integral; **Barra 1: 0/16; Barra 2: 0/16**.
