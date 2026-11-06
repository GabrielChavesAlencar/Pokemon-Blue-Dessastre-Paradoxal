# Encontros raros e menus leves

O manifesto `data/fan-encounters.json` define os 44 Paradoxos autorais prontos, distribuídos por 33 tabelas de encontro em 30 mapas. Cada espécie ocupa exatamente **5% do método indicado**, e não 5% da chance total de andar sem encontro. Áreas com três espécies autorais reservam 15% e mantêm 85% para os Pokémon originais. Espécies pendentes, Megas e evoluções autorais não foram liberadas como novos encontros.

A localização considera o tema da espécie: cavernas, túmulos, florestas, vulcões, águas profundas, gelo e cidades tecnológicas. O manifesto inclui a justificativa de cada habitat. A instalação remove as antigas concentrações das duas grutas, mantém todas as espécies originais e seus níveis e redistribui os pesos restantes para somar 100%. A operação também cobre variantes das tabelas e pode ser repetida sem duplicar encontros.

Com a progressão Blue ativa na História, os espaços seguem o gerador selvagem existente: 0–1 cristais permitem até 350 BST, 2–4 até 450, 5–10 até 540, e 11+ não têm teto. Os Paradoxos de 570 BST só aparecem na fase Master; antes, a mesma seleção gera um substituto legal. A Habitat Dex usa a mesma regra. O site mostra a tabela base, a chance e a condição de desbloqueio.

## PC, Hub e loja

- O PC reconhece os espaços das boxes, a equipe, as setas das boxes e Sair. As ações retornam os mesmos valores do teclado e continuam passando pelas verificações nativas de depósito, retirada, troca e liberação.
- O Hub usa ícones estáticos de até 96 pixels, cache limitado de imagens, reaproveitamento da lista filtrada e busca com teclado na tela no Android. A superfície mobile é 640 × 480, com conversão das coordenadas do toque. As animações das batalhas continuam usando a engine habitual.
- A escolha de quatro Pokémon usa os mesmos ícones estáticos e a mesma conversão de toque. A ordem escolhida determina a dupla inicial. Os times salvos continuam com seis membros.
- A loja desenha até cinco itens por página. Busque por nome, ID do item ou golpe da TM/TR. Os filtros são Todos, Posso comprar, Não possuo e Na mochila. Abas, pesquisa e páginas não alteram preços nem as verificações de dinheiro e espaço na mochila.

## Atualizar o Android sem perder o save

O plugin de múltiplos saves grava **File A.rxdata a File H.rxdata**, **Auto 1.rxdata a Auto 3.rxdata**, cópias `.bak` e possivelmente o save antigo `Game.rxdata`. A pasta é `SaveData::SAVE_DIR`: ela usa `System.data_directory` quando disponível e a pasta do jogo caso contrário. Por isso, um caminho fixo de outro aparelho não é uma indicação segura.

No menu inicial Android, abra **Onde fica meu save?**. O jogo mostra a pasta real e registra o caminho em `Data/blue-save-location.txt`. Esse arquivo só contém o caminho; ele **não é uma cópia do save**. Copie os arquivos de save existentes para um local separado antes de apagar a instalação. Extraia o pacote atualizado, cadastre seu `Game.exe` no JoiPlay e restaure as cópias na pasta de saves da nova entrada, conferindo o caminho novamente. Preserve o backup até confirmar o carregamento da sua partida.

## Verificação

`BlueMenuValidation` testa na engine os quatro estágios de encontros, PC por ponteiro, coordenadas mobile, ordem dos quatro Pokémon, cache do catálogo, dimensões das imagens e filtros/páginas da loja. Os testes Python verificam migração e idempotência dos encontros; os testes do site comparam as chances de todas as espécies com o manifesto. O desempenho e o teclado ainda precisam de confirmação em aparelhos Android reais.
