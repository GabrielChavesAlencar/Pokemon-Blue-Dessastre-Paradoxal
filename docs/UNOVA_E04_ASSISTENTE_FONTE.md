# Unova — E04: assistente seguro para adquirir a fonte original

**Projeto:** Pokémon Blue: Dessastre Paradoxal | **Data:** 17/11/2026 | **Estado:** ferramenta pronta, **ZIP original ainda não foi obtido nem auditado nesta execução**.

## Objetivo

Simplificar a preparação do Pokémon World V18 em uma área privada da instalação de trabalho. O assistente **não** transfere os arquivos ao jogo, não executa os scripts do fornecedor, não instala plugins, não altera Game.exe, Blue-Story, MapInfos, PBS, o site, Kanto/Johto/Hoenn/Sinnoh ou saves.

**Fonte primária:** https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/  
**ZIP anunciado:** https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file  
**Créditos anunciados:** https://www.mediafire.com/file/gdtsjg5lbnstzo1/Credits.txt/file

O autor afirma que o projeto RPG Maker XP/Essentials v18 cobre apenas **parte** de Unova. Ter um arquivo com esse nome não comprova origem; a ferramenta registra o SHA-256 local, mas **não possui um hash de referência publicado pelo autor** com que conferir autenticidade.

## Procedimento Windows — dois cliques

1. Atualize o repositório para obter **UNOVA_E04_ESCOLHER_FONTE.bat**.
2. Dê dois cliques nesse BAT. Ele abre a **publicação do autor** no navegador para você obter o ZIP e, se possível, Credits.txt.
3. Selecione o ZIP baixado na janela que aparece. Também é possível arrastar um ZIP sobre o BAT, com Credits.txt como segundo argumento opcional.
4. A ferramenta confere a estrutura do ZIP sem extrair, valida limites de tamanho, nomes e MapNNN, calcula o SHA-256, e copia a fonte sem sobrescrever arquivos diferentes.
5. O assistente chama **UNOVA_VALIDAR_DOCUMENTACAO.bat**, que executa os auditores U02, RXDATA, E05 e E06 no conteúdo local.
6. Analise os relatórios privados em **.blue-work/unova/audit/**, incluindo e04-intake.json, u02-source.json, u02-rxdata-detail.json, e05-crosswalk.json e e06-rights-inventory.json.

**Atenção:** requer Python 3.11 compatível com o projeto e o pacote Tkinter no Windows para seleção gráfica. O modo por arrastar e soltar não requer Tkinter. Nada depende de PowerShell.

## Invariantes e segurança

- Entrada externa somente por escolha explícita; não há downloader automático opaco, execução do Game.exe de terceiros ou descompactação.
- ZIP com caminhos inseguros, duplicados, links simbólicos, mais de um projeto incompatível ou estruturas inválidas é rejeitado.
- Só grava a fonte e comprovantes em **.blue-work/unova/**, ignorada pelo Git. Os dados do jogo permanecem intactos.
- Se um ZIP já estiver no destino com conteúdo diferente, o assistente **não sobrescreve**: bloqueia e preserva o anterior.
- Créditos podem estar ausentes, mas E06 continuará pendente. Mesmo com créditos presentes, toda licença e autorização de redistribuição precisa de avaliação humana e documental.
- Um relatório E04 registra explicitamente **source_origin_verified_by_author=false**, **published_author_hash_matched=false**, **rights_per_asset_verified=false**, **can_install=false**, **game_exe_tested=false** e **android_tested=false**.
- O número de MapNNN do fornecedor representa **todos os mapas do fangame**, jamais a contagem confirmada de Unova.
- Os testes de ZIP sintético validam o mecanismo de bloqueio, mas não certificam o conteúdo do pacote original.

## Escopo de fechamento E04

O marco E04 depende de **dois insumos reais**: a fonte ZIP íntegra associada ao criador e os créditos/proveniência verificados. Sem acesso ao arquivo nesta execução, a ferramenta preparatória não permite marcar E04 concluído.

## Barras de progresso

| Barra | Estado após esta entrega |
|---|---|
| A — Mapas/MapIDs | 0/8 |
| B — História/NPCs | 0/8 |
| C — Treinadores/selvagens/música | 0/8 |
| D — Game.exe/Blue-Story/JoiPlay | 0/8 |
| **E — Documentação/ferramentas** | **4/8 (50%)**, E04 preparatório apenas |
| Fases U01–U32 efetivamente jogáveis | **0/32** |

**Próximo passo:** usar a fonte real para auditar RXDATA, cruzar as 74 áreas, verificar os direitos e só então planejar eventual importação isolada, sem sobrescrever regiões existentes.
