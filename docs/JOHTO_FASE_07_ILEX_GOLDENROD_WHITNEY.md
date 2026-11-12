# Johto — Etapa 07/16: Ilex Forest, Rota 34, Goldenrod e Whitney

**Estado:** PARCIAL. O código Ruby para a história, o contrato simbólico de mapas e os testes estão implementados. **Mapas reais, sprites, equipes PBS, interiores, deslocamento, músicas, batalhas no Game.exe e jogabilidade ainda NÃO foram integrados.**

**Início deste núcleo:** 12/11/2026  
**Referências:** [plano de 16 fases](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md), [acompanhamento](JOHTO_ETAPAS.md), [Etapa 06 — Azalea e Bugsy](JOHTO_FASE_06_AZALEA_BUGSY.md).

## Entregas adicionadas ao repositório

| Arquivo | Conteúdo entregue |
|---|---|
| [scripts/regions/JohtoGoldenrod.rb](../scripts/regions/JohtoGoldenrod.rb) | Núcleo de eventos Ilex → Goldenrod, duas etapas de Farfetch'd, recompensa de Cut condicionada, entrada da Rota 34, Day Care, Rádio, Whitney, Floricultura e Sudowoodo opcional |
| [tests/johto_goldenrod_runtime.rb](../tests/johto_goldenrod_runtime.rb) | Teste Ruby com estados simulados de Kanto/Decades/Johto, perdas, vitórias, itens, puzzle, insígnia única, Cut/Strength, save/reload e eventos não duplicados |
| [tests/test_johto_goldenrod_runtime.py](../tests/test_johto_goldenrod_runtime.py) | Inclui o teste Ruby nas verificações Python do Blue Studio |
| [data/regions/johto-phase07.json](../data/regions/johto-phase07.json) | Grafo simbólico dos mapas e interiores previstos de Ilex Forest, Rota 34 e Goldenrod, requisitos de treinadores e gates de aceitação |
| [tests/test_johto_phase07_contract.py](../tests/test_johto_phase07_contract.py) | Valida continuidade com Azalea, grafo sem IDs fictícios, registros de PLAIN/Strength e estado não instalado |

**Proibição:** esses arquivos não são plugins ativos do `game/` principal. Não importar eventos Ruby da fonte de terceiros nem instalar os novos módulos globalmente. A inclusão dos eventos nos mapas só poderá ocorrer na **cópia isolada de Johto**, com origem e licenças verificadas.

## Eventos implementados em Ruby

### Ilex Forest — dois Farfetch'd e Cut

1. `ilex_entrance` exige **HIVE** de Johto e vitória contra o rival de Azalea.
2. `woodcutter` registra a primeira conversa com o lenhador, uma única vez.
3. `farfetchd(0)` e `farfetchd(1)` exigem a conversa e o estado correto; o segundo só avança depois do primeiro. Não aceitam índices fora da lista.
4. `cut_reward` exige os dois Farfetch'd devolvidos e um item real `HM01` confirmado no catálogo do jogo. Sem item existente ou marcador local verificado, **não inventa prêmio nem altera o inventário**. Registra `ilex_cut_rewarded` somente após `pbReceiveItem` devolver sucesso.
5. `forest_exit(tool_ready)` exige o prêmio registrado, a HIVE regional e a ferramenta de Cut disponível; apenas depois marca a passagem para a Rota 34.

**Limite importante:** o estado do puzzle foi programado, mas a orientação dos Farfetch'd, a IA, as posições de NPCs, o caminho e as colisões ainda dependem dos eventos/cartas RMXP efetivos. O script não comprova que o puzzle seja jogável. A chave `HM01` precisa ser confrontada com o catálogo real de itens antes da criação do marcador.

### Rota 34 e Goldenrod

- `day_care`: apresenta o serviço, **sem implementar criação de ovos ou substituir o Day Care do jogo nativo**.
- `goldenrod_arrive` e `underground`: registram introduções locais idempotentes.
- `radio_quiz`: três perguntas **originais de orientação sobre as regras regionais Blue**; respostas incorretas ou cancelamento não registram o quiz como concluído. Não é uma transcrição do HGSS e **não concede Radio Card nem item fictício**.
- A planta futura inclui Centro Pokémon, Mart/Department Store, Rádio, Ginásio, Loja de Bicicletas, Underground (duas entradas), Floricultura e suas escadas/saídas de volta.

### Whitney — Ginásio de Goldenrod

