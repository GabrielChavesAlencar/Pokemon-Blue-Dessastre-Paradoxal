# Sinnoh — G05: auditoria privada de saves da B11

**17/11/2026 — entrega GitHub-only.** A G05 endurece o comparador **antes/depois** que já existia na B11. Não acessa o computador do usuário, não executa Windows Sandbox ou `Game.exe`, não carrega saves reais na CI e **não** altera os estágios B07–B10.

## Resultado: o que a B11 faz

1. A partir de uma sessão B10 com WSB original conferido, a B11 calcula **hash SHA-256 e tamanho** de cada arquivo somente nos diretórios **explicitamente selecionados ou nos padrões existentes**. As identidades dos nomes ficam em HMAC local com chave aleatória por sessão.
2. Salva o **baseline privado** na pasta local `.blue-work/sinnoh-b11-save-audit/watch-<id>/private-baseline.json`, com *caminhos, hashes, chave HMAC* e escopos. **Nunca anexar esse arquivo ao ChatGPT/GitHub; não é seguro para compartilhar.**
3. Depois da sessão, compara os mesmos diretórios e informa os **totais de arquivos criados, removidos ou alterados** e se os escopos selecionados ficaram inalterados.
4. O resumo compartilhável **não inclui caminhos de usuário, nomes de arquivos, hashes de saves, bytes de saves ou chave privada**. Uma observação de que o jogo iniciou dentro da VM é autodeclarada e não equivale à validação independente.

## Correções da G05

| Risco | Proteção aplicada | Resultado |
| --- | --- | --- |
| Falha de acesso durante `os.walk` | `onerror` bloqueia a varredura e evita um falso resultado de arquivos inalterados | Erros de leitura **não** são tratados como ausência de arquivos |
| Diretórios padrão inexistentes | O modo padrão informa apenas `default_scopes_not_monitored` (número), mantendo `coverage_is_partial=true` | Não oculta lacunas conhecidas de cobertura |
| Diretório fora do escopo | O modo explícito informa `scope_selection_mode=explicit`, sem inferir contagem de outros diretórios | `watch_unchanged=true` **nunca** afirma que todos os possíveis saves no host ficaram protegidos |
| Link ou junction em ancestral | Rejeita o diretório e qualquer ancestral com symlink/junction | Evita atravessar caminhos vinculados ou confundir escopos |
| Save alterado durante hash | Compara `size`, `mtime_ns`, `ctime_ns` e inode antes/depois de ler o arquivo | Bloqueia snapshots inconsistentes, inclusive alterações durante a leitura |
| Baseline privado adulterado ou malformado | Validação de esquema estrito, SHA, HMAC, total de arquivos, bytes, identidade e escopo; digest HMAC para coerência local | Detecta corrupção e adulteração simples. **Não autentica contra quem possui o arquivo inteiro e sua chave** |
| Caminho pessoal em erro inesperado | CLI usa mensagem de bloqueio sanitizada para exceções de sistema | Evita compartilhar nomes de saves pela saída de erro |
| Execução acidental do diagnóstico no host | CMD B11 exige o nome/perfil típico `WDAGUtilityAccount` e arquivos mapeados; não inicia `Game.exe` | Barreira operacional adicional; **não comprova** que o processo está em uma VM |

**Nota sobre compatibilidade:** o formato interno do baseline G05 foi atualizado para registrar `scope_selection_mode`, `default_scopes_not_monitored` e digest HMAC. Um baseline criado pelo código anterior da B11 deve ser considerado legado e **não deve ser editado manualmente nem reaproveitado**. Faça novo snapshot *antes* de uma sessão, sempre após preparar a B10 adequada; não inicie o jogo no Windows principal para contornar bloqueios.

## Código, testes e CI

- [Auditor B11](../scripts/regions/audit_sinnoh_b11_host_saves.py): verificação de integridade, estrutura do baseline, detecção de mudanças e resumo sanitizado.
- [29 testes B11](../tests/test_sinnoh_b11_host_saves.py): 19 pré-existentes e 10 novos cenários de cobertura, corrupção de baseline, permissões, symlinks, arquivos alterados durante hash, salvamento com tamanho idêntico e mensagens de erro.
- [GitHub Actions G05](../.github/workflows/sinnoh-g05-b11-saves.yml): executa fixtures sintéticas em Ubuntu, verifica contrato congelado e publica **apenas um marcador JSON de teste offline**, sem arquivo de save real ou baseline privado.
- A regressão **Sinnoh S30 e CH19** também deve passar antes da integração do PR.

No Windows, o fluxo continuaria B10 → **snapshot B11 ANTES** → abrir a VM isolada, fazer o teste manual → **snapshot B11 DEPOIS**. O BAT B11 preexistente usa essa ordem; a execução real depende do ambiente do usuário e da versão sincronizada dos scripts do GitHub.

## Restrições de aprovação

Mesmo com `watch_unchanged=true`, o relatório continua com:

- `coverage_is_partial=true`
- `guest_vm_execution_independently_verified=false`
- `complete_host_save_coverage_verified=false`
- `true_runtime_save_path_in_source_verified=false`
- `host_saves_globally_isolated_proven=false`
- `gameplay_approved=false`

As regras de saves reais da engine Decades ainda não foram integralmente auditadas. B10/B11 não substituem R07, R08, R09 ou o aceite dos 44 casos nativos. **Barras B/C/D permanecem 0/13**, e nenhum clone B09 deve ser aberto no Windows principal.

**Próxima entrega: G06 — auditoria estática de PNGs e tilesets de Sinnoh.**
