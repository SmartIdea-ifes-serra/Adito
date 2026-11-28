# Sprint Planning — Sprint 02: Refatoração de Carga ETL e das 6 Views Analíticas

**Data:** 28/11/2026  
**Participantes:** Gabriela Prajo Beretta + Antigravity  
**Sprint Duration:** 1 ciclo (entrega contínua na branch `refactor/138-etl-views-analiticas`)  
**Sprint Goal:** Corrigir a integridade da carga ETL (`orientacao` sem duplicidades por `id_origem` e `etl-cruzar` automático no `make db`) e refatorar as 6 views analíticas em `04_fatos_views.sql` com flags padronizadas (`flag_*`), IDs estruturais e de pessoa (`id_pessoa_<papel>`), novos atributos do banco e política única de nulos, mantendo contexto, validador SQL e `make test-core` 100% consistentes.  
**GitHub Project:** SmartIdea-ifes-serra/Adito  
**GitHub Sprint Iteration:** -  
**GitHub Sprint Milestone:** Issue #138  

---

## Sprint Capacity

- **Velocity anterior:** 18 pts (Sprint 01 — EPIC-08 completo)
- **Capacidade estimada:** 8 pts (EPIC-16 completo: 2 vertical slices)
- **Dias úteis disponíveis:** execução focada na entrega da Issue `#138`
- **Impedimentos conhecidos:** `scriptLattes` temporariamente quebrado por mudança externa de URLs no CNPq; mitigado validando as 6 views e `make test-core` sobre cópia de `~/Downloads/dados.db` (sem modificar o original).

---

## Sprint Goal

> Entregar uma base `dados.db` íntegra (sem orientações duplicadas nem descarte silencioso por `pessoas.json` defasado) e 6 views analíticas limpas, padronizadas e enriquecidas com chaves exatas (`id_pessoa_<papel>`, `id_projeto`, `id_plano_trabalho`, `id_acao_pai`, `id_grupo_pesquisa`), com 100% dos artefatos dependentes e testes passando.

---

## User Stories Selecionadas

### [US-ETL-08] Deduplicação de orientações na carga e `etl-cruzar` automático no `make db`

- **Prioridade:** Alta (Vertical Slice 1)
- **GitHub Epic Issue:** -
- **GitHub US Issue:** #138
- **Story Points:** 3
- **Assignee:** Gabriela Prajo Beretta
- **Nivel ScrumAIDev:** 1
- **Exige Spec governada?** Nao
- **Spec:** -
- **Exige Contract governado?** Nao
- **Contract:** -
- **BDD:** -
- **Behavior change esperado:** YES
- **Criterios de Aceitacao:**
  - [ ] `popular_banco.py` grava no máximo 1 registro por `id_origem` em `orientacao`, mantendo o estado atualizado (`cancelado`, `nome_cancelador`, `data_cancelado`, `relatorio_enviado`) do ano mais recente (`FR01`, `KD01`).
  - [ ] `validar_sanidade_banco` garante ausência de `id_origem` duplicado em `orientacao`.
  - [ ] `make db` no `Makefile` executa `adito-etl cruzar` automaticamente sempre que `pessoas.json` não existir ou algum arquivo em `Adito/etl/brutos/` for mais novo que `pessoas.json` (`FR02`).
  - [ ] Teste automatizado cobre deduplicação por `id_origem`, validado em banco temporário sem alterar `~/Downloads/dados.db` nem sobrescrever `Adito/app/data/dados.db` (`NFR01`, `NFR02`).

### [US-SQLITE-05] Refatoração das 6 views analíticas e consistência de contexto, validador e testes

- **Prioridade:** Alta (Vertical Slice 2)
- **GitHub Epic Issue:** -
- **GitHub US Issue:** #138
- **Story Points:** 5
- **Assignee:** Gabriela Prajo Beretta
- **Nivel ScrumAIDev:** 2
- **Exige Spec governada?** Sim (nota de revisão em `Adito/docs/specs/especificacao_resolucoes_fatos_v2.md` / `Adito/docs/requirements/refatoracao-etl-views-analiticas.md`)
- **Spec:** `Adito/docs/specs/especificacao_resolucoes_fatos_v2.md`
- **Exige Contract governado?** Nao
- **Contract:** -
- **BDD:** -
- **Behavior change esperado:** YES
- **Criterios de Aceitacao:**
  - [ ] Limpeza aplicada em `04_fatos_views.sql`: removidas `relatorio_aprovado`, `certificado_emitido`, `cancelado`, `relatorio_enviado` e todas as 6 `qtd_* = 1`; `sigilo` → `flag_sigilo`; mantidos `flag_aprovado`, `status_participacao` + `flag_ativo` e `qtd_atividades_vinculadas` (`FR03`).
  - [ ] IDs expostos ao lado dos nomes: `id_pessoa_coordenador`, `id_pessoa_participante`, `id_pessoa_orientador`, `id_pessoa_orientado`, `id_pessoa_autor`, `id_pessoa_membro`, `id_projeto`, `id_plano_trabalho`, `id_acao_pai`, `id_grupo_pesquisa` (`FR04`, `BR02`).
  - [ ] Novos atributos adicionados sem *fan-out*: `titulo_acao_pai` e `qtd_equipe_execucao` (Extensão Ação); `grupos_pesquisa` (`"Nome Completo (SIGLA)"` sem repetir sigla), `grupos_externos`, `qtd_pesquisadores_equipe`, `qtd_estudantes_equipe` (Projetos); `linhas_pesquisa`, `instituicoes_parceiras`, `data_situacao`, `data_ultimo_envio` (Grupos CNPq) (`FR05`, `BR01`, `KD02`).
  - [ ] Política de nulos padronizada: `'Não Informado'` para textos categóricos ausentes sem rótulo próprio; rótulos semânticos próprios mantidos/adicionados; `NULL` real preservado em datas, anos/meses, números/durações, IDs e `nome_cancelador` quando `flag_cancelado = 0` (`FR06`, `BR03`).
  - [ ] `views.json`, `rules.md`, `examples.json`, `eval_dataset.json`, `sql_validator.py` (NULL guard) e `core/tests.py` atualizados e consistentes, com `make test-core` 100% verde sobre cópia de `~/Downloads/dados.db` em `Adito/app/data/dados.db` (`FR07`, `FR08`, `BR05`, `NFR01`, `KD03`).