1. Exige HIVE, saída de Ilex concluída e quiz da Rádio.
2. A equipe PBS `BLUE_JOHTO_WHITNEY` versão 0 precisa estar **compilada e verificada**. O piloto só então pode escrever `Data/blue-johto-goldenrod-ready.txt` com `BLUE_JOHTO_GOLDENROD_V1_READY`.
3. `whitney`: somente vitória verdadeira marca `goldenrod_whitney_won=true`; perder não atribui PLAIN.
4. `whitney_badge`: a segunda conversa após Whitney chorar concede **PLAIN** exatamente uma vez com `BlueRegions.award(state, "JOHTO", "PLAIN")`. Repetir o encontro ou carregar o save não cria outra insígnia.
5. A soma global de esmeraldas permanece responsabilidade do circuito original (`BlueRegions.crystal_total`), não do evento do ginásio.
6. `strength_allowed?(tool_ready)` só autoriza Strength com **PLAIN local + ferramenta real**, sem usar insígnia de Kanto.

A equipe, os níveis, a formação de Whitney e o Master Mode devem ser definidos no PBS futuro usando **os mesmos hooks de balanceamento já existentes em Decades**. Nada no módulo altera a escala ou inventa uma equipe antes de inspecionar o jogo.

### Floricultura e Sudowoodo (preparação para a Rota 36)

- `flower_shop` só concede uma SquirtBottle se PLAIN existir, o marcador do piloto estiver validado, a chave `SQUIRTBOTTLE` existir no catálogo real e `pbReceiveItem` retornar sucesso. Sem isso, fica bloqueada.
- `sudowoodo` é apenas um **gancho futuro**. Exige SquirtBottle na Bag, espécie existente, mapa/evento revisado, marcador do piloto e resultado confirmado da batalha. Não modifica a Rota 36 nem concede passagem no jogo atual.
- O evento físico da Rota 36, as reações da árvore, a captura, derrota, fuga e persistência devem ser verificados no Game.exe; o retorno booleano de `pbWildBattle` precisa ser conferido no runtime real **antes** de liberar o gancho.

## Contrato de mapas

O [grafo simbólico](../data/regions/johto-phase07.json) conecta:

**Azalea → Ilex Forest Gate → Ilex Forest → Rota 34 → Goldenrod.**

Os interiores e conexões são **planejados**; não existem MapIDs, coordenadas, tilesets ou warps auditados. O grafo também prevê o templo da floresta, Day Care, Centro Pokémon, Ginásio, Rádio, lojas, entradas do Underground e Floricultura. A Rota 35/National Park e a passagem de Sudowoodo na Rota 36 terão validação na **Etapa 08**.

A validação de mapas verdadeiros continua bloqueada pela ausência do ZIP/RAR auditado do Map Pack, incluindo direitos individuais de gráficos e músicas.

## Verificações automatizadas

```powershell
python -m unittest discover -s tests -p "test_johto_goldenrod_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase07_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
```

A infraestrutura sintética simula recompensa de item entregue/não entregue, vitória/derrota, marcação e não duplicação da PLAIN, tentativas de pular Farfetch'd, resposta errada no quiz, uso de Strength/Cut sem ferramenta, roteiro de Sudowoodo, troca de região e save/reload.

Os testes só provam o **comportamento do código isolado**. Não provam que os NPCs ou mapas estão corretamente posicionados, que equipes PBS realmente existam, nem que o Game.exe execute os eventos.

## Critérios pendentes para conclusão real de 07/16

- [ ] Extrair pacote autorizado e auditar mapas/tilesets em `.blue-work/`; preservar hashes do Kanto e Decades.
- [ ] Remapear IDs sem colisão e montar Ilex/Route 34/Goldenrod em `.blue-work/johto-pilot/`.
- [ ] Implementar física e IA das duas capturas de Farfetch'd; HM Cut com **ID verdadeiro** e testes em campo.
- [ ] Validar Day Care, todas as portas, elevadores, lojas, Rádio, Underground, NPCs e saídas bidirecionais.
- [ ] Compilar as equipes de Whitney e treinadoras do ginásio; aplicar balanceamento normal e Master Mode do projeto, sem reescrever níveis em scripts.
- [ ] Executar Whitney no Game.exe: derrota sem prêmio, vitória, choro, segunda conversa e exatamente uma PLAIN em ambos os cartões de treinador.
- [ ] Verificar a SquirtBottle e o encontro especial de Sudowoodo na sua fase física correspondente; sem antecipar o desbloqueio da Rota 36.
- [ ] Repetir regressão Blue Studio, piloto de Kanto, saves Decades e teste Windows/JoiPlay quando os mapas estiverem disponíveis.

**Barra 1 (núcleos integralmente aprovados): 0/16. Barra 2 (gameplay integralmente aprovado): 0/16.** A Etapa 07 está **PARCIAL**.
