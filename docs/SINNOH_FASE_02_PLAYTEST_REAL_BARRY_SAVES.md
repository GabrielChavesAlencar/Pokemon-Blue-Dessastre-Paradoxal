# Sinnoh — teste manual real de Barry, nível dinâmico, portais e saves

**Situação:** 13/11/2026 — ferramentas publicadas. **Não foi executado Game.exe nem JoiPlay real nesta conversa.** Os resultados do CI são sintéticos e os casos locais seguem pendentes.

## O que mudou nesta etapa

O piloto autoral [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) tinha um bloqueio circular: sua primeira batalha contra Barry precisava do marcador `Data/blue-sinnoh-rival-ready.txt`, mas esse marcador era reservado para *depois* de testar a batalha. O código agora permite **tentar** Barry **apenas no QA isolado comprovado**, quando [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) confirma a compilação, a sondagem de todos os eventos e os hashes dos mapas e PBS. Esse mecanismo não cria o marcador de publicação e não habilita Barry em Decades, Kanto, Johto ou Hoenn.

- Se o resultado da engine for nulo (batalha não iniciada), o campo `rival_fought` permanece falso.
- Vitória ou derrota com `canLose` podem ser experimentadas, mas os testes de jogo real ainda não foram executados.
- O marcador final de Barry **não** é produzido automaticamente; não usá-lo para saltar os testes.

A segunda entrega é o roteiro de evidências [audit_sinnoh_playtest.py](../scripts/regions/audit_sinnoh_playtest.py). Ele exige uma cópia experimental existente com `--verify` válido e cria **44 casos individuais** na pasta privada `.blue-work`:

| Escopo | Casos | O que observar |
|---|---:|---|
| Três Poké Bolas | 3 | Turtwig, Chimchar, Piplup e tentativa de pegar um segundo inicial rejeitada |
| Barry | 12 | Três iniciais × Normal/Master × vitória/derrota, espécie rival, nível e quantidade da party |
| Portais | 16 | Todos os warps do roteiro, mapa/posição final real |
| NPCs | 5 | Mãe, Barry (introdução e batalha), Rowan (maleta e Pokédex) |
| Save/load | 3 | Um save para cada inicial, retomando o mesmo perfil e sem perder Pokémon ou Pokédex |
| Regressões | 4 | Decades, Kanto, Johto e Hoenn sem alteração indevida de save |
| Android/JoiPlay | 1 | Instalação independente, inicial e transição real no aparelho |
| **Total** | **44** | Exige observações nativas e evidências de cada caso |

## Execução no Codex / Windows

**Pré-requisitos:** fonte de mapas com direitos confirmados; nove mapas/24 eventos/16 warps auditados, pacote de Sinnoh privado montado, cópia Game.exe QA gerada, compilação Essentials concluída e relatório estrutural `engine_structural_report_consistent:true` pelo [instalador](../scripts/regions/install_sinnoh_qa_copy.py). Sem eles a ferramenta recusa gerar o roteiro.

**1. Verificar a cópia antes de testar:**

```powershell
python scripts/regions/install_sinnoh_qa_copy.py --verify ".blue-work/game-sinnoh-qa-PERFIL_REAL"
```

**2. Criar apenas uma vez o roteiro privado:**

```powershell
python scripts/regions/audit_sinnoh_playtest.py --qa ".blue-work/game-sinnoh-qa-PERFIL_REAL" --create
```

Isso cria `sinnoh-native-playtest.json` nessa cópia e **não** marca casos como executados. Nunca copiar os arquivos de QA, sprites, saves ou relatórios reais para o GitHub.

**3. Testar no Game.exe da cópia**, com um save separado por inicial e modo. Registrar os valores efetivamente vistos durante a batalha e a navegação. Para cada caso no JSON, preencher `observation` e `evidence`. Um exemplo **ilustrativo, não observado**, de batalha Normal com jogador de nível máximo 50:

```json
{
  "platform": "windows",
  "pass": true,
  "species": "CHIMCHAR",
  "version": 0,
  "outcome": "win",
  "highest_party_level": 50,
  "growth_rate_max_level": 100,
  "enemy_level": 35,
  "enemy_party_size": 1
}
```

No Master, com esse mesmo jogador, o nível esperado é **45** (90% de 50), com equipe maior conforme as regras do Blue. O verificador calcula `max(1, min(limite_de_crescimento, nível_máximo_da_party × porcentagem // 100))` para confrontar o nível observado, mas **não infere** o nível por foto ou substitui uma batalha.

Salvar uma captura PNG ou log local em `qa-evidence/` dentro da cópia, com nome simples sem espaços, e registrar:

```json
{
  "path": "qa-evidence/barry-TURTWIG-normal-win.png",
  "sha256": "COLOCAR_SHA256_REAL_DE_64_CARACTERES"
}
```

Para obter o SHA real da captura:

```powershell
(Get-FileHash ".blue-work/game-sinnoh-qa-PERFIL_REAL/qa-evidence/barry-TURTWIG-normal-win.png" -Algorithm SHA256).Hash.ToLower()
```

**4. Auditar sem alterar o jogo:**

```powershell
python scripts/regions/audit_sinnoh_playtest.py --qa ".blue-work/game-sinnoh-qa-PERFIL_REAL" --audit
```

O resultado apresenta `completed/total` e cada categoria individualmente. Rejeita captura fora da pasta privada, arquivo sem hash correspondente, tipo de Pokémon incorreto, versões trocadas, nível diferente de 70%/90%, time Master incompleto, save alterado, coordenadas erradas, Android confundido com Windows ou casos modificados. Ele **nunca altera** `game/`, saves, `blue-sinnoh-rival-ready.txt` ou o próprio JSON de observação.

**Atenção:** quando 44/44 capturas e observações estiverem preenchidas, a ferramenta retorna `MANUAL_EVIDENCE_RECORDED_NEEDS_HUMAN_REVIEW`. Isso apenas significa que os registros têm formato e hashes consistentes; **não prova por si só que uma pessoa jogou, que a captura é autêntica ou que Sinnoh está aprovado**. Ainda é necessário conferir visualmente as evidências, inspecionar os saves e aprovar manualmente a execução Windows/Android.

## Barra real de aceite

- **Código de apoio:** implementado no GitHub e testado com fixtures sintéticas.
- **Batalhas reais 70/90:** não executadas aqui.
- **Save/reload Windows:** não executado aqui.
- **Android/JoiPlay:** não executado aqui.
- **Aprovação técnica/jogável:** continua **0/13** até haver mapas reais e evidências aceitas.

## Testes sem ROM

```powershell
python -m unittest discover -s tests -p "test_sinnoh_playtest_audit.py" -v
ruby tests/sinnoh_pilot_runtime.rb scripts/regions/SinnohPilot.rb
ruby tests/sinnoh_qa_start_runtime.rb scripts/regions/SinnohQAStart.rb
```

Referências: [progresso central](SINNOH_PROGRESSO.md) e [pendências exclusivas do Codex](SINNOH_CODEX_PENDENCIAS.md).
