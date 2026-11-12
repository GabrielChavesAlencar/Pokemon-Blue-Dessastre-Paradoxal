# Próximos passos — Pokémon Blue: Dessastre Paradoxal

**Acompanhe as [16 etapas de conclusão de Kanto](KANTO_ETAPAS.md).** O contador é atualizado somente com testes concluídos.

**Comece pela etapa 1.** O piloto de Kanto já compila e recarrega um save no teste nativo, mas o percurso completo com os controles ainda precisa ser jogado. Esse teste decide se o piloto está pronto para servir de base às próximas regiões.

## Especificações de referência — regras já definidas

As decisões funcionais do circuito regional, balanceamento, pós-jogo, regras locais, viagens e preservação de saves **já estão especificadas** nos documentos abaixo. Este roteiro acompanha a implementação e a validação; **não substitui nem redefine** essas decisões.

- [Plano de regiões Dessastre v2 — especificação funcional principal](PLANO_REGIOES_DESSASTRE_V2.md): escolha da região inicial, duas regiões vizinhas por Liga, integração com esmeraldas e balanceamento atuais, pós-jogo após dez Ligas, classificação/bloqueio de especiais, NPC de transporte, HMs/montarias regionais, saves e testes.
- [Estudo de fangames e todas as regiões — referência técnica](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md): levantamento de fontes, licenças, importação modular de mapas e eventos, remapeamento de IDs, compatibilidade do Essentials e critérios de validação.

Se houver diferença entre uma sugestão exploratória do estudo e uma decisão explícita do Plano v2, usar a decisão do Plano v2. O estado do código deve ser verificado separadamente: documentação de regra não equivale a funcionalidade implementada.

## Ponto de partida

