import {esc,icon} from './utils.js';

// Painel editorial sincronizado às regras dos módulos Battle Polish.
// Não altera PBS, probabilidade de encontro nem dados dos saves.
export const KANTO_DIFFICULTY=Object.freeze([
  {label:'Inicial',emeralds:'0–1',percent:70,bst:'350',power:'60'},
  {label:'Intermediário',emeralds:'2–4',percent:70,bst:'450',power:'90'},
  {label:'Avançado',emeralds:'5–10',percent:70,bst:'540',power:'Sem teto'},
  {label:'Master',emeralds:'11+',percent:90,bst:'Sem teto',power:'Sem teto'}
]);
export const KANTO_EVOLUTION=Object.freeze([
  {method:'Por nível',gate:'Nível natural + 5',example:'Rattata → Raticate: 25; Bulbasaur → Ivysaur: 21'},
  {method:'Pedra ou item simples',gate:'Progresso 30',example:'Pikachu → Raichu'},
  {method:'Troca, inclusive com item',gate:'Progresso 40',example:'Kadabra → Alakazam'},
  {method:'Felicidade',gate:'Progresso 45',example:'Golbat → Crobat'}
]);
export const KANTO_WILD_CHANCE=Object.freeze([
  {gap:'Abaixo do requisito',chance:'0%'},
  {gap:'Do requisito até +4',chance:'15%'},
  {gap:'+5 até +14',chance:'30%'},
  {gap:'+15 até +24',chance:'45%'},
  {gap:'+25 ou mais',chance:'60%'}
]);
const source='https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/';
const documentation=(path,label)=>'<a class="text-link" href="'+esc(source+path)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' '+icon('arrow')+'</a>';
export const kantoBalanceLink=()=>'<a class="text-link" href="/balanceamento?regiao=kanto">Entender o balanceamento de Kanto '+icon('arrow')+'</a>';
export function kantoBalanceNote(kind){
  const notes={
    wild:'<strong>Encontros selvagens dinâmicos.</strong> Os percentuais da tabela pertencem aos slots originais do PBS. Uma forma evoluída pode substituir parte desses slots quando o maior nível não-ovo da equipe libera sua evolução, sem eliminar a forma básica. A chance interna começa em 15% e chega a 60%; não some essa chance ao percentual original da rota.',
    trainer:'<strong>Treinadores comuns.</strong> Níveis calculados em 70% do maior Pokémon não-ovo do jogador, ou 90% no Master. Pokémon do adversário podem evoluir após o escalonamento: nível natural +5, pedra 30, troca 40 e felicidade 45. Em Master, equipes pequenas podem receber reforços para cobrir fraquezas.',
    boss:'<strong>Primeiro desafio de ginásio.</strong> O nível escala como o dos demais adversários (70%, ou 90% no Master), mas os líderes preservam as espécies e golpes autorais: sem reduzir BST nem potência por estágio. A evolução dinâmica automática não substitui essas espécies. No Master, o ajuste de tamanho de equipes curtas é tratado separadamente.',
    rival:'<strong>Rivais e chefes de história.</strong> O jogo preserva suas espécies autorais da evolução automática de treinadores comuns. A exceção especial de BST e potência do primeiro confronto regional vale para líder, Elite Four e campeão, não para qualquer rival.',
    league:'<strong>Elite Four e campeão de Kanto.</strong> O primeiro confronto preserva a equipe autoral, sem os cortes de BST ou potência base dos golpes; o nível ainda escala com a dificuldade. Equipes Full Power são perfis separados de pós-jogo, com os limites da fase novamente aplicáveis.'
  };
  return '<aside class="story-honesty kanto-balance-note">'+notes[kind]+'<p>'+kantoBalanceLink()+'</p></aside>';
}
const table=(headers,rows)=>'<div class="kanto-balance-scroll"><table class="kanto-balance-table"><thead><tr>'+
  headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+
  rows.map(row=>'<tr>'+row.map(value=>'<td>'+esc(value)+'</td>').join('')+'</tr>').join('')+
  '</tbody></table></div>';
