# User Story: [US-SQLITE-05] Refatoração das 6 views analíticas e consistência de contexto, validador e testes

**Epic:** Refatoração de Carga ETL e das 6 Views Analíticas
**GitHub Epic Issue:** -
**GitHub US Issue:** #138
**Prioridade:** Alta
**Story Points:** 5
**Sprint:** 02
**Status:** Review
**Behavior Change Esperado:** YES

---

## Historia

**Como** usuário e mantenedor do Adito
**Eu quero** que as 6 views em `04_fatos_views.sql` tenham colunas redundantes removidas, flags padronizadas (`flag_*`), IDs estruturais e de pessoa (`id_pessoa_<papel>`), novos atributos já disponíveis no banco e política única de nulos (`'Não Informado'` + rótulos semânticos + `NULL` real onde devido), mantendo `views.json`, `rules.md`, `examples.json`, `eval_dataset.json`, `sql_validator.py` e `core/tests.py` consistentes
**Para que** as consultas SQL sejam mais limpas, confiáveis e preparadas para cruzamentos exatos por ID

### Contexto Adicional

- **Discovery:** `Adito/docs/discovery/refatoracao-etl-views-analiticas.md` (`PROBLEM_READY`)
- **Requirements:** `Adito/docs/requirements/refatoracao-etl-views-analiticas.md` (`REQUIREMENTS_READY` — `FR03–FR08`, `BR01–BR05`, `NFR01`, `NFR03`, `NFR04`, `A01`, `KD02`, `KD03`)
- Esta story consolida a refatoração das 6 views atuais junto com a atualização atômica de todos os artefatos que referenciam suas colunas, garantindo um vertical slice 100% testável e verde em `make test-core`.
- **Fora de escopo:** criação de novas views (equipes, currículo, atividades), ajustes no Orquestrador, otimização de embeddings e criação completa da matriz de cruzamento + novos exemplos avançados (próxima etapa).

### Pontos de Esclarecimento

Nenhum ponto pendente.

---

## Criterios de Aceitacao

- [x] **Criterio 1 (Limpeza — `FR03`):** Em `Adito/scripts/sql/04_fatos_views.sql`, removidas `relatorio_aprovado`, `certificado_emitido`, `cancelado`, `relatorio_enviado` e todas as 6 colunas constantes `qtd_* = 1`; `sigilo` renomeada para `flag_sigilo`; mantidos `flag_aprovado`, `status_participacao` + `flag_ativo` e `qtd_atividades_vinculadas`.
- [x] **Criterio 2 (IDs — `FR04`, `BR02`):** Expostos ao lado dos nomes: `id_pessoa_coordenador`, `id_pessoa_participante`, `id_pessoa_orientador`, `id_pessoa_orientado`, `id_pessoa_autor`, `id_pessoa_membro`, além de `id_projeto` e `id_plano_trabalho` (Bolsas), `id_acao_pai` (Extensão Ação) e `id_grupo_pesquisa` (Projetos, com `MIN` para preservar grão 1:1 — `BR01`). Nenhum ID de domínio auxiliar exposto (`NFR04`).
- [x] **Criterio 3 (Novos atributos — `FR05`, `BR01`, `KD02`):** Adicionados `titulo_acao_pai` e `qtd_equipe_execucao` (`vfact_extensao_acao_resolved`); `grupos_pesquisa` no formato `"Nome Completo (SIGLA)"` sem repetir sigla já contida no nome, `grupos_externos`, `qtd_pesquisadores_equipe` e `qtd_estudantes_equipe` (`vfact_projeto_pesquisa_resolved`); `linhas_pesquisa`, `instituicoes_parceiras`, `data_situacao` e `data_ultimo_envio` (`vfact_grupo_pesquisa_membro_resolved`), com zero *fan-out* (contagem de linhas de cada view preservada).
- [x] **Criterio 4 (Padronização de nulos — `FR06`, `BR03`):** Textos categóricos sem rótulo específico unificados em `'Não Informado'` (eliminando `'Não Informada'`, `'Campus Não Informado'`, `'Não Especificado'`, `'Não Classificado'`, `'Não Vinculada'` e `NULL` em textos categóricos); rótulos próprios aplicados (`'Recurso Próprio / Sem Fomento'`, `'Recurso Institucional Ifes'`, `'Sem Parceiro Demandante'`, `'Sem Edital Vinculado'`, `'Externo / Não Vinculado'`, `'Sem Ação Vinculante'`, `'Sem Instituição Parceira'`, `'Sem Grupo de Pesquisa Vinculado'`, `'Sem Grupo Externo Vinculado'`, `'Sem Linha de Pesquisa Informada'`); `NULL` real preservado em datas, anos/meses, números/durações, IDs e `nome_cancelador` quando `flag_cancelado = 0` (`'Não Informado'` apenas se `flag_cancelado = 1` sem nome).
- [x] **Criterio 5 (Consistência e testes — `FR07`, `FR08`, `BR05`, `NFR01`, `KD03`):** `views.json`, `rules.md`, `examples.json`, `eval_dataset.json`, `sql_validator.py` e `core/tests.py` atualizados sem referências a colunas removidas (mantendo zero *data leakage* e cobertura das 6 views no Top-16), e `make test-core` 100% verde sobre cópia de `~/Downloads/dados.db` em `Adito/app/data/dados.db` com `04_fatos_views.sql` aplicado (sem modificar o arquivo original em `~/Downloads`).

