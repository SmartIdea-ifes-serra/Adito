# Requirements — Refatoração de Carga ETL e das 6 Views Analíticas

**Status:** REQUIREMENTS_READY
**Discovery de origem:** `Adito/docs/discovery/refatoracao-etl-views-analiticas.md`
**Classificacao de Processo:** NORMAL PROCESS
**Issue / Branch:** `#138` (`refactor/138-etl-views-analiticas`)

## Intent Summary
Garantir integridade dos dados carregados no `dados.db` (sem orientações duplicadas e sem descarte silencioso por `pessoas.json` defasado) e refatorar as 6 views analíticas atuais com nomes padronizados, chaves estruturais e de pessoa (`id_pessoa_<papel>`), atributos úteis já presentes no banco e política única de nulos, mantendo 100% de consistência com contexto, validador SQL, gabaritos e testes.

## Functional Requirements
- **FR01 — Deduplicação de orientações por `id_origem`:** Em `Adito/scripts/popular_banco.py`, deduplicar registros da tabela `orientacao` por `id_origem` (mantendo apenas 1 registro quando o mesmo `Id` aparecer em múltiplos arquivos anuais de `brutos/sigpesq/orientacoes/`).
- **FR02 — Atualização automática de `pessoas.json` em `make db`:** No `Makefile`, o alvo `db` deve executar `adito-etl cruzar` automaticamente quando `Adito/etl/trabalho/pessoas.json` não existir **ou** quando qualquer arquivo regular em `Adito/etl/brutos/` tiver timestamp de modificação mais recente que `pessoas.json`.
- **FR03 — Limpeza de colunas redundantes nas 6 views (`04_fatos_views.sql`):**
  - Remover `relatorio_aprovado` (manter `flag_relatorio_aprovado`) em `vfact_extensao_acao_resolved`.
  - Remover `certificado_emitido` (manter `flag_certificado` e `flag_aprovado`) em `vfact_extensao_participacao_resolved`.
  - Remover `cancelado` (manter `flag_cancelado`) e `relatorio_enviado` (manter `flag_relatorio_enviado`) em `vfact_orientacao_bolsa_resolved`.
  - Renomear `sigilo` para `flag_sigilo` em `vfact_projeto_pesquisa_resolved`.
  - Remover as 6 colunas constantes `= 1`: `qtd_acoes`, `qtd_participacoes`, `qtd_projetos`, `qtd_orientacoes`, `qtd_autorias`, `qtd_membros`.
  - Manter `status_participacao` + `flag_ativo` em `vfact_grupo_pesquisa_membro_resolved` e `qtd_atividades_vinculadas` em `vfact_extensao_acao_resolved`.
- **FR04 — Exposição de IDs estruturais e de pessoa nas 6 views (`04_fatos_views.sql`):**
  - Expor `id_pessoa_<papel>` ao lado do nome correspondente: `id_pessoa_coordenador` (`vfact_extensao_acao_resolved` e `vfact_projeto_pesquisa_resolved`), `id_pessoa_participante` (`vfact_extensao_participacao_resolved`), `id_pessoa_orientador` e `id_pessoa_orientado` (`vfact_orientacao_bolsa_resolved`), `id_pessoa_autor` (`vfact_producao_cientifica_resolved`), `id_pessoa_membro` (`vfact_grupo_pesquisa_membro_resolved`).
  - Expor IDs estruturais faltantes: `id_projeto` e `id_plano_trabalho` em `vfact_orientacao_bolsa_resolved`; `id_acao_pai` em `vfact_extensao_acao_resolved`; `id_grupo_pesquisa` em `vfact_projeto_pesquisa_resolved`.
- **FR05 — Enriquecimento de atributos de conteúdo nas 6 views (`04_fatos_views.sql`):**
  - `vfact_extensao_acao_resolved`: adicionar `titulo_acao_pai` e `qtd_equipe_execucao`.
  - `vfact_projeto_pesquisa_resolved`: adicionar `grupos_pesquisa` (formato `"Nome Completo (SIGLA)"` sem duplicar sigla já presente no nome; apenas `"Nome Completo"` quando sem sigla), `grupos_externos`, `qtd_pesquisadores_equipe` e `qtd_estudantes_equipe`.
  - `vfact_grupo_pesquisa_membro_resolved`: adicionar `linhas_pesquisa`, `instituicoes_parceiras`, `data_situacao` e `data_ultimo_envio`.
- **FR06 — Padronização da política de valores ausentes/nulos nas 6 views (`04_fatos_views.sql`):**
  - Substituir textos categóricos ausentes sem justificativa específica por `'Não Informado'` (unificando `'Não Informada'`, `'Campus Não Informado'`, `'Não Especificado'`, `'Não Classificado'`, `'Não Vinculada'` e `NULL` em textos categóricos).
  - Aplicar rótulos semânticos próprios: `'Recurso Próprio / Sem Fomento'`, `'Recurso Institucional Ifes'`, `'Sem Parceiro Demandante'`, `'Sem Edital Vinculado'`, `'Externo / Não Vinculado'` (`campus` no Lattes), `'Sem Ação Vinculante'` (`titulo_acao_pai`), `'Sem Instituição Parceira'` (`instituicoes_parceiras`), `'Sem Grupo de Pesquisa Vinculado'` (`grupos_pesquisa`), `'Sem Grupo Externo Vinculado'` (`grupos_externos`) e `'Sem Linha de Pesquisa Informada'` (`linhas_pesquisa`).
  - Manter `NULL` real em datas (`data_*`), anos/meses (`ano*`, `mes_*`), números/durações (`duracao_*`, `tempo_participacao_dias`), IDs (`id_*`) e `nome_cancelador` quando `flag_cancelado = 0` (`'Não Informado'` apenas quando `flag_cancelado = 1` e sem nome preenchido).
