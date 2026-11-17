# Unova — G05.2: insígnias únicas, esmeraldas e bloqueio de especiais

**WHITE_BW** · **Status: planned, somente contrato de GitHub** · **Jogo, mapas, badges nativos e saves intactos.**

## Fontes e limites

- [G02.2 — história dos oito ginásios](../data/regions/unova-g02-gym-story-contracts.json) contém eventos simbólicos, sem provas de ginásios físicos instalados.
- [Registro de regiões](../site/public/data/regions.json) define a ordem dos marcos de Unova e o circuito regional.
- [Regions.rb](../scripts/battle_polish/Regions.rb) é a fonte existente para `award` (não duplica), `local_achievements`, `crystal_total`, `allow_specials?` e `transfer_plan`.
- [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb) identifica Pokémon especiais por **flags da espécie**, inclusive flags da espécie-base em formas não zero, e exige reservas de Box para cada Pokémon que precise ser depositado.
- [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb) mantém o bloqueio no uso da party, retirada do PC e coleta; o contrato G05.2 **não altera esses handlers**.
- [Contrato G05.1](../data/regions/unova-g05-regional-items-contract.json) continua responsável por HMs e itens-chave regionais, não por Pokémon especiais.

A implementação consta do [contrato G05.2](../data/regions/unova-g05-badges-specials-contract.json) e do [auditor com fixtures](../scripts/regions/audit_unova_g05_badges_specials.py). Não usa `$PokemonGlobal`, salva, transpõe ou modifica Pokémon reais, nem instala Unova.

## Oito insígnias locais de Unova

| Ordem | Insígnia | Evidência atual |
|---|---|---|
| 1 | TRIO | Somente contrato de ginásio G02.2 |
| 2 | BASIC | Somente contrato de ginásio G02.2 |
| 3 | INSECT | Somente contrato de ginásio G02.2 |
| 4 | BOLT | Somente contrato de ginásio G02.2 |
| 5 | QUAKE | Somente contrato de ginásio G02.2 |
| 6 | JET | Somente contrato de ginásio G02.2 |
| 7 | FREEZE | Somente contrato de ginásio G02.2 |
| 8 | LEGEND | Somente contrato de ginásio G02.2 |

Todas têm `native_badge_index=null`, `native_switch_id=null`, `native_event_id=null` e `installed=false`. A G05.2 permite somente uma concessão **sintética** de insígnia, no contexto da própria região, sem item de recompensa e sem duplicação. Uma tentativa de conquista fora da região é rejeitada.

## Cálculo das esmeraldas/progresso

O motor compartilhado calcula o progresso global como:

**Total = total nativo de insígnias de Decades + soma das insígnias únicas de cada região do circuito, exceto Decades.**

O cálculo não sobrescreve as insígnias nativas; o argumento `native_total` vem de uma fonte validada pelo jogo real. Na G05.2, ele é apenas um número explícito em uma massa de teste.

Exemplo puramente sintético: Decades com 3 insígnias nativas, Kanto com 2 e Unova com 3 representa **8 pontos**. Se a 4ª insígnia de Unova for simulada corretamente, o total muda para **9**. Repetir a mesma insígnia deixa o total intacto. O resultado não escreve badges ou progresso em saves reais. Conquistas de Hisui não entram no circuito; o desbloqueio especial de Hisui depende de `hisui_complete`, regra separada.

## Restrição de Pokémon especiais — oito conquistas na região de destino

O código nativo trata estas quatro flags como especiais:

| Flag de metadados | Comportamento planejado |
|---|---|
| `Legendary` | Bloqueado antes de oito conquistas locais |
| `Mythical` | Bloqueado antes de oito conquistas locais |
| `UltraBeast` | Bloqueado antes de oito conquistas locais |
| `Paradox` | Bloqueado antes de oito conquistas locais |

A categoria é baseada nos **metadados reais da espécie e da forma**, nunca em nome, BST ou aparência.

**Oito esmeraldas globais não equivalem a oito insígnias de Unova.** O jogador pode ter todas as insígnias de Kanto e progresso global elevado, mas ainda não poderá usar especiais em Unova até ter as oito conquistas *da própria Unova*. O contrário também vale na volta a Kanto.

Ao viajar, a simulação identifica os Pokémon restritos, exige ao menos **um Pokémon não-ovo e não desmaiado** que permaneça na party e reserva uma vaga livre de Box para cada especial a depositar. Sem espaço ou sobrevivente, a prévia é bloqueada. **Nenhum Pokémon é movido ou liberado pela G05.2**. A gravação nativa e a transação real devem permanecer com o serviço já existente; não há inferência de que Unova seja destino instalável.

## Testes e execução

```bash
python scripts/regions/audit_unova_g05_badges_specials.py --check
python scripts/regions/audit_unova_g05_badges_specials.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g05_badges_specials.py' -v
```

Os **120 testes** abrangem positivos e negativos: identidade dos oito marcos, duplicação, badge estrangeira, esmeraldas globais, sete/oito insígnias, formas alternativas, quatro flags especiais, vagas insuficientes, party sem sobreviventes, entradas forjadas, mudanças indevidas no Ruby, fontes G02/G05.1 e falsos estados jogáveis.

Sem fonte física de Unova, permanecem `null` os índices de insígnia, switches, eventos de NPC, IDs de MapIDs, itens de recompensa e provas de QA nativo. CI de Linux/Windows/portal deve aprovar antes da Barra G ser atualizada na `main`. Barra A deve permanecer **0/8** e Unova jogável **0/32**.

## Próxima implementação — G05.3

Contratar NPC de viagem e retorno entre regiões, com precondições de mapa, destino instalado, capacidade de Box e fallback seguro, **sem** declarar Unova integrada fisicamente.
