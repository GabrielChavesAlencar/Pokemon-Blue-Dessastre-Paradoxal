# Unova G04.4 — auditoria de encontros, probabilidades e lacunas

**WHITE_BW** · **Status: somente GitHub, planned** · **Nenhuma fonte nativa de encontros foi verificada.**

## Escopo desta entrega

A G04.4 encerra a trilha G04 da Barra G como auditoria *offline*, **não** como instalação de encontros. A G04.1 catalogou 74 áreas U03; a G04.2 verificou 20 nomes de métodos PBS e gerou perguntas para 34 áreas; a G04.3 registrou regras de evolução dinâmica. A G04.4 valida agora a **integridade de tabelas sintéticas** e torna explícitos os dados reais ainda faltantes.

Arquivos:
- [Contrato G04.4](../data/regions/unova-g04-encounter-validation-contract.json)
- [Validador somente leitura](../scripts/regions/audit_unova_g04_encounter_validation.py)
- [88 testes automatizados](../tests/test_unova_g04_encounter_validation.py)
- [Contrato G04.2](../data/regions/unova-g04-encounter-methods-contract.json)
- [Contrato G04.3](../data/regions/unova-g04-wild-scaling-contract.json)

## O que é validado

Uma tabela de exemplo só pode ser avaliada quando fornece explicitamente um agrupamento com os campos **área, método PBS, período, estação e versão (White BW)**. A soma de pesos é verificada separadamente **dentro de cada agrupamento**, sem somar listas distintas de período, estação, método ou área.

- **Tabela sintética completa:** todas as espécies, faixas de nível, pesos e taxa de encontro estão preenchidas; os pesos de slots precisam totalizar 100%.
- **Tabela sintética incompleta:** qualquer espécie, peso, faixa de nível, taxa ou lista de slots ausente deixa a soma global como **null** (desconhecida); ela não é aceita como tabela integral.
- **Duplicações:** duas tabelas com exatamente as mesmas cinco chaves são bloqueadas. Um slot exatamente repetido dentro da mesma tabela também é bloqueado. A mesma espécie em faixas de nível diferentes continua permitida.
- **Faixas:** níveis precisam ser inteiros positivos e respeitar o máximo do motor fornecido no fixture; limites mínimo/máximo invertidos são bloqueados.
- **Identidades:** só são aceitos IDs `FIXTURE_*` em simulações. Não é permitido declarar `PATRAT` ou qualquer Pokémon real de Unova sem proveniência.
- **Eventos especiais:** áreas como Liberty Garden, ginásios e locais marcados como eventos não recebem tabelas selvagens sintéticas.
- **Taxa de encontro:** mantida separada dos pesos dos slots. A unidade real da taxa PBS não é presumida como percentual; não ocorre normalização automática.

O sistema de evolução dinâmica da G04.3 oferece chances condicionais de **15%, 30%, 45% ou 60%** para transformar a espécie de um slot existente, o que **não** cria novas chances de encontro nem modifica a soma dos pesos.

### Exemplo reproduzível (não nativo)

Uma tabela de exemplo de Route 1 com dois slots fictícios de 80% e 20% na primavera é considerada **completa apenas como fixture**. Um exemplo para a noite/inverno com espécie, peso, nível e taxa `null` é sinalizado como **incompleto**. Outro exemplo no verão/método Water é avaliado independentemente; seus pesos não são somados aos da primeira tabela.

Todas as taxas e espécies dos exemplos são inventadas **exclusivamente como massa de teste**, sem corresponder aos encontros de Unova.

## Proveniência e lacunas

Em cada uma das **74 áreas simbólicas**, os campos `native_species`, `native_encounter_rate`, `native_weights`, `native_levels`, `native_map_id` e `native_table_provenance` permanecem `null`; `native_slots=[]`, `native_pbs_verified=false` e `native_method_verified=false`.

O inventário de evidências continua **todo null**, incluindo caminho e SHA-256 do PBS real de encontros, fonte/licença, vínculos de mapas, períodos, estações, versões, espécies e taxas. **Null não significa 0% ou ausência de Pokémon.** As 40 áreas sem métodos candidatos também não são declaradas vazias no jogo.

A G04.4 **não** altera PBS, Game.exe, RXDATA, scripts nativos, saves, níveis, pesos ou instalações. Nenhuma simulação valida a jogabilidade Windows/Android.

## Como executar

~~~bash
python scripts/regions/audit_unova_g04_encounter_validation.py --check
python scripts/regions/audit_unova_g04_encounter_validation.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g04_encounter_validation.py' -v
~~~

O CI executa o auditor e os testes na suíte Linux/Windows de Unova, além do portal.

## Próxima frente: G05.1

Após a G04.4, a próxima tarefa da Barra G é **G05.1 — HMs e itens-chave exclusivos por região**, começando com um contrato não intrusivo para inventário regional, sem transferir itens-chave entre regiões, sem quebrar a persistência dos saves ou presumir Unova instalada.