- **FR07 — Consistência dos artefatos de contexto, validador e gabaritos:**
  - Atualizar `Adito/app/contexts/pesquisa-extensao-ifes/views.json`, `rules.md`, `examples.json` e `Adito/app/scripts/eval_dataset.json` para refletir exatamente os novos nomes de colunas, remoções e política de `'Não Informado'` (incluindo pequenos ajustes óbvios reportados explicitamente ao usuário).
  - Atualizar `Adito/app/backend/nucleo/agents/bi_agent/nodes/sql_validator.py` (NULL guard de `coordenador_nome` e `programa_fomento`) para refletir que esses campos agora usam `'Não Informado'` em vez de `NULL` real.
- **FR08 — Testes automatizados e validação no `dados.db`:**
  - Atualizar/adicionar testes em `Adito/app/backend/nucleo/core/tests.py` (e teste específico para deduplicação de `orientacao` em `popular_banco.py`), garantindo que `make test-core` passe integralmente sobre a cópia de `~/Downloads/dados.db` com `04_fatos_views.sql` aplicado.

## Business / Domain Rules
- **BR01 — Preservação estrita de grão (zero fan-out):** toda junção 1:N ou N:N nas 6 views deve ser agregada previamente em subquery (`GROUP_CONCAT(..., '; ')`, `COUNT(...)`, `MIN(...)`). Em `vfact_projeto_pesquisa_resolved`, `id_grupo_pesquisa` usa `MIN(id_grupo_pesquisa)` se houver mais de 1 grupo vinculado ao mesmo projeto.
- **BR02 — Chave universal de pessoa:** todas as colunas `id_pessoa_<papel>` nas 6 views apontam para `pessoa.id` e sempre coexistem com a respectiva coluna de nome.
- **BR03 — Semântica limpa de `nome_cancelador`:** nunca preencher `nome_cancelador` com texto de status quando `flag_cancelado = 0` (manter `NULL`), evitando poluir `COUNT(DISTINCT nome_cancelador)` e rankings de canceladores.
- **BR04 — Independência entre `flag_aprovado` e `flag_certificado`:** em `vfact_extensao_participacao_resolved`, aprovação e emissão de certificado são conceitos distintos e ambos devem ser preservados.
- **BR05 — Zero data leakage e cobertura Top-16:** `examples.json` não pode duplicar perguntas verbatim de `eval_dataset.json` e suas 16 primeiras entradas devem continuar cobrindo as 6 views.

## Non-Functional Requirements
- **NFR01 — Proteção do arquivo de referência:** `~/Downloads/dados.db` é somente leitura lógica e jamais deve ser modificado; validações das views ocorrem exclusivamente sobre cópia em `Adito/app/data/dados.db`.
- **NFR02 — Validação isolada do ETL:** testes da carga em `popular_banco.py` (sem Lattes local) devem usar banco temporário/testes unitários, sem sobrescrever a cópia completa com Lattes em `Adito/app/data/dados.db`.
- **NFR03 — Compatibilidade SQLite 3 e LGPD:** 100% compatível com SQLite 3, mantendo `PRAGMA foreign_key_check` zerado e zero exposição de PII (CPF, e-mail, telefone).
- **NFR04 — DDL enxuto:** não expor colunas descartadas no Discovery (`websites`, `repercussoes`, `equipamentos_softwares`, extras de patentes/datas, IDs de domínios auxiliares).

## User Scenarios
### Main flow
1. Desenvolvedor executa `make db` após nova extração parcial ou completa em `Adito/etl/brutos/` → `Makefile` detecta arquivos mais novos que `pessoas.json`, executa `etl-cruzar` e popula `dados.db` sem duplicar orientações.
2. Analista ou usuário consulta o Adito usando qualquer uma das 6 views refatoradas → DDL limpo, IDs consistentes (`id_pessoa_*`, `id_projeto`, `id_plano_trabalho`, `id_acao_pai`, `id_grupo_pesquisa`) e textos ausentes padronizados em `'Não Informado'` ou rótulo semântico claro.
3. Suíte `make test-core` valida segurança SQL, zero data leakage, cobertura Top-16, NULL/missing guard e execução com linhas positivas no `dados.db` completo.

