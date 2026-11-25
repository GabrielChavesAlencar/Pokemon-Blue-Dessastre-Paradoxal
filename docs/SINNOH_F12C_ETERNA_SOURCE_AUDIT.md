# F12C — Eterna Galactic Building: investigação de fontes

Dependências: PRs #314–#317 e issue #318. Auditoria somente leitura, sem autorizar instalação.
A fonte F03 (job 138719583390) possui 238 mapas. Map090 e Map119 têm hashes fixados no auditor; Map119 é genérico, não identificado como Galactic. A auditoria percorre os mapas anônimos e os eventos de todos os mapas, registra candidatos, transferências e metadados sem executar scripts doadores. Nenhum MapID reservado, portal criado, item concedido ou checkpoint marcado.

Referências históricas (não são dados PBS recuperados): 
- https://bulbapedia.bulbagarden.net/wiki/Team_Galactic_Eterna_Building
- https://www.serebii.net/pokearth/sinnoh/4th/eternagalacticbuilding.shtml

Platinum: acesso com Forest Badge e Cut, quatro andares, Jupiter com Zubat 21 e Skuntank 23, resgate dos Pokémon e obtenção posterior de Bicycle na loja. Níveis de referência, não substituem balanceamento. A geometria autoral só deve ser criada depois da auditoria e revisão de acessos, escadas e saída. Não habilitar HM, recompensa, batalha ou flags antes de validar catálogo, progresso regional e regras existentes.

F12B: diagnóstico local para POTION, TM24 (Thunderbolt), ELECTIRIZER e MAXELIXER, com quantidade unitária original, hashes do PBS e rejeição de duplicidades. Mesmo com quatro identidades locais válidas, compilação e semântica de coleta permanecem pendentes: nenhum grant habilitado. Não acessa saves. CI pendente; sem QA nativa.


## Evidência definitiva F12B5B
PR #317 integrado em 424ebfda8d4d991cdd1e74e555212433c0a20446; HEAD c55143dbbd584a60ad739fed6c9e2413fe0ab0e4; 11 workflows e 26 jobs aprovados contra 8624d31f6a1797871a54e31bacaf830a619cdda8. Source job 139126501756: SINNOH_REAL_F12B5_AUTHORED_FIVE_EVENTS_FIXTURE_PREPARED_OK; cinco eventos autorais, catálogo REFERENCE_FIXTURE_NOT_LOCAL_DATABASE, zero grants, zero bindings nativos. Windworks Map581, 140 mapas preparados, 89 portais e sete conexões anteriores preservados. QA nativa não executada.
