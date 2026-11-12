# Kanto — Fase 1/6: escopo regional e MapIDs compilados

Data: 12/11/2026. Código e testes: [PR #19](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/19).

## Implementação

- Regras versionadas em `data/kanto-music-rules.json`: **51 mapas, 8 classes de batalha, 7 eventos ME, 5 cenas BGM**. Todos os vínculos têm `enabled: false` nesta fase. Nenhuma música foi ativada por padrão.
- Compilador `scripts/music/compile_kanto_music.py`: cruza as regras simbólicas com o catálogo de 64 MP3 e os **MapIDs realmente gerados** por `Kanto pilot.json` ou `Data/blue-kanto-install.json`. Confere os 142 mapas, 45 prévias, arquivo MapXXX.rxdata, duplicações, categoria BGM/ME e integridade do escopo.
- Arquivo isolado `Data/blue-kanto-music.txt`: contém cabeçalho com versão/hash, 142 registros SCOPE com MapIDs **compilados** e somente MAP/BATTLE aprovados e com áudio disponível. Uma prévia não recebe BGM antes de ser promovida legitimamente.
- `BlueMusic.rb`: fallback regional ativável somente se `BlueRegionalPolicy.state["current"] == "KANTO"` e mapa atual constar no escopo compilado. Quando a região não existe, é Decades, ou arquivo está ausente/inválido, conserva áudio nativo.
- Preferências manuais do editor e sorteios atuais mantêm prioridade; músicas globais `wild`, `trainer`, `gym` e `*Victory` de Decades permanecem iguais.
- O piloto gera seu manifesto antes da publicação da cópia; a importação Kanto carrega esse arquivo na mesma transação de mapas. Um jogo com Kanto já instalado pode recompilar a configuração no instalador de música sem apagar `Data/blue-music.json` e `Data/blue-music.rxdata`.
- Atualização explícita é atômica e mantém backup da versão anterior do manifesto regional.

## Matriz de aceite

| Medida | Fase 1 |
|---|---|
| Músicas no pacote | 64, sendo 50 BGM e 14 ME |
| Regras de mapa planejadas | 51 |
| Batalhas planejadas | 8 |
| Eventos ME planejados | 7 |
| Cenas planejadas | 5 |
| Mapas de Kanto verificados pelo compilador | 142, incluindo 45 prévias |
| Música de mapa aplicada | **0** (Fase 2) |
| Música de batalha aplicada | **0** (Fase 3) |
| Eventos ME aplicados | **0** (Fase 4) |
| Playback interativo no Game.exe | **Não comprovado (BLOCKED_ENV)** |
| Barra de aceite integral | **Não alterada** |

Os IDs originais (como Pallet Town = 5 em FRLG) **não são** os MapIDs finais: o compilador lê os IDs reais gerados a cada preparação/importação. O ID 705 usado no teste é somente um *fixture* sintético, não uma afirmação sobre o mapa do usuário.

## Validação reproduzível

Executar na raiz do repositório:

~~~powershell
python scripts/music/install_kanto_music.py --audit
python -m unittest discover -s tests -p "test_kanto_music*.py" -v
ruby -c scripts/music/BlueMusic.rb
ruby tests/kanto_music_runtime.rb
# Depois de preparar a copia de Kanto:
python scripts/music/compile_kanto_music.py --game .blue-work/kanto-pilot
python scripts/music/compile_kanto_music.py --game .blue-work/kanto-pilot --apply
~~~

A [CI de regressão](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/regression.yml) verifica Python, Ruby e 64 hashes reais. A [CI nativa de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml) verifica a compilação e transferência dos 142 MapIDs. Nenhum desses testes, isoladamente, comprova o áudio sendo reproduzido pelo jogador num Game.exe interativo.

## Próxima fase

**Fase 2 — BGM de cidades, rotas, interiores e transporte.** Ativar somente associações que tiverem mapas funcionais, faixas presentes e confirmação de transições. Fallback no áudio nativo para localidades sem faixa aprovada; preservar Decades e prévias.

> Mensagem pronta: Aplique a Fase 2 do plano musical de Kanto no GitHub, usando o adaptador regional e os MapIDs compilados da Fase 1. Teste e publique.
