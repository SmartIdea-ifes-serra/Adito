# Discovery — Refatoração de Carga ETL e das 6 Views Analíticas

**Status:** PROBLEM_READY
**Classificacao de Processo:** NORMAL PROCESS
**Origem:** hibrido (auditoria do banco/código + decisões alinhadas com o usuário)
**Issue / Branch:** `#138` (`refactor/138-etl-views-analiticas`)

## Intent
Corrigir falhas de integridade na carga do `dados.db` e refatorar, limpar e enriquecer as 6 views analíticas atuais (`Adito/scripts/sql/04_fatos_views.sql`), tornando os dados confiáveis e preparando chaves exatas para cruzamentos entre views.

## Problem
1. **Duplicação em `orientacao`:** bolsas do SigPesq que atravessam a virada do ano aparecem em dois arquivos anuais (`2016..2026.json`) e `popular_banco.py` não deduplica por `id_origem`, inflando contagens e somas de investimento em R$.
2. **Descarte silencioso de dados novos na carga:** `make db` reaproveita `Adito/etl/trabalho/pessoas.json` antigo mesmo quando há extrações mais recentes em `Adito/etl/brutos/`, fazendo `popular_banco.py` descartar pessoas e centenas de registros novos.
3. **Inconsistências nas 6 views analíticas:** colunas `0/1` duplicadas, colunas constantes `qtd_* = 1`, `sigilo` fora do padrão `flag_*`, ausência de IDs estruturais (`id_projeto`, `id_plano_trabalho`, `id_acao_pai`, `id_grupo_pesquisa`) e de pessoa (`id_pessoa_<papel>`), omissão de atributos já existentes no banco e 6 variações inconsistentes de textos nulos/ausentes.

## Users / Stakeholders relevantes
- Equipe de desenvolvimento do Adito (manutenção de ETL, views, contexto e testes).
- Alunos, docentes/pesquisadores e servidores/diretoria do Ifes (consumidores das consultas do Adito).

## Current Situation
- `popular_banco.py` insere orientações com `self.novo("orientacao", ...)` sem deduplicar `id_origem`.
- `Makefile` (`make db`) só executa `adito-etl cruzar` se `pessoas.json` não existir.
- As 6 views em `04_fatos_views.sql` não expõem `id_pessoa_*`, `id_projeto` (em Bolsas), `id_plano_trabalho`, `id_acao_pai` nem `id_grupo_pesquisa` (em Projetos), e alternam textos nulos (`'Não Informado'`, `'Não Informada'`, `'Campus Não Informado'`, `'Não Especificado'`, `'Não Classificado'`, `'Não Vinculada'` e `NULL`).
- O extrator do Lattes (`scriptLattes`) está temporariamente indisponível por mudança externa de URLs no CNPq; há um `dados.db` completo (com Lattes) em `~/Downloads/dados.db`.

## Desired Outcome
Banco `dados.db` carregado sem orientações duplicadas e com `pessoas.json` sempre atualizado; 6 views limpas, padronizadas (`flag_*`, `id_pessoa_<papel>`, política única de nulos) e enriquecidas; e todos os artefatos dependentes (`views.json`, `rules.md`, `examples.json`, `eval_dataset.json`, `sql_validator.py`, `core/tests.py`) consistentes e passando em `make test-core`.

## Success Criteria
- `popular_banco.py` não gera `id_origem` duplicado em `orientacao` mesmo quando o mesmo `Id` aparece em múltiplos arquivos anuais.
- `make db` dispara `etl-cruzar` automaticamente sempre que existir arquivo em `Adito/etl/brutos/` mais novo que `Adito/etl/trabalho/pessoas.json`.
- Todas as 6 views em `04_fatos_views.sql` refletem exatamente a limpeza de colunas, IDs (`id_pessoa_<papel>` + IDs estruturais), novos atributos e política de nulos definida.
- `views.json`, `rules.md`, `examples.json`, `eval_dataset.json`, `sql_validator.py` (NULL guard) e `core/tests.py` atualizados e passando integralmente em `make test-core` sobre cópia de `~/Downloads/dados.db` com `04_fatos_views.sql` aplicado (sem alterar o arquivo original em `~/Downloads`).

## Scope

