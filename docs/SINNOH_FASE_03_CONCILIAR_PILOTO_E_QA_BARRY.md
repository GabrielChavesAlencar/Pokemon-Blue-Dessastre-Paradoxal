# Sinnoh — reconciliação do piloto legado e pré-verificação de Barry

**Atualização:** 13/11/2026. **Situação:** ferramentas e testes publicados no GitHub; **sem jogo real instalado, sem mapas migrados, sem batalha nativa e sem liberação de marcador**.

## Diagnóstico comprovável no código

O piloto antigo [pilot_sinnoh.py](../scripts/regions/pilot_sinnoh.py) associa os mapas-fonte `32, 102, 42, 43, 104, 96` a IDs de destino `800–805`. Ele instala o plugin [SinnohPreview.rb](../scripts/regions/SinnohPreview.rb), cujo método `rowan` permite escolher o inicial por **diálogo**.

O planejamento compartilhado, por sua vez, reserva **600–999** para Johto. O novo roteiro [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) e [sinnoh-twinleaf-events.json](../data/regions/sinnoh-twinleaf-events.json) implementam a escolha em **três Poké Bolas físicas**, com Barry depois da escolha e eventos isolados por região.

**Não são implementações equivalentes.** Os IDs 800–805 podem continuar sendo usados numa cópia autônoma estritamente isolada, desde que não seja adicionada ao mundo multi-regional. **Não são aprovados para merge no jogo principal**. Também não há mapeamento completo para os nove mapas simbólicos e os eventos exigidos pelo novo roteiro.

## Ferramentas novas

1. [audit_sinnoh_pilot_compat.py](../scripts/regions/audit_sinnoh_pilot_compat.py) lê **somente** os quatro arquivos de código dos dois pilotos e do menu. Extrai os IDs antigos da declaração Python, aponta a sobreposição com Johto e registra as diferenças de fluxo. Rejeita código inesperado em vez de inventar novos IDs. A auditoria física de MapIDs pode ser adicionada por um relatório verdadeiro gerado por `audit_sinnoh_rxdata.py --game-data game/Data`.
2. [preflight_sinnoh_barry_qa.py](../scripts/regions/preflight_sinnoh_barry_qa.py) exige uma **cópia já preparada** dentro de `.blue-work/`, distinta de `game/`. Compara os dois PBS do QA com os hashes do draft verificado por [verify_sinnoh_barry_pbs.py](../scripts/regions/verify_sinnoh_barry_pbs.py), confere o executável, procura o candidato de sprite do Barry e rejeita o arquivo `Data/blue-sinnoh-rival-ready.txt` prematuro em QA ou game. Informa se existem MapIDs 800–805 fisicamente na cópia e **não escreve arquivo algum**.
3. Testes: [test_sinnoh_pilot_compat.py](../tests/test_sinnoh_pilot_compat.py) e [test_sinnoh_barry_qa.py](../tests/test_sinnoh_barry_qa.py). Testam MapIDs, discrepância de fluxos, adulteração de PBS, falta de sprite, perfil separado, symlinks e marcador indevido usando dados sintéticos.

## Execução local — só após ter o Blue de verdade

A auditoria de conflitos de **código** já funciona sem os mapas reais:

```powershell
python scripts/regions/audit_sinnoh_pilot_compat.py
python -m unittest discover -s tests -p "test_sinnoh_pilot_compat.py" -v
```

Quando existir uma fonte Sinnoh **autorizada**, a auditoria física poderá ser acrescentada:

```powershell
New-Item -ItemType Directory -Force .blue-work/sinnoh | Out-Null
python scripts/regions/audit_sinnoh_rxdata.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/rxdata-report.json
python scripts/regions/audit_sinnoh_pilot_compat.py --installed-ids-report .blue-work/sinnoh/rxdata-report.json
```

Para os PBS de Barry, usar os passos do [guia PBS](SINNOH_FASE_03_BARRY_PBS.md) para **gerar o draft**, copiá-lo **somente para um QA separado** e conferir:

```powershell
python scripts/regions/build_sinnoh_barry_pbs.py --game game --output .blue-work/sinnoh-barry-pbs-v1
python scripts/regions/verify_sinnoh_barry_pbs.py --game game --draft .blue-work/sinnoh-barry-pbs-v1

# A cópia deve existir ANTES deste comando; não é criada pelo auditor.
python scripts/regions/preflight_sinnoh_barry_qa.py --game game --draft .blue-work/sinnoh-barry-pbs-v1 --qa .blue-work/sinnoh-qa
```

**Importante:** a pré-verificação não compila PBS, não executa Ruby/Essentials, não confirma qual gráfico o trainer type escolherá e não marca nenhuma versão de Barry como funcional no Game.exe. A presença de PNG é apenas um candidato a conferir visualmente no motor. O auditor **nunca** cria o marcador de pronto.

## Decisão operacional para a integração

- **Fluxo legado:** manter intacto apenas como experiência autônoma, com diretório e saves exclusivos. Não reutilizar `Data/System.rxdata` nem `SinnohPreview.rb` numa instalação conjunta com Johto.
- **Fluxo multi-regional novo:** seguir [plan_sinnoh_remap.py](../scripts/regions/plan_sinnoh_remap.py) e [build_sinnoh_twinleaf_events.py](../scripts/regions/build_sinnoh_twinleaf_events.py). São necessários os mapas reais autorizados, todos os MapIDs/destinos e coordenadas auditados, sprites e nove mapas simbólicos. Usar `BlueSinnohPilot` como roteiro; não transportar o diálogo de escolha do legado.
- **Migração de saves:** não automática. Se houver saves legados, documentar MapID anterior, novo mapa e posição segura, inventário, flags de Barry e conteúdo da party antes de migrar uma **cópia**. Não há prova que essa migração esteja implementada ou seja segura hoje.
- **PBS:** apenas três versões compiladas e verificadas no QA podem ser candidatas à ativação posterior. Confirmar em jogo níveis dinâmicos 70%/90%, três escolhas, derrota/vitória e save/load antes de criar qualquer marcador, e nunca no game principal.

## Gates ainda não aprovados

- [x] Detectar estaticamente MapIDs 800–805 e incompatibilidade entre os dois roteiros
- [x] Preparar verificador offline da cópia QA de Barry com arquivos PBS íntegros
- [x] Testar os contratos sem ROM e sem gravar em `game/`
- [ ] Identificar e reservar MapIDs reais não conflitantes com Johto/Hoenn/Kanto/Decades
- [ ] Preparar a cópia real do piloto com fonte autorizada, sprite e PBS compilados
- [ ] Testar Barry/Rowan no Game.exe e Android, nível 70%/90%, save/load e regressões

**Progresso:** o subtrabalho de compatibilidade/QA tem código pronto, mas não valida jogo; o nível de preparação geral e os 13 gates do jogo não devem aumentar sem provas locais. Atualizações ficam em [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md) e [sinnoh-progress.json](../data/regions/sinnoh-progress.json).
