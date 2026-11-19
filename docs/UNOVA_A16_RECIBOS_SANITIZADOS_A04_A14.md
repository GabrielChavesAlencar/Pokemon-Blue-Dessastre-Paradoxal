# Unova A16 — recepção offline de recibos A04–A14 sanitizados

**Versão:** A16, schema JSON 2020-12, 17/11/2026. **Estado da região:** `planned`. **Barra G:** 32/32; **Barra A técnica:** 0/8; **Unova jogável:** 0/32. Esta entrega é de diagnóstico/documentação e **não aprova MapIDs, fontes de mapas, direitos, runtime nem distribuição**.

## Resultado entregue no GitHub

| Artefato | Função |
| --- | --- |
| [Schema A16](../data/regions/unova-a16-receipt.schema.json) | Estrutura JSON com `additionalProperties=false`, tipos restritos, fingerprints SHA-256 e onze recibos obrigatórios |
| [Contrato A16](../data/regions/unova-a16-receipt-contract.json) | Fontes A15/A05/G08, limite 128 KiB, dois modos e condições explícitas para A17 |
| [Auditor A16](../scripts/regions/audit_unova_a16_receipt_intake.py) | Verificação offline, hash-chain de recibos, hashes de manifests/Map001 e bloqueios de licenças/QA falsos |
| [Testes Python](../tests/test_unova_a16_receipt_intake.py) | Fixtures positivas/negativas, inclusive com **todos os hashes recalculados** para comprovar que hash válido não é autorização |
| [Testes portal](../site/tests/unova-a16.test.mjs) | CI protege o registro Unova `planned`, G 32/32 e as duas barras nativas em zero |
| [CI Unova](../.github/workflows/unova-documentation.yml) | `--check` e `--simulate-demo` no Linux, testes Python/Node no Linux/Windows e build/testes do portal |

O auditor revalida primeiro a [matriz A15](../data/regions/unova-a15-native-readiness-matrix.json), com onze etapas A04–A14, oito portas nativas e suas 17 provas ausentes. **Passar na validação A16 não significa verificar essas provas**: o resultado de um pacote consistente é sempre `UNVERIFIED_RECEIPTS_AWAIT_INDEPENDENT_REVIEW`.

## 1. Modelo de recibo

O bundle usa uma única versão de schema (`schema_version=1`) e exige, de forma exata:

- **Identidade de origem:** `A16`, `UNOVA`, `WHITE_BW` e `mode` igual a `SYNTHETIC_FIXTURE` ou `REDACTED_UNVERIFIED`; não existe modo `NATIVE_APPROVED`.
- **Baseline B01/B04/B05:** SHA-256 histórico de `MapInfos`, 648 mapas relatados, revisão `HISTORICAL_UNVERIFIED`, intervalo candidato `518–599` (82 sem reserva), retenção Sinnoh `442–517` (76 sem reserva) e zero MapIDs atribuídos. A16 **não** relê os bytes nativos e não confirma que o snapshot ainda corresponde ao jogo atual.
- **Seis manifestos regionais:** Decades, Kanto, Johto, Hoenn, Sinnoh, Unova. Apenas dados reduzidos `source_status=UNVERIFIED_SOURCE_METADATA_ONLY`, SHA-256 de metadados de origem opcional e `native_claims=[]`. Um resumo sem manifesto não prova ausência de reivindicações de MapID; a cadeia inclui `regional_manifests_sha256` calculado sobre todos esses metadados.
- **Map001 / destino 3:** duas entradas simbólicas (`map_id=1`, eventos `1` e `2`, página `1`, destino `3`) segundo relatórios históricos; `mapid_3_resolved=false`, **20 expressões computadas ainda sem resolução**, `script_runtime_verified=false`. A impressão `intro_map001_sha256` evita que o resumo mude sem detectar inconsistência.
- **A04→A14:** 11 recibos ordenados, com `depends_on` idêntico à matriz A15, `baseline_sha256`, `mapinfos_sha256`, `mapids_inventory_sha256` (opcional e **não homologado**), `source_revision`, hashes dos manifestos e de Map001, `previous_receipt_sha256` e `receipt_sha256`. A16 recalcula todas as impressões e bloqueia qualquer lacuna, reordenação, mudança de baseline ou dependência.
- **Direitos e review:** `asset_review_status=REVIEW_REQUIRED_NOT_LICENSED`, `license_verified=false`, `redistribution_approved=false`, `human_decision=NOT_REVIEWED` e `approval_receipt_sha256=null`. QA Game.exe/Android, instalação, reserva e salvamento permanecem **false**.
- **Integridade completa:** `bundle_sha256` é calculado sobre todo o JSON canônico (ordem lexicográfica das chaves, separadores compactos, ASCII, sem NaN) excluindo o próprio campo. O SHA-256 **detecta alterações, mas não autentica o autor, a origem, a licença ou os bytes reais**.

O validador exige exatamente as chaves permitidas. Não existem campos para caminhos de arquivos fonte, URLs de downloads, binários, dados pessoais, texto de eventos, perfis de save ou conteúdo de assets. Alterações desconhecidas são rejeitadas.

## 2. Como usar sem acessar o jogo

