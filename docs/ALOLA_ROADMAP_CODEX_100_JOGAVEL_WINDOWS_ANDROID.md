# Alola — roadmap para 100% jogável, Windows e Android

Plano futuro, não autorização de implementar. Antes de qualquer fase,
ler [planejamento AD00–AD05](ALOLA_PESQUISA_E_PLANEJAMENTO.md),
[contrato multirregional](PLANO_REGIOES_DESSASTRE_V2.md) e main atual.
Uma jornada USUM nas quatro ilhas e uma instalação multirregional.
SM entra como referência de variantes, sem duplicar localidades,
provas, Liga, save ou recompensa.

## Regras que não mudam

- Sem ginásios ou HMs fictícias: Poké Ride por evento local. Oito provas
  USUM para os marcos Alola, uma esmeralda por primeira conclusão;
  quatro Kahunas separados. Poni Vast e Mina contam separadamente e
  não inventam capitão. Especiais usam as oito chaves do Blue.
- Observar trilhas, entradas e marcos do [atlas](ALOLA_AD05_ATLAS_VISUAL_E_TILES_KANTO.md).
  Mapa editável de RPG Maker só se aprovado. Se não, recriar com os
  tiles de Kanto em uso e marcar adaptações, sem importar as imagens.
- Aplicar [save, balanço e viagem](PLANO_REGIOES_DESSASTRE_V2.md) do
  Blue, sem criar política paralela. Separar história de entrada livre
  entre regiões instaladas; não dar viagem livre entre ilhas bloqueadas.
- Mudança que chega ao jogador exige Windows e Android pela fonte, no
  mesmo produto, conforme [AD04](ALOLA_AD04_VALIDACAO_E_HANDOFF.md).
  Até então tudo permanece `planned` e os testes, `NOT_RUN`.

## Sequência de execução futura

| Fase | Recorte | Critério de saída |
|---|---|---|
| AL00 | Baseline e planejamento técnico | Inventário real de IDs/reservas, contrato do motor e fotos/tiles auditados sem modificar sistemas globais. |
| AL01 | Melemele D01–D03 | Casa, Mahalo, escola, Hau’oli, R02/R03, Ilima, Hala e Tauros em percurso real; somente depois liberar a chegada a Akala. |
| AL02 | Akala: chegada, Paniola e Lana | Travessia e volta, Heahea, R04/R05/R06, Paniola Ranch, Brooklet Hill e Lapras; preservar ordem e bloqueios entre ramos. |
| AL03 | Akala: etapas restantes | Royal Avenue, R07/R08, Wela/Kiawe, Lush Jungle/Mallow, R09, Konikoni e Olivia; acesso correspondente a Aether e Ula’ula. |
| AL04 | Ula’ula: Malie a Tapu Village | R10–R14 e observatório, Sophocles, Thrifty Megamart abandonado/Acerola, Mudsdale por evento e portas laterais auditadas. |
| AL05 | Ula’ula: Po Town e Aether | R15–R17, Sharpedo, Po Town, Nanu e capítulo principal de Aether Paradise; sem reencenar a visita inicial nem duplicar batalhas. |
| AL06 | Poni e clímax Ultra | Seafolk, áreas nomeadas, Machamp, Vast Poni, Altar e Ultra Megalopolis/Necrozma; prever variantes Ultra sem repetir clímax. |
| AL07 | Mina, Hapu e Liga | Ordem USUM, oitava chave, grande prova final, Mount Lanakila e Elite Four. Hau é o primeiro desafio de título USUM, não Campeão prévio; Kukui pertence ao comparativo SM. |
| AL08 | Pós-jogo e áreas restantes | Defesas, Rainbow Rocket, Ultra Beasts, Tapu, áreas de Poni, Battle Tree e serviços opcionais; gates separados, exclusividades coerentes e equivalentes offline aprovados. |
| AL09 | Fechamento de cobertura | Inventário área por área com entrada/volta, serviços e variantes, regressões do save e transportes, releases Windows/Android correspondentes e QA física pendente identificada. |

O inventário AD02 define o que conta como visita obrigatória, ramal ou
conteúdo de variante. Antes de cada recorte, comparar o grafo e ordem com
USUM. Se uma cidade tiver várias zonas, manter portos e serviços
conectados por caminho, não encurtar geografia com teleporte. Ultra Space,
variações de Altar e Liga são estados próprios, não rotas numeradas.

## Diferenças que exigirão prova explícita

| Superfície | Limite |
|---|---|
| Ultra Sun × Ultra Moon | Uma única campanha; registrar variante de Totem, espécies e cenas em tabela por evento. Nenhum segundo marco por variante. |
| USUM × SM | Documentar seleção de inicial e início, totem de Vast Poni, sequência de Mina/Hapu, Liga e pós-jogo; não combinar versões por coincidência de nome. |
| Windows × Android | Mesmo grafo, itens, progresso, save e terreno na mesma revisão. Não criar versão Android incompleta ou redistribuir os arquivos de origem. |
| Instalação limpa × existente | Atualização idempotente; saves e outras regiões intactos, travas e retorno preservados. Ninguém precisa trocar de instalação para visitar Alola. |
| Serviços 3DS × Blue | Fazer equivalentes offline só se projetados e autorizados; não exigir conexão desativada, nem inventar progresso por serviço indisponível. |

Não iniciar AL00–AL09 neste trabalho documental.
