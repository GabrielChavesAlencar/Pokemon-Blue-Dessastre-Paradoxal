# Kanto — Fase 08/16: Vermilion e Lt. Surge — auditoria inicial

**Data:** 12/11/2026. **Estado:** etapa iniciada, **não jogável nem concluída**. A fase 07 continua sendo a última expansão implementada (25 mapas). Não declarar a fase 08 implementada antes de importar e testar os mapas da fonte.

## Objetivo da expansão

Estender a campanha de Cerulean para as Rotas 5 e 6, passagens subterrâneas, Vermilion City, S.S. Anne e o Ginásio de Lt. Surge; adaptar os diálogos necessários, evento de embarque e ticket, Capitão/HM Cut, quebra-cabeça do ginásio, treinadores e Thunder Badge. Preservar a equipe, o sistema Blue, o estado das insígnias e o perfil isolado de saves.

## Trabalho publicado nesta etapa

- `scripts/regions/audit_vermilion.py` identifica candidatos **diretamente na versão FRLG pinada**, seus IDs, dimensões, eventos relevantes, warps, condicionais e chamadas de script, sem executar scripts da origem.
- `.github/workflows/kanto-pilot-check.yml` executa a auditoria no Windows após validar o hash da fonte e publica o inventário `kanto-phase-08-audit.json` como artefato **kanto-fase-08-auditoria**.
- Não foram importados mapas extras, dados de terceiros ou executáveis para o GitHub. Nenhum save da instalação principal foi alterado.

## Requisitos de implantação (ainda pendentes)

- [ ] Conferir no inventário os IDs **reais** de rotas, cidade, porto, cabines, navio, edifícios e ginásio; não inferir IDs só por sequência.
- [ ] Examinar eventos e transferências de ida e volta, incluindo acessos e bloqueios de história, e escolher pontos de entrada válidos.
- [ ] Expandir `data/regions/kanto-source.json` sem reordenar IDs dos 25 mapas anteriores.
- [ ] Adaptar treinadores/PBS/encounters e importar apenas eventos revisados, nunca scripts estrangeiros indiscriminadamente.
- [ ] Conceder Thunder Badge uma única vez após vitória efetiva sobre Lt. Surge, integrando a permissão local de Fly prevista no plano.
- [ ] Incluir atalhos experimentais seguros para acessar os mapas novos, sem dar badge ou alterar o save principal.
- [ ] Ampliar o verificador de topologia, progressão, limites de coordenadas e testes nativos no `Game.exe`.
- [ ] Publicar a expansão no portal com localizações, treinadores e equipes extraídas da fonte.
- [ ] Testar caminhada, batalha real, eventos do navio, portas, save/reload e retorno no Windows.

## Evidências e contadores

A coleta inicial deve ser conferida em [GitHub Actions — Piloto de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml). A execução da CI não é evidência de jogabilidade gráfica.

**Desenvolvimento implementado:** 7/16 (43,75%). A etapa 08 está **em andamento**, não faz parte desse total até existir implementação integrada.

**Etapas inteiramente aceitas:** 1/16 (6,25%). Faltam **15** para a aceitação completa; a revisão manual das fases anteriores continua pendente.

**Próxima ação técnica:** usar o inventário gerado pela CI para implementar a primeira integração real de Vermilion, mantendo o mesmo `Testar Kanto` da tela de título e uma cópia isolada.