A16 é um programa **Python padrão**, não um instalador. Não roda `Game.exe`, Windows Sandbox, JoiPlay ou Blue-Story e não usa rede. Só lê os contratos versionados do GitHub, ou um **único** JSON sanitizado que o operador indicar expressamente.

~~~bash
python scripts/regions/audit_unova_a16_receipt_intake.py --check
python scripts/regions/audit_unova_a16_receipt_intake.py --simulate-demo
python scripts/regions/audit_unova_a16_receipt_intake.py --print-synthetic-fixture
python scripts/regions/audit_unova_a16_receipt_intake.py --verify-json recibos_unova_sanitizados.json
~~~

`--print-synthetic-fixture` imprime um pacote **sintético e não probatório** com os onze recibos e digests gerados para dados fictícios/relatados. A fixture pode ser copiada para um JSON independente para testar `--verify-json`, mas **não deve ser enviada como comprovante de execução nativa**.

`--verify-json` exige arquivo `.json` explicitamente indicado, sem symlink, com no máximo **128 KiB**; rejeita encoding inválido, BOM, chaves duplicadas, NaN e dados fora do schema. Não abre arquivos citados no conteúdo, não segue caminhos de mapas/manifestos, não lê saves e não produz relatórios em disco. O resultado na saída padrão é **apenas o estado de pré-validação**, mesmo quando todos os hashes conferem.

**Saída esperada de um pacote internamente consistente:**

~~~json
{"phase":"A16","status":"UNVERIFIED_RECEIPTS_AWAIT_INDEPENDENT_REVIEW","receipts_verified_for_internal_integrity":11,"can_reserve_mapids":false,"can_install":false,"can_release":false,"native_technical_completed":0,"native_playable_completed":0}
~~~

*O comando real inclui campos adicionais de ressalvas; a linha acima mostra somente os indicadores essenciais.*

## 3. Testes positivos e negativos

As fixtures em memória exercitam os dois modos permitidos: `SYNTHETIC_FIXTURE` e `REDACTED_UNVERIFIED`. Nenhum modo representa um atestado real. São testados:

- **Hashes e proveniência:** mudança do SHA histórico de MapInfos, contagem de mapas, troca de revisão, snapshot novo, cadeia A04–A14 quebrada, recibos duplicados, ordem trocada e dependências ausentes.
- **Manifestos e MapIDs:** integridade da lista de seis regiões, manifest ausente/inventado, claim doador atribuído sem prova, reserva em 518–599, sobreposição de Sinnoh, MapID de destino arbitrário, intro Map001 adulterada ou MapID 3 falsamente resolvido.
- **Direitos/segurança:** licenças fabricadas, revisão humana `APPROVED`, permissão de redistribuição, recibo de autorização, Game.exe/JoiPlay simulados como testados, saves lidos ou modificados, pacote nativamente instalável e status `playable`.
- **Ataques ao formato:** payload JSON com chaves duplicadas, extensões inesperadas, tipo incorreto, 128 KiB ultrapassados, `.exe` no lugar de JSON e caminhos/atributos extras.
- **Rehash total:** os testes também recalculam o SHA de **cada** receipt e do bundle depois de adulterar MapIDs, versões, direitos, status e QA. Mesmo com digests matematicamente corretos, a política fail-closed **deve recusar a prova falsa**.

No CI a suíte A16 é executada juntamente com as regressões A04–A15, G01–G08 e portal. O Windows realiza verificação Python e o portal mantém seus testes de build e estado `planned`. Falha de qualquer etapa impede o merge.

## 4. Limitações que não desaparecem

A16 não é verificação forense do jogo instalado. O SHA histórico de MapInfos e a contagem 648 são baseados em relatórios anteriores, **não rechecados no computador atual**. Os 82 IDs 518–599 são candidatos sem reserva; não é permitido inferir que 74 áreas simbólicas cabem neles. Dois comandos da intro ainda apontam ao destino MapID 3 ausente no histórico, e as referências calculadas não foram resolvidas em execução real.

Os resumos reduzidos **não validam autoria, permissão, integridade de bytes originais, instalação nem local real dos saves**. Mesmo o recebimento de recibos coerentes não modifica as **17 evidências A15** (todas continuam `null`) nem permite promover a Barra A.

## 5. Próxima ação técnica segura — A17

Preparar **revisão independente e conciliação** dos recibos A04–A14 efetivamente obtidos, verificando:

1. Baseline atual MapInfos/MapIDs com recibos originais auditados fora do repositório;
2. Manifestos regionais completos e reservas dos instaladores (inclusive Sinnoh/Unova) e destinos dinâmicos;
3. Contexto de `Map001` eventos 1 e 2 para decidir o MapID 3 **sem modificar os eventos por suposição**;
4. Proveniência e direitos verificáveis por asset;
5. QA em Windows Sandbox e JoiPlay com dados descartáveis isolados, somente quando o operador tiver controlos e autorização adequados.

A17 poderá formalizar inconsistências e decisões humanas, mas **não deve automaticamente aprovar licenças, reservar MapIDs, instalar mapas ou alterar saves**. Nenhum dos dados privados/raw deve ser colocado no GitHub. Manter `A 0/8` e `Unova jogável 0/32` até haver evidências nativas aceitas em fases distintas.
