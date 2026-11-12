# Kanto — teste real de abertura e jogabilidade no Windows (etapa 02/16)

**Estado:** teste automatizado de janela adicionado; **validação manual de toda a jornada ainda pendente**.  
**Referências:** [Contador Kanto](KANTO_ETAPAS.md) · [Plano definitivo v2](PLANO_REGIOES_DESSASTRE_V2.md) · [Guia do piloto](CIRCUITO_REGIONAL.md).

## 1. Iniciar com um clique

1. Atualize a branch `main` e confirme que o jogo Blue está preparado em `game/`, com a fonte editável Essentials FRLG 1.1 em `.blue-work/frlg-source/Essentials FRLG` — consulte [instalação](INSTALACAO.md) e [circuito](CIRCUITO_REGIONAL.md). O BAT **não baixa recursos de terceiros** nem executa um EXE de fonte desconhecida.
2. Execute **`KANTO_TESTAR_WINDOWS.bat`** na raiz do repositório. Ele usa Python 3.10+, cria uma cópia se não existir e abre o `Game.exe` da cópia, nunca o Decades principal.
3. Mantenha a janela de comando aberta e jogue até terminar os testes. Ao fechar o jogo, o BAT mostra o resultado da inicialização e o local do relatório JSON.

**Alternativa no terminal**, na raiz do repositório:

```powershell
python scripts/regions/gui_diagnostics.py
```

O atalho agora **detecta automaticamente quando os scripts do piloto foram alterados desde a última construção**. Nesse caso, monta uma nova pasta `kanto-pilot-revisao-...` sem apagar a cópia antiga. A execução não atualiza silenciosamente os arquivos dentro de um piloto já preparado.

Se quiser forçar uma nova cópia para investigar um problema, mesmo sem mudanças no código, use:

```powershell
python scripts/regions/gui_diagnostics.py --rebuild
```

Se já existir uma cópia preparada, o script a reutiliza. O `--rebuild` cria outra pasta, mas **ambas podem usar o mesmo perfil de saves de teste `Kanto Piloto`**, então escolha "Nova partida" e não sobrescreva slots de teste importantes. Os saves de Decades ficam em outro perfil.

## 2. Comportamento e limites do diagnóstico

- O script verifica a integridade do piloto com `verify_pilot.py`, inicia `Game.exe` com a pasta de trabalho correta, monitora janelas visíveis do processo e captura stdout, stderr e eventuais erros do motor.
- O registro fica em **`.blue-work/kanto-gui-reports/kanto-gui-<data>.json`**, acompanhado dos logs de saída. Esses arquivos não são enviados automaticamente ao GitHub e estão fora do versionamento.
- Caso apareça **PhysFS**, o relatório marca `physfs_error` quando identificado nos logs. Verifique também se `Game.exe`, `Game.ini`, `mkxp.json`, `Data/` e `Graphics/` estão na **mesma pasta do piloto** e se o executável foi iniciado com a pasta de trabalho correta.
- `window_observed_not_gameplay_verified` confirma **somente que uma janela foi observada**. Não confirma mapa caminhável, controles, batalhas, encontros, recompensas ou compatibilidade dos saves.
- O monitoramento não injeta teclado/mouse e não modifica a campanha principal. Em ambientes sem desktop interativo (GitHub Actions), ausência de janela pode ser uma limitação do runner: **não atribuir automaticamente o problema ao jogo do usuário**.

### Diagnóstico automático (não substitui jogar)

```powershell
python scripts/regions/gui_diagnostics.py --probe --seconds 25 --no-build
```

O modo `--probe` encerra o processo de teste após o tempo definido, grava relatório e **não disputa o controle do mouse nem do teclado**. O workflow [kanto-pilot-check.yml](../.github/workflows/kanto-pilot-check.yml) executa essa sondagem depois da compilação e do teste nativo, restaurando o script de início normal; falhas de janela ficam registradas sem invalidar a verificação estrutural.

