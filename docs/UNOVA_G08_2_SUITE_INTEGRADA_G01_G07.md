# Unova G08.2 — suíte integrada G01–G07 (somente offline)

**Entregável:** auditoria de integração e testes de contratos de Unova White; não existe instalação de mapas de Unova no Game.exe nem em JoiPlay.

## Finalidade

A G08.2 adiciona **testes cruzados de fontes de verdade**. Enquanto as tarefas G01–G07 já testavam seus próprios contratos, esta etapa confere que os vínculos entre capítulos, ginásios, eventos, encontros, inventário regional, blackout, viagem, portal e atualizações sintéticas não divergem quando utilizados em sequência. Todos os dados permanecem `planned` e nenhum nível, MapID, encontro ou batalha nativa é criado.

Os principais arquivos:

| Caminho | Propósito |
| --- | --- |
| `data/regions/unova-g08-integrated-contract.json` | Cobertura obrigatória, 22 marcos G01–G07, 74 áreas e regras fail-closed |
| `scripts/regions/audit_unova_g08_integrated.py` | Verificador cruzado, `--check` e demo encadeada `--simulate-demo` |
| `tests/test_unova_g08_integrated.py` | Cenários positivos, adulteração de contratos, CAS, fontes falsas e falhas injetadas |
| `site/tests/unova-integration.test.mjs` | Ligações do guia/portal G06 com contratos G01/G02/G03/G04/G05/G07; filtros e conteúdos falsamente jogáveis |
| `.github/workflows/unova-documentation.yml` | Auditorias e testes em Linux/Windows; testes do guia/portal em Node |

## Matriz de integração

| Blocos | Evidência cruzada e teste |
| --- | --- |
| **G01.1–G01.4** | 12 capítulos de campanha, 12 missões, 12 transições em ordem e validadores de serialização/reentrada de estado sintético |
| **G02.2–G02.4** | 8 ginásios vinculados a missões, líderes e áreas, suas 8 insígnias *sintéticas*, 4 membros da Elite Four, Castelo de N e pós-jogo sem itens nativos |
| **G03.2–G03.4** | Rivais e Plasma: equipes e níveis PBS não verificados, recibos narrativos únicos, evolução e balanceamento MASTER simulados e catálogo de rematches sem duplicar recompensas |
| **G04.2–G04.4** | Cobertura das **mesmas 74 áreas** entre métodos, escala e validação de encontros; nenhuma taxa, espécie, slot ou MapID nativo pode se tornar válido por inferência |
| **G05.1–G05.4** | Item-chave/HM da região atual separado de TMs compartilhadas, proteção de insígnias, viagem para Unova negada; blackout retorna ao Centro da região atual e mantém dinheiro, Boxes, progresso e mecânicas |
| **G06.2–G06.3** | Portal de 74 áreas, 12 capítulos, 12 missões, ginásios e treinadores indexados pelas mesmas chaves, URLs e buscas contextuais, nunca exibindo conteúdo falsamente instalado |
| **G07.2–G07.4** | Manifesto SHA-256 e direitos obrigatórios, canais Windows/Android apenas contratuais, CAS completo, backup e rollback em memória em 7 etapas por perfil |
| **Barra A e jogabilidade** | 0/8 e 0/32; Unova continua `planned`, inclusive depois de concluir a Barra G |

Os módulos originais são carregados e **validam as fontes existentes**, antes de verificar os cruzamentos. Não se substituem as validações internas por mocks de dados inventados. `validate_links` recusa capítulos fora de ordem, missões sem áreas, insígnias com ID nativo, equipes e níveis falsificados, treinadores Plasma com eventos inexistentes e tabelas de encontro G04 com MapIDs e rates falsamente verificados.

## Demonstração encadeada

`--simulate-demo` executa, na mesma invocação Python:

1. Campanha simbólica G01 até o último capítulo, com serialização e reentrada validadas pelos módulos predecessores.
2. Oito ginásios G02.2 e Elite Four/castelo G02.3 sem créditos reais; rivais/Plasma G03.3 com recompensas sintéticas e escala G03.2.
3. Tabelas de encontros G04.4 apenas de fixtures, isolamento regional de HMs/TMs G05.1/G05.3 e perda de batalha G05.4 preservando dinheiro, Boxes e estado.
4. Pacote de dois arquivos **documentais** G07.2, versão e origem simuladas; cada perfil G07.4 (Windows/Android) usa o CAS G07.3 e passa pelos sete pontos de falha com restauração integral.

**Limite:** os demos dos contratos não são o jogo rodando. Os módulos verificam cenários de referência e retornam apenas objetos Python; não alteram Game.exe, saves, instaladores, pastas de assets nem arquivos RXDATA.

## Testes negativos

A suíte injeta alterações no catálogo carregado: MapIDs em capítulos, NPCs, líderes e encontros; equipe e níveis de rival falsificados; registros de vitória/recebimento de insígnia com proveniência inexistente; áreas removidas ou duplicadas; transição de capítulo incorreta; promoção da região a `playable`; direitos nativos inventados e release autorizado sem licença.

Também executa falhas G07.3 antes e depois de staging, após backup e após o primeiro arquivo alterado, durante CAS e antes da publicação, nas duas plataformas. Editar saves, checkpoints, Boxes, itens-chave, mecânicas e cada região protegida entre staging/CAS precisa impedir a publicação do candidato. Quando ocorre rollback, o estado sintético completo é idêntico ao original; operações reais nunca acontecem.

Testes do portal também verificam crosswalk de 74 áreas de G04 com G06, vínculo das 12 missões G01, 8 ginásios G02, Elite Four, confrontos de G03 e bloqueio de atribuições nativas falsas a qualquer cartão, filtro ou URL.

## Comandos

~~~bash
python scripts/regions/audit_unova_g08_integrated.py --check
python scripts/regions/audit_unova_g08_integrated.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g08_integrated.py' -v
npm run build --prefix site
npm test --prefix site
~~~

A esteira `unova-documentation.yml` valida o auditor e as regressões Python/Node no Linux e a suíte Python no Windows. O workflow de portal executa build e testes do site. Atualizar a Barra G para **31/32 (97%)** apenas depois de todos os jobs passarem e do merge na `main`.

### Pendências reais

Continuam sem confirmação os mapas, MapIDs, equipes nativas, rates/slots, batalhas de treinadores e NPCs, licenças, QA de Windows e JoiPlay e a instalação de Unova. A Barra A **0/8** e Unova jogável **0/32** não podem ser alteradas com base nesta suíte.

**Próximo marco: G08.3**, matriz de regressão multirregional offline cruzando Kanto, Johto, Hoenn, Sinnoh e Decades, mantendo as mesmas fronteiras de licenças, progresso e estado sintético.
