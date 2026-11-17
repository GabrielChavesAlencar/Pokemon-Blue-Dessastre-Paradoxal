# S11 — Piloto Sinnoh com saves isolados (aceite de código)

**O que esta entrega conclui:** o contrato de isolamento dos saves do piloto experimental de Sinnoh no Windows, reutilizando o instalador privado, a inicialização Ruby e o lançador da S10. A S11 **não** implica que os nove mapas reais foram importados ou que o jogo está jogável. A montagem efetiva do piloto é a S12 e a execução nativa continua na S31.

## Isolamento efetivamente implementado

1. [`sinnoh_save_isolation.py`](../scripts/regions/sinnoh_save_isolation.py) gera, a partir de um token privado de 12 hexadecimais, as chaves determinísticas `Sinnoh-QA-<token>` e `Dessastre-Sinnoh-QA-<token>`. Verifica que a pasta QA fica em `.blue-work/game-sinnoh-qa-<token>` e que `mkxp.json`, `Game.ini` e o manifesto apontam **exatamente** para o mesmo token.
2. [`install_sinnoh_qa_copy.py`](../scripts/regions/install_sinnoh_qa_copy.py) integra esse contrato à preparação e verificação; rejeita save paths customizados, tokens trocados, symlinks e namespace igual ao jogo principal quando a configuração original está disponível. Continua copiando a base **sem arquivos de save**, bloqueando a presença de saves herdados. Não modifica os arquivos originais.
3. [`SinnohQAStart.rb`](../scripts/regions/SinnohQAStart.rb) verifica o namespace real de `mkxp.json` **na própria engine**, além das provas de mapas/PBS. Ao carregar um save existente, exige `blue_regions.version=1`, `current=SINNOH` e `initial=SINNOH`; se o registro estiver ausente ou for de Decades/Kanto/Johto/Hoenn, bloqueia **antes de delegar ao loader nativo**. Novo Jogo não reescreve uma origem estrangeira e continua exigindo a prova estrutural do piloto.
4. [`launch_sinnoh_qa.py`](../scripts/regions/launch_sinnoh_qa.py) agora exige `save_namespace_verified=true` e `foreign_save_inherited=false` antes de qualquer subprocesso. O [BAT S10](../SINNOH_JOGAR_EXPERIMENTAL.bat) continua com duplo clique e sem fallback para o `Game.exe` principal.

**Não é migração de saves:** Sinnoh QA não importa saves antigos nem sobrescreve saves de Decades/Johto/Hoenn/Kanto. Os identificadores de perfil são específicos da instância privada. A verificação do diretório de saves real usado pelo runtime mkxp, assim como salvar/fechar/abrir no jogo, **ainda depende de teste no Windows**.

## Cobertura de testes S11

- [Testes Python S11](../tests/test_sinnoh_s11_save_isolation.py): token, exclusividade de perfil, injeção em save paths, Game.ini, pasta fora de `.blue-work`, symlinks, ausência de modificação de saves originais, montagem de cópia QA com assets sintéticos, bloqueio de saves estrangeiros, mudança posterior do mkxp e bloqueio antes do lançamento.
- [Fixture Ruby](../tests/sinnoh_qa_start_runtime.rb): confirma carregamento de um save Sinnoh válido na simulação, rejeição de registro regional ausente, campo `initial` ausente, região estrangeira e namespace falsificado **sem delegar à inicialização principal**.
- [Testes S10](../tests/test_sinnoh_s10_launcher.py) passam a incluir a nova exigência `save_namespace_verified`; [manifesto S30](../scripts/regions/audit_sinnoh_s30_suite.py) passa a exigir os arquivos e testes da S11.
- As regressões são exclusivamente **Python/Ruby com mocks e fixtures**. Nenhum save real ou `Game.exe` foi acessado.

## Validação e limites do aceite

```bash
python -m unittest discover -s tests -p 'test_sinnoh_s11_save_isolation.py' -v
python scripts/regions/sinnoh_ci_ch19.py --suite python
python scripts/regions/sinnoh_ci_ch19.py --suite ruby
```

A S11 só será marcada `done` após **GitHub Actions CH19/S30 completos e aprovação do PR na `main`**. Isso elevará a **Barra A para 14/32 (43%)**, 6 parciais e 12 pendentes. **B/C/D continuam 0/13**, Barra E 20/20; 44 casos reais Windows/JoiPlay ainda pendentes.

**Pendências para depois:** S12 — instalar overlay real autorizado em cópia QA sem substituir `game/`; S31 — observar nível, save/reload, batalha, NPCs, warps e JoiPlay em dispositivos reais. A proteção contra saves de outras regiões **não equivale à confirmação de que o save/load da engine funciona no Windows**.
