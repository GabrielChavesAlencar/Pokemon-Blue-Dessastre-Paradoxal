# Sinnoh G11 — Integração CI B07–B11

**17/11/2026 — entrega exclusivamente pelo GitHub.** A G11 integra os cinco contratos públicos B07, B08, B09, B10 e B11 em uma auditoria encadeada, com testes de ponta a ponta **somente sintéticos**. Não lê a instalação do PC, arquivos do doador, saves reais ou executa Game.exe/Windows Sandbox/JoiPlay.

## Cadeia de integridade

| Etapa | Contrato preservado | O que a CI pode testar sem dados particulares |
| --- | --- | --- |
| B07 | 54 terrenos 442–495 em stage privado, 22 placeholders excluídos e sem eventos de origem | Conversão de mapas, geometria e manifestos **sintéticos** |
| B08 | Prova do stage B07, hashes e referências gráficas, overlay não executável | Três PNGs sintéticos e alterações em arquivos/manifestos; os **14 PNGs reais** não são inspecionados |
| B09 | Clone QA separado, sem saves; 648 mapas da base mais 54 candidatos | Clone com Game.exe inerte fictício, hashes e detecção de alterações, sem abrir o programa |
| B10 | Duas pastas WSB somente leitura; sem rede, clipboard ou autoexecução | Verificação XML, sessão simulada e bloqueio de política insegura, **sem VM real** |
| B11 | Snapshot privado de diretórios de saves explicitamente monitorados | Hash/compare de save sintético, inclusive modificação de mesmo tamanho; nunca prova cobertura global |

O auditor G11 chama os validadores oficiais existentes de B07–B11. Além de reconciliar 54 IDs 442–495, 648 mapas-base, 702 esperados no clone e hashes dos contratos, ele impede alteração de direitos, reservas R07 e execução R09 declaradas falsas, além de verificações nativas marcadas como aprovadas sem prova. A G11 **não muda o nível de segurança ou a permissão de lançamento do clone B09**.

## Arquivos de entrega

- [Auditor público G11](../scripts/regions/audit_sinnoh_g11_ci_chain.py): cruza os cinco contratos, valida as referências B00–B06, verifica a estrutura WSB sem executar a VM e descobre os testes versionados em cada etapa. Emite somente JSON público sem paths, saves ou dados proprietários.
- [18 testes integrados e negativos](../tests/test_sinnoh_g11_ci_chain.py): além das falhas de contratos, constroem a cadeia sintética B07 → B08 → B09 → B10 → B11 e exigem isolamento dos saves, hashes e WSB seguros.
- [Workflow G11](../.github/workflows/sinnoh-g11-b07-b11-integration.yml): três jobs, um de pré-voos/metadados, outro das cinco suítes de testes já existentes e um da regressão integrada. Arquiva apenas o relatório público em JSON.

## Proteções comprovadas nos fixtures

1. O clone sintético contém Game.exe **fictício** mas exclui os saves do jogo-base fictício. Nenhum processo é iniciado.
2. A sessão B10 sintética precisa manter dois mapeamentos somente leitura, rede/clipboard desligados e ausência de autostart.
3. A auditoria B11 informa quando um save sintético mudou, inclusive se o tamanho permanecer igual.
4. O relatório B11 **não** publica caminhos, nomes, bytes ou chave HMAC. Um snapshot inalterado ainda não prova isolamento global.
5. Um arquivo B09 modificado é rejeitado antes de se construir a sessão B10; WSB adulterado é rejeitado antes do snapshot B11.

### Como validar no checkout do repositório

~~~bash
python scripts/regions/audit_sinnoh_g11_ci_chain.py
python -m unittest discover -s tests -p 'test_sinnoh_g11_ci_chain.py' -v
~~~

**Status do auditor:** B07_B11_PUBLIC_CONTRACT_CHAIN_RECONCILED_SYNTHETIC_ONLY.

## Limites e próximos passos

A CI não examina os 14 PNGs reais, MapIDs/tilesets físicos, licenças de ativos, diretórios efetivos dos saves da engine ou renderização de tilesets gigantes. Windows Sandbox, Game.exe e JoiPlay exigem testes controlados fora da CI. **B/C/D permanecem em 0/13; R07/R08/R09 não foram aprovados.**

**Próxima entrega G12:** consolidar a esteira e seus comprovantes públicos, auditar gates finais e preparar um roteiro seguro para QA nativa — sem abrir o Game.exe nem afirmar jogabilidade por antecipação.