export function kantoBalancePage(){
  return '<div class="kanto-balance-page">'+
    '<section class="section"><h2>Dificuldade global e escalonamento</h2>'+
    '<p class="data-note">Somam-se os cristais de Decades e uma esmeralda por insígnia regional única. O nível de batalha é calculado a partir do Pokémon não-ovo de maior nível da equipe do jogador, arredondado para baixo e limitado a 1–100. Os valores abaixo são regras, não níveis fixos de treinadores.</p>'+
    table(['Dificuldade','Esmeraldas totais','Nível do adversário','BST máximo comum','Poder base máximo comum'],
      KANTO_DIFFICULTY.map(d=>[d.label,d.emeralds,d.percent+'% do maior nível',d.bst,d.power]))+
    '<p class="data-note">Exceção de Kanto: no primeiro confronto, líder, Elite Four e campeão não sofrem cortes de BST nem de potência; seguem escalando de nível. Os limites voltam para revanches Full Power explicitamente autorizadas.</p></section>'+
    '<section class="section"><h2>Pokémon selvagens: evolução por progresso</h2>'+
    '<p>O encontro continua pertencendo ao habitat original: grama, caverna, água, pesca e outros métodos normais. As probabilidades dos slots não são reescritas. O progresso de evolução usa o <strong>maior nível de um Pokémon não-ovo da equipe</strong>, não a quantidade de insígnias e nem o nível sorteado originalmente para o slot.</p>'+
    table(['Método','Quando liberar no habitat','Exemplo'],KANTO_EVOLUTION.map(d=>[d.method,d.gate,d.example]))+
    '<h3>Chance de aparecer evoluído dentro do slot original</h3>'+
    table(['Distância até o requisito','Chance interna da evolução'],KANTO_WILD_CHANCE.map(d=>[d.gap,d.chance]))+
    '<p class="data-note">Exemplo: Rattata ainda aparece; com progresso 30, um slot de Rattata pode gerar Raticate com 30% de chance interna. Se evoluir, o Pokémon aparece no mínimo no nível de liberação (Raticate: 25). Pikachu/Raichu segue 30, Kadabra/Alakazam 40 e Golbat/Crobat 45. Não é preciso usar pedra ou trocar um Pokémon selvagem.</p>'+
    '<p class="data-note">Ramificações (como Eevee), formas regionais e condições especiais sem validação segura são protegidas. O Habitat Dex no jogo informa as formas liberadas. A referência global para nível selvagem no modo história é 45% do maior nível; os níveis-base exibidos nas rotas continuam sendo os valores de origem do PBS.</p>'+
    '<p>'+documentation('docs/EVOLUCAO_DINAMICA_TREINADORES_SELVAGENS.md','Regras e testes da evolução dinâmica')+'</p></section>'+
    '<section class="section"><h2>Treinadores comuns e Master</h2>'+
    kantoBalanceNote('trainer')+
    '<div class="regular-grid">'+
    '<article class="panel"><h3>Evolução após a escala</h3><p>Exemplo: Bulbasaur passa a Ivysaur a partir de nível 21 e a Venusaur a partir de 37. O jogo consulta os métodos de evolução do Essentials e não reescreve os times-base.</p></article>'+
    '<article class="panel"><h3>Times de Master</h3><p>O modo Master calcula 90% do maior nível e pode completar times de menos de quatro Pokémon com parceiros de cobertura de tipos, respeitando o limite da batalha. Chefes e equipes autorais têm proteções específicas.</p></article>'+
    '</div></section>'+
    '<section class="section"><h2>Líderes de ginásio</h2>'+kantoBalanceNote('boss')+
    '<p class="data-note">Brock, Misty, Lt. Surge, Erika, Koga, Sabrina, Blaine e Giovanni possuem insígnias locais diferentes. A primeira vitória conta uma vez para a progressão global; uma revanche não concede outra insígnia.</p>'+
    '<p><a class="text-link" href="/chefes?regiao=kanto">Ver os oito líderes e times-base '+icon('arrow')+'</a></p></section>'+
    '<section class="section"><h2>Elite Four, campeão e revanches Full Power</h2>'+kantoBalanceNote('league')+
    '<p>Em Kanto, a formação clássica é <strong>Lorelei, Bruno, Agatha e Lance</strong>, seguida pelo campeão <strong>Blue</strong> (equipe variável conforme o inicial escolhido). O catálogo de times mais fortes preserva as referências históricas, inclusive grupos de cinco Pokémon e repetições canônicas.</p>'+
    '<p class="data-note"><strong>Desbloqueio Full Power:</strong> concluir as dez Ligas do circuito e iniciar uma revanche validada. Não basta derrotar a Liga de Kanto. As fichas históricas do site não constituem confirmação de batalha jogável no Game.exe; a QA manual da campanha e das revanches permanece separada.</p>'+
    '<p><a class="text-link" href="/liga?regiao=kanto">Ver Elite Four, campeão e times mais fortes '+icon('arrow')+'</a></p>'+
    '<p>'+documentation('docs/REGIOES_BALANCEAMENTO_PRIMEIRO_DESAFIO_E_FULL_POWER.md','Contrato regional de primeiro desafio e revanche')+'</p></section>'+
    '<section class="section"><h2>Restrições locais e status</h2><p>Pokémon especiais do jogador dependem de oito conquistas <strong>na região atual</strong>; itens-chave e HMs não são compartilhados entre regiões. Isso não impede que um chefe use sua equipe canônica. As regras estão presentes nos scripts, mas o resultado jogável continua exigindo conferência dentro do Windows e Android/JoiPlay.</p>'+
    '<p>'+documentation('docs/KANTO_BALANCEAMENTO_PALLET_CARTOES_REGIONAIS.md','Balanceamento regional e cartões de Kanto')+'</p></section>'+
    '</div>';
}
