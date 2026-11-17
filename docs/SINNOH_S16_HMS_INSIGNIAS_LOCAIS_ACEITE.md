# Sinnoh S16 — oito HMs e insígnias locais (contrato offline)

**28ª entrega da Barra A, após CI e merge.** O contrato não instala itens, eventos, mapas, código da engine ou scripts globais.

## Entregues

- [Manifesto S16](../data/regions/sinnoh-hms-s16.json) vincula cada uma das **oito permissões CH11** (Coal/Rock Smash HM06, Forest/Cut HM01, Cobble/Fly HM02, Relic/Defog HM05, Fen/Surf HM03, Mine/Strength HM04, Icicle/Rock Climb HM08, Beacon/Waterfall HM07) aos líderes S15 sem inverter as ordens: **Platinum narrativo Fantina 3ª/Maylene 4ª; CH11 armazena Cobble antes de Relic**.
- [Adaptador Ruby](../scripts/regions/SinnohHMContracts.rb) oferece `preview` somente leitura e `record_from_native` falha fechada, com `VERIFIED_NATIVE_SOURCES = {}`. Ausência de callback local verificado impede que seja emitida qualquer confirmação de coleta real.
- [Auditor](../scripts/regions/audit_sinnoh_s16_hms.py) depende dos contratos já verificados CH11 e S15, do `RegionalPolicy`, de `BlueRegions` e de `RegionTravel`. O [teste Python](../tests/test_sinnoh_s16_hms.py) exerce **24 verificações** incluindo manipulação de insígnia, MapID, item ou falso recibo.
- [Teste Ruby](../tests/sinnoh_s16_hms_runtime.rb) executa o `BlueRegions` real com bolsa e estado sintéticos: insígnia ausente bloqueia; HM emprestado de outra região continua bloqueado após insígnia; recibo local confirmado permite a permissão no modelo; duplicação ou perda do HM mantém bloqueio; troca de região e save inválido também falham. A chamada que simula um comprovante é feita **exclusivamente dentro do teste**, não através do adaptador nativo.

## Invariantes e pendências

Nenhum arquivo `scripts/battle_polish/Regions.rb`, `RegionalPolicy.rb`, `RegionTravel.rb` nem configuração de Kanto, Johto, Hoenn, Decades ou BlueMusic foi alterado. **S16 concluído em contratos e regressões offline** significa que a cadeia foi validada com entradas sintéticas; **não significa obtenção ou uso dos HMs dentro do Game.exe/JoiPlay**.

Ainda são necessários mapas RMXP permitidos, coleta com callback realmente compilado, validação de tipagem/IDs, integridade da fonte, save/load real e ensaios de cada movimento no Windows e Android. **Barra A 28/32 (87%), 4 parciais, nenhum pendente; E 20/20; B/C/D 0/13, 44 casos nativos sem observação.**

## Aceite

Aprovação em CI CH19 Python/Ruby, S30 cinco jobs, CH20 estático e Portal; depois PR integrado à `main`. Provas de fixture não certificam jogabilidade.
