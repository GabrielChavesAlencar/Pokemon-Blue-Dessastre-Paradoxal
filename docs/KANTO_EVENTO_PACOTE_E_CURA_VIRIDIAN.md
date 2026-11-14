# Kanto — Evento do pacote de Oak, Poké Mart e acesso à Rota 2

**Referência de sequência:** [Detonado FireRed/LeafGreen organizado](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md), seções 2.1 e 2.2. Este documento corrige o local do bloqueio da primeira versão do evento, sem importar scripts/flags de projetos externos.

## A sequência correta

1. Depois de obter o inicial e enfrentar o rival, o jogador chega a Viridian pela Rota 1.
2. Ao atravessar a entrada do **Poké Mart de Viridian**, o evento único é preparado novamente caso um save antigo tenha marcado seu self-switch antes da entrega. O evento **Autorun** chama o jogador.
3. O protagonista **caminha automaticamente até uma casa adjacente ao vendedor**, seguindo uma rota calculada com a passabilidade real do mapa; aguarda o movimento e inicia o diálogo do pacote. Não é necessário interagir manualmente nem o personagem atravessa prateleiras.
4. Ao receber a encomenda, registra `pilot_oak_parcel_received`; nessa primeira entrega **a loja não abre compras**. Interações seguintes permitem compras normalmente.
5. Em Pallet, Oak recebe o pacote, ativa Pokédex e concede **cinco Poké Bolas**. Registrar `pilot_oak_parcel_delivered` somente após conseguir dar a recompensa, impedindo duplicação e permitindo recuperar Bolsa cheia.
6. O **bloqueio é a saída NORTE de Viridian City antes de entrar na Rota 2**, na conexão real `10 ↔ 18`, e não os túneis/portarias da Viridian Forest. A barreira usa eventos locais de `Player Touch` nas colunas exatas da conexão, com uma **segunda proteção no movimento para o norte** ao atravessar a borda: mesmo se um evento invisível não colidir, o jogador não muda de mapa antes da entrega. Os transfers entre portarias e Viridian Forest permanecem intactos.
7. O Centro Pokémon de Kanto mantém sua vinheta `healed` e retorno à BGM.

## Segurança e compatibilidade

- O mapeamento lê o arquivo `PBS/map_connections.txt` da fonte FRLG previamente auditada. Se a conexão `10↔18` não existir ou não for a conexão norte/sul, o gerador **falha** em vez de colocar barreira no mapa errado.
- A barreira só acrescenta eventos no mapa **Viridian City**, sem trocar MapIDs, tilesets, encontros, música, Johto, Sinnoh ou saves de Decades.
- A barreira possui dois mecanismos: eventos sólidos com mensagem no limite da cidade e uma interceptação de movimento exclusivamente sobre os marcadores da saída norte, para impedir passagem por conexão direta. Após a entrega, a interceptação fica inativa e o self-switch A local abre a passagem; ao tentar novamente, atravessa normalmente.
- A entrada normal do Mart rearma o autorun somente se o pacote ainda estiver pendente, recuperando saves anteriores em que era preciso conversar manualmente.
- Atalhos do menu **Testes Kanto (experimental)** podem teleportar para além do bloqueio, propositalmente, apenas para QA; isso não conta como progressão.
- O algoritmo de caminho limita a busca a 1024 casas; se não encontrar um percurso, o funcionário entrega o pacote à distância sem prender o jogo. Esta exceção deve ser revisada em teste de movimento real.

## Critérios de aceite

- [ ] No primeiro ingresso normal no Mart, o NPC chama o personagem sem pressionar ação; animação conduz até o balcão e concede pacote apenas uma vez
- [ ] O primeiro atendimento não abre uma tela de compra; segunda visita abre a loja
- [ ] Antes de levar o pacote a Oak, não é possível sair de Viridian para a Rota 2, inclusive depois de salvar e recarregar
- [ ] Após a entrega, atravessar a mesma saída para Rota 2 normalmente; as portarias/floresta não impõem bloqueio adicional
- [ ] Verificar saves antigos, Bolsa cheia, Johto/Decades, áudio da cura, Windows e Android/JoiPlay
- [ ] `python -m unittest tests.test_kanto_parcel_story -v`
- [ ] `python -m unittest discover -s tests -v`
- [ ] `ruby -c scripts/regions/KantoPilot.rb`
- [ ] Verificação estrutural do piloto, CI Windows, e caminhada real; se a CI não puder validar o arquivo FRLG fixado pelo SHA, manter aceite visual como pendente

**Instalação:** atualizar a fonte e reconstruir o piloto/versão Android. O executável já instalado não é modificado por alterações no GitHub.
