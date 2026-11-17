# Unova G01.4 — Serialização, round-trip e migração de estado sintético

**Escopo:** exclusivamente simulação em memória para os contratos G01.1 (estado v1), G01.2 (transições) e G01.3 (recibos e intenções de recompensa U07). **Nenhuma operação lê, grava, migra ou interpreta os arquivos de save do Game.exe/Decades/JoiPlay.** Os jogos nativos continuam pendentes de testes e fontes.

## Arquivos entregues

- [Contrato de persistência G01.4](../data/regions/unova-g01-serialization-contract.json)
- [Codec e migrador explícito](../scripts/regions/audit_unova_g01_serialization.py)
- [110 testes de serialização e migração](../tests/test_unova_g01_serialization.py)

## Formato sintético atual v1

O codec `encode_current(envelope,ctx)` recebe **somente** um envelope válido da G01.3, já conferido pela progressão G01.2 e pelo schema v1 da G01.1. Retorna bytes UTF-8 JSON canônicos com chaves ordenadas, separadores compactos e sem NaN/Infinity.

Campos obrigatórios: `format=UNOVA_G01_4_OFFLINE_STATE_V1`, `storage_version=1`, `region=UNOVA`, `campaign=WHITE_BW`, `scope=SIMULATED_ONLY_NOT_GAME_SAVE`, `state_schema_version=1`, `ledger_schema_version=1`, `canonical_sha256` e `payload` (envelope G01.3).

O SHA-256 cobre os bytes canônicos do payload. **É checksum de integridade, não assinatura/autenticação de segurança.** Se alguém puder substituir o payload e recalcular o hash, o checksum sozinho não distingue manipulação intencional; a estrutura continua sendo validada pelas regras G01.1–G01.3.

`decode_current(bytes,ctx)` aplica limite de **256 KiB**, exige bytes UTF-8 sem BOM, recusa chaves JSON duplicadas e números não finitos, valida campos e versões estritamente, confere SHA-256 e recusa formas não canônicas. Todo payload restaurado passa novamente pela validação G01.3. Não há salvamento automático em disco.

## Migração **explícita** de um formato legado de testes

A G01.4 define um formato **sintético v0 de armazenamento**, `UNOVA_G01_4_SYNTHETIC_FIXTURE_V0`. **Não é um schema G01.1 v0 e não corresponde a arquivos `.rxdata`, `.sav` ou estados de outros jogos.** A versão de estado G01.1 permanece sempre `schema_version=1`.

Um fixture v0 inclui `state` G01.1, eventos sintéticos em sequência (`event_key`, `starter_choice`, `outcome`), intenções de recompensa, `history_sha256` para detectar alteração acidental, identidade regional, versão de armazenamento 0 e marcador `EXPLICIT_TEST_FIXTURE_ONLY`.

O migrador `migrate_legacy(blob,ctx,acknowledge_fixture_only=True)` só funciona após confirmação explícita (nem `1` nem `False` valem), verifica o checksum do histórico e **reexecuta** os eventos via G01.3, comprovando ordem U07, resultados das batalhas, recompensas, marcações de missão e capítulo. Reconstitui o estado por avanço sintético G01.2 e **exige igualdade exata** com o estado e as recompensas apresentadas no v0. Estados que não são replayáveis por esse contrato são rejeitados sem perda ou modificação do original.

O migrador produz bytes **v1**, nunca altera o v0 ou cria arquivos de save. O leitor corrente v1 recusa v0: não existe migração implícita. Um atacante que reescreva todo o histórico e seus hashes pode produzir outro fixture internamente coerente; não existe autenticação da origem. Essa limitação é intencional para dados sintéticos.

## Testes e limites

A suíte automatizada cobre round-trip de CH00, CH01 parcial, os 13 eventos U07, conclusões de todos os capítulos até CH12, três iniciais, derrotas de rivais permitidas, cinco intenções únicas de recompensa, determinismo e cópias independentes. Testes negativos cobrem corrupção/truncamento, UTF-8, BOM, excesso de bytes, JSON duplicado, versões desconhecidas, mapa nativo falsificado, payload alterado com hash válido, recibos incorretos, falsas recompensas, migrador sem permissão, histórico legado incompleto/desordenado e estados impossíveis de reproduzir.

```bash
python scripts/regions/audit_unova_g01_serialization.py --check
python scripts/regions/audit_unova_g01_serialization.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g01_serialization.py' -v
```

Todos executados pelo GitHub Actions Linux e Windows. Nenhum comando precisa ser executado no PC do usuário.

## Progresso e sequência

Após aprovação do CI e integração na `main`, a frente G01 passa a **4/4** e a Barra G para **12/32 (38%)**. Barra técnica A permanece **0/8** e Unova jogável **0/32**, com a região `planned`.

**Próxima frente:** G02.2, contratos dos capítulos e ginásios, mantendo trechos sem dados nativos identificados como pendentes. A integração do codec com arquivos de save reais não está autorizada pela G01.4.
