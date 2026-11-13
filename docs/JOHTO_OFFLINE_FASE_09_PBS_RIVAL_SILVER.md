# Johto — etapa OFFLINE 09/12: três equipes PBS do rival Silver

**Status da entrega:** PBS gerados a partir dos arquivos nativos exportados da instalação Blue/Decades, conferidos com os três mapas do estágio privado da etapa 08. **Sem executar Game.exe.** Dados nativos continuam fora do GitHub.

## Implementação

Novo gerador **`scripts/regions/build_johto_rival_pbs_v2.py`**, independente do rascunho antigo usado pelo piloto legado, que:

1. Lê exclusivamente PBS da instalação local do Blue: `trainer_types.txt`, `pokemon.txt`, `moves.txt`, e catálogos de espécies/movimentos.
2. Exige treinador nativo `RIVAL1`; copia apenas os campos de seu tipo de treinador para um **novo** tipo isolado `BLUE_JOHTO_RIVAL`, impedindo colisões com qualquer trainer type ou trainer já existente.
3. Para cada espécie do trio original, deriva o moveset de `Moves = nível,golpe` do `pokemon.txt` **somente até o nível 5**; exige que todos os IDs existam no catálogo nativo `moves*.txt`.
4. Verifica `BaseStats`, `Types` e `Abilities` das três espécies; confere que os três registros PBS gerados possuem Pokémon, nível e golpes corretos.
5. Opcionalmente confere o estágio **08/12** privado de New Bark por SHA-256 dos mapas `Map625`, `Map675`, `Map676`. O vínculo é um **relatório de auditoria**, não instalação ou partida jogável.
6. Salva **somente em uma pasta NOVA** dentro de `.blue-work/`, sem sobrescrever `game/`, PBS originais, Kanto, Decades, Hoenn, saves ou qualquer `ready marker`.

### Três equipes de Silver

| Inicial escolhido pelo jogador | Pokémon de Silver | Nível | Movimentos válidos na base | Versão |
|---|---|---:|---|---:|
| CHIKORITA | CYNDAQUIL | 5 | LEER, TACKLE | 0 |
| CYNDAQUIL | TOTODILE | 5 | LEER, SCRATCH | 1 |
| TOTODILE | CHIKORITA | 5 | GROWL, TACKLE | 2 |

Os pares seguem a lógica previamente implementada em `scripts/regions/JohtoPilot.rb` → `RIVAL_CHOICES`. O evento de Silver da etapa 08 chama `BlueJohtoPilot.rival`, que usa `TrainerBattle.start(:BLUE_JOHTO_RIVAL, "Rival", rival_version)`. O código já bloqueia combate enquanto não existir o **marcador legítimo de PBS compilado e testado**, que **não foi criado** nesta etapa.

O nível 5 é o **nível fixo da primeira batalha piloto** e corresponde ao inicial fornecido ao jogador. **Ainda falta testar e integrar o escalonamento com o level cap/esmeraldas do Blue**, especialmente após trocar de região. Não afirmar que esse balanço dinâmico já está comprovado.

### Prova a partir do pacote nativo privado

Os seguintes arquivos foram **lidos** da exportação privada do próprio usuário, sem enviá-los ao GitHub:

- `PBS/trainer_types.txt`: SHA-256 `cb22425baa7cfcb480a551761ba27f918bd6b1346c0f3c9c9fb644f82c1dff12`.
- `PBS/pokemon.txt`: SHA-256 `3444a5c9f51d0f3c72ffbed5e9dae25c5949dde018e2b14129e301d868f7da8e`.
- `PBS/moves.txt`: SHA-256 `3660c7ccc3f0f91a732ad3ce32a2f83a47d9559ac0f9ea6afd1b91f47d27f9ef`.

Foram gerados estes **dois PBS privados novos**, disponibilizados somente no ZIP entregue nesta conversa:

- `PBS/trainer_types_johto.txt` — SHA-256 `b03b67d002a3da65a9879365c17a1b7c1ae0b5ee1948366bbf335e06638a29a9`.
- `PBS/trainers_johto.txt` — SHA-256 `4f31591afe6e5266e31d2b8065648a891e47b534d83ac590c2bb9862c908edef`.

O relatório `johto-pbs09-report.json` também foi vinculado ao estágio real da etapa 08 (SHA-256 do manifesto `ef2067eeeed085756083293ee9bfecd80eb9726511596080daa6a3dab84d4de9`) e aos mapas `625`, `675`, `676` pelos respectivos hashes. **Não houve alteração de RXDATA na etapa 09.**

### Testes automatizados

- `tests/test_johto_rival_pbs_v2.py`: **10 testes Python** de versão 0/1/2, learnsets válidos, espécie/golpe ausentes, colisão de nomes de treinador, sobrescrita, arquivo de ready indevido, integridade e falta de QA real.
- `tests/johto_rival_three_versions_runtime.rb` + `tests/test_johto_rival_versions_runtime.py`: **1 teste Ruby executado via Python**, cobrindo as três escolhas e suas versões de batalha, bloqueio sem marcador, save/reload, duplicação e isolamento contra Kanto.
- **11 testes novos passaram no ambiente local.** O Ruby simula `TrainerBattle`: ele **não compila PBS nem executa a batalha real**. A CI de GitHub ainda precisa confirmar esses mesmos testes na `main`.

### Comando para regenerar sem abrir o jogo

```powershell
python scripts/regions/build_johto_rival_pbs_v2.py
python -m unittest discover -s tests -p "test_johto_rival_pbs_v2.py" -v
python -m unittest discover -s tests -p "test_johto_rival_versions_runtime.py" -v
```

Opcional, com os arquivos da etapa 08 disponíveis no workspace privado:

```powershell
python scripts/regions/build_johto_rival_pbs_v2.py --stage08 .blue-work/johto-staging-story-v1 --output .blue-work/johto-rival-pbs09-vinculado
```

Os arquivos são gerados **fora do repositório público** em `.blue-work/`. Se a pasta de saída já existir, o comando recusa sobrescrita. **Não copiar PBS manualmente para a campanha principal e não criar `Data/blue-johto-rival-ready.txt`.** A instalação automática pelo `Blue-Story.exe` segue **pendente**.

## Limites e próxima etapa

- A compilação real PBS/Essentials, o sprite gráfico `Graphics/Trainers/BLUE_JOHTO_RIVAL.png`, o combate real, seu nível com level cap global, o save após combate e os testes Windows/JoiPlay **não foram comprovados**.
- O script antigo `draft_johto_rival_pbs.py` e a montagem experimental legada `pilot_johto.py` permanecem preservados para evitar regressões; a integração final das etapas 08–12 e do instalador precisará usar explicitamente os novos PBS antes de habilitar qualquer região.
- **Próxima etapa OFFLINE 10/12:** encontros e treinadores das Rotas 29–31 com tabelas de PBS auditadas e integração segura em cópia isolada.
- **Barras: OFFLINE 9/12 (75%) · JOGÁVEIS 0/13 · TESTADAS NO EXE 0/13.**
