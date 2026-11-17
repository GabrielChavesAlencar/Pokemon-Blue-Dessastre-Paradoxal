# Unova — A09: auditoria de introduções e indícios de transferências

**17/11/2026 | somente leitura, sem modificação no jogo e sem instalar Unova**

## Evidência A08 recebida

A instalação local examinada contém 648 mapas/648 MapInfos, mesma SHA de MapInfos \`8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420\`. O relatório \`LEIA_AQUI_UNOVA_MAPIDS(2).txt\` identificou no Map001:

- Evento 1: **Intro** (2 páginas), uma referência estática a **MapID 3**;
- Evento 2: **Quick start intro** (2 páginas), uma referência estática a **MapID 3**;
- MapID 3 não está registrado fisicamente ou declarado; as duas referências batem com A07;
- Bloco candidato 518–599 desocupado no snapshot, sem reserva nativa;
- 37 ocorrências de nomes de APIs de transferências em texto de scripts; não são 37 teletransportes problemáticos;
- Manifestos Kanto, Johto e Hoenn vistos parcialmente; Sinnoh e Unova não encontrados. Zero colisões reconhecidas no bloco, com cobertura incompleta.
- A08 não verificou ativação dos eventos no Game.exe nem referências dinâmicas exaustivas.

## Implementação A09

O auditor \`scripts/regions/audit_unova_a09_intro_and_claims.py\` usa dados A04/A06/A07/A08 da **mesma execução**; relê Map001 usando o SHA do A04 e descreve:

1. Gatilhos RMXP por página, condições (switch/variável/self-switch) e respectivos IDs, sem avaliar sua ativação;
2. Transferências por comando 201 para MapID 3 ou candidatos Unova (e formas dinâmicas), coordenadas, índice e códigos de até três comandos próximos, incluindo ramos, switches e variáveis, sem executar nem reproduzir texto completo de scripts;
3. Proveniência por evento/página/índice comparada com A07;
4. Varredura textual *heurística* do código em eventos 1 e 2 e \`Scripts.rxdata\`, classificando **DEFINITION**, **LITERAL_TARGET_3**, **LITERAL_UNOVA_CANDIDATE**, **LITERAL_OTHER**, **SYMBOLIC_OR_COMPUTED** e **INCOMPLETE_OR_UNCERTAIN**. Não interpreta Ruby, não cobre todas as APIs, plugins, CommonEvents ou scripts de outros mapas;
5. Inspeção de metadados dos manifestos regionais locais conhecidos, com SHA e schema parcial; ausências ou desconhecimento de reivindicações futuras NÃO liberam os IDs;
6. Relatório privado e imutável \`a09-intro-claims-HASH.json\`, seção A09 em \`LEIA_AQUI_UNOVA_MAPIDS.txt\`, execução A04→A09 num BAT de duplo clique a partir de Downloads.

A auditoria só grava na pasta privada de relatórios do executável portátil, nunca em Data, Game.exe, Blue-Story, saves ou mapas. Os números de erros/pendências nunca autorizam reserva; status **REVIEW_REQUIRED_NO_RESERVATION** mesmo se a varredura não sinalizar uma colisão.

## Próximos critérios de aprovação

Para decidir um redirecionamento do MapID 3: examinar o JSON A09, comparar os gatilhos e as flags com o comportamento da introdução em Windows/Android, identificar destino pretendido pelos designers e testar o fluxo real; não alterar por suposição.

Para reservar MapIDs 518–599: reconciliar integralmente os manifests instalados e reivindicações futuras de Kanto/Johto/Hoenn/Sinnoh e do Blue-Story, ampliar auditoria de scripts dinâmicos, obter mapas-fonte legalmente utilizáveis e preparar mapeamento, backup, rollback e QA nativo antes de qualquer escrita.

**Barra A 0/8 · Unova jogável 0/32 · IDs sem reserva nativa.** A09 não altera esses indicadores.
