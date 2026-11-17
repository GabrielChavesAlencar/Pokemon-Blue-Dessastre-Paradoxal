# Unova — próxima entrega: conferência cruzada de evidências E04–E06

**Data:** 17/11/2026. **Estado:** ferramenta de consistência pronta; arquivo original de Pokémon World V18 ainda não foi obtido ou validado neste ambiente. Nenhum mapa, NPC, evento ou áudio foi instalado.

## Resultado técnico

A ferramenta `scripts/regions/audit_unova_e04_e06_evidence.py` reúne cinco relatórios independentes e privados: `e04-intake.json`, `u02-source.json`, `u02-rxdata-detail.json`, `e05-crosswalk.json` e `e06-rights-inventory.json`. Todos ficam somente em `.blue-work/unova/audit/`.

O programa confirma a coincidência do SHA-256 do ZIP em todas as etapas, verifica a contagem de MapNNN (projeto **inteiro**, não apenas Unova), compara o hash de MapInfos, confirma que cada MapID candidato e hash vêm do mesmo relatório RXDATA e identifica divergências no arquivo Credits.txt.

Também recusa qualquer declaração prematura de mapa instalado, direito autoral comprovado, MapID de destino alocado, Game.exe testado, JoiPlay testado ou áudio autorizado.

### Resultado possível

| Resultado | Interpretação |
|---|---|
| `BLOCKED_MISSING_SOURCE_EVIDENCE` | Um ou mais relatórios não existem. Na ausência do ZIP real, é o resultado esperado |
| `UNOVA_E04_E06_INCONSISTENTE` | Hashes, contagens, nomes ou aprovações incompatíveis; não confiar nesse conjunto |
| `CONSISTENT_PRIVATE_REPORTS_NOT_LICENSED_OR_INSTALLED` | Os relatórios internos concordam entre si, mas a fonte não está autenticada, mapas não estão confirmados como Unova e licenças/QA continuam pendentes |

**Nenhum dos três resultados habilita instalação.** Mesmo a consistência total não prova que o ZIP veio do autor ou que os arquivos podem ser redistribuídos.

## Usar sem PowerShell

Depois de baixar e selecionar o ZIP no `UNOVA_E04_ESCOLHER_FONTE.bat`, a ferramenta `UNOVA_VALIDAR_DOCUMENTACAO.bat` executa U02, inspeção RXDATA, crosswalk E05, inventário E06 e, finalmente, o gate de coerência. O resultado é salvo como `.blue-work/unova/audit/e04-e06-evidence-gate.json`.

Se um relatório anterior divergir, o sistema não o substitui silenciosamente; preserve a evidência antiga e faça uma auditoria nova em ambiente de trabalho separado.

## Regra de progresso

- **E = 4/8 (50%)**: E01, E02, E03 e E07 documentados.
- **E04** exige ZIP real, origem e créditos; não foi concluído nesta entrega.
- **E05** exige identificação/revisão de mapas/eventos verdadeiros; não foi concluído.
- **E06** exige autoria e direitos para cada recurso; não foi concluído.
- **E08** depende de teste real no Game.exe Windows e Android JoiPlay.
- **A/B/C/D = 0/8** nesta entrega e **Unova jogável = 0/32**.

O CI roda testes sintéticos, não o jogo. Esta entrega modifica apenas ferramentas, testes e documentação, preservando arquivos jogáveis e saves.
