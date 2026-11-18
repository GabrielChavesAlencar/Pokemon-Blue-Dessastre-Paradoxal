# Unova G08.3 — regressão multirregional offline e critérios para jogabilidade real

**Escopo:** uma matriz de **6 regiões** executada **somente com dados sintéticos em memória**. Não lê saves reais, não executa Game.exe/Blue-Story/JoiPlay, não baixa nem instala mapas. Mesmo após concluir G08, Unova continua `planned`, Barra A técnica **0/8**, Unova jogável **0/32**.

## O que esta entrega acrescenta

- `data/regions/unova-g08-multiregional-contract.json` — contrato fail-closed, dependências G08.2/G05/G07, seis perfis, lista de transições permitidas apenas em fixture, recursos protegidos, 16 pontos de falha e evidências nativas `null`.
- `scripts/regions/audit_unova_g08_multiregional.py` — verifica G08.2 como pré-requisito, registos do portal, políticas G05/G07, matriz de compatibilidade, viagens simuladas, checkpoints, CAS de todo o estado e retorno após falhas.
- `tests/test_unova_g08_multiregional.py` — testes positivos, entradas indevidas, contratos adulterados, dados nativos falsificados, conflitos e rollback.
- `site/tests/unova-multiregional.test.mjs` — comparação dos seis perfis do portal com fontes G05/G07 e proibição de interpretar a Barra G **100%** como jogabilidade.
- `.github/workflows/unova-documentation.yml` — CLI de auditoria e demo no Linux, Python de regressão Linux/Windows, Node do portal e compilação Python Windows.

## 1. Estado real conhecido vs permissões de fixture

| Região | Registry do portal | G05.3: roteável em fixture? | Afirmar instalada nesta entrega? |
| --- | --- | --- | --- |
| Decades | `playable` | Sim | **Não**; o jogo-base já existente não é testado nativamente pela G08.3 |
| Kanto | `prototype` | Sim | **Não**; o piloto existente não é certificado pela fixture |
| Johto | `planned` | Sim | **Não**; a allowlist Ruby não é prova de instalação |
| Hoenn | `planned` | Sim | **Não**; a allowlist Ruby não é prova de instalação |
| Sinnoh | `planned` | **Não** | **Não**; nenhum portal nativo/MapID é considerado aprovado |
| Unova | `planned` | **Não** | **Não**; 74 áreas simbólicas não equivalem a 74 mapas instalados |

O catálogo G05.3 contém `DECADES/KANTO/JOHTO/HOENN` como destinos reconhecidos pelo adaptador **sintético**. A G08.3 não altera essa lista. G05.4, por sua vez, reconhece apenas os mesmos quatro blocos nos seus **fixtures** de respawn. Sinnoh e Unova são recusadas antes de qualquer viagem ou blackout. A lista de regiões do circuito no site é **informativa** e não substitui verificações de instalação, MapIDs, proveniência ou execução.

## 2. Matriz de viagens e persistência

A rota **artificial** exercitada é:

`KANTO → HOENN → JOHTO → DECADES → KANTO`

Cada segmento chama a implementação existente `G05.3 travel.simulate`, precedida por um SHA-256 de **todo o estado de integração**, incluindo dinheiro, moedas, dados de progresso, Boxes e todos os namespaces protegidos pela G07.3. Após simular um retorno, os testes verificam:

| Recurso | Invariante |
| --- | --- |
| HM e itens-chave | Somente o estoque regional acompanha a região ativa; o HM e a chave do PC de Kanto reaparecem após o retorno; o HM de Hoenn e de Johto ficam nas respectivas coleções sintéticas |
| TMs | `FIXTURE_TM_GLOBAL` permanece disponível e não é duplicada no cofre regional |
| Insígnias e progresso | A coleção de marcos por região permanece intacta ao viajar e durante blackout |
| Pokémon restritos | Um Legendary sintético é movido para o Box de referência quando a região ainda não tem oito insígnias; não é duplicado nem transferido para outra região sem verificação |
| Box e Party | A inserção no Box acontece apenas no candidato em memória, nunca nos saves ou PCs do usuário |
| Dinheiro e moedas | Valores artificiais, explicitamente 4500/125, permanecem constantes; não se simula a penalidade real da engine |
| Mecânicas | Configurações sintéticas (Mega, Dynamax e Z-Move) são guardadas e restauradas ao retornar à região correspondente |
| Checkpoints | Centros Pokémon de referência pertencem à região correta; não há centro para Sinnoh ou Unova |
| Dados globais | Progresso compartilhado, armazenamento especial e hashes de namespaces preservados; conflito simultâneo bloqueia a publicação do candidato |

**Fica explícito:** a rota usa `install_proofs=true` **apenas como booleanos de fixture**. Não verifica se existe uma instalação real de Johto/Hoenn nem a compatibilidade de saves reais.

## 3. Testes de falhas, conflitos e isolamento

