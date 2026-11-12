# Kanto — Fase 07/16: Mt. Moon, Cerulean e Misty

**Estado:** desenvolvimento publicado e testes nativos automatizados aprovados; **aceitação interativa ainda pendente**.  
**Desenvolvimento:** **07/16 = 43,75%**.  
**Etapas integralmente aceitas:** **01/16 = 6,25%**; **15 pendentes**.

## 1. Fontes auditadas e mapas importados

Os mapas foram identificados **na fonte pinada** Essentials FRLG 1.1, TheTinfoilTemplar (ver [manifesto da origem](../data/regions/kanto-source.json) e [auditoria de eventos](../scripts/regions/audit_next_segment.py)). O projeto preserva os arquivos e nomes originais de Decades.

A fase importa **12 mapas adicionais aos 13 do piloto original**, totalizando **25**:

| ID na origem | Mapa |
| --- | --- |
| 26–27 | Centro Pokémon e Poké Mart de Pewter |
| 32–33 | Rota 3 e Rota 4 |
| 34 | Centro Pokémon de Mt. Moon |
| 36–38 | Mt. Moon 1F, B1F e B2F |
| 39–41 | Cerulean City, Centro Pokémon e Poké Mart |
| 42 | Ginásio de Cerulean / Misty |

O auditor [audit.py](../scripts/regions/audit.py) preserva **a alocação dos 13 mapas originais do piloto**, reservando novos IDs para os demais. Assim, os IDs do ginásio de Brock e demais mapas anteriores não são deslocados na cópia nova. IDs do projeto Decades continuam separados.

[verify_pilot.py](../scripts/regions/verify_pilot.py) exige os 25 arquivos e verifica conectividade de ida e retorno até Pallet, pontos de transferência, bounds e os nove destinos de teste. A [CI nativa](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43143778517) compilou os 25 mapas, confirmou o trajeto de retorno e verificou o save.

## 2. Treinadores, eventos e insígnias

Foram associados às chamadas auditadas do FRLG os novos treinadores de Rota 3, Mt. Moon e ginásio de Cerulean, incluindo os Rockets com versões de time distintas. Os retratos das **12 classes regionais** são copiados para `Graphics/Trainers/BLUE_KANTO_*.png` no jogo preparado, com checagem de ausência/colisão.

O [KantoPilot.rb](../scripts/regions/KantoPilot.rb) registra vitórias com chaves únicas de mapa/evento e é compatível com os registros antigos por nome.

**Ginásio de Misty:** Luis, Diana e Misty. A fonte auditada oferece à Misty **Staryu nível 18** e **Starmie nível 21**. Ao vencer, o jogo registra **CASCADE** uma única vez, sem alterar a Boulder e sem aumentar duas vezes a progressão Blue.

Também foram adaptados centros de cura, marts, passagens e uma Moon Stone que não pode ser retirada repetidamente pelo mesmo personagem. As tabelas de encontros preservam métodos como **CaveDay**, com verificação da distribuição de probabilidades.

**Limites deliberados:** a importação não executa indiscriminadamente os scripts originais FRLG. Fósseis, cenas mais complexas de Rocket, rivais de Cerulean, NPCs secundários e itens ainda não auditados permanecem fora do protótipo, e precisarão de implementação específica. Não interpretar ausência desses eventos como bug da campanha original de Decades.

## 3. Teste experimental para você

O [KANTO_JOGAR_EXPERIMENTAL.bat](../KANTO_JOGAR_EXPERIMENTAL.bat) abre o piloto em uma cópia sob `.blue-work` com perfil de saves separado da instalação normal, sem depender da enumeração de janelas Windows que produziu `WinError 0` nos testes externos.

Após escolher o inicial com Oak, use **menu de pausa → Testes Kanto (experimental)** para viajar diretamente a pontos auditados em Mt. Moon/Cerulean. Isso **não existe na campanha principal** e não concede insígnias automaticamente. Ao fechar o jogo, o BAT gera um checklist de observações **preenchido pelo usuário**, em `.blue-work/kanto-gui-reports`. Não envia logs ou saves automaticamente ao GitHub.

**Instruções:** [KANTO_TESTE_EXPERIMENTAL.md](KANTO_TESTE_EXPERIMENTAL.md).

## 4. Publicação no portal

A [base de dados do portal](../site/public/data/kanto.json) foi atualizada usando os encontros e as equipes compiladas na fonte auditada: **25 localizações e 28 treinadores identificados**, incluindo Brock e Misty, com variações quando existem. Os dados respeitam os nomes, níveis e golpes presentes na fonte licenciada do piloto.

## 5. Instalação principal e saves anteriores

**Não foi feita migração automática de uma instalação principal já integrada com 13 mapas para 25.** Um jogador pode ter saves ou alterações locais vinculados aos mapas antigos. Para testar a fase 07 **use o piloto experimental**, que cria uma cópia nova caso os scripts tenham mudado e preserva a anterior. Em uma instalação principal nova, o instalador importa os 25 mapas após prévia/confirmação, mas a atualização incremental de instalações antigas exige um migrador versionado e auditado separado.

A cópia isolada mantém o perfil `Kanto Piloto`. Mesmo com IDs do piloto original preservados, **faça um novo slot de teste** para validar a fase 07 e mantenha seus saves anteriores.

## 6. Pendências da fase 07

- [x] Identificar IDs, NPCs, coordenadas e equipes na fonte FRLG pinada.
- [x] Importar 12 mapas adicionais, incluindo escadas, centros, rota e ginásio.
- [x] Ligar treinadores e Misty; registrar Cascade uma vez.
- [x] Provar estruturalmente os 25 mapas e caminho de retorno.
- [x] Compilar no Windows runner, verificar Misty e salvar/recarregar com resultados de batalha simulados.
- [x] Criar atalho e teletransportes **somente para teste experimental**.
- [x] Atualizar a Dex/portal com dados auditados.
- [ ] Confirmar manualmente a navegação/colisão real entre as rotas e escadas.
- [ ] Confirmar encontros e batalhas reais de Route 3 / Mt. Moon / Misty, incluindo derrota e revanche.
- [ ] Verificar visualmente centros, marts, Moon Stone, Cascade, HMs e save/reload.
- [ ] Completar/adaptar os eventos de história pendentes e testar migração segura para o jogo principal.

**Próxima fase de desenvolvimento: 08/16 — Vermilion e Lt. Surge.** Os testes manuais das fases anteriores continuam abertos no [contador de Kanto](KANTO_ETAPAS.md).
