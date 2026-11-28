# KD01 — fontes, direitos e decisão para Kalos 2D

Auditado em 28/11/2026. Esta matriz registra o que as páginas públicas
sustentam. Não baixei arquivos de terceiros nem inspecionei mapas, código,
ROMs ou assets dos candidatos. Os estados abaixo classificam o uso no
planejamento do Blue, não são aprovação jurídica ou técnica de material.

## Referências e candidatos

| ID | Fonte e versão observada | O que sustenta | Decisão |
|---|---|---|---|
| CANON_XY | [Nintendo: Pokémon X](https://www.nintendo.com/en-gb/Games/Nintendo-3DS-games/Pokemon-X-766699.html), [Pokémon Y](https://www.nintendo.com/en-gb/Games/Nintendo-3DS-games/Pokemon-Y-766700.html), [abertura](https://www.nintendo.com/tw/pressrelease/3ds_20130808_3.html) | X/Y de Nintendo 3DS, Kalos, os três iniciais, mudança para Vaniville e jornada com amigos. Não contém terreno XP ou ordem detalhada de todos os eventos. | REFERENCIA_APENAS: fatos e topologia conceitual; não copiar mídia, falas ou arquivos da Nintendo. |
| CANON_MEGA | [Brochura X/Y da Nintendo](https://www.nintendo.com/eu/media/downloads/games_8/3ds_pokemonxandy_1/PokemonXandY_Brochure_enGB.pdf) | Mega Evolução temporária na batalha, exemplos oficiais, Lumiose e tipo Fada. | REFERENCIA_APENAS: não copiar imagens ou texto; regra do Blue verificada à parte. |
| FIRE_ASH | [Luc-ker, Fire Ash 3.7.1](https://www.eeveeexpo.com/threads/9489/) | Candidato visual 2D; o autor declara Kalos, RPG Maker XP/Essentials v19.1, narrativa do anime e um sistema de campo diferente de X/Y. | BLOQUEADO_IMPORTACAO: campanha, portas, eventos e licença por arquivo não comprovados. Não usar o 19.1 como base do Blue. |
| VIRTUALIZATION | [Vince&Sylveon, Virtualization](https://eeveeexpo.com/threads/8573/) | O autor descreve sua própria história, ambientada após XYZ, e uma Lumiose voltada a serviços. Não autentica um inventário X/Y. | BLOQUEADO_IMPORTACAO: versão exata do arquivo, cobertura, editabilidade e licenças não validadas. Não copiar campanha ou progressão. |
| WORLD | [SocomSeal, World Project 1.1](https://mail.eeveeexpo.com/resources/1877/) e [repositório](https://github.com/SocomSeal/The-PMon-World-Project) | A versão pública documenta Essentials 21.1 e Kalos em 0%; isso não serve como inventário de Kalos completa. | REFERENCIA_APENAS: possível referência estrutural mas não fonte de mapas Kalos. Créditos do projeto não resolvem direitos de cada dependência. |
| POKEX | [peanutseagull, pokex](https://github.com/peanutseagull/pokex) | Demake em andamento sobre pokecrystal, stack de Game Boy diferente de Essentials/RMXP. | FORA_DA_BASE_TECNICA: não usar ROM, binário, scripts, gráficos ou áudio como entrada. |

## Escolha por frente

| Frente | Padrão escolhido para o planejamento | O que falta comprovar antes de uma implementação |
|---|---|---|
| Vaniville → Aquacorde → Santalune | Topologia funcional autoral 2D orientada pelo original; preservar a sequência de rotas e os gatilhos, não copiar a malha 3D. | Confrontar portas, retorno, regras do tutorial e Viola com referências independentes. |
| Lumiose e ligações centrais | Dividir setores por conexões físicas e pré/pós-energia; Virtualization e Fire Ash não substituem a ordem de X/Y. | Confirmar cada transição de campanha, serviço e acesso; discutir corte de detalhes 3D. |
| Costa, montanha, Liga e pós-jogo | Matriz de lacunas por local, rota, sala e serviço; uma segunda referência ajuda a verificar a topologia, não concede uso de mídia. | Cobertura exata, pontos narrativos divergentes X/Y e equivalentes offline em decisão separada. |
| Diálogos, arte, áudio, scripts, engine e saves | PT-BR reescrito, arte e áudio próprios ou comprovadamente autorizados, runtime Blue já existente, fixtures sintéticas. | Autoria/licença de cada componente e revisão dos termos aplicáveis antes de adquirir ou incorporar. |

**Decisão:** caminho autoral 2D como padrão, em vez de depender de um
doador. Os candidatos continuam como referências ou bloqueados. Não há
nenhum SHA-256, tamanho de arquivo, cobertura de mapas físicos ou pacote
de doador homologado nesta fase.

## Gate de um futuro arquivo

Para cada arquivo **antes** de qualquer reutilização: autor/titular,
licença e permissão específica, URL do autor, versão e arquivo, data da
consulta, tamanho e SHA-256 medidos, componente e uso autorizado
(inspecionar, adaptar, instalar localmente, redistribuir), atribuição,
exclusões e revisor. Engenharia em etapa posterior, só com autorização:
identificar estrutura sem executar código do doador nem publicar
binários; conferir formato e compatibilidade, e recusar arquivos
indiretos, fora da lista ou divergentes do hash. Preencher
`NAO_VERIFICADO` se não há prova. Retirar material incompatível do
planejamento, não fazer exceção implícita.

A distribuição futura deverá distinguir código/receita próprios de
entradas externas obtidas na origem pelo instalador. Baixar na origem
não dispensa a permissão de reutilização, e não implica republicar um
ZIP de assets. Nenhum site de terceiro foi contatado em nome do projeto.