### IN
- **ETL/Carga:** deduplicar `orientacao` por `id_origem` em `popular_banco.py`; atualizar `Makefile` (`make db`) para rodar `etl-cruzar` quando `brutos/` for mais novo que `pessoas.json`.
- **Limpeza das 6 views:** remover `relatorio_aprovado`, `certificado_emitido`, `cancelado`, `relatorio_enviado` (manter `flag_*` + manter `flag_aprovado`); renomear `sigilo` → `flag_sigilo`; remover `qtd_acoes`, `qtd_participacoes`, `qtd_projetos`, `qtd_orientacoes`, `qtd_autorias`, `qtd_membros`; manter `status_participacao` + `flag_ativo` e `qtd_atividades_vinculadas`.
- **IDs (ID + Nome):** `id_pessoa_coordenador`, `id_pessoa_participante`, `id_pessoa_orientador`, `id_pessoa_orientado`, `id_pessoa_autor`, `id_pessoa_membro`; `id_projeto` e `id_plano_trabalho` (Bolsas); `id_acao_pai` (Extensão Ação); `id_grupo_pesquisa` (Projetos).
- **Novos atributos:**
  - `vfact_extensao_acao_resolved`: `titulo_acao_pai`, `qtd_equipe_execucao`.
  - `vfact_projeto_pesquisa_resolved`: `grupos_pesquisa` (`"Nome Completo (SIGLA)"` sem repetir sigla; só nome se não houver sigla), `grupos_externos`, `qtd_pesquisadores_equipe`, `qtd_estudantes_equipe`.
  - `vfact_grupo_pesquisa_membro_resolved`: `linhas_pesquisa`, `instituicoes_parceiras`, `data_situacao`, `data_ultimo_envio`.
- **Padronização de nulos:** `'Não Informado'` para textos categóricos ausentes sem rótulo próprio; rótulos específicos mantidos/definidos (`'Recurso Próprio / Sem Fomento'`, `'Recurso Institucional Ifes'`, `'Sem Parceiro Demandante'`, `'Sem Edital Vinculado'`, `'Externo / Não Vinculado'`, `'Sem Ação Vinculante'`, `'Sem Instituição Parceira'`, `'Sem Grupo de Pesquisa Vinculado'`, `'Sem Grupo Externo Vinculado'`, `'Sem Linha de Pesquisa Informada'`); `NULL` real mantido em datas, anos/meses, números/durações, IDs e `nome_cancelador` quando `flag_cancelado = 0` (`'Não Informado'` apenas se `flag_cancelado = 1` sem nome).
- **Consistência:** atualizar `views.json`, `rules.md`, `examples.json`, `eval_dataset.json`, `sql_validator.py`, `core/tests.py` e outros pontos afetados (com pequenos ajustes óbvios informados explicitamente).

### OUT
- Enriquecimento de áreas vazias via LLM.
- IDs de domínios auxiliares (`id_campus`, `id_grande_area`, `id_tipo_acao`, etc.).
- `websites`, `repercussoes` e `equipamentos_softwares` em Grupos CNPq; colunas extras de patentes/datas em Produções Lattes.
- Ajustes no Orquestrador.

### LATER
- Definição completa da matriz de cruzamento, novas regras e novos exemplos avançados (lembrar explicitamente ao final da execução).
- Avaliação e criação de novas views (equipes, currículo, atividades).
- Otimização e automação de embeddings.

## Constraints / Feasibility
- `~/Downloads/dados.db` não deve ser modificado; validações das views e `make test-core` rodarão sobre cópia em `Adito/app/data/dados.db`, e as correções do `popular_banco.py` serão validadas separadamente (banco temporário/testes) sem sobrescrever a cópia com Lattes.
- `dashboard.py` já foi verificado e não depende das colunas removidas.
- Todas as edições ocorrem na branch `refactor/138-etl-views-analiticas`, criada a partir de `development`.

## Assumptions
- `[ASSUMPTION]` Caso no futuro um projeto possua mais de 1 grupo de pesquisa vinculado, `id_grupo_pesquisa` exporá `MIN(id_grupo_pesquisa)` enquanto `grupos_pesquisa` concatena todos com `; `, preservando o grão 1:1.
- `[ASSUMPTION]` `~/Downloads/dados.db` contém as tabelas base compatíveis com `04_fatos_views.sql` (será conferido antes de aplicar o DDL na cópia).
- `[ASSUMPTION]` Os arquivos `diagnostico_rules_examples.md` e `diagnostico_embeddings.md` permanecem intocados fora dos commits desta branch.

## Risks
- Remoção/renomeação de colunas e mudança de nulos podem afetar consultas em `examples.json`, `eval_dataset.json`, `sql_validator.py` ou `core/tests.py` (mitigado por busca global + `make test-core`).
- Usuários finais precisarão de um novo `dados.db` publicado no GitHub Releases sincronizado com a atualização do app.

## Open Questions
- Nenhuma pergunta bloqueante aberta.

## Review & Adjust

- [x] Usuario revisou a proposta completa
- [x] Alteracoes solicitadas foram incorporadas
- [x] Decisoes relevantes foram confirmadas
- [x] Nao existem perguntas bloqueantes abertas

### User adjustments
- Branch definida como `refactor/138-etl-views-analiticas` vinculada à Issue `#138`.

## Gate G0 — PROBLEM READY

**Status:** APPROVED

**Aprovado pelo usuario:** sim
