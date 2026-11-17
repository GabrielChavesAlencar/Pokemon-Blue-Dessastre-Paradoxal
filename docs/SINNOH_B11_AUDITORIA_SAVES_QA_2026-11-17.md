# Sinnoh — B11: auditoria de saves antes e depois da Windows Sandbox

**17/11/2026.** Código e testes sintéticos implementados. **Nenhum relatório B10 de execução real nem observação de Game.exe/Windows Sandbox foi enviado até esta etapa.** R07/R08/R09 pendentes; B/C/D 0/13; regiões Sinnoh e Unova planned.

## Objetivo

Verificar, sem extrair ou publicar saves, se as pastas **explicitamente monitoradas no Windows principal** tiveram arquivos adicionados, removidos ou modificados durante uma sessão de testes no Windows Sandbox da B10. Fornecer instruções para observar a renderização do Game.exe e o aparecimento de saves **somente dentro da VM**. O sistema não altera o caminho real dos saves do Decades e não inicia o jogo.

## Auditoria do Windows principal

O [script B11](../scripts/regions/audit_sinnoh_b11_host_saves.py) exige uma sessão B10 previamente gerada e confere seu WSB e arquivo preparador inalterados. Verifica também o clone de 702 MapIDs via B10/B09/B08/B07, ZIP B01 e compatibilidade com Windows Sandbox habilitada antes de registrar o snapshot.

Antes da sessão, ele captura **hashes SHA-256, contagens e tamanhos dos arquivos**, apenas nas pastas selecionadas. Por padrão procura as pastas com nome `PokemonBlueDessastreParadoxal` sob APPDATA, LOCALAPPDATA, Documents e Saved Games. Se o jogo salvar em outras pastas, configure explicitamente `--watch-dir`. Pastas ausentes não são monitoradas e se não houver nenhuma pasta válida a ferramenta **bloqueia**. Links e junctions são recusados. Os bytes dos saves nunca saem da máquina.

O histórico com caminhos reais, hashes e chave HMAC fica em `.blue-work/sinnoh-b11-save-audit/watch-<id>/private-baseline.json` e **NÃO deve ser enviado ao chat**. O relatório de compartilhamento contém apenas contagens, observações auto-informadas e estado `watch_unchanged`; ele não contém nomes, caminhos, hashes individuais nem saves.

Depois da sessão, o auditor compara os mesmos escopos com a chave de sessão, detectando arquivos novos, excluídos ou com conteúdo alterado. Mesmo que `watch_unchanged=true`, não declara que **todos os caminhos possíveis** de salvamento no host foram protegidos: o runtime do Decades ainda precisa de investigação específica.

## Dentro da Windows Sandbox

O arquivo `.wsb` gerado pelo B11 mapeia **exclusivamente** a cópia B09 e dois CMDs B10/B11 em modo **somente leitura**, com rede/clipboard/printer/input áudio/vídeo e vGPU desativados, sem comando de início automático. Após executar dentro da VM `C:\SinnohB10Tools\B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd`, o usuário pode abrir **manualmente e somente dentro da VM** `C:\SinnohB10Game\Game.exe` para um teste, observando:

- Se Game.exe abre corretamente e responde aos controles;
- Se o mapa candidato Twinleaf `442` e os demais terrenos de Sinnoh não aparecem corrompidos (os eventos, portas e warps do doador **foram removidos** e não há garantia de acesso normal aos mapas);
- Se os tilesets originais `OutsideWorld2.7` (256×50.000) e `SinnohCompleteTileset` (256×70.000) apresentam erros de renderização;
- Se o jogo cria um save **dentro da VM** e se os arquivos do host continuam iguais nos locais monitorados.

O diagnóstico `C:\SinnohB10Tools\B11_DIAGNOSTICAR_DENTRO_DA_SANDBOX.cmd` apenas confere arquivos esperados e conta candidatos a save em pastas **da VM**; não exporta arquivos. Ele **não faz teleporte para Twinleaf** e não comprova renderização ou jogabilidade automaticamente.

## Windows em um clique

Na cópia local do repositório (com B07→B10 já preparados), execute [SINNOH_B11_AUDITAR_SAVES_QA.bat](../SINNOH_B11_AUDITAR_SAVES_QA.bat). O BAT coleta o estado anterior, pergunta se quer abrir a VM e, depois do teste, solicita uma observação simples (N/F/R/S), coleta o estado posterior e gera `SINNOH_B11_RELATORIO_*.json` ao lado do BAT.

**Envie somente o relatório JSON de B11 ao ChatGPT.** Não envie o arquivo de baseline privado nem saves. Para diagnóstico parcial, os comandos Python `--before --latest --native-inventory ZIP_B01`, seguido de `--after ID --observation not_run`, também estão disponíveis.

Se seu Windows não suporta Sandbox (por exemplo, Windows Home), B11 bloqueia a coleta vinculada à B10 e não tenta executar a cópia privada diretamente. Essa restrição é intencional.

## Critérios de aprovação

**B11 implementa a auditoria, mas não prova que a VM ou Game.exe funcionaram.** O resultado Windows real ainda não foi enviado; tampouco foram descobertos todos os caminhos possíveis dos saves do runtime. Nenhum mapa de Sinnoh foi aprovado jogável. As permissões dos 14 gráficos e as reservas futuras R07/R08 ainda precisam ser verificadas. **Barra B 0/13, C 0/13, D 0/13.**

[Contrato B11](../data/regions/sinnoh-b11-host-save-audit.json) · [Auditor B11](../scripts/regions/audit_sinnoh_b11_host_saves.py) · [19 testes](../tests/test_sinnoh_b11_host_saves.py).
