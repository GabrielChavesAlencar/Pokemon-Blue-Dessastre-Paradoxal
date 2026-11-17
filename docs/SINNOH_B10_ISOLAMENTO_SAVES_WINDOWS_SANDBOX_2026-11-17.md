# Sinnoh — Barra B / B10: isolamento de saves com Windows Sandbox

**17/11/2026.** Engenharia B10 implementada e coberta por testes sintéticos. **Nenhuma sessão Windows Sandbox foi iniciada no computador do usuário**, nenhum Game.exe foi executado e o salvamento real da versão Decades ainda **não foi rastreado**. R07/R08/R09 seguem pendentes, **Barra B/C/D 0/13**, Sinnoh e Unova continuam planned.

## Por que não basta copiar o jogo

A B09 exclui os arquivos de save da cópia, mas o Game.exe pode gravar saves em `%APPDATA%`, `%LOCALAPPDATA%`, Documentos ou outras pastas globais, independentemente de sua localização. O código do runtime responsável pelo caminho de saves **ainda não foi inspecionado**. Logo, não usar simplesmente variáveis APPDATA redirecionadas ou iniciar diretamente o Game.exe da pasta `.blue-work` no Windows principal.

## Técnica escolhida: VM descartável do próprio Windows

Com base na [documentação oficial Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/), a B10 utiliza isolamento de VM com kernel separado, não apenas um diretório diferente. O recurso está disponível nas edições Windows **Pro, Enterprise e Education** quando habilitado e com virtualização disponível. **Windows Home não é suportado**. O programa faz preflight do EditionID e do recurso `Containers-DisposableClientVM`; se indisponível, aborta sem usar uma solução mais fraca. Não instala nem habilita Windows Sandbox por conta própria.

Segundo a [documentação da Microsoft para arquivos WSB](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file), o `.wsb` criado contém:

- `Networking=Disable`, `ClipboardRedirection=Disable`, `PrinterRedirection=Disable`, `AudioInput=Disable`, `VideoInput=Disable` e `vGPU=Disable` (renderização de software pode ficar mais lenta);
- `ProtectedClient=Enable` e **nenhum `LogonCommand`**: abrir a sandbox não inicia o jogo;
- **somente 2 mapeamentos**, sempre `ReadOnly=true`: B09 local → `C:\SinnohB10Source`; scripts de preparação B10 → `C:\SinnohB10Tools`;
- Nenhuma pasta do Decades principal, do usuário, dos saves, AppData, Documents ou Downloads é mapeada.

O mapeamento é somente para leitura no host. **Dentro da sandbox**, a pessoa executa `C:\SinnohB10Tools\B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd` para copiar o clone para `C:\SinnohB10Game` gravável na VM. O script valida que existam `Game.exe`, os mapas `442` e `495`, não sobrescreve pastas existentes e **não executa `Game.exe`**. Para experimentar o jogo, somente após conferir visualmente a janela Windows Sandbox, a pessoa pode abrir **manualmente** `C:\SinnohB10Game\Game.exe`. Ao encerrar a sandbox, seus dados descartáveis são removidos (exceto mudanças em pastas explicitamente compartilhadas; todas as pastas B10 são somente leitura).

**Cuidado:** a estrutura acima reduz o risco de acesso do jogo aos saves do host por virtualização, mas a própria criação do WSB **não comprova que o Game.exe iniciou, renderizou mapas ou salvou corretamente dentro da VM**. A compatibilidade real ainda precisa ser testada pelo usuário. O sistema não altera nenhuma configuração dos saves da instalação original.

## Auditorias B10 antes de gerar WSB

O [preparador B10](../scripts/regions/prepare_sinnoh_b10_save_isolation.py) exige, quando usado em modo real:

1. A cópia B09 dentro de `.blue-work/sinnoh-b09-native-qa/native-<sha>`, com manifesto original inalterado e sem declaração falsa de testes.
2. Recalcular o SHA do plano B09 e de **todos os arquivos** do clone, rejeitando arquivos extras, links, junctions, alterações de tamanho, saves ou perfis.
3. Confirmar os 648 MapIDs da B01, os 54 de Sinnoh `442–495` (total **702**) e a integridade de MapInfos/Tilesets e seus hashes.
4. Revalidar o **ZIP B01 real**, o estágio B07 e o overlay B08. Cada arquivo do clone sobreposto precisa ser idêntico ao overlay B08, incluindo tilesets e PNGs. Caso falte qualquer evidência B07/B08/B09, a B10 bloqueia.
5. Conferir Windows Sandbox suportado/habilitado **antes** de gravar o `.wsb`. Exigir mapa e arquivos corretos; nunca instalar nada no Decades principal.

Após aprovação somente desses checks de engenharia, o código cria a sessão privada `.blue-work/sinnoh-b10-sandbox/session-<SHA>`, com `B10_ISOLAMENTO.wsb`, `tools/B10_PREPARAR_NO_WINDOWS_SANDBOX.cmd` e `B10_SESSAO.json` (prova de preparação, não de gameplay). O código não executa o Windows Sandbox ou o Game.exe.

## Usar no Windows com duplo clique

