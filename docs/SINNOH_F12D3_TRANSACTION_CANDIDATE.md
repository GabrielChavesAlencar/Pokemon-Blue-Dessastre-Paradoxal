# F12D3 — candidato de transação, não instalado

Branch separada da auditoria #325 (HEAD ae14ebd7668b27a9e1d92bfb0794960062b6cbb3), para não invalidar os checks em execução. A lógica prepara cópias de bolsa e estado, sem escrever em saves, sem modificar globais e sem criar eventos. Exige sequência F12D2 completa e estado SINNOH, catálogo compilado de item-chave e provas de catálogo/geométricas fornecidas pelo futuro integrador. Rejeita entrega duplicada, item preexistente, consumo fora de ordem, quantidade incorreta e falha de bolsa; a liberação depende do ledger completo. O PBS local deve conter uma única definição exata SECRETPOTION com KeyItem e Pocket válido. Testes de regressão isolados de catálogo e transação, incluindo roundtrip Marshal (não save nativo).

O futuro adaptador deve confirmar a cópia privada, região, posição e interação, caminho e bloqueio físico/alternativas de passagem, aplicar bolsa e ledger juntos e restaurar ambos em falha; vincular páginas e atualização visual sem alterar portais ou outros eventos. Nenhuma prova de geometria ou catálogo real é alegada. Nenhum evento ou item instalado. Não mesclar antes da auditoria e da revisão do integrador.

# Auditoria integrada e nova revisão

#325 merged 7f06fdac338b6b4c2699a98d4e15727604cba862: 11/11 workflows, 26/26 jobs, real job 139262668218 confirmed all three required markers. 62 events, zero exact identity markers, reachability 451/0/0. Source 80 events 10–13 at x92–95,y75 blocked; source 116 events 32–35 at x12–15,y7 ordinary. These groups are unidentified, not confirmed Psyduck. New review expands exact-marker search across all 238 maps and PBS, diagnoses original connection alignment and current reachable sides, reports topology-only paths separately from real walking. No event binding or native claims. Transaction and catalogue candidates copied from 5ca6bb8e62dda8cb2da896da18477202b55b75a2 and covered by new CI.

## Correção do índice de componentes

HEAD beaba6d022ef5cc7def91e7cfbc1aa178eaee3f2: 10/11 workflows, 25/26 jobs. O job real 139274207840 verificou as duas fontes e confirmou F12C4, F12D2 e F12D3 inicial. Falhou antes da auditoria ampliada porque access_graph retorna listas de conjuntos de células, e o auditor usou esses conjuntos como rótulos hashable. Correção: enumerar índices inteiros das componentes, mantendo as mesmas regras de caminhada; novo teste usa index_components real com duas componentes, outra isolada e mapa sem células. Busca de caminhos Data/ case-insensitive igual ao F03. Nenhuma alteração de mapas ou eventos. Novo CI necessário.