**Fase 16:** o relatório manual agora possui cinco grupos (início, ginásios, Liga, integração e Android/JoiPlay). Para quem executa `KANTO_JOGAR_EXPERIMENTAL.bat` pelo menu do jogo, o programa pergunta a seção na saída e grava `.md` + `.json` localmente. Para gerar modelo de todas as fases sem inventar testes: `python scripts/regions/kanto_feedback.py --no-prompt --scope all`. Ver [KANTO_FASE_16.md](KANTO_FASE_16.md). **CI confirma execução/estrutura, não batalha visual/captura real.**

### Atalho específico — última etapa de núcleo (02/16)

Para testar somente **caminhada, portas e passabilidade do caminho Pallet → Cerulean**, abra **`KANTO_VALIDAR_CAMINHADA.bat`** na raiz do repositório (ou inicie `Game.exe → Testar Kanto` e escolha a seção **caminhada** ao sair). O atalho usa o mesmo piloto e saves separados e oferece **13 testes manuais S/F/N** com relatório local `.md` e `.json`. Confira o [guia completo da fase 02](KANTO_FASE_02_MOVIMENTO.md).

O teste nativo usa `Game_Player` em 16 destinos e verifica possíveis rotas até portas, mas não injeta teclas nem simula o resultado do jogador. **Não marca a Barra 2 por conta própria.**

## 3. Checklist de jogabilidade (executar em janela de desktop real)

Executar uma nova partida do piloto e marcar os itens **somente após observar de verdade**:

- [ ] O jogo abre, exibe menu inicial e aceita WASD/setas/teclas configuradas. Não ocorre erro PhysFS.
- [ ] Pallet Town aparece sem tiles quebrados; personagem pode andar e entrar no laboratório de Oak.
- [ ] Oak oferece Bulbasaur, Charmander ou Squirtle; cada escolha funciona em sua **própria partida/slot de teste**, sem duplicar iniciais ou recompensas.
- [ ] Blue usa o inicial apropriado ao jogador. Testar **vitória e derrota em batalha real**; derrota não causa softlock.
- [ ] O jogador consegue deixar Pallet e entrar na Rota 1; há encontro real e captura de Pokémon com Poké Balls.
- [ ] Viridian City, Centro Pokémon e Poké Mart funcionam; curar, comprar e retornar às rotas é possível.
- [ ] Rota 2, portaria sul, Floresta de Viridian, portaria norte e Pewter têm transições/portas corretas. Testar também o caminho de volta.
- [ ] Treinadores da floresta iniciam batalhas reais e não repetem indevidamente após vitória. Derrota permite recuperação.
- [ ] Liam e Brock iniciam batalhas reais. Após vencer Brock, a Boulder Badge aparece **uma vez**; nova interação não duplica a recompensa.
- [ ] Salvar e sair pelo menu. Reabrir: posição, equipe, Pokémon capturados, itens, dinheiro e Boulder Badge continuam corretos.
- [ ] Abrir separadamente uma campanha/salvamento existente do Decades e confirmar que não foi alterado.

Se algum item falhar, anotar **mapa, evento/NPC, sequência de ações, mensagem de erro, resultado esperado/observado e log**. Isso alimenta a etapa 03 (correções do piloto).

## 4. Critério de aprovação da etapa 02

A etapa **02/16 só pode ser marcada como concluída** após **abertura em sessão gráfica Windows e checklist acima reproduzido**, com relatório/evidência do teste manual. Uma janela observada em CI ou um teste nativo com resultados de batalha simulados não basta. Até lá, o contador permanece **1/16 concluída; 15 restantes**.

## 5. Cuidados com instalação e dados

Não apagar `game/`, `Data/`, `PBS/`, `Graphics/`, diretórios de save ou a cópia anterior do piloto para investigar o problema. Não versionar executáveis, músicas, gráficos de terceiros nem saves. Logs podem conter caminhos locais; revise antes de compartilhar.