### Alternative / Error / Edge cases
- Mesma orientação (`Id`) presente em `2025.json` e `2026.json` com atributos ligeiramente atualizados (ex.: relatório enviado ou cancelamento registrado no ano mais recente): a deduplicação deve preservar os dados mais completos/recentes (ou a última ocorrência ordenada por ano) em vez de duplicar a linha.
- Projeto sem grupo de pesquisa vinculado: `id_grupo_pesquisa` é `NULL` e `grupos_pesquisa` é `'Sem Grupo de Pesquisa Vinculado'`.
- Grupo cujo `nome` já termina ou contém a própria sigla (ex.: `'Grupo de Automação Industrial - GAIn'` com sigla `'GAIn'`): `grupos_pesquisa` não deve repetir `' - GAIn (GAIn)'`.
- Orientação cancelada (`flag_cancelado = 1`) com `nome_cancelador` ausente: `nome_cancelador` vira `'Não Informado'`; se `flag_cancelado = 0`, `nome_cancelador` permanece `NULL`.
- `Adito/etl/brutos/` vazio ou `pessoas.json` inexistente: `make db` trata com segurança (executando `etl-cruzar` quando `brutos/` existir).

## Business / Domain Context
- Base institucional do Ifes unificando SRC (Extensão), SigPesq (Projetos e Bolsas), Lattes (Produções) e CNPq DGP (Grupos de Pesquisa) em 82 tabelas 3FN expostas por 6 views analíticas (`vfact_*_resolved`).

## Technical Context & Constraints
- Arquivos impactados: `Adito/scripts/popular_banco.py`, `Makefile`, `Adito/scripts/sql/04_fatos_views.sql`, `Adito/app/contexts/pesquisa-extensao-ifes/{views.json,rules.md,examples.json}`, `Adito/app/scripts/eval_dataset.json`, `Adito/app/backend/nucleo/agents/bi_agent/nodes/sql_validator.py`, `Adito/app/backend/nucleo/core/tests.py` (e `Adito/scripts/popular_banco.py` `validar_sanidade_banco` se afetado).
- `Adito/app/backend/nucleo/rpc/dashboard.py` já verificado como sem dependência das colunas removidas (será revalidado após edições).

## Quality Attributes
- **Integridade de dados:** 0 orientações duplicadas por `id_origem` e 0 regressões de grão nas 6 views.
- **Testabilidade:** `make test-core` 100% verde + teste automatizado cobrindo deduplicação de `orientacao`.
- **Manutenibilidade:** convenção uniforme `flag_*`, `id_pessoa_<papel>` e `'Não Informado'`.

## Assumptions
- **A01** — Em `vfact_orientacao_bolsa_resolved`, `vfact_producao_cientifica_resolved` e demais views, `~/Downloads/dados.db` contém as 82 tabelas base no schema esperado por `04_fatos_views.sql`.
- **A02** — Na deduplicação de `orientacao` por `id_origem`, manter a ocorrência do arquivo de ano mais recente (ordem crescente de arquivos `2016..2026.json` atualizando o registro existente) captura o estado mais atualizado de `cancelado` e `relatorio_enviado`.
- **A03** — Os arquivos untracked `diagnostico_rules_examples.md` e `diagnostico_embeddings.md` ficam fora dos commits da branch `refactor/138-etl-views-analiticas`.

## Out of Scope
- Criação de novas views (equipes, currículo, atividades).
- Enriquecimento de áreas vazias via LLM.
- Ajustes no Orquestrador (liberar "currículo").
- Otimização/automação de embeddings.
- Definição completa da matriz de cruzamento e novos exemplos avançados (próxima etapa após esta entrega).

## Open Questions
- Nenhuma pergunta bloqueante aberta.

## Key Decisions Proposed
- **KD01 — Deduplicação por último ano (estado mais recente) em `orientacao`:** quando o mesmo `id_origem` aparecer em `2025.json` e `2026.json`, atualizar os campos mutáveis (como `cancelado`, `data_cancelado`, `relatorio_enviado`) com a leitura mais recente em vez de ignorar silenciosamente a segunda ocorrência ou duplicar a linha.
- **KD02 — Formato de `grupos_pesquisa` sem sigla duplicada:** usar `CASE WHEN g.sigla IS NOT NULL AND TRIM(g.sigla) <> '' AND INSTR(LOWER(g.nome), LOWER(TRIM(g.sigla))) = 0 THEN g.nome || ' (' || TRIM(g.sigla) || ')' ELSE g.nome END`.
- **KD03 — `sql_validator.py` alinhado a `'Não Informado'`:** ajustar o `check_missing_null_guard` para exigir checagem de `'Não Informado'` (em vez de exigir `IS NULL` em colunas que não serão mais `NULL`), ou mantê-lo apenas para colunas que continuam `NULL` real (ex.: `ano` em Produções).

## Review & Adjust

O usuario pode **aprovar, editar, adicionar, remover ou reclassificar** qualquer requisito/regra antes do gate.

- [x] Proposta completa apresentada ao usuario
- [x] Ajustes solicitados incorporados
- [x] IDs estabilizados depois da revisao
- [x] Nenhuma pergunta bloqueante aberta

### User adjustments
- Aprovado integralmente sem alterações.

## Gate G1 — REQUIREMENTS READY

**Status:** APPROVED

**Aprovado pelo usuario:** sim
