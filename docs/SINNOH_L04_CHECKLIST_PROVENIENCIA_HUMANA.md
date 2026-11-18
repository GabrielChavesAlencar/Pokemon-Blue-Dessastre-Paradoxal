# Sinnoh L04 — Checklist de proveniência e critérios de revisão humana

**18/11/2026 · issue #177 · implementação GitHub-only.** Esta fase consolida o handoff documental L03 em um protocolo versionado de **20 critérios de verificação humana independente**, sem criar aprovação automática, token, botão de executar, liberação de VM ou direito de instalação.

## Arquivos da entrega

- [Checklist versionado L04](../data/regions/sinnoh-l04-independent-review-checklist.json) — cinco grupos B09/B10/B11/R07/R08, quatro critérios por grupo, com `review_state=NOT_REVIEWED`, `independent_evidence_present=false`, `local_human_signoff=false`. Esses valores **não são preenchidos automaticamente pelo auditor**.
- [Auditor L04](../scripts/regions/audit_sinnoh_l04_human_review.py) — valida o contrato por uma cópia fixa independente das expectativas, reutiliza L03→L02→L00→G12, compara estados e contagens, e cria somente um resumo estático sem valores sensíveis de origem.
- [35 testes positivos/negativos](../tests/test_sinnoh_l04_human_review.py) — adulteração da matriz, injeção de comandos/paths, falsos direitos, alterações de progresso, falsas decisões humanas e vínculos documentais inconsistentes.
- [Workflow CI](../.github/workflows/sinnoh-l04-human-provenance.yml) — dois jobs: L04 (35 testes) e regressões L03/L02/L01/L00/G12 (154 testes), sem publicar artifacts privados.

## Critérios humanos independentes

| Grupo | Critérios | Evidência que o relatório público sozinho **não comprova** |
| --- | --- | --- |
| **B09** — origem e clone | B09_ORIGIN, B09_CLONE, B09_ASSETS, B09_RECEIPT | Titularidade da fonte e doador, integridade física da cópia, correspondência entre dry-run e instalação local |
| **B10** — isolamento | B10_LINK, B10_READONLY, B10_OFFLINE, B10_PLATFORM | Que o B10 pertence à mesma cópia B09; que o WSB e o sistema Windows realmente respeitam a política somente leitura, rede/clipboard desabilitados e ausência de autostart |
| **B11** — saves | B11_SESSION, B11_SCOPE, B11_DIFFERENCE, B11_LIMIT | Que o B11 pertence à mesma sessão B10; que todos os caminhos reais de save da engine foram cobertos; que `watch_unchanged` significaria isolamento global (não significa) |
| **R07** — MapIDs | R07_NATIVE, R07_REGIONS, R07_CONFLICT, R07_TOPOLOGY | Propriedade/reserva de MapIDs futuros e conferência de nove áreas simbólicas e dezesseis transferências reais em uma cópia QA |
| **R08** — direitos e integração | R08_LICENSE, R08_GRAPHICS, R08_EVENTS, R08_PBS | Licenças reais de cada ativo; gráficos/tilesets instalados; handlers, mapas e PBS realmente compilados |

**Nenhum critério é declarado comprovado** por esta entrega. A conferência de documentos reais e qualquer decisão futura precisam ocorrer num procedimento separado, por responsável humano e fora do GitHub. Os registros públicos não contêm datas físicas de execução nem identificadores privados da sessão B11. Um SHA autorreferenciado não é certificado de procedência.

## Estados e ações documentais

O protocolo L04 continua distinguindo os quatro estados existentes na L02/L03:

- `MISSING_REPORT`: solicitar um novo resumo sanitizado;
- `SELF_REPORTED_AWAITING_HUMAN_REVIEW`: agendar **análise documental**, não teste do jogo;
- `PREREQUISITE_MISSING_BLOCKED`: reconciliar dependências B09→B10→B11;
- `CONFLICTING_EVIDENCE_BLOCKED`: bloquear e revisar a divergência.

As únicas disposições previstas para atividade documental de um revisor são `REVIEW`, `REQUEST_NEW_SANITIZED_REPORT`, `BLOCK` e `SCHEDULE_DOCUMENTARY_ANALYSIS`. A L04 **não oferece a opção `APPROVE_NATIVE_QA`**, não emite token e não agenda a abertura do jogo ou VM.

### Protocolo descritivo para eventual futura autorização

Antes de considerar uma autorização separada, uma pessoa responsável precisará conferir **fora do repositório**, com provas legítimas e sem publicar dados privados:

1. **Proveniência B09:** fonte e ativos autorizados, clone físico, hashes/inventário cotejados com a origem real, sem considerar SHA autodeclarado prova final.
2. **Política B10:** política WSB e capacidades reais do host; montagens somente leitura, rede/clipboard desligados e nenhuma inicialização automática. O relatório do GitHub **não comprova execução da VM**.
3. **Cobertura B11:** vínculo privado entre sessão e B10, escopos reais de save da engine e análise antes/depois. Uma lista de arquivos inalterados não demonstra isolamento global.
4. **Reserva R07:** MapIDs presentes e planejados, direitos sobre cada reserva, ausência de conflitos entre regiões e vínculos reais Twinleaf, sem substituir a revisão física pelo mero total `702`.
5. **Direitos R08:** permissões individuais dos 14 PNGs e demais materiais e compilação real de PBS/eventos em ambiente que já tenha sido aprovado para QA.
6. **Decisão futura independente:** somente após essas verificações, elaborar *um procedimento diferente*, explicitamente autorizado e que não dependa da saída L04 para permitir operações de runtime. A L04 **não possui tal autorização**.

Nenhum desses itens foi executado ou verificado no computador nesta entrega.

## Operação documental voluntária

Somente para consultar os contratos **públicos** do repositório:

```sh
python scripts/regions/audit_sinnoh_l04_human_review.py
```

Um usuário que *já tenha criado e revisado voluntariamente* o arquivo sanitizado da L01 pode optar por analisar **apenas** esse arquivo, de caminho previamente determinado:

```sh
python scripts/regions/audit_sinnoh_l04_human_review.py --workspace-reports
```

O segundo modo lê exclusivamente `.blue-work/sinnoh-l00-input/public-reports.json`. Não faz varredura de máquina, não lê os saves, não extrai PNGs, não executa Game.exe/Windows Sandbox/JoiPlay nem transmite os recibos. Argumentos de caminho arbitrário são recusados sem aparecer na mensagem de erro. **Nenhum desses comandos foi executado no PC do usuário por esta conversa.**

## Estado inalterado e limites da entrega

- G01–G12: entregas técnicas e documentais versionadas, não jogabilidade nativa.
- L00/L01/L02/L03/L04: contratos e análise documental; nenhuma delas libera execução do jogo.
- Relatórios locais fornecidos ao projeto nesta entrega: **0/5**; checklist físico aprovado: **0/20**.
- Sinnoh permanece `planned`, R07/R08/R09 pendentes, B/C/D **0/13**, nativo Windows/Android **0/44** (43 Windows + 1 Android).
- Nenhum acesso ao PC, `Game.exe`, JoiPlay, Sandbox, ZIP do doador, saves, HMAC, dados de licença privados ou imagens reais.

**Próxima fase segura sugerida — L05:** auditoria apenas documental de consistência entre os 20 critérios e 44 testes nativos pendentes, gerando roteiro de revisão humana e bloqueios por etapa, sem abrir o jogo nem criar permissão executável.
