# Sinnoh — verificação estrutural nativa pós-compilação (sem aprovação de gameplay)

**13/11/2026 — entregue em código na main; QA com o Game.exe real ainda pendente.**

O piloto novo de Sinnoh é preparado em uma **instalação de testes separada** por [install_sinnoh_qa_copy.py](../scripts/regions/install_sinnoh_qa_copy.py). Esta etapa acrescenta uma **sondagem estrutural pós-compilação do Essentials**: [SinnohQAProbe.rb](../scripts/regions/SinnohQAProbe.rb).

Essa sondagem não executa batalhas nem percorre mapas. Não altera saves, não libera o encontro com Barry e não produz comprovação de Windows/Android jogável.

## Funcionamento

1. O Codex gera o overlay de Sinnoh a partir da **fonte realmente autorizada** (mapas, NPCs, sprites, posições e hashes conferidos), usando [prepare_sinnoh_pilot_bundle.py](../scripts/regions/prepare_sinnoh_pilot_bundle.py).
2. O instalador cria uma pasta nova em `.blue-work`, copia a base limpa de Decades **sem saves** e configura um perfil exclusivo `dataPathApp`/`dataPathOrg`/`Game.ini`. O instalador registra os nove mapas e seus 24 eventos em `Sinnoh qa.json > event_contract`, com nomes, coordenadas e comandos esperados.
3. A primeira execução do **Game.exe da cópia privada** solicita a compilação PBS. Após `Compiler.main`, a sondagem Ruby é chamada pelo bootstrap compilador, **somente no QA**, sem ser carregada na instalação principal.
4. O `BlueSinnohQAProbe.run!` consulta os dados reais do motor compilado: `GameData::Trainer.get(:BLUE_SINNOH_RIVAL, "Barry", versão)` e `load_data("Data/MapNNN.rxdata")`. Confere os dados por tipo, espécie, nível-base, mapa, evento, comando, sprite de evento e transição.
5. Apenas após todas as verificações, escreve o relatório local `Data/blue-sinnoh-qa-engine-check.json`, grava `Data/blue-sinnoh-qa-compiled.txt` vinculado ao identificador da cópia e remove o pedido de compilação. Se houver falha, escreve o log em `Data/blue-sinnoh-qa-compile-error.txt`.
6. O comando Python `--verify` confere novamente o token, os hashes de **todos** os mapas Sinnoh preparados, o relatório nativo, a quantidade de eventos/warps e as três espécies de Barry. O plugin [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) também exige esse relatório antes de autorizar **Novo Jogo** no QA.

## Contrato da auditoria

| Item | Confirmação exigida |
|---|---|
| Nove mapas | Todos presentes e carregados como RPG::Map |
| 24 eventos | Lista e posições idênticas ao contrato do overlay |
| Cinco NPCs | Handlers originais Blue: mãe, Barry (introdução/batalha) e Rowan (maleta/Pokédex) |
| Três Poké Bolas | Eventos físicos de `TURTWIG`, `CHIMCHAR` e `PIPLUP`; sem seleção por diálogo |
| Dezesseis warps | Código `201`, MapID de destino, x/y de chegada e trigger touch exatos |
| Barry 0 | Turtwig escolhido pelo jogador → Chimchar do rival |
| Barry 1 | Chimchar escolhido pelo jogador → Piplup do rival |
| Barry 2 | Piplup escolhido pelo jogador → Turtwig do rival |
| Nível-base PBS | `5` é somente o valor inicial na serialização; **não comprova** os 70%/90% do nível em batalha |
| Preservação | Nenhum `blue-sinnoh-rival-ready.txt` prematuro, nenhuma aprovação automática do jogo |

O relatório identifica apenas `ENGINE_STATIC_INDEX_AND_EVENTS_PROBE_ONLY`, com estado `NATIVE_STRUCTURAL_CHECK_NOT_GAMEPLAY` e os campos `gameplay_approved:false`, `battle_executed:false`, `dynamic_level_verified:false`, `save_reload_tested:false` e `android_verified:false`.

**Nota:** o compilador e a sondagem usam dados nativos em uma cópia de QA quando o Codex executar os comandos no Windows. **Nesta conversa foram aprovados apenas testes sintéticos em CI**, não houve execução com a cópia verdadeira.

## Comandos no Windows / Codex

Todos os passos a seguir exigem fonte autorizada, coordenadas reais e um pacote de integração local de Sinnoh pronto. A criação da cópia é descrita em [SINNOH_FASE_02_INSTALACAO_QA_SAVES_E_PBS.md](SINNOH_FASE_02_INSTALACAO_QA_SAVES_E_PBS.md).

**Verificar a cópia antes de abrir:**

```powershell
python scripts/regions/install_sinnoh_qa_copy.py --verify ".blue-work/game-sinnoh-qa-PERFIL_REAL"
```

**Primeiro Game.exe (cópia QA apenas):** compilar dados PBS e rodar a auditoria estrutural. A janela deve encerrar após a compilação; não aceitar o início de jogo como prova automática.

**Verificar novamente:**

```powershell
python scripts/regions/install_sinnoh_qa_copy.py --verify ".blue-work/game-sinnoh-qa-PERFIL_REAL"
```

O relatório válido deve incluir:

```json
{
  "region": "SINNOH",
  "mode": "QA_READ_ONLY_VERIFICATION",
  "compiled_marker_present": true,
  "engine_structural_report_consistent": true,
  "compile_request_pending": false,
  "ready_to_launch_for_manual_testing": true,
  "playable_approved": false
}
```

Esse é um **exemplo de estrutura esperada**, não o resultado de uma execução real na máquina do usuário. O marcador `Data/blue-sinnoh-rival-ready.txt` continua ausente.

**Segundo Game.exe:** testar em save novo dentro do quarto, mãe, Barry, Rowan, três Poké Bolas, dezesseis transições, ganho/perda contra Barry, Pokédex, evolução/level cap e save/load. O nível final do rival deve ser observado no jogo com a regra Blue **70% Normal / 90% Master**, e deve haver testes no Android/JoiPlay e regressões Decades/Kanto/Johto/Hoenn. Somente essa validação posterior pode justificar avanços nas fases jogáveis.

## Testes automatizados disponíveis sem ROM

```powershell
python -m unittest discover -s tests -p "test_sinnoh_*.py" -v
ruby -c scripts/regions/SinnohQAProbe.rb
ruby tests/sinnoh_qa_engine_probe_runtime.rb scripts/regions/SinnohQAProbe.rb data/regions/sinnoh-twinleaf-events.json
ruby tests/sinnoh_qa_start_runtime.rb scripts/regions/SinnohQAStart.rb
```

Eles são executados em [regression.yml](../.github/workflows/regression.yml) usando **fixtures sintéticas**, inclusive uma simulação de GameData e de RPG::Map que rejeita espécies erradas de Barry, eventos alterados, warps para IDs 800–805 e ausência de mapas.

## Pendências e restrições

- Os IDs `800–805` do piloto antigo de Sinnoh não podem ser mesclados à faixa reservada `600–999` de Johto. O novo piloto só usa IDs e coordenadas locais auditados.
- Não presumir direitos de redistribuição de mapas, músicas, gráficos, sprites ou projetos de terceiros.
- Não alterar `game/`, não usar saves existentes e não instalar a sondagem de QA no jogo principal.
- Não elevar as **13 fases técnicas/jogáveis/nativas** apenas por presença de relatório ou CI verde.

Ver [progresso de Sinnoh](SINNOH_PROGRESSO.md) e [pendências reais do Codex](SINNOH_CODEX_PENDENCIAS.md).
