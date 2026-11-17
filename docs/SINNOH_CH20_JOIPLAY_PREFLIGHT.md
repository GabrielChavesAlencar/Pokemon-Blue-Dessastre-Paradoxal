# Sinnoh — CH20: pré-voo Android/JoiPlay + checklist 44 casos

**Data:** 16/11/2026 · **Estado:** implementação estática publicada; [CI CH20 43985365818](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43985365818) passou em PR; aceite final CH20 ainda não registrado. **Nenhum Game.exe ou JoiPlay foi executado.**

## Reutilização sem duplicar os dados de jogo

- [Auditor de Android/JoiPlay CH20](../scripts/regions/audit_sinnoh_android_ch20.py) deriva 44 IDs do [contrato simbólico Twinleaf](../data/regions/sinnoh-twinleaf-events.json), revalidado pelo [auditor CH06 de topologia, schema, eventos e sprites](../scripts/regions/audit_sinnoh_twinleaf_events.py) e segue a divisão do [auditor nativo preexistente](../scripts/regions/audit_sinnoh_playtest.py). A CH20 não substitui esse auditor de evidências, nem cria MapIDs/posições de chegada fictícios.
- [15 casos de teste](../tests/test_sinnoh_android_ch20.py) incluem ZIP seguro e malicioso, arquivos obrigatórios, prefixo de pasta, colisões 800–805 como **alerta a auditar**, casos duplicados, falsificação de aprovação/posição, isolamento de saída em `.blue-work` e proteção contra sobrescrita/symlink.
- [CI separado CH20](../.github/workflows/sinnoh-ch20.yml): verifica sintaxe, testes, gera artefato JSON sempre com 44 casos nativos **pendentes**. O CI não baixa e não publica assets privados.

| Categoria | Casos | O que exige teste real |
|---|---:|---|
| Três Poké Bolas | 3 | Iniciais físicos corretos e bloqueio do segundo inicial |
| Barry | 12 | Três iniciais × Normal/Master × vitória/derrota, escala 70%/90%, times |
| Save/reload | 3 | Um por inicial, sem vazamento de perfil de outra região |
| Warps | 16 | MapID, origem e posição de chegada obtidos da cópia instalada |
| NPCs | 5 | Mãe, Barry, Rowan e progressão de diálogos/eventos |
| Regressão regional | 4 | Decades, Kanto, Johto, Hoenn; saves intactos |
| Android/JoiPlay | 1 | Início e carregamento no aparelho, perfil próprio, iniciais e warps |
| **Total** | **44** | **0 executados/comprovados por esta CH20** |

O campo `native_status: pending` impede que um caso derivado de JSON simbólico apareça como observação real. Os nomes e símbolos não demonstram existência de mapas ou eventos instalados.

## Como executar o pré-voo local

Sem pacote (verifica somente os contratos que estão no GitHub):

```bash
python scripts/regions/audit_sinnoh_android_ch20.py
python -m unittest discover -s tests -p 'test_sinnoh_android_ch20.py' -v
```

Com um **ZIP local** Android/JoiPlay disponível, somente para metadados, sem extrair nem executar:

```bash
python scripts/regions/audit_sinnoh_android_ch20.py --package "PACOTE_ANDROID.zip" --output .blue-work/sinnoh-ch20/relatorio-local.json
```

A gravação em arquivo é **opt-in** e permitida apenas em caminho novo dentro de `.blue-work`. O pré-voo rejeita ZIP com caminho absoluto, `../`, barra invertida, symlink, entrada repetida (ignorando maiúsculas/minúsculas), criptografia e tamanho descompactado excessivo; exige uma raiz inequívoca com `Data/MapInfos.rxdata`, `Data/System.rxdata` e `Data/Scripts.rxdata`. A estrutura mínima presente resulta em `STRUCTURE_PRESENT_UNVERIFIED`, **não** em aprovação JoiPlay. Ausência do ZIP resulta em `NOT_PROVIDED`; estrutura incompleta em `BLOCKED`.

Se existirem arquivos com IDs 800–805, o relatório exige identificação da região de origem por causa da reserva de Johto. Isso **não** determina se os mapas são de Sinnoh, nem efetua remapeamento. SHA-256 é calculado sobre o ZIP fechado para reproduzir a inspeção; os bytes internos não são extraídos nem executados.

## O que CH20 não certifica

1. Disponibilidade de assets reais de Sinnoh com direitos confirmados e ausência de conflitos nativos.
2. Compatibilidade de scripts, `JSON`, controles, fontes, áudio ou RPG Maker XP no runtime específico do JoiPlay.
3. Compilação de PBS, battle 70%/90%, warps, save/reload e retorno ao Centro Pokémon no Windows ou no Android.
4. Autenticidade de capturas e logs de um aparelho; a revisão precisa ser local, e o [auditor do playtest](../scripts/regions/audit_sinnoh_playtest.py) continua sendo o responsável por validar as 44 observações e seus hashes.

**Critério para `done` na Barra E:** arquivos, 15 testes e execução do novo workflow CH20 comprovados na `main`. Se não houver prova de CI, o status permanece **partial**, mesmo com o código publicado. Conclusão estática da CH20 **nunca** aumenta as barras técnicas/jogáveis.

**Situação das barras:** Barra E **19/20 (95%)** após conclusão da CH19 (CI Python 374/374 e Ruby 22/22); CH20 continua parcial aguardando revisão de seu relatório final. A 8/32 (25%), B/C/D 0/13, sem alteração. Não foi usado o jogo principal nem seus saves.