---

## Governanca e Rastreabilidade

- **Nivel ScrumAIDev:** 2
- **Justificativa do nivel:** Altera o schema analítico compartilhado das 6 views (contrato entre SQLite, agente BI, contexto, validador e testes), já documentado em `Adito/docs/specs/especificacao_resolucoes_fatos_v2.md`.
- **US exige Spec governada?** Sim (atualização da spec existente)
- **Justificativa da Spec:** As 6 views possuem especificação de referência em `Adito/docs/specs/especificacao_resolucoes_fatos_v2.md` e requisitos aprovados em `Adito/docs/requirements/refatoracao-etl-views-analiticas.md`.
- **Spec prevista:** `Adito/docs/specs/especificacao_resolucoes_fatos_v2.md` (nota de revisão) / `Adito/docs/requirements/refatoracao-etl-views-analiticas.md`
- **US exige Contract governado?** Nao
- **Justificativa do Contract:** US nao exige Contract — não altera contratos RPC/HTTP externos.
- **Contract previsto:** N/A
- **Padrao de erro aplicavel:** N/A
- **BDD previsto:** N/A
- **Gates opcionais aplicaveis:** N/A
- **Touch List preliminar:** `Adito/scripts/sql/04_fatos_views.sql`, `Adito/app/contexts/pesquisa-extensao-ifes/{views.json,rules.md,examples.json}`, `Adito/app/scripts/eval_dataset.json`, `Adito/app/backend/nucleo/agents/bi_agent/nodes/sql_validator.py`, `Adito/app/backend/nucleo/core/tests.py`
- **Task Issues previstas:** #138

---

## Notas Tecnicas

### Arquitetura

- **Componentes afetados:** DDL de views SQLite (`04_fatos_views.sql`), contexto analítico (`views.json`, `rules.md`, `examples.json`), validador SQL (`sql_validator.py`), dataset de avaliação (`eval_dataset.json`) e suíte `core/tests.py`.
- **APIs necessarias:** N/A (confirmado que `dashboard.py` não depende das colunas removidas).
- **Database changes:** Recriação das 6 views dinâmicas (`DROP VIEW IF EXISTS ...; CREATE VIEW ...`) em `Adito/scripts/sql/04_fatos_views.sql`.
- **Referencias do modelo de dados:** `Adito/scripts/sql/02_tabelas.sql`, `Adito/scripts/sql/04_fatos_views.sql`
- **Erros observaveis esperados:** Validação em `sql_validator.py` alinhada ao novo padrão `'Não Informado'` para `coordenador_nome` e `programa_fomento`.

### Dependencias

- [x] Cópia de `~/Downloads/dados.db` em `Adito/app/data/dados.db` (somente leitura do original) para validação integral das 6 views, incluindo Produções Lattes.

### Consideracoes de Performance

- Todas as agregações 1:N/N:N permanecem em subqueries pré-agrupadas por chave primária antes do `LEFT JOIN`, preservando latência < 10 ms em SQLite.

---

## Plano de Testes

### Testes Unitarios
- [x] `make test-core` (valida segurança SQL, `views.json`, `rules.md`, `BASE_SQL_RULES`, `examples.json` com linhas no `dados.db`, cobertura Top-16, zero *data leakage* com `eval_dataset.json`, `sql_validator.py` e contratos das views).
- [x] Conferência automatizada de ausência das colunas removidas, presença de todos os novos IDs/atributos e preservação exata da contagem de linhas (zero *fan-out*) nas 6 views antes vs. depois de aplicar `04_fatos_views.sql`.

### Testes de Integracao
- [x] Aplicar `04_fatos_views.sql` sobre cópia de `~/Downloads/dados.db` em `Adito/app/data/dados.db` e executar `validar_sanidade_banco` + `make test-core`.

### Testes de Contract
- N/A

### Testes Manuais
- [x] Conferir amostras de `grupos_pesquisa` (`"Nome (SIGLA)"` sem repetição), `nome_cancelador` (`NULL` quando `flag_cancelado = 0`), rótulos `'Sem ...'` e `'Não Informado'`.
- [x] Confirmar que `~/Downloads/dados.db` não foi modificado.

---

## Tasks (Breakdown)

- [x] **[TASK-SQLITE-05.1]** Refatorar as 6 views em `Adito/scripts/sql/04_fatos_views.sql` (limpeza, IDs, novos atributos e política de nulos).
- [x] **[TASK-SQLITE-05.2]** Atualizar `views.json`, `rules.md`, `examples.json`, `eval_dataset.json` e `sql_validator.py` para total consistência.
- [x] **[TASK-SQLITE-05.3]** Atualizar `core/tests.py`, aplicar `04_fatos_views.sql` sobre cópia de `~/Downloads/dados.db` e validar `make test-core`.

---

## Definition of Done Checklist

- [x] Codigo implementado conforme criterios de aceitacao
- [x] Decisao sobre Spec governada foi registrada
- [x] Decisao sobre Contract governado foi registrada
- [x] Nivel ScrumAIDev foi registrado
- [x] Testes unitarios com cobertura adequada
- [x] Testes de integracao passando
- [x] Documentacao atualizada
- [x] `Behavior change` documentado no PR
