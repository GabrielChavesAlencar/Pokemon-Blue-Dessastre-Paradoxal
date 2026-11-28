# GD04 — validação e entrega futura de Galar

Documento de aceitação, não publicação ou prova de execução. A CI
documental não equivale a teste no Game.exe ou no Android.

| Prova | Cenário futuro | Falha bloqueadora |
|---|---|---|
| T01 | Conferir [fontes](GALAR_GD01_FONTES_E_DIREITOS.md), origem, SHA-256 e escopo autorizado; comparar croqui com o [atlas](GALAR_GD05_ATLAS_VISUAL_E_TILES_KANTO.md). | Dependência de doador não aprovado, mapa global substituído ou identidade geográfica perdida. |
| T02 | Caminhar pelo recorte nos dois sentidos, atravessar portões, trem, mina e estádio; repetir após reabrir. | Softlock, mapa de teste no lugar do destino, retorno quebrado ou só teleporte de QA. |
| T03 | Nova partida e visita; repetir inicial e Milo sob falha/recarga, verificar Centro e saves sintéticos. | Itens, equipe, flags ou premiação duplicados; jogador preso sem destino. |
| T04 | Táxi de Motostoke, Rotom Bike da R05 e Water Mode na R09. Testar antes/depois e operação inter-regional. | Atalho antes do desbloqueio, HM fictício, chegada a mapa ainda não instalado ou bike de outra região. |
| T05 | Duplas Sword/Shield em vagas compartilhadas, progressão de Opal/Bede, oito insígnias e regras do Blue sobre especiais. | Nona insígnia ou esmeralda duplicada, Dynamax reativado ou exceção não autorizada. |
| T06 | Champion Cup, Darkest Day, final contra Leon, vitória, recarga, pós-jogo e DLC separados. | Elite Four fictícia, DLC necessária à campanha ou encerramento falso. |
| T07 | Windows e Android mesma revisão funcional; instalar e atualizar de uma versão real, repetir e recuperar falha sem tocar outras regiões. | Falta paridade, saves/dados externos alterados, SHA/receita não validados ou redução do gate do atualizador. |
| T08 | QA física futura com revisão publicada, caminhos do recorte e regressões. | Sem ambiente marcar `BLOCKED_ENV`; adiamento autorizado mantém `DELIVERED_WITH_QA_PENDING`, nunca afirmar teste físico feito. |

Tudo acima está `NOT_RUN`. Só começar o lote seguinte depois de entregar
as duas plataformas; se houver falha, corrigir o lote e validar de novo.
Avisar bloqueios novos e seguir o que não depende deles.

## Evidência de publicação futura

- Conferir PR e SHA exatos, escopo, saves protegidos e regressões no motor
  antes do merge. Verificar pacotes realmente publicados, não apenas
  um job verde, e provar digest do lançador `Blue-Story.exe`.
- Android usa o atualizador existente: receita versionada para o mesmo
  produto e fonte original SHA-256, com staging, lock, rollback e
  repetição. Não exigir novo APK, não trocar de canal, não redistribuir
  arquivos de doador, dumps, mapas crus, save, runtime ou ZIP geral.
- Falha de qualquer plataforma é `BLOCKED_RELEASE`. Guardar SHA de
  produto, receita, runs, jobs, links, versão anterior validada e prova
  pendente, separando simulação, CI nativa e teste em aparelho.
- Referências: [entrega Windows/Android de Kanto](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md),
  [instalação pela fonte](ANDROID_INSTALACAO_PELAS_FONTES.md) e
  [atualização incremental](ANDROID_ATUALIZACOES_INCREMENTAIS.md).
