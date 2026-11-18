# Unova A15 — portas técnicas A04–A14, proveniência e prontidão nativa

**Data do inventário histórico:** 17/11/2026. **Escopo desta entrega:** GitHub, exclusivamente leitura e validação de fontes, sem acessar o PC do usuário.

Esta matriz começa **após G08.3**: desenvolvimento documental **Barra G 32/32 (100%)**, enquanto **Barra A técnica 0/8**, **Unova jogável 0/32** e **status `planned`** permanecem inalterados. O auditor A15 passa somente quando **todos os bloqueios ainda são verdadeiros e explicitamente registrados**. Passar na CI **não** significa aprovar um MapID, licença, instalador, QA ou uma região jogável.

Arquivos:

- [Matriz versionada A15](../data/regions/unova-a15-native-readiness-matrix.json) — 11 etapas A04–A14 e 8 portas técnicas de aceite com dependências e recibos ausentes como `null`
- [Auditor A15](../scripts/regions/audit_unova_a15_native_readiness.py) — só lê scripts, documentação e JSON do repositório, verifica fontes cruzadas e impede falsos `approved`/`installable`
- [Testes A15](../tests/test_unova_a15_native_readiness.py) — casos de proveniência, alterações de MapID/registry, direitos falsos, checksums históricos, dependências perdidas, tentativas de promover A e Unova
- [Workflow de CI](../.github/workflows/unova-documentation.yml) — regressão Linux e Windows; portal permanece sujeito ao seu build/teste de GitHub Actions

## 1. O que a investigação existente realmente comprova

| Tema | Observado/documentado | Não autoriza |
| --- | --- | --- |
| Baseline B01/B04/B05 | Histórico de **648 MapIDs** e hash MapInfos `8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420`, registrado nos relatórios e no [catálogo A05](../data/regions/unova-a05-mapid-candidates.json) | Garantir que **a instalação atual** ainda possui os mesmos dados; provar identidade de dono de cada mapa |
| Unova | `518–599`: **82 candidatos** historicamente não ocupados; outras **92** posições de planejamento. O catálogo U03 descreve **74 áreas simbólicas**, e o mapeamento físico por área está vazio | Reservar os 82 IDs, atribuí-los a mapas ou assumir um mapa por área |
| Sinnoh | `442–517`: **76 IDs em retenção administrativa** | Tratar essa retenção como mapa Sinnoh instalado ou liberar automaticamente IDs Unova |
| MapID 3 | A06/A07/A08/A09 relataram duas transferências em `Map001`, eventos **1 Intro** e **2 Quick start intro**, para destino **3** não observado no inventário | Remover ou redirecionar os eventos sem confirmar lógica de introdução e destino real |
| Referências dinâmicas | A09/A10 relataram **20 expressões computadas**; os scanners inertes não executaram os scripts | Declarar as referências resolvidas ou provar ausência de conflito em `518–599` |
| Manifests regionais | Fontes Kanto/Johto/Hoenn apareceram nas análises locais, mas com cobertura parcial; Sinnoh/Unova não comprovaram todos os manifestos de origem/instalação | Atribuir ownership nativo ou direitos de redistribuição |
| QA privada | A13 documentou cópia QA privada; A14 documentou preparação de Windows Sandbox e isolamento de saves | Afirmar `Game.exe` executado e validado, save path efetivo confirmado ou JoiPlay testado |
| Assets/licenças | Auditor [E06](../scripts/regions/audit_unova_e06_rights_inventory.py) classifica os assets como `REVIEW_REQUIRED_NOT_LICENSED` até revisão individual | Redistribuir material de terceiros com base apenas em créditos ou hash |

**Limite de proveniência:** vários números acima vieram de resumos e arquivos apresentados no chat, preservados na documentação. Esta etapa **não** recebeu nem processou os bytes de `MapInfos.rxdata` da instalação atual, os JSONs privados A04–A14, o ZIP doador, o arquivo `Credits.txt` original, logs Game.exe ou dados pessoais. A existência desses relatórios em um PC não equivale à sua validação independente no GitHub.

## 2. Matriz A04–A14: ferramentas já disponíveis, aceites ainda bloqueados

| Etapa | Recurso seguro existente | Condição concreta que ainda impede o aceite nativo |
| --- | --- | --- |
| **A04** | Auditor de MapInfos/MapNNN inerte | Provar baseline e ownership contra instalação efetivamente usada e relatórios brutos auditáveis |
| **A05** | Proposta de 174 candidatos, sem reserva | Conciliar MapInfos, uso dinâmico, outras reservas e origem Unova licenciada |
| **A06** | Leitura de transferências estáticas | Disponibilizar relatório completo das referências e cobertura de scripts/eventos |
| **A07** | Localizador de MapID 3, CommonEvents/Scripts | Revisar os dois eventos de `Map001` com JSON e contexto de execução |
| **A08** | Auditor de eventos e manifests instalados | Resolver ausência/cobertura parcial de manifestos e preservar referências não confirmadas |
| **A09** | Forense das páginas Intro/Quick Start | Validar switches, variáveis, condicional e destino real do warp no jogo |
| **A10** | Matriz de 82 entradas 518–599 | Resolver destinos calculados e reivindicações em todas as versões dos instaladores |
| **A11** | Pré-reserva reversível sem escrita | Manter `reserved=false` até MapIDs e rollback comprovados e revisados |
| **A12** | Análise estática AST dos instaladores | Aceite humano de ownership, versões, fontes, colisões e claims futuros |
| **A13** | Preparador de cópia QA privada | Verificar isolamento efetivo, hashes e recibo da cópia existente; não homologar runtime |
| **A14** | Preparador de VM Windows Sandbox | Executar e relatar QA dentro do ambiente isolado, confirmar localização de saves sem expô-los; a configuração .wsb não é execução |

