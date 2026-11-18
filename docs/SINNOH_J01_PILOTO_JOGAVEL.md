# Sinnoh jogável — J01: pré-voo executável do piloto Twinleaf → Sandgem

Essa é a nova barra **J01–J08**, exclusiva da integração jogável. Nenhuma fase documental L00–L20 avança a barra. A J01 entrega código executável, **não** instala mapas ou prova jogabilidade.

## Primeira fase implementada
- `scripts/regions/preflight_sinnoh_playable_j01.py`: diagnóstico de leitura dos arquivos `game/Data`, hashes de MapInfos, inventário de MapIDs, fonte RMXP/ZIP e contrato original com 9 mapas, 16 portais, 5 NPCs e 3 Poké Bolas.
- `SINNOH_J01_DIAGNOSTICAR_JOGAVEL.bat`: launcher Windows opcional; identifica instalação no `%LOCALAPPDATA%` quando presente. A fonte autoral é opcional como primeiro argumento. Não executa Game.exe nem JoiPlay.
- `site/public/sinnoh-jogavel.html`: nova barra no site, separada de documentação (1/8 de implementação de código, 0/8 de validação nativa).
- `data/regions/sinnoh-playable-progress.json`: dados versionados e 8 fases.
- `tests/test_sinnoh_j01_playable_preflight.py`: teste de contratos e bloqueios. CI `sinnoh-playable-j01.yml`.

## Como funciona
Por padrão, apenas imprime um JSON sanitizado em stdout e retorna código 2 quando faltam entradas. Com **fonte autorizada** e jogo local já disponível, o status máximo da J01 é `BASELINES_OBSERVED_UNVERIFIED`. Isso ainda bloqueia a instalação.

No checkout do GitHub, a ferramenta pode ser usada em modo leitura:
```sh
python scripts/regions/preflight_sinnoh_playable_j01.py --game-data "CAMINHO_DA_INSTALACAO/game/Data" --source "FONTE_AUTORIZADA.zip"
```
Para um resumo local explícito, `--write-local-report` cria apenas `.blue-work/sinnoh-jogavel/j01-preflight.json` sem sobrescrever arquivo anterior; nunca grava em `game/`.

## O que falta para poder jogar
**J02** exige combinar 9 símbolos Twinleaf/Sandgem com MapIDs reais e hashes, sem invadir Kanto/Johto/Hoenn/Unova. Em seguida J03 converterá os recursos autorizados em stage isolado, J04/J05 integrarão portais e batalhas, J06 construirá um instalador Windows de QA, J07 testará o jogo e J08 fará Android/JoiPlay. Até lá: R07/R08/R09 pendentes, 0/44 QA nativa e Sinnoh *planned*.

**Segurança:** sem redistribuir fonte, ROM, assets ou dados privados; não ler nem alterar saves, não tocar na instalação principal, não inventar direitos ou aprovações. Conclusão da fase J01 significa ferramenta de diagnóstico executável e tests CI, não jogo pronto.
