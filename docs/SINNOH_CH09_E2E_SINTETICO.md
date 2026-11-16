# Sinnoh — CH09: prova de integração sintética ponta a ponta

**Data:** 16/11/2026  
**Etapa:** CH09 · Barra E (desenvolvimento por chat).  
**Arquivo de teste:** [`tests/test_sinnoh_ch09_integration.py`](../tests/test_sinnoh_ch09_integration.py)  
**CI:** [execução 43923392072](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43923392072) · job `Sinnoh - contratos isolados (sem ROM)`.

## O que foi efetivamente testado

Os **oito testes** criam uma pasta descartável `TemporaryDirectory` e geram dados inéditos **apenas para teste** (nove mapas Ruby Marshal com IDs de origem 10–18, candidatos 500–508 e PBS sintéticos). Estes números **não são MapIDs aprovados** para a instalação. O conteúdo inclui um script e uma música doadora fictícios para confirmar sua remoção total, sem executar script algum.

1. **Audit:** `audit_sinnoh_rxdata.audit_rxdata` lê a fonte sintética, indexa os 9 mapas, calcula SHA-256 e identifica scripts doadores não executados, transferências e ausência de assets.
2. **Remap:** `plan_sinnoh_remap.make_plan` recebe auditoria, hashes de origem e mapeamento *explícito* sintetizados. Rejeita colisões com mapas nativos, Johto 600–999, Sinnoh 800–805, reservas declaradas e hashes alterados. Continua `REMAP_CANDIDATE_ONLY`, sem alocar IDs.
3. **Geometry:** `convert_sinnoh_geometry.build_geometry` confere de novo os arquivos locais e remove eventos, áudio, scripts e encontros do doador. Produz MapInfos/Tilesets mesclados **em memória**, sem editar `game/Data`.
4. **Atomic stage:** `sinnoh_staging_transaction.preview/stage` valida hashes e grava apenas em `.blue-work/sinnoh-stage/`. Duas execuções idênticas produzem bytes e SHA-256 iguais.
5. **Own-story overlay:** `audit_sinnoh_twinleaf_events.audit` + `build_sinnoh_twinleaf_events.compile_events` criam 24 eventos próprios (16 warps, 5 handlers, 3 Poké Bolas) para os nove mapas artificiais, com um segundo stage independente.
6. **Bundle:** o gerador do Barry cria 3 PBS privados; `prepare_sinnoh_pilot_bundle.build/publish` confere hashes, recompila eventos autorais para comparação, inclui apenas plugin `BlueSinnohPilot` e arquivos permitidos, e publica uma pasta **privada e nova** com relatório `NOT_PLAYABLE_PBS_NOT_COMPILED`.

## Falhas, rollback e isolamento

- Arquivos PBS ausentes/adulterados, PNG ausente, transferência/mapa incompatível, IDs proibidos, hash de mapa de origem alterado ou mapa nativo ocupando um destino interrompem o fluxo.
- `stage` e `publish` receberam falhas simuladas de `fsync`. Ambos precisam descartar a pasta temporária sem criar pacote final.
- O rollback rejeita SHA incorreto e stage contaminado por arquivo modificado; com a integridade restaurada, remove **somente** as pastas de stage identificadas por label e SHA.
- Hashes de arquivos do jogo local sintético, saves de **Decades, Kanto, Johto e Hoenn**, `System.rxdata` e plugin Blue original são comparados após os passos. O bundle nunca é copiado para `game/`.
- O pipeline bloqueia `Scripts.rxdata`, `System.rxdata`, `SinnohPreview.rb` e marcadores de batalha Barry antes da integração. A presença de arquivo público real de origem, mesmo que válido tecnicamente, **não** implica direito de distribuição.

## Verificações reproduzíveis

```bash
python -m unittest discover -s tests -p 'test_sinnoh_ch09_integration.py' -v
python -m unittest discover -s tests -p 'test_sinnoh_*.py' -v
python scripts/regions/validate_sinnoh_chat_progress.py
```

**Resultados registrados:** 8/8 testes CH09 e 225/225 testes Python isolados de Sinnoh passaram no CI acima. Nenhuma instalação real ocorreu.

**Limites:** isso é um teste de integração *headless* com fixtures sintéticas, não teste de `Game.exe`, movimento nos mapas, walkability, áudio, saves reais, JoiPlay ou direitos dos assets. As reservas reais de Kanto/Hoenn/Johto e a ocupação de `game/Data` são desconhecidas sem auditoria local. As barras A/B/C/D de Sinnoh permanecem nos valores anteriores.

**Próxima etapa — CH10:** endurecer interface e pré-voo de inicialização/instalação do piloto QA, sem permitir fallback para outras regiões ou interferência no instalador multirregional.
