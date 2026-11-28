# Galar — roadmap para 100% jogável, Windows e Android

Plano para execução futura, **não** autorização para modificar o jogo.
Começar pelo [planejamento GD00–GD05](GALAR_PESQUISA_E_PLANEJAMENTO.md),
[atlas visual](GALAR_GD05_ATLAS_VISUAL_E_TILES_KANTO.md) e
[contrato multirregional](PLANO_REGIOES_DESSASTRE_V2.md).
Uma campanha Sword/Shield, oito vagas de ginásio, Champion Cup e
pós-jogo; Isle of Armor e Crown Tundra sem bloquear a campanha principal.

| Fase | Recorte futuro | Evidência necessária |
|---|---|---|
| GL00 | Baseline, fontes e IDs | Conferir MapInfos, reservas e IDs indiretos; provar suporte do motor/Android antes de propor faixas. Não renumerar saves. |
| GL01 | Postwick a Turffield | Casa, R01/R02, Weald inicial, trem, Wild Area sul, Motostoke, R03/mina/R04, Milo. Primeiro recorte do [GD03](GALAR_GD03_DESENHO_E_PRIMEIRO_RECORTE.md). |
| GL02 | R05, Hulbury e Motostoke | Day Care, bicicleta, Nessa, Galar Mine No. 2 e volta para Kabu. |
| GL03 | Hammerlocke, R06 e R07 | Wild Area norte no momento correto, variantes de Stow-on-Side, Glimwood, Opal/Ballonlea e acessos a Circhester no capítulo correspondente. |
| GL04 | Circhester, R08/R09 e Spikemuth | Gordie ou Melony numa vaga, Water Mode em R09, Piers, volta pela ligação liberada e Raihan em Hammerlocke. |
| GL05 | R10, Wyndon e Champion Cup | Trem e percurso até Wyndon, semifinais, Rose Tower, finais, Darkest Day, desafio de Leon e retorno; nenhuma Elite Four. |
| GL06 | Pós-jogo de base | Segundo arco da Weald, legendário do jogador conforme variante, Battle Tower e rematches; efeitos em save e recompensa não repetível. |
| GL07 | Isle of Armor | Estação, setores, dojo, provas, Kubfu e uma evolução autorizada; sem adiantar o fim da campanha nem ativar Dynamax por padrão. |
| GL08 | Crown Tundra | Estação/Freezington, expedições de Peony, Calyrex, ruínas e aves; Max Lair e Galarian Star Tournament conforme pré-requisitos e adaptações aprovadas. |
| GL09 | Fechar cobertura e paridade | Inventário auditado, todos os acessos previstos, versões, saves, recuperação e entregas Windows/Android. Distinguir QA física de CI. |

A cada recorte, testar teleporte indevido e fechamento de gates,
passabilidade, retorno sem atalho e isolamento multirregional. Visual:
onde não houver mapa aprovado, reconstruir do zero com tiles de Kanto
já em uso, preservando traçado, marcos e entradas com o atlas. Sword e
Shield não duplicam terreno quando muda só o elenco ou o desafio.

**Separar três sistemas:** transporte de trem e táxi visitado, bike terrestre
e Water Mode, e viagem entre regiões pelo NPC do Blue. Sem HM fictício;
sem Dynamax/Gigantamax ativo no Blue enquanto a política atual os mantiver
desligados. Propor eventual equivalente local de atividade online ou
de DLC em revisão separada, não prometer funcionalidade desligada.

Toda entrega futura exige [GD04](GALAR_GD04_VALIDACAO_E_HANDOFF.md):
mesma revisão Windows e Android pela fonte sem novo ZIP geral. Não
avançar GL00–GL09 nesta etapa; tudo permanece `planned`/`NOT_RUN`.