A15 valida a presença dos **11 auditores e seus 11 documentos**, mas **não os executa contra arquivos do PC**, não gera uma cópia de QA e não cria recibos nativos. Todos os campos `verified_receipt` permanecem `null` e os respectivos estados são `BLOCKED_MISSING_REVIEWED_EVIDENCE`.

## 3. Oito portas de aceite da Barra A — todas pendentes

Estas identificações são **critérios técnicos de revisão internos** à A15, não são oito fases de jogo executadas. O objetivo é tornar as dependências explícitas sem renomear etapas antigas nem inflar o progresso.

| Porta | Entrega física necessária | Dependências e prova faltante |
| --- | --- | --- |
| **A_TECH_01** | Direitos e autoria por asset | A04, A12; inventário doador verificável e aprovação de cada licença |
| **A_TECH_02** | MapIDs físicos reserváveis e propriedade auditada | A04–A12; cobertura de scripts, MapID 3 resolvido, reservas de outras regiões e revisão humana |
| **A_TECH_03** | Mapas e transferências reais de Unova | Portas 01/02; remap `origem → destino` e permissão de utilização dos assets |
| **A_TECH_04** | Instalador reversível em QA isolada | Porta 03, A13/A14; hashes, backup seguro e rollback real com teste |
| **A_TECH_05** | Dados nativos de história e gameplay | Porta 03; eventos das 12 missões, oito ginásios, Elite, rivais, Plasma, equipes, PBS, encontros e balanceamento comprovados |
| **A_TECH_06** | Save e isolamento regional nativos | Portas 04/05; HMs, itens-chave, Boxes, insígnias, restrições de especiais, Centros, blackout, migração e recuperação comprovados |
| **A_TECH_07** | Windows e Android/JoiPlay instaláveis | Portas 04/06; manifestos de release autorizados, incremental confiável, fallback e QA por plataforma |
| **A_TECH_08** | Aprovação humana independente para distribuição | Portas 01–07; evidências reproduzíveis e testes nativos de novos jogos, save/reload, viagens, derrotas e atualização |

Na A15, cada porta mantém `status=PENDING_NATIVE_EVIDENCE`, `approved=false` e `can_install=false`. As **17 evidências obrigatórias** foram criadas com valor `null`. A CI recusa alterar um valor para `true`, `passed`, colocar MapIDs, adicionar novas regiões roteáveis ou mudar as barras sem uma nova fase de review e código correspondente.

## 4. Próximo plano seguro em sequência

**Primeira transição — A16 (inteiramente GitHub):** implementar um *recebedor/verificador de recibos reduzidos* e schema de evidências A04–A14. Aceitar somente **JSONs sanitizados com hashes, metadados de proveniência e decisões humanas explicitamente identificadas**. Detectar dados inconsistentes, snapshots divergentes, versões incompatíveis, referências não resolvidas e provas ausentes. Nenhuma aceitação automática de reserva ou licença.

**Depois da A16:** somente quando existirem evidências suficientes e autorização expressa, revisão de ownership/mapas, obtenção legal de assets, desenho de remap físico, criação de um ensaio de instalação reversível em cópia QA realmente isolada e QA nativo Windows/Android. É proibido pular para instalação ao receber apenas um TXT de resumo ou um hash válido.

**Dependências do usuário para aprovação futura:** JSONs A04–A14 relevantes sem dados pessoais nem arquivos do jogo, referência de origem de mapas, créditos e licenças efetivas, e relatórios de teste dentro de ambiente isolado. Não enviar Game.exe, mapas de terceiros, perfis de saves nem saves pessoais ao GitHub.

## 5. Executar a nova revisão segura no GitHub ou localmente

~~~bash
python scripts/regions/audit_unova_a15_native_readiness.py --check
python scripts/regions/audit_unova_a15_native_readiness.py --matrix
python -m unittest discover -s tests -p 'test_unova_a15_native_readiness.py' -v
~~~

`--check` verifica invariantes e retorna status `SOURCE_GATES_VERIFIED_NATIVE_BLOCKED`. `--matrix` imprime os 11 bloqueios, as oito portas e as provas ausentes em **stdout**, sem gravar relatórios, ler saves, executar instaladores ou acessar Game.exe/JoiPlay.

### Regras de publicação

O GitHub CI Linux e Windows deve passar integralmente. O portal deve preservar 32/32 apenas na **Barra G**, a Barra A em **0/8**, Unova jogável **0/32** e o registro de Unova como `planned`. Só então o PR documental pode ser integrado à `main`. Não será criado pacote nativo, reserva ou licença fictícia nesta etapa.