- **Cinco falhas G05.3**: após Party, mudança de região, Bag, PC e posição. O estado original deve sobreviver sem alterações.
- **Quatro falhas G05.4**: após checkpoint, proprietário, cura e transferência. O retorno deve restaurar integralmente dinheiro, Bag/PC, Boxes, flags e posição do fixture.
- **Sete falhas G07.3**, verificadas também por Windows e Android/JoiPlay via contratos G07.4: validação, staging, backup, CAS, primeira alteração, candidato completo e publicação.
- **CAS em todos os namespaces**: mudanças simultâneas em save sintético, checkpoints, itens-chave, Boxes, progresso, mecânicas, arquivos globais e outras regiões invalidam o digest completo. O candidato não pode sobrescrever a edição concorrente.
- **Táticas negativas**: falsificar licença, MapID, QA Android/Windows, ativar Unova ou Sinnoh, adicionar região indevida à allowlist, misturar checkpoint de Johto com Kanto, introduzir save real, retirar TM compartilhada ou inserir HMs de fora do cofre rejeita a operação.
- **Portal**: com `32/32` entregas GitHub, o HTML continua exibindo `Unova não jogável`, `Barra A técnica: 0/8` e `Unova jogável: 0/32`.

### Executar

~~~bash
python scripts/regions/audit_unova_g08_multiregional.py --check
python scripts/regions/audit_unova_g08_multiregional.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g08_multiregional.py' -v
npm run build --prefix site
npm test --prefix site
~~~

Após CI Linux, Windows e portal concluírem com sucesso, a Barra G pode registrar **32/32 (100%)** e G08 **4/4**. Trata-se da conclusão das tarefas de *planejamento/documentação/testes no GitHub*, **não** de completude da região no jogo.

## 4. Balanço para Unova realmente se tornar jogável

A conclusão G01–G08 **não** substitui as etapas técnicas/nativas. Para avançar a Barra A de **0/8** e liberar uma implementação jogável, ainda são necessários, com evidência independente:

1. **Proveniência, direitos e licenças:** localizar fontes autorizadas de mapas/tilesets, scripts, eventos, gráficos, música e demais assets; comprovar direitos de uso e redistribuição. Identificadores simbólicos ou checksums SHA-256 não suprem consentimento ou licença.
2. **Inventário físico e propriedade de MapIDs:** comparar o projeto real e `MapInfos.rxdata`, identificar colisões, transferências estáticas/dinâmicas, scripts e eventos comuns; completar a cadeia A04–A12 de propriedade/proveniência. A G08 não inventa MapIDs e não promove IDs reservados a mapas instalados.
3. **Integrar o mapa de Unova ao jogo:** obter/criar ou converter legitimamente a geografia das **74 áreas de referência**, ligar rotas/cidades/portais/chegadas e instalar recursos em `Data`, `Graphics`, `PBS` e scripts apenas após revisão de origem e backup seguro.
4. **Implementar história e progressão nativas:** transformar as 12 missões, 8 ginásios, Elite Four, Castelo de N, Ghetsis, rivais, Plasma, sábios, pós-jogo, NPCs e eventos de `planned` em conteúdo da engine; conferir travas, revisitas, derrotas e recompensas idempotentes em runtime.
5. **Treinadores, encontros e balanceamento verificados:** definir equipes, golpes, níveis, itens e Battle AI por fonte autorizada; gerar/validar os encontros White com espécies, rates, níveis, versões e variação dia/noite/estação. Os atuais dados `null` são **pendentes**, não zero.
6. **Persistência e isolamento regional reais:** implementar em Ruby e testar HMs, itens-chave, insígnias, requisitos de campo, progresso, troca de party/Boxes, restrições de Legendary/Mythical/UB/Paradox, moeda e mecânicas. Consertar/verificar os **dois riscos nativos G05.4** de checkpoint/fallback que o simulador documenta mas não corrige.
7. **Viagem, Centros e recuperação nativas:** assegurar NPC de acesso, ponto de chegada/retorno real, suporte a mapa/portal, Centros Pokémon da própria região, blackout, cura/penalidade de dinheiro e fallback; testar escolhas, travas, save/reload e combate em transições inter-regionais.
8. **Distribuição e QA por plataforma:** integrar ao Blue-Story Windows e ao atualizador incremental Android/JoiPlay com manifesto confiável, integridade, direitos, versão, transações reais, rollback seguro e testes de atualização a partir de instalações existentes. Executar QA nativo supervisionado em Windows e Android, validar CI, capturar logs e evidências para review humano antes de liberar um build.

Até que essas ações sejam **implementadas, testadas e aprovadas**, o único indicador correto de jogabilidade é **Unova 0/32**, com Barra A **0/8** e `planned`. Os testes de regressão G08.3 são importantes para reduzir o risco futuro, mas não satisfazem nenhuma dessas provas nativas automaticamente.

### Advertências preservadas

- G05.4 documenta dois riscos no Ruby nativo: ausência de um Centro fallback pode deixar checkpoint antigo; e uma validação baseada só em `regional_pokecenter_owner` pode aceitar ponto de mapa de outra região.
- G07.2/G07.3 são fixtures com hash e rollback em memória, não validação de assinatura, direitos de terceiros ou atualização de arquivos no disco.
- A matriz não executa Windows Sandbox, Game.exe, JoiPlay, nem lê, copia ou modifica saves reais.