- [x] Decades é a campanha principal. O menu **Circuito de Regiões** reconhece o encerramento de Decades em saves existentes. As regras de progresso regional, viagem e pós-jogo já têm uma base em [`Regions.rb`](../scripts/battle_polish/Regions.rb).
- [x] Kanto tem um piloto separado de **Pallet Town a Pewter City**. São 13 locais, sete treinadores e Brock, com três equipes para o rival Blue. A fonte, os créditos e a preparação estão no [guia do circuito](CIRCUITO_REGIONAL.md).
- [x] O portal publica as fichas do piloto. [Localizações](https://pokemondessastreparadosal.vercel.app/localizacoes?regiao=kanto) · [Treinadores](https://pokemondessastreparadosal.vercel.app/treinadores?regiao=kanto) · [Brock](https://pokemondessastreparadosal.vercel.app/chefes/kanto-brock).
- [x] O teste nativo compilou o conteúdo, carregou Pallet e o laboratório, consultou encontros e equipes, registrou a Boulder Badge e recarregou o save. As vitórias de batalha foram simuladas pelo teste. [Execução no GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43123226204).
- [ ] Jogar o percurso manualmente. Na última tentativa de abrir a cópia local por automação, o motor falhou ao inicializar o sistema de arquivos (PhysFS). A abertura em uma sessão normal do Windows ainda precisa ser confirmada.

## 1. Validar o piloto de Kanto

Prepare a [instalação do Blue](INSTALACAO.md) e extraia o Essentials FRLG 1.1 conforme o [guia do circuito](CIRCUITO_REGIONAL.md). Na raiz do repositório, execute:

```powershell
python scripts/regions/pilot.py --launch
```

O comando usa `.blue-work/kanto-pilot` e o perfil de save **Kanto Piloto**. Se precisar reconstruir a cópia após mudar mapas ou scripts, passe um caminho novo, por exemplo `--output .blue-work/kanto-pilot-revisao`.

- [ ] Abrir o piloto no Windows. Se houver erro do motor, registrar a mensagem e o log, corrigir a causa e repetir a abertura.
- [ ] Em partida nova, entrar no laboratório de Oak, escolher um inicial e jogar a batalha contra Blue. Conferir as três escolhas e o comportamento após vitória e derrota.
- [ ] Sair de Pallet, encontrar e capturar um Pokémon na Rota 1, curar em Viridian e atravessar as conexões, portarias e saídas da floresta até Pewter.
- [ ] Jogar as lutas de Liam e Brock. Conferir o time de Brock, a Boulder Badge concedida uma vez e a recuperação após derrota.
- [ ] Salvar e reabrir pelo menu do jogo. Conferir posição, equipe, Pokémon capturado, itens e progresso. Reabrir também um save de Decades para conferir a compatibilidade.
- [ ] Testar o piloto no Android depois de validar no Windows, seguindo o [guia de JoiPlay](ANDROID_JOIPLAY.md).

## 2. Integrar uma viagem de ida e volta

- [ ] Colocar o agente de transporte depois do encerramento real de Decades. A confirmação deve usar os marcos auditados da Esmeralda Stellar e do Hall da Fama, descritos no [guia do circuito](CIRCUITO_REGIONAL.md).
- [ ] Ligar o agente a um ponto de chegada confirmado em Kanto e a um ponto de retorno acessível. Mostrar destinos jogáveis, condições de bloqueio e opção de cancelar. Validar em uma cópia antes de abrir a viagem na campanha.
- [ ] Usar um único save para a campanha integrada. Acrescentar estado regional versionado e preservar equipe, PC, Pokédex, itens, dinheiro, conquistas e missões. Exercitar save antigo, viagem, retorno, salvamento e recarga.
- [ ] Integrar a seleção da região inicial antes da escolha do inicial regional. Exibir como jogáveis as regiões cujo começo e percurso já foram validados.
- [ ] Integrar o cálculo de insígnias ao balanceamento atual. Cada conquista de ginásio ou equivalente soma uma esmeralda global uma vez. As permissões de campo e de Pokémon especiais usam conquistas locais.
- [ ] Classificar lendários, míticos, Ultra Beasts e Paradoxos, incluindo os autorais. Aplicar a regra das oito conquistas locais à equipe e ao PC. Na viagem, reservar slots antes de depositar os especiais e validar que sobra equipe utilizável. Se faltar espaço ou equipe, manter o estado anterior e permitir reorganizar a equipe.
- [ ] Ligar HMs, montarias e outras ações de campo às permissões da região atual. Usar as provas de Alola e a conclusão do arco de Hisui conforme o [catálogo regional](../site/public/data/regions.json).

## 3. Completar Kanto

- [ ] Expandir o trecho de Pewter aos oito ginásios e à Liga. Recriar eventos, rival, treinadores e marcos de história. Avaliar Sevii Islands conforme a disponibilidade de mapas e o escopo da campanha.
- [ ] Mesclar encontros de FireRed e LeafGreen preservando habitats, horários, métodos, níveis e pesos. Conferir espécies, golpes, itens e equipes-base contra as referências.
- [ ] Auditar IDs de mapas, switches, variáveis, tilesets, portas, pontos de cura e conexões. Resolver dependências em cada lote e registrar origem, créditos, remapeamento e como desfazer a importação.
- [ ] Validar a jornada até a Liga. Kanto deve liberar **Decades e Johto** somente após o encerramento da Liga. Repetir a finalização não duplica a conquista nem desbloqueios.

## 4. Expandir o circuito

O circuito de desbloqueio é **Decades ↔ Kanto ↔ Johto ↔ Hoenn ↔ Sinnoh ↔ Unova ↔ Kalos ↔ Alola ↔ Galar ↔ Paldea ↔ Decades**. A ordem abaixo é de desenvolvimento. Ao jogar, cada Liga libera as duas vizinhas, conforme o progresso do save.

| Ordem | Região | Trabalho a entregar |
| --- | --- | --- |
| 1 | Johto | Unificar HeartGold e SoulSilver, validar ginásios, Liga e viagens com Kanto e Hoenn. |
| 2 | Hoenn e Sinnoh | Fundir Ruby/Sapphire com Emerald e Diamond/Pearl com Platinum. Auditar conexões, encontros e eventos das Ligas. |
| 3 | Unova, Kalos e Alola | Tratar Black/White e Black 2/White 2 por era, unificar X/Y e adaptar as ilhas e provas de Ultra Sun/Ultra Moon. |
| 4 | Galar e Paldea | Tratar versões e conteúdo adicional por escopo. Implementar o Champion Cup de Galar e a progressão de Paldea. Encontrar uma fonte editável adequada para Paldea ou construir mapas próprios. |
| 5 | Hisui | Encontrar fonte editável ou construir mapas 2D. Criar expedição, permissões de campo e viagem temporal. Hisui tem encerramento próprio e fica fora da contagem das dez Ligas. |

- [ ] Para cada região, verificar a permissão da fonte, registrar créditos, importar primeiro um trecho em cópia isolada e validar mapas, eventos, batalhas, save e rollback antes de integrar.
- [ ] Depois das dez Ligas, ativar o pós-jogo mundial. Catalogar por região as equipes oficiais mais fortes de líderes, Elite Four onde houver e campeões. Registrar jogo, versão e referência de cada equipe antes de habilitar a revanche correspondente.

## 5. Atualizar o portal e o Blue Studio junto com cada lote

- [ ] Gerar localizações, encontros, treinadores e líderes dos mesmos dados usados pelo jogo. Para o piloto atual, use [`export_kanto.py`](../scripts/regions/export_kanto.py) a partir do diretório de prévia.
- [ ] Atualizar os estados no [catálogo de regiões](../site/public/data/regions.json) e vincular fichas da Pokédex, Habitat Dex, Pokégear e Álbum de Treinadores aos IDs efetivamente importados.
- [ ] Conferir seletores de região, fichas, equipes e links em desktop e celular. Informar no portal o que já pode ser jogado e o que ainda está em preparação.
- [ ] Rodar `npm test --prefix site` e `npm run build --prefix site`. Depois do push, conferir os testes do GitHub Actions e o [portal publicado](https://pokemondessastreparadosal.vercel.app/regioes).

## 6. Retomar as outras frentes do projeto

- **Pokédex autoral:** fechar os dados das espécies pendentes, revisar sprites, golpes e evoluções, e testar em batalha antes de liberar. [Geração Dessastre Paradoxal](GERACAO_DESSASTRE_PARADOXAL.md) · [Estudo dos sete Paradoxos futuros](PARADOXOS_FUTURO_7_POKEMON_ESTUDO.md).
- **Blue Studio:** revisar o plano de edição de mapas, flags, encontros e equipes. Priorizar validação de referências, pesos de encontros, backups e integração com a compilação. [Plano do editor](PLANO_EDITOR_EMERALD_BLUE.md).
- **Hub de Batalha:** usar o multiplayer sincronizado existente como referência. Retomar o experimento de servidor autoritativo se o projeto avançar para partidas com ranking. [Roadmap do Hub](ROADMAP_HUB.md) · [Manual do multiplayer](MULTIPLAYER.md).
- **Instalação e distribuição:** verificar instalação limpa, atualização, recuperação de falha e compatibilidade com saves. Versionar scripts e dados próprios. Manter a instalação do jogo, as fontes de terceiros, binários e saves nas cópias locais. [Instalação](INSTALACAO.md) · [Android](ANDROID_JOIPLAY.md).

Antes de retomar uma etapa, confira a `main` e marque neste arquivo o que tiver sido reproduzido. Quando concluir um lote, registre o teste, o commit e a próxima tarefa que ficou aberta.
