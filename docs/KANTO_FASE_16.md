# Kanto — etapa 16/16: prontidão da integração e aceite controlado

**Data:** 12/11/2026. **Estado:** núcleo funcional de preparação de release; o aceite manual de Kanto **NÃO** está concluído. Os mapas do jogo, as oito insígnias e a Liga continuam experimentais e o catálogo regional continua com `status: prototype`.

## O que foi implementado

1. **Gate de publicação `scripts/regions/release_gate.py`:** cruza o manifesto da fonte com o catálogo do portal, as insígnias da região, os IDs de mapas/treinadores e as espécies da Pokédex, incluindo os aliases Nidoran♀/♂ do PBS. Recusa mapas ausentes, referências quebradas, porcentagens inválidas, mudança indevida das prévias ou alteração do estado de Kanto para `playable`.
2. **Integração com a prova Windows:** `scripts/regions/native_check.py` verifica a prontidão **na cópia isolada antes de injetar qualquer script de teste**; o teste integrado no `Game.exe` principal continua garantindo casa inicial de Pallet, NPC de viagens, proteção dos Pokémon especiais, PC e bag, origem Decades e save/reload. A CI não altera saves reais.
3. **Portal corrigido:** a antiga descrição limitada a “Pallet até Pewter” foi substituída por uma descrição do catálogo experimental completo; cada líder exibe a insígnia correta (**Boulder, Cascade, Thunder, Rainbow, Soul, Marsh, Volcano, Earth**) em vez de todos mostrarem Boulder.
4. **Mapa com estado explícito:** os 142 locais agora distinguem `experimental` (96), `preview` (45) e `encounter_review` (1, Route 23/Map209). Um mapa apenas de cenário não é apresentado como uma área funcional e Route 23 avisa que a tabela `LandDay` duplicada permanece suspensa.
5. **Pokédex vinculada ao guia:** os nomes internos `NIDORANfE` e `NIDORANmA` são resolvidos no site para os registros de Nidoran♀ e Nidoran♂ sem modificar o PBS, o Pokémon salvo ou o time-base.
6. **Relatório humano ampliado:** `scripts/regions/kanto_feedback.py` agora pergunta qual parte foi de fato testada: início/rotas, ginásios e eventos, Liga, integração/viagem/PC ou Android/JoiPlay. O botão **Testar Kanto** do menu principal continua abrindo o piloto isolado; após sair, `KANTO_JOGAR_EXPERIMENTAL.bat` apresenta as perguntas da seção escolhida.
7. **Evidência local protegida:** cada sessão de relato cria um `.md` e um `.json` dentro de `.blue-work/kanto-gui-reports`. Não há upload automático nem coleta de save. Mesmo respostas marcadas como “passou” são **autorrelatadas** e não podem marcar `accepted_integrally=true`; falhas e não testados ficam visíveis. O novo gate pode ler um relatório explicitamente indicado com `--manual-report`, mas não certifica aceitação por isso.

## Comandos para o usuário no Windows

**Fluxo recomendado:** iniciar `Blue-Story.exe`, selecionar **Testar Kanto**, jogar de verdade, sair do jogo normalmente, selecionar a seção correspondente à área que acabou de visitar e marcar **S/F/N**. O relatório fica exclusivamente no computador.

Alternativas a partir da raiz do repositório:

```bat
KANTO_JOGAR_EXPERIMENTAL.bat
```

Para gerar um relatório sem alegar nenhum teste:

```bat
python scripts\regions\kanto_feedback.py --no-prompt --scope all
```

Para validar a publicação *sem modificar o jogo nem aceitar resultados manuais*:

```bat
python scripts\regions\release_gate.py
```

O relatório de pré-publicação permanece em `.blue-work/kanto-phase-16-release-gate.json`. `ci_preflight_passed=true` é uma verificação **automática** de dados e mapas, **não** um laudo de jogabilidade.

## Verificações implementadas

- 142 mapas e **MapIDs históricos fixos**; 45 previews sem NPCs ou encontros; 1 exceção de encounters em análise.
- 144 perfis de treinadores e as oito recompensas corretas; times e encontros com espécies válidas na Pokédex, incluindo os aliases de Nidoran.
- 22 locais selvagens, 64 métodos e 52 espécies auditados no guia, com porcentagens somando 100% por método.
- Selo regional continua `prototype`; impossível converter em `playable` apenas por CI ou relatório autorrelatado.
- Testes Python para anomalias de catálogo, falsos resultados e seções Windows/JoiPlay; testes Node do portal; nativo Windows compilando o piloto e prova do jogo integrado.

## Pendências obrigatórias para **aceite integral**

A etapa 02 **ainda não foi aceita**. Portanto não se deve marcar Kanto como finalizada apenas porque a Barra 1 avançou. Os testes com usuário precisam cobrir:

- Nova partida dentro da casa de Pallet; movimento, colisões, portas, NPC Oak, pacote e os três iniciais.
- Percurso de oito ginásios sem teletransporte experimental, vitória/derrota/cura/captura, badges únicas e save/reload.
- Puzzles reais de Lt. Surge, Sabrina, Mansion e **Strength na Victory Road** (ainda possui adaptação experimental); Surf/Cut e regras locais de HMs.
- Route 23 (oito guardas, sem liberar encounter não auditado), Elite Four na ordem, Campeão Blue com as três variantes, Hall of Fame apenas na vitória e saída/retorno.
- Troca de região pelo NPC, mesmo save e PC, restrição de lendários/ultra beasts/paradoxos antes das oito insígnias, integridade do Decades legado.
- JoiPlay/Android com testes de input, mapas, travamentos, captura e save.
- Validação independente das exclusividades das ROMs FireRed/LeafGreen, itens e histórias canônicas pendentes, licença de sprites/áudio/créditos e pós-jogo.

**Importante:** esta entrega **não** implementa automaticamente os eventos/puzzles que ainda faltam (Safari Zone, Rocket Hideout, Strength físico, acesso integral marítimo, etc.). Eles continuam registrados como bloqueadores para a Barra 2.

## Duas barras

- **Barra 1 — núcleos funcionais:** após os testes Windows/Blue Studio/portal desta fase, **15/16 (93,75%)**, faltando apenas o núcleo 02 de caminhada manual.
- **Barra 2 — etapas integralmente aceitas:** **1/16 (6,25%)**, faltando 15. Nenhum resultado de CI deve alterar essa contagem.

A região continuará `prototype` até existirem evidências manuais suficientes e correções dos bloqueadores de história, HMs e Android. Os relatórios têm autoria local e devem ser revisados pelo responsável antes de qualquer mudança de status.
