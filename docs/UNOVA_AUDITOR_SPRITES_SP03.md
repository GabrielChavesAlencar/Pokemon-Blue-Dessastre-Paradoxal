# Unova — Auditor de sprites SP03 (somente leitura)

**Data:** 17/11/2026 | **Projeto:** Pokémon Blue: Dessastre Paradoxal | **Estado:** ferramenta de inventário, não conteúdo instalado.

## Objetivo

O script [audit_unova_sprite_pack.py](../scripts/regions/audit_unova_sprite_pack.py) analisa packs de sprites PNG/GIF/APNG dentro de ZIP **sem exigir MapInfos.rxdata ou Tilesets.rxdata**. É independente do auditor E04 de Pokémon World V18, que espera um jogo completo. Nenhum recurso de terceiros foi baixado ou instalado.

### Pacotes candidatos

- [Gen 5 Overworld Pack — Radical Raptr](https://eeveeexpo.com/resources/25/): primeiro candidato para NPCs.
- [ULTIMATE Gen 5 Overworlds — PurpleZaffre](https://eeveeexpo.com/resources/619/): fonte alternativa; autor restringe redistribuição.
- [Gen 5 Characters in Gen 4 OW Style — DiegoWT](https://eeveeexpo.com/resources/370/): outra estética, verificar licença.
- [Ultimate BW Pack 7](https://www.pokecommunity.com/threads/ultimate-bw-pack-for-pok%C3%A9mon-essentials.270197/): pacote legado, nunca substituir PBS/scripts/Graphics atuais por ele.

**Créditos não são automaticamente licença.** Confirmar autoria, termos e autorização por arquivo antes de usar sprites na distribuição do jogo.

## Uso no Windows (sem PowerShell)

1. Obtenha o ZIP original do pack da página do autor.
2. Clique duas vezes em **[UNOVA_AUDITAR_SPRITES.bat](../UNOVA_AUDITAR_SPRITES.bat)**, na pasta principal do projeto.
3. Selecione o ZIP na janela do Windows.
4. Opcionalmente, escolha a pasta **Graphics/Characters da instalação do Decades**. A pasta será lida, mas não modificada. Sem ela, o relatório identifica a comparação como não fornecida.
5. Confira o resultado em **.blue-work/unova/audit/sprite-packs/sprites-SHA16.json**. É uma área privada ignorada pelo Git.

Também pode arrastar um ZIP sobre o BAT ou executar o script com o argumento --zip e --write; para comparação, passe --reference-dir apontando explicitamente para Graphics/Characters. Não requer Pillow nem execução de Python/Ruby doador.

**Pacotes em RAR/7z não são suportados diretamente.** Não basta renomear a extensão: obtenha ZIP autorizado ou prepare uma cópia ZIP exclusivamente local, sem publicar assets de terceiros.

## Campos que o relatório produz

| Elemento | O que identifica | Limitação |
|---|---|---|
| Formato e tamanho | PNG, GIF e APNG (inclusive arquivos .apng) e largura/altura em pixels | Apenas metadados/estrutura, não renderiza arte |
| Animação | Quadros declarados de GIF/APNG, atrasos GIF | Não confirma reprodução na engine |
| Direções/grades | Possíveis folhas 4x4 RMXP ou 3x4, tamanhos de células | Grades são hipóteses, não prova de poses, pivôs ou ordem |
| Nomes | Cheren, Bianca, Juniper, N, Ghetsis, Team Plasma, líderes, Elite etc., por nome do arquivo | Falta de nome não prova ausência do personagem |
| Duplicatas | SHA-256 igual de imagens com caminhos diferentes | Não identifica desenhos parecidos com bytes diferentes |
| Conflitos | Basename repetido dentro do ZIP e em referência Decades | Não substitui nenhum arquivo |
| Escala | Dimensões divergentes, proporções estimadas por célula | Alertas, não medida de escala no Game.exe |
| Referência | SCANNED_READ_ONLY ou NOT_PROVIDED | Sem pasta Decades não é possível comparar instalações |
| Permissões/instalação | rights_verified, can_install, game_exe_tested e android_tested = false | Exige comprovação externa e QA real |

O auditor não infere que uma folha é personagem jogável só por ter largura divisível por 3 ou 4. Para GIF/APNG identifica estruturas, não interpreta pixels, composição de frames ou compatibilidade nativa. A comparação de altura por célula é indicativa, não uma medição do personagem em tela.

## Segurança

- Rejeita path traversal, nomes ZIP duplicados sem distinguir caixa, symlinks, entradas criptografadas, excesso de membros e razões suspeitas de descompactação.
- Impõe limite de bytes de imagem e dimensão. Inspeciona os CRCs dos chunks de PNG, frames GIF e metadados APNG sem executar conteúdo externo.
- Se houver imagens inválidas, registra o alerta e não declara auditoria limpa.
- Lê a referência Decades sem modificar arquivos; symlinks na pasta de referência são bloqueados.
- Relatórios apenas na área privada .blue-work/unova/audit/sprite-packs/, em arquivos nomeados por hash e não sobrescritos quando diferentes.
- Nunca altera Game.exe, game/Data, arquivos PBS, NPCs, scripts, Blue-Story, saves, registro de regiões ou outras regiões.

## Próxima fase sugerida

**SP04 — Catálogo auditável dos NPCs:** relacionar os resultados reais do pack aos personagens do roteiro Black/White e registrar para cada um: fonte, autor, licença, uso permitido, dimensões, quadro, pivô, sprite escolhido, variações e estado. A compatibilidade no Game.exe/Android exige revisão visual e teste manual.

**SP05 — Um NPC piloto** somente após direitos claros; criar overlay separado e namespaced sem sobrescrever Graphics/Characters global. Testar 4 direções, animação, posição e escala com Decades, depois save/reload. Não escolher MapID sem MapInfos real.

**Barras não aumentam apenas pelo auditor:** E = 4/8, A/B/C/D = 0/8, jogável Unova = 0/32. O pack real e seus direitos ainda não foram auditados.

**Ajustes após CI:** o auditor aceita extensões .apng, bloqueia PNG sem IDAT e trata uma pasta de referência Decades explicitamente indicada mas inexistente como erro, em vez de simular comparação. A inspeção continua somente por metadados.
