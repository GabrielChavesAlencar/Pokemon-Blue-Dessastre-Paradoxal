# Johto — Etapa 05/16: Cherrygrove, Violet City, Torre Sprout e Falkner

**Status:** PARCIAL — lógica regional implementada, mapa e ligações reais pendentes.  
**Data:** 12/11/2026  
**Plano:** [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)  
**Progresso:** [JOHTO_ETAPAS.md](JOHTO_ETAPAS.md)

## Entregas reais publicadas no GitHub

| Arquivo | Entrega |
|---|---|
| [scripts/regions/JohtoViolet.rb](../scripts/regions/JohtoViolet.rb) | Funções regionais para a primeira entrada em Violet, Elder Li na Torre Sprout e Falkner; insígnia ZEPHYR e autorização local para Rock Smash |
| [tests/johto_violet_runtime.rb](../tests/johto_violet_runtime.rb) | Testes Ruby independentes de Game.exe: pré-requisitos, derrota, vitória, badge única, esmeraldas, reload e isolamento de Kanto/Decades |
| [tests/test_johto_violet_runtime.py](../tests/test_johto_violet_runtime.py) | Integra os testes Ruby à regressão Python do Blue Studio |
| [data/regions/johto-phase05.json](../data/regions/johto-phase05.json) | Contrato de locais e ligações simbólicas **sem MapIDs inventados**, trainer IDs futuros e flags explícitas de não implantação |
| [tests/test_johto_phase05_contract.py](../tests/test_johto_phase05_contract.py) | Garante o caminho New Bark → Violet, a correspondência de Zephyr com o registro regional e a proibição de declarar etapa instalada sem fonte |

## Comportamento dos eventos

1. **Chegada a Violet City:** `BlueJohtoViolet.violet_intro`, com mensagem de ambientação e progresso registrado uma só vez em `blue_regions["johto_pilot"]`.
2. **Torre Sprout:** `BlueJohtoViolet.sprout_elder` exige início regional válido e encontro com o rival. A batalha contra `BLUE_JOHTO_ELDER` (versão 0) **somente** pode ser invocada depois que o piloto compilar o treinador e registrar o marcador local de prontidão. Derrota não avança a história; vitória só marca o ancião e **não concede** a insígnia do ginásio.
3. **Ginásio de Falkner:** `BlueJohtoViolet.falkner` exige inicial, progresso de rival e treinador PBS compilado. A batalha é `BLUE_JOHTO_FALKNER` (versão 0). **Só após vitória confirmada** chama `BlueRegions.award(state, "JOHTO", "ZEPHYR")`; a própria regra regional impede duplicação no save.
4. **Esmeraldas e duas páginas de treinadores:** a insígnia entra em `achievements["JOHTO"]` e é contabilizada pela regra global de `BlueRegions.crystal_total`, não por incrementos próprios do evento. A ficha local de Johto e a ficha mundial devem reutilizar `BlueRegionalCards`; não duplicar telas nem conceder insígnia nativa de Kanto.
5. **Rock Smash:** `BlueJohtoViolet.rock_smash_allowed?` consulta a regra existente de Johto (ZEPHYR e ferramenta apropriada), sem afrouxar permissões nas outras regiões.
6. **Balanceamento:** este núcleo **não fixa níveis ou equipes fictícias**. Quando o treinador PBS for adicionado, aplicar os hooks atuais de Decades (inclusive Master Mode: 4 Pokémon e escala de 90% segundo a configuração vigente), com comparação com o perfil normal do jogo. O código não deve substituir a lógica geral de batalhas.

Nenhum script modifica os eventos, mapas, itens ou saves instalados de Decades/Kanto. O módulo deve ser carregado **somente** no plugin do futuro piloto isolado de Johto, quando o instalador comprovar mapas e treinadores reais.

## Percurso de mapa obrigatório

O arquivo `data/regions/johto-phase05.json` prevê:

**New Bark Town → Route 29 → Cherrygrove City → Route 30 → Route 31 → Violet City.**

Em Violet, conectar Centro Pokémon, Torre Sprout e Ginásio de Falkner com portas de ida e volta. Antes de concluir a etapa, conferir também as residências, Mart, encontros selvagens e mapas secundários conforme o pacote HGSS/Crystal real.

**Importante:** esses nós são **símbolos planejados**, não MapIDs, nem transições verificadas. O Map Pack original continua indisponível para auditoria aqui; nenhuma dessas ligações foi aplicada à instalação do jogo.

## Pré-requisitos para habilitar treinadores

O comando de batalha de Falkner e o de Elder Li exigem um arquivo **somente no piloto de Johto**:

`Data/blue-johto-violet-ready.txt` contendo exatamente `BLUE_JOHTO_VIOLET_V1_READY`.

**Não criar esse arquivo antecipadamente.** O futuro instalador deverá validá-lo somente após compilar e revisar os treinadores PBS `BLUE_JOHTO_FALKNER` e `BLUE_JOHTO_ELDER`. Ele não existe no jogo principal. Um marcador é uma trava operacional, não substitui os testes de que o treinador realmente existe.

## Testes automáticos

```powershell
python -m unittest discover -s tests -p "test_johto_violet_runtime.py" -v
python -m unittest discover -s tests -p "test_johto_phase05_contract.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
```

Os testes simulam batalha vencida/perdida, salvamento, recebimento único da insígnia, autorização do movimento local, ausência de treinadores, não mistura de conquistas regionais e grafo simbólico. **Passar nesses testes não prova que os mapas, encontros ou ginásio sejam jogáveis.**

## Pendências antes de declarar 05/16 concluída

- [ ] Obter e auditar o Map Pack real com permissões e SHA-256 fixados.
- [ ] Remapear MapIDs verdadeiros e conectar física e bidirecionalmente todos os locais.
- [ ] Construir interiores funcionais e posicionar os eventos e treinadores.
- [ ] Montar equipes PBS e variações de dificuldade de Falkner, treinadores locais e Elder Li com as regras atuais de Decades e Master Mode.
- [ ] Instalar os eventos no piloto isolado, mantendo `Testar Kanto` intacto e saves distintos.
- [ ] Executar o Game.exe de Johto, validar passabilidade, animações, batalhas, ida/volta, obtenção de exatamente **1** ZEPHYR, persistência, repetição sem prêmio duplo e duas fichas de treinador.
- [ ] Validar o uso de Rock Smash somente com a insígnia local e a ferramenta; testar sem badge após viajar de outra região.
- [ ] Exigir regressões automatizadas e aceite manual separado em Windows/JoiPlay.

**Resultado:** primeira lógica de Violet/Falkner implementada. **Barra 1: 0/16; Barra 2: 0/16**, porque as cinco primeiras etapas ainda não satisfazem todos os critérios de aceitação.
