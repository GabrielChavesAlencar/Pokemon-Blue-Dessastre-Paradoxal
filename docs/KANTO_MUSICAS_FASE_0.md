# Kanto — Fase 0/6: auditoria e linha de base das músicas

**Data:** 12/11/2026. **Status:** verificação somente leitura; **nenhuma música aplicada automaticamente**, nenhum save, mapa ou arquivo de áudio modificado e nenhuma reprodução real no `Game.exe` comprovada.

[Plano de aplicação](KANTO_PLANO_APLICAR_MUSICAS.md) · [Mapeamento das 64 faixas](KANTO_MUSICAS_MAPEAMENTO.md) · [Catálogo JSON](../data/kanto-music.json)

## 1. Inventário e integridade

| Checagem | Resultado |
|---|---|
| Arquivos no catálogo Kanto | **64/64 MP3s** |
| Músicas contínuas | **50 BGM** em `assets/music/kanto/BGM/` |
| Vinhetas musicais | **14 ME** em `assets/music/kanto/ME/` |
| Total de bytes | **135.768.381** |
| Comparação de SHA e tamanho com os blobs do GitHub | **64/64 corretos** na árvore da `main` antes desta fase |
| Arquivos de origem do Kanto | **142 mapas**, **45 áreas em prévia** |
| Instalação local do `Game.exe` | **Não inspecionada**, pois `game/` é ignorado pelo Git |
| Playback em janela nativa Windows | **Não testado** |
| Novas associações de mapa, evento e batalha | **Zero** nesta fase |
| Direitos de distribuição de músicas oficiais | **Não comprovados** |

O manifesto `data/kanto-music.json` informa o nome, tamanho, tipo e Git blob SHA de cada MP3. O auditor de instalação já existente verifica os **bytes reais** de todas as 64 músicas no checkout. O novo relatório da fase 0 executa a mesma verificação e acrescenta o status dos mapas e hooks.

## 2. Locais de Kanto realmente identificados

Os números a seguir são **IDs originais da fonte FRLG**, e **não os MapIDs compilados do Decades**. Não usar esses números diretamente para atribuir BGM no jogo.

| Grupo | Constatado na fonte |
|---|---|
| Pallet Town / laboratório | 2 mapas: `PALLET_TOWN` (5) e `OAK_LAB` (6) |
| Mt. Moon | 3 mapas (1F, B1F e B2F) |
| Silph Co. | 12 mapas, com **uma prévia de geometria** |
| Ginásios | 8 mapas terminados em `_GYM` |
| Pokémon Centers | 9 mapas terminados em `_CENTER` |
| Lavender / Pokémon Tower | **Não constam** do manifesto atual |
| Rocket Game Corner / Hideout | **Não constam** do manifesto atual |
| Sevii / Pokémon Net Center | **Não constam** do manifesto atual |

O auditor lista grupos com IDs originais e os separa em `experimental`, `preview_only` e `absent_from_pilot_manifest`. Mapas ausentes não podem ser inventados na Fase 1.

## 3. Capacidade atual do BlueMusic (análise do Ruby, não reprodução)

| Recurso | Situação |
|---|---|
| BGM de mapas via `Game_Map`/`apply_map` | Hook presente no código |
| Música selvagem `pbGetWildBattleBGM` | Hook presente, configuração **global** |
| Música de treinador/líder `pbGetTrainerBattleBGM` | Hook presente, configuração **global** |
| Vitória selvagem `pbGetWildVictoryBGM` | Hook presente |
| Vitória treinador `pbGetTrainerVictoryBGM` | Hook presente |
| Vitória exclusivamente de ginásio | Hook específico ainda ausente |
| Vinhetas ME após eventos | Hook de reprodução **não encontrado** em `BlueMusic.rb` |
| Resolução regional automática só para Kanto | **Não implementada** nesse plugin |
| Decodificador MP3/ME em execução Windows | Não testado |

**Risco principal:** escrever temas de Kanto nas chaves globais `wild`, `trainer` ou `gym` também alteraria Decades. Por isso a **Fase 1 deve implementar isolamento por região antes de qualquer atribuição**.

## 4. Implementação da Fase 0 no repositório

- `scripts/music/audit_kanto_phase0.py` — script somente leitura que valida SHA/tamanho de todos os MP3s, 142 mapas/45 prévias e detecta os hooks BGM, Victory BGM, ME e região.
- `tests/test_kanto_music_phase0.py` — testes para contagens, agrupamentos, mapeamento de locais ausentes, hooks e segurança contra gravação fora de `.blue-work`.
- `.github/workflows/regression.yml` — passa a executar a nova auditoria junto com a auditoria de integridade e todos os testes unitários.
- `docs/KANTO_MUSICAS_FASE_0.md` — este registro de baseline.

A fase **não modifica** `scripts/music/BlueMusic.rb`, `Data/blue-music.json`, `MapXXX.rxdata`, áudio original, saves ou arquivos privados em `game/`.

## 5. Comandos reproduzíveis

Executar a partir da raiz do repositório:

```powershell
python scripts/music/install_kanto_music.py --audit
python scripts/music/audit_kanto_phase0.py
python -m unittest discover -s tests -p "test_kanto_music*.py"
```

O relatório JSON local fica em `.blue-work/kanto-music-phase0.json`. Ele registra `PASS_STATIC_BASELINE` sem fingir que houve áudio reproduzido.

**Opcional**, quando uma instalação do jogo estiver disponível, verificar a presença e o hash dos arquivos instalados, sem reproduzi-los nem copiar novos arquivos:

```powershell
python scripts/music/audit_kanto_phase0.py --game game
```

O comando apenas lê `game/Audio/BGM/Kanto` e `game/Audio/ME/Kanto`, se disponíveis. Sem instalação local, informa `not_checked`. Relatórios só podem ser gravados dentro da pasta ignorada `.blue-work`.

## 6. Critério de fechamento e próxima fase

Fase 0 tecnicamente concluída **apenas após a CI confirmar** 64/64 faixas reais com SHA correto, 50 BGM, 14 ME, 142 mapas, 45 prévias e relatório de capacidades com pendências explícitas. Testes unitários e regressões devem passar na mesma revisão do código.

**Continuam pendentes:** MapIDs compilados, músicas ativadas nos eventos, testes nativos de áudio/codec/loop/fade, GYM Victory, 14 ganchos ME, viagem Kanto ↔ Decades com música aplicada e testes no Windows/JoiPlay.

**Próxima fase:** implementar regras versionadas de escopo regional, compilação do mapeamento de MapIDs e guardas para preservar as músicas de Decades antes de ligar qualquer faixa.

> **Mensagem para continuar no chat:** Aplique a Fase 1 do plano musical de Kanto no GitHub, seguindo `docs/KANTO_PLANO_APLICAR_MUSICAS.md` e `docs/KANTO_MUSICAS_FASE_0.md`, e publique após testes.

**Esta fase não altera a Barra 2 de aceite integral de Kanto.**