---

## Rastreabilidade da Sprint

- **Backlog fonte:** `Adito/docs/product_backlog.md` (`EPIC-16`)
- **Discovery / Requirements:** `Adito/docs/discovery/refatoracao-etl-views-analiticas.md` / `Adito/docs/requirements/refatoracao-etl-views-analiticas.md`
- **TODO técnico:** N/A
- **GitHub Sprint Container em uso:** Issue `#138` (branch `refactor/138-etl-views-analiticas`)
- **Specs a criar/atualizar:** atualização documental em `Adito/docs/specs/especificacao_resolucoes_fatos_v2.md` (opcional/resumo de revisão)
- **Contracts a criar/atualizar:** N/A
- **BDD a criar/atualizar:** N/A
- **Gates opcionais da sprint:** N/A (`make test-core` + validação SQLite pós-carga)
- **Task Issues a criar/atualizar:** #138

## Definition of Done

- [ ] Código revisado e implementado na branch `refactor/138-etl-views-analiticas`
- [ ] Decisões sobre Spec e Contract registradas nas 2 US
- [ ] Nível ScrumAIDev registrado nas 2 US
- [ ] Testes unitários e `make test-core` 100% verdes (sobre cópia de `~/Downloads/dados.db`, preservando o original intacto)
- [ ] Deduplicação de `orientacao` validada em teste automatizado e carga isolada
- [ ] Pequenos ajustes óbvios em `rules.md`/`examples.json` reportados explicitamente ao usuário
- [ ] Lembrete final emitido ao usuário sobre a próxima etapa: definição da matriz de cruzamento, novas regras e novos exemplos
- [ ] Documentação atualizada e `Behavior change` documentado no PR

---

## Riscos e Dependencias

| Risco/Dependencia | Impacto | Mitigacao |
|---|---|---|
| `scriptLattes` quebrado externamente impede gerar Lattes via `make etl` | Médio | Validar `04_fatos_views.sql` e `make test-core` sobre cópia de `~/Downloads/dados.db`; validar `popular_banco.py` em banco temporário/teste unitário sem sobrescrever a cópia completa |
| Remoção/renomeação de colunas quebrar referências ocultas em código ou gabaritos | Médio | Busca global (`grep`) em `Adito/` por todas as colunas removidas/renomeadas + execução integral de `make test-core` |
| Mudança de `NULL` → `'Não Informado'` conflitar com `check_missing_null_guard` em `sql_validator.py` | Médio | Atualizar `sql_validator.py` e os testes correspondentes junto com `04_fatos_views.sql` (`KD03`) |
| Multiplicação de linhas (*fan-out*) ao incluir `grupos_pesquisa`, `linhas_pesquisa`, `instituicoes_parceiras` e contagens de equipe | Alto | Pré-agregar 100% das relações 1:N/N:N em subqueries por chave primária e conferir contagens exatas antes vs. depois (`BR01`) |

---

## Notas e Decisoes

- **Fora de escopo desta sprint:** novas views (currículo, equipes, atividades), Orquestrador, otimização de embeddings e expansão completa da matriz de cruzamento + novos exemplos avançados.
- **Follow-up obrigatório ao final da execução:** lembrar explicitamente a usuária que a matriz de cruzamento, novas regras e novos exemplos precisam ser definidos na próxima etapa (ex.: Issue `#119`).
- **Arquivos untracked na raiz:** manter `diagnostico_rules_examples.md` e `diagnostico_embeddings.md` intocados fora dos commits.

---

## Assistencia IA Utilizada

- [x] Refinamento de user stories
- [x] Estimativa de complexidade
- [x] Identificacao de riscos tecnicos
- [x] Sugestoes de arquitetura
- [x] Definicao de Spec e Contract
- [x] Outros: auditoria de banco `dados.db`, alinhamento `/grill-me`, `/scope-idea`, `/discover`, `/requirements` e `/sprint-planning`
