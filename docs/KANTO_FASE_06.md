# Kanto — Fase de desenvolvimento 06/16

**Estado:** implementação e testes nativos/unitários **aprovados** na CI; aceitação de jogabilidade e cobertura de fluxos alternativos **pendente**.  
**Barra de desenvolvimento:** **06/16 = 37,5%**.  
**Barra de aceitação concluída:** **01/16 = 6,25%**, **15 pendentes**.  
**Plano de referência:** [PLANO_REGIOES_DESSASTRE_V2.md](PLANO_REGIOES_DESSASTRE_V2.md), seções 17, 19 e 20.

## 1. Correções dos testes adicionais do Codex

O diagnóstico relatou dois problemas reproduzíveis que precedem a fase 06:

### A. PC de Decades bloqueado sem a expansão

**Correção:** [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb) exige que Kanto tenha sido realmente instalada e que exista um save regional v1 válido. Uma partida legada que permaneceu em Decades **não recebe retroativamente** bloqueios de lendários/Paradoxos no PC, mesmo se os mapas forem instalados posteriormente. Ao visitar outra região, o histórico de viagem passa a informar a política regional correspondente.

**Regressão:** [region_policy_runtime.rb](../tests/region_policy_runtime.rb) verifica os casos sem instalação, após instalar Kanto e com a expansão regional realmente em uso. Nenhum save antigo precisa ser migrado destrutivamente.

### B. Quatro retratos de treinadores ausentes na instalação integrada

**Correção:** [install_kanto.py](../scripts/regions/install_kanto.py) inclui os quatro PNGs `Graphics/Trainers/BLUE_KANTO_{RIVAL,BUGCATCHER,CAMPER,LEADER}.png` gerados pelo piloto. O importador não copia gráficos indiscriminadamente. A CI exige os quatro retratos na instalação integrada.

**Instalações já existentes:** rode [KANTO_CORRIGIR_RETRATOS.bat](../KANTO_CORRIGIR_RETRATOS.bat) **com o jogo fechado**. O modo `--repair-portraits` usa os retratos originais correspondentes já presentes em `game/Graphics/Trainers/`, exibe uma prévia, pede confirmação e adiciona apenas os PNGs faltantes. Se encontrar um PNG modificado, **recusa sobrescrevê-lo**. Mantém backup do manifesto e rollback de alterações parciais. O [atalho original](../KANTO_INSTALAR_NO_JOGO.bat) redireciona ao reparo quando Kanto já está instalada; não reinstala os 13 mapas.

## 2. Insígnias regionais e balanceamento Blue

- `BlueRegions.award` preserva a chave da conquista `KANTO:BOULDER` e todas as demais como identificadores únicos e impede prêmio duplicado.
- `BlueRegions.crystal_total` adiciona as conquistas regionais **ao total nativo** sem modificar o array de esmeraldas/badges de Decades.
- `BlueStory.stage`, quando chamado sem um total explícito, considera **esmeraldas nativas + conquistas locais únicas**, mantendo os limites de estágio anteriores. Chamadas com um total explícito continuam reproduzíveis.
- O único ginásio real disponível no piloto ainda é **Brock**; não se atribuem sete insígnias fictícias só para testar. Testes unitários podem concedê-las no estado descartável para validar a liberação.

## 3. Pokémon especiais — política regional

[RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb) reaproveita o classificador por flags `Legendary`, `Mythical`, `UltraBeast` e `Paradox` de [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb). O gerador atual das espécies autorais marca explicitamente as espécies com categoria `past_paradox` ou `future_paradox` com a flag `Paradox`; não bloqueia todas as espécies com a flag geral `DessastreParadoxal`.

- Até **8 conquistas locais**: especiais não podem ser retirados da Box para a party; inserções diretas via `PokemonStorage` são rejeitadas; presentes via funções nativas do Essentials são direcionados ao PC; capturas tentam armazenamento direto na Box.
- Ao ganhar a oitava conquista da região, o bloqueio desaparece automaticamente **sem forçar o retorno dos Pokémon à party**.
- A entrada em um mapa regional pode reconciliar uma party alterada por scripts/loads, **somente se houver vaga no PC e sobrar Pokémon comum utilizável**. Caso contrário, não descarta nem substitui Pokémon.
- No caso extremo de PC totalmente cheio durante uma captura, mantém-se o fluxo original do jogo para **não perder silenciosamente o Pokémon capturado**. Esse cenário exige tratamento adicional de UI antes de declarar cobertura integral.
- A política não se aplica ao Hub de Batalha nem a saves antigos de Decades que não iniciaram viagens regionais.

**Ainda não totalmente coberto:** plugins de terceiros que alterem a party diretamente, troca externa por scripts sem entrar em mapa, certos fluxos de criação/evolução, e teste de capturas/PC cheio em sessão gráfica real.

## 4. HMs e movimentos de campo

`BlueRegions.field_access` já armazena os pré-requisitos por região no registro. Agora [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb) integra a checagem aos handlers do Essentials 21.1 para Cut, Flash, Fly, Strength, Surf, Rock Smash, Waterfall, Dive e os movimentos com regras cadastradas.

- **Kanto:** Flash exige Boulder, Cut exige Cascade, Fly exige Thunder, Strength exige Rainbow, Surf exige Soul, Rock Smash exige Marsh, Waterfall exige Volcano.
- A checagem respeita a *insígnia local* do mapa/região atual em vez do contador global.
- **Decades:** os métodos nativos permanecem com seus próprios pré-requisitos; não se altera a progressão de HMs da campanha original.
- O guard intercepta uso a partir do menu da equipe e chamadas padrão de campo; métodos específicos de plugins e ações alternativas ainda precisam de auditoria manual.

## 5. Testes e evidências

- [test_regions.py](../tests/test_regions.py) executa as regras Ruby de Kanto, Decades, PC, presentes, oito badges locais e HM.
- [test_kanto_installer.py](../tests/test_kanto_installer.py) comprova que os quatro retratos são exigidos, o reparo é idempotente, os saves são preservados e imagens personalizadas não são sobrescritas.
- [KantoIntegratedCheck.rb](../scripts/regions/KantoIntegratedCheck.rb) valida a política dentro do `Game.exe` em uma cópia descartável da instalação; a CI também verifica os quatro retratos na instalação integrada.
- [GitHub Actions — Kanto: teste nativo aprovado, incluindo 4 retratos, PC, presente especial, insígnia e HM](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43139789644)
- [GitHub Actions — regressões Ruby/Python aprovadas](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43139468440)

## 6. Pendente para a aceitação final

- [ ] Confirmar o fluxo de PC e captura **visualmente no Windows**, com especiais, ovos, party completa, PC cheio e 8 insígnias.
- [ ] Confirmar os efeitos reais de Cut/Surf/Flash e permissões regionais no mapa.
- [ ] Testar contra cenários de presentes, trocas/evoluções e plugins customizados que alterem party.
- [ ] Confirmar o balanceamento Blue antes/depois de cada conquista regional e a integração com os registros de esmeraldas do jogo instalado.
- [ ] Fechar as verificações manuais herdadas das etapas 2–5, inclusive a viagem pelo menu e o NPC pós-Liga.

O diagnóstico gráfico local do Codex terminou em `WinError 0`, que **não demonstra por si só falha na engine** nem sucesso no teste interativo; a validação visual permanece aberta. **A contagem de etapas totalmente aceitas continua em 1/16 até evidências manuais.**