Na cópia local do repositório atualizada, com os estágios B07, B08 e B09 já criados, dê dois cliques em [SINNOH_B10_ISOLAR_SAVES_SANDBOX.bat](../SINNOH_B10_ISOLAR_SAVES_SANDBOX.bat). É necessário Python 3, assim como nos estágios anteriores; não exige abrir PowerShell manualmente.

O BAT tenta encontrar `SINNOH_B01_INVENTARIO_DECADES.zip` em Downloads. Ele executa a verificação, produz `SINNOH_B10_RELATORIO_*.json` para enviar à conversa e **pergunta se deseja abrir o Windows Sandbox**. Mesmo aceitando, não inicia o Game.exe. Na sandbox, execute o CMD de preparação do guest. Só então faça um teste manual do jogo, exclusivamente **dentro** da VM, se desejar.

Se Windows Sandbox estiver desabilitado, use o painel **Ativar ou desativar recursos do Windows** para verificar se o recurso existe e ativá-lo, conforme [instruções da Microsoft](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install). O projeto **não** faz a ativação automática e **não tem fallback inseguro para Windows Home**. Uma VM separada pode ser projetada no futuro caso necessário.

## Testes e critérios de conclusão

O código inclui [27 testes offline](../tests/test_sinnoh_b10_save_isolation.py) com fixtures sintéticas: confirmação exata de 702 IDs, rejeição de saves/junctions/manifestos falsos, Windows Home/feature desativado, WSB somente leitura e sem rede/clipboard/execução automática, impedimento de sobreposição e invariância do jogo principal.

**Não foram executados testes reais Windows Sandbox neste ambiente.** Para declarar que o isolamento funciona na máquina do usuário, são necessários o relatório gerado pelo BAT, confirmação de que a janela da sandbox iniciou, que a cópia do jogo ficou dentro da VM e que o Game.exe testado na VM não alterou dados do host. O último ponto requer um procedimento de comparação read-only de hashes dos saves externos antes/depois — **a B10 ainda não afirma esse resultado.**

**R07:** reservas futuras de Kanto/Johto/Hoenn não homologadas. **R08:** direitos sobre tilesets/ativos ainda pendentes. **R09:** Game.exe/JoiPlay e jogabilidade de Sinnoh não homologados. **B/C/D permanecem 0/13.**

## Próxima etapa — B11

Coletar o relatório B10, auditar os locais reais de save do Decades (sem copiar seus saves), verificar hashes antes/depois do teste em Windows Sandbox, conferir o renderizador com PNGs de 50 mil/70 mil pixels e estabelecer critérios de QA nativa, sem instalar os mapas na versão principal.

[Contrato B10](../data/regions/sinnoh-b10-save-isolation.json) · [Preparador B10](../scripts/regions/prepare_sinnoh_b10_save_isolation.py) · [20 testes](../tests/test_sinnoh_b10_save_isolation.py).

## Endurecimento G04 — verificação de política e proteção adicional do CMD

**Escopo estritamente estático, somente GitHub (17/11/2026).** [Entrega G04](SINNOH_G04_SEGURANCA_WINDOWS_SANDBOX.md) reforçou a preparação B10 sem alterar o contrato de 702 MapIDs, sem executar `Game.exe` e sem emitir aprovação nativa:

- Antes da criação da sessão, exige clone em `.blue-work/sinnoh-b09-native-qa/native-<SHA>`, SHA completo vinculado ao recibo B09, 648 MapIDs da base + 54 Sinnoh, e fonte do stage com hash válido.
- A auditoria do recibo B09 só aceita as duas sobreposições naturais do overlay de `MapInfos.rxdata` e `Tilesets.rxdata`; nomes com grafias ambíguas, caracteres proibidos do Windows, reparse points e duplicatas entre origens diferentes são bloqueados.
- `check_wsb_policy` reabre o XML gerado e verifica **exatamente** dois mapeamentos, ambos `ReadOnly=true`, destinos de convidado esperados, nenhuma tag `LogonCommand`, rede, clipboard e dispositivos desabilitados, `ProtectedClient=Enable`.
- O CMD do convidado verifica o usuário/perfil padrão `WDAGUtilityAccount` e a existência do mapeamento esperado antes de criar o destino; recusa a execução fora desse contexto aparente. A cópia usa `robocopy /XJ /SL` para não seguir junctions ou destinos de links simbólicos encontrados durante a transferência.
- **A checagem do nome do usuário é uma barreira contra erro operacional, NÃO uma prova de virtualização ou fronteira de segurança.** Não substitui o Windows Sandbox real e não impede que alguém execute um script deliberadamente adulterado.
- Sete testes negativos adicionais foram incluídos: campos WSB alterados, host share inesperado, caminhos Windows irregulares, guard do guest, pasta de clone indevida, prova B09 adulterada, colisão de arquivos e symlink no clone.

A configuração `.wsb` continua precisando ser gerada e aberta na máquina do usuário em **Windows Pro/Enterprise/Education com o recurso Sandbox habilitado**. Não abrir o clone `Game.exe` no host; B11 ainda precisa comprovar os diretórios de saves observados antes/depois. Os resultados da CI G04 são **somente metadados/fixtures** e não aprovam B/C/D.
