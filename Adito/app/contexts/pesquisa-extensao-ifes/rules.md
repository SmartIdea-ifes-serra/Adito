# Regras de Negócio e Modelagem Dimensional — Pesquisa, Extensão e Produção Científica (Ifes)

O banco **SQLite 3 (`dados.db`)** expõe **6 views analíticas (`vfact_*_resolved`)**. Nunca use `INTERSECT` ou `EXCEPT`.

> **REGRA GERAL #0 — Origem / Raiz dos Dados:**
> Em consultas consolidadas (`UNION ALL`) ou panoramas, rotule sempre a origem amigável de cada linha (`origem` / `categoria`), ex.: `'Projetos de Pesquisa (SigPesq)'`, `'Projetos de Extensão (SRC)'`, `'Ações de Extensão (SRC)'`, `'Ações de Ensino (SRC)'`, `'Orientações/Bolsas (SigPesq)'`, `'Produções Científicas (Lattes)'`, `'Grupos de Pesquisa (CNPq DGP)'`.

> **REGRA CRÍTICA — `"projetos"` e `"ações"` (View Única vs. Cruzamento por Pessoa):**
> - **Só `"projetos"` (solto):** retorne via `UNION ALL` (sem cruzamento/`JOIN`) **Projetos de Pesquisa (SigPesq)** (`vfact_projeto_pesquisa_resolved`) + **todas as ações do SRC** (`vfact_extensao_acao_resolved`, **sem** filtrar `tipo_acao` nem `natureza`). **NUNCA** some `vfact_orientacao_bolsa_resolved` na conta de projetos.
> - **`"projetos de pesquisa"`:** retorne via `UNION ALL` (sem cruzamento/`JOIN`) **Projetos de Pesquisa (SigPesq)** (`vfact_projeto_pesquisa_resolved`) + ações do SRC com `natureza LIKE 'Pesquisa' AND tipo_acao LIKE 'Projeto'` (`vfact_extensao_acao_resolved`). *(Em consultas que pedem colunas exclusivas do SigPesq como `flag_projeto_completo`, `natureza_projeto` ou `parecer_diretoria`, consulte diretamente `vfact_projeto_pesquisa_resolved`.)*
> - **`"projetos de extensão"`:** retorne **todas as ações** de `vfact_extensao_acao_resolved` com `natureza LIKE 'Extensão'` (sem filtrar `tipo_acao`).
> - **`"projetos"` que uma pessoa específica participou (cruzamento):** retorne via `UNION ALL` os **Projetos de Pesquisa** em `vfact_projeto_pesquisa_resolved` (`coordenador_nome LIKE ...`) + **todas as ações** de `vfact_extensao_acao_resolved` (coordenador em `vfact_extensao_acao_resolved.coordenador_nome` ou participante via `vfact_extensao_participacao_resolved.nome_participante`, deduplicando por `id_acao`, **sem** filtrar `tipo_acao`).

---

## 1. As 6 Views Fato (Grão e Regras de Negócio)

1. **`vfact_extensao_acao_resolved` (1 Ação no SRC por linha — `id_acao`)**
   - Contém 4 naturezas em `natureza`: `'Extensão'`, `'Ensino'`, `'Pesquisa'` e `'Desenv. Institucional'`.
   - **Domínio exclusivo de `"ações"` (estritamente SRC — nunca consultar SigPesq):**
     - **`"ação"` / `"ações"` (solto):** **NUNCA** filtre `natureza` nem `tipo_acao` — entregue todas as ações de `vfact_extensao_acao_resolved` (`COUNT(DISTINCT id_acao)`).
     - **`"ação de extensão"` ou `"projeto de extensão"`:** entregue todas as ações de `vfact_extensao_acao_resolved` com **`natureza LIKE 'Extensão'`** (sem filtrar `tipo_acao`, salvo quando pedirem explicitamente `'Curso'`, `'Evento'`, `'Programa'` ou `'Prestação de Serviço'`).
     - **`"ação de pesquisa"`:** entregue todas as ações de `vfact_extensao_acao_resolved` com **`natureza LIKE 'Pesquisa'`**.
     - **`"ação de <natureza>"`** (ex.: `"ação de ensino"`, `"ação de desenvolvimento institucional"`): entregue todas as ações de `vfact_extensao_acao_resolved` com **`natureza LIKE '<natureza>'`** (ex.: `natureza LIKE 'Ensino'`).
   - **Relatório aprovado:** `flag_relatorio_aprovado = 1`. **`campus` e `orgao_fomento`:** pré-agregados com `; ` — nesta view use **`LIKE '%Termo%'`** (ex.: `campus LIKE '%Serra%'`). **Sem valores R$**.

2. **`vfact_extensao_participacao_resolved` (1 Participação em Atividade do SRC por linha — `id_participacao`)**
   - Use para **público atendido, participantes, inscritos, certificados (`flag_certificado = 1`), aprovação (`flag_aprovado = 1`) e `carga_horaria`**.
   - **Grão N:N:** total de participações/certificados = `COUNT(*)`; **pessoas distintas** = `COUNT(DISTINCT nome_participante)`.
   - **Limite da base:** registra coordenadores (`vfact_extensao_acao_resolved.coordenador_nome`) e participantes (`nome_participante`), mas **não** possui `"equipe de execução"`.

3. **`vfact_projeto_pesquisa_resolved` (1 Projeto de Pesquisa SigPesq por linha — `id_projeto`)**
   - Use para **projetos de pesquisa**, parecer (`flag_aprovado = 1` ou `parecer_diretoria = 'APROVADO'`), natureza (`'PESQUISA_APLICADA'` vs `'PESQUISA_BASICA'`), origem (`origem_registro`: `'CADASTRO_COMPLETO_SIGPESQ'` vs `'INFERIDO_DE_ORIENTACAO'`; `flag_projeto_completo`: `1` vs `0`), `parceiros_demandantes` e `coordenador_nome`.
   - Para **"projetos de pesquisa"**, conte todos (`COUNT(DISTINCT id_projeto)`) sem filtrar `flag_projeto_completo = 1` nem `natureza_projeto IS NOT NULL` (salvo se pedido).
   - **Registros inferidos (`flag_projeto_completo = 0`):** têm `coordenador_nome`, `natureza_projeto`, `parecer_diretoria`, `data_inicio`, `data_fim`, `ano_inicio` e `ano_fim` como `NULL`.

4. **`vfact_orientacao_bolsa_resolved` (1 Concessão de Orientação/Bolsa por linha — `id_orientacao`)**
   - **Bolsas vs. Orientações vs. Voluntários:** todo registro é uma **orientação** dividida por `modalidade`:
     - **"Orientações" / "orientandos" / "planos de trabalho"** → **não** filtra `modalidade` (`'BOLSISTA'` + `'VOLUNTARIO'`).
     - **"Bolsas" / "bolsistas" / "cotas de bolsa"** → **filtra `modalidade = 'BOLSISTA'`** (obrigatório em contagens de bolsas e médias financeiras, pois voluntários têm valor `0.0`).
     - **"Voluntários"** → **filtra `modalidade = 'VOLUNTARIO'`**.
   - **Valores reais:** `programa_fomento` é minúsculo com underscore (`'pibic'`, `'pibic_jr'`, `'pibiti'`, `'pivic'`, `'pibic_em'`, `'pibic_af'`, `'propos'`, etc.) — use `LOWER(programa_fomento) = 'pibic_em'` (nunca `'PIBIC-EM'`). `nivel_treinamento_aluno` é maiúsculo com underscore (`'GRADUACAO'`, `'ENSINO_MEDIO_2O_GRAU'`, `'MESTRADO'`, `'ESPECIALIZACAO'`).
   - **Cancelamentos e vigência:** pessoas = `COUNT(DISTINCT nome_orientado)`; registros = `COUNT(DISTINCT id_orientacao)`. Geral: `flag_cancelado = 1`. **Antecipadamente / antes do fim / antes do prazo:** `flag_cancelado = 1 AND data_cancelado IS NOT NULL AND data_fim IS NOT NULL AND julianday(data_cancelado) < julianday(data_fim)`. **Vigentes/ativas:** `flag_cancelado = 0` (e `data_fim >= date('now')` se foco for vigência atual).
   - **Financeiro e duração:** `SUM(investimento_total_estimado)` (já desconta cancelamentos; `investimento_previsto_original` é o previsto integral; `valor_bolsa_mensal` é a cota mensal) e `AVG(duracao_meses_efetiva)`. Trate valores R$ sempre como **estimativa calculada** (não há folha de pagamento). **Não existe coluna de coorientador**.

5. **`vfact_producao_cientifica_resolved` (1 Autoria Lattes por linha — `id_producao` + `id_pessoa_lattes`)**
   - Use para **publicações, artigos (`flag_artigo_periodico = 1`), livros/capítulos (`tipo_macro_producao = 'LIVRO_OU_CAPITULO'`), softwares registrados (`flag_patente_software = 1`), softwares sem patente (`flag_software_sem_patente = 1`) e `veiculo_publicacao`**.
   - **Obras vs. Autorias vs. Autores:** **obras únicas** = `COUNT(DISTINCT id_producao)` (nunca `SUM(flag_obra_unica)` com filtro de campus/autor); **autorias** = `COUNT(*)` ou `SUM(qtd_autorias)`; **autores distintos** = `COUNT(DISTINCT nome_autor)`; **autor único** = `id_producao IN (SELECT id_producao FROM vfact_producao_cientifica_resolved GROUP BY id_producao HAVING COUNT(DISTINCT id_pessoa_lattes) = 1)`.
   - **Bibliográficas:** `tipo_macro_producao IN ('ARTIGO_OU_EVENTO', 'LIVRO_OU_CAPITULO')`.
   - **Campus:** `'Externo / Não Vinculado'` indica autor externo (`instituicao_vinculo`). Para autores do Ifes, filtre `campus NOT LIKE 'Externo%'`. Considere que há registros com `ano IS NULL` (`COALESCE(CAST(ano AS TEXT), 'Sem Ano')` quando solicitado).

6. **`vfact_grupo_pesquisa_membro_resolved` (1 Vínculo de Membro em Grupo CNPq por linha — `id_membro_grupo`)**
   - Use para **Grupos CNPq**, `situacao_grupo` (`'CERTIFICADO'`, `'CERTIFICADO_NAO_ATUALIZADO'`, `'EM_PREENCHIMENTO'`, `'EXCLUIDO'`; para certificados use `situacao_grupo LIKE 'CERTIFICADO%'`), líderes (`flag_lider = 1`), status (`'ATIVO'`/`'EGRESSO'`, `flag_ativo = 1`), papel (`'Pesquisador'`, `'Estudante'`, `'Técnico'`, `'Membro'`) e `tempo_participacao_dias`.
   - **Grupos distintos:** `COUNT(DISTINCT id_grupo_pesquisa)` (em `GROUP BY` por grupo, inclua sempre `id_grupo_pesquisa, nome_grupo`).
   - **Pessoas vs. Vínculos:** pessoas/integrantes distintos = `COUNT(DISTINCT nome_membro)`; membros ativos por grupo/papel = filtre `WHERE flag_ativo = 1` e use `COUNT(*)` (com `COUNT(DISTINCT nome_membro)` em paralelo se pedido).
   - **Papéis (`"pesquisadores"` = SEMPRE esta view):** filtre com `LIKE` (`papel_membro LIKE 'Pesquisador'`, `'Estudante'`, `'Técnico%'`). **Nunca** use `coordenador_nome` ou `nome_orientador` para contar `"pesquisadores"`.

---

## 2. Mapa de Papéis, Pesquisa Ampla e Perfil de Pessoa

| Termo na pergunta | Regra exata |
|---|---|
| **`projetos`** (solto) | `UNION ALL` (sem cruzamento): `vfact_projeto_pesquisa_resolved` (SigPesq) + **todas as ações** de `vfact_extensao_acao_resolved` (SRC, sem filtrar `tipo_acao`/`natureza`). Nunca somar orientações. |
| **`projetos de pesquisa`** | `UNION ALL` (sem cruzamento): `vfact_projeto_pesquisa_resolved` (SigPesq) + `vfact_extensao_acao_resolved WHERE natureza LIKE 'Pesquisa' AND tipo_acao LIKE 'Projeto'`. |
| **`projetos de extensão`** | **Todas as ações** de `vfact_extensao_acao_resolved WHERE natureza LIKE 'Extensão'` (sem filtrar `tipo_acao`). |
| **`ações`** (solto) | **Todas as ações** de `vfact_extensao_acao_resolved` (estritamente SRC, sem filtrar `natureza`, nunca SigPesq). |
| **`ações de extensão` / `pesquisa` / `<tal_coisa>`** | `vfact_extensao_acao_resolved WHERE natureza LIKE '<natureza>'` (ex.: `'Extensão'`, `'Pesquisa'`, `'Ensino'`). |
| **`projetos` de uma pessoa** | Cruzamento por pessoa via `UNION ALL`: `vfact_projeto_pesquisa_resolved` (`coordenador_nome`) + todas as ações de `vfact_extensao_acao_resolved` (`coordenador_nome` / `vfact_extensao_participacao_resolved.nome_participante`, sem filtrar `tipo_acao`). |
| **`pesquisa`** (ampla, ex.: *"panorama de pesquisa no campus X"*) | `UNION ALL` rotulado: Projetos de Pesquisa + Grupos CNPq + Orientações/Bolsas + Produção Científica (Lattes) + Ações do SRC com `natureza LIKE 'Pesquisa'`. Se específica (*"projetos de pesquisa"*), consulte só a view pedida. |
| **`extensionistas`** | Coordenadores (`vfact_extensao_acao_resolved.coordenador_nome`) + participantes (`vfact_extensao_participacao_resolved.nome_participante`) via `UNION` (total único) ou `UNION ALL` (detalhado). |
| **`coordenadores`** | Qualificado → só a view pedida (`pesquisa` ou `extensão`). Sem qualificar → `UNION ALL` das duas. |
| **`pesquisadores`** (sem qualificar) | `vfact_grupo_pesquisa_membro_resolved WHERE papel_membro LIKE 'Pesquisador'`. |
| **`autores`** / **`orientadores`** / **`líderes`** | `nome_autor` (Lattes) / `nome_orientador` (Bolsas) / `flag_lider = 1` (CNPq). |
| **2 papéis juntos** (ex.: *"pesquisadores e coordenadores"*) | **Proibido** colunas paralelas roubando papéis. Use `UNION ALL` rotulado na view correta de cada papel. |
| **`docentes / professores / servidores`** | Não existe cadastro de RH/cargo; informe o limite e use o papel acadêmico do contexto. |

- **Perfil / Currículo / Projetos de uma pessoa (`"atuação / projetos de [Nome]"`):** **nunca** use `=` nem `IN (...)` para nomes próprios — use `LIKE` por partes (`col LIKE '%João%' AND col LIKE '%Silva%'`). Consolide as 6 views via `UNION ALL` rotulado por frente (`Projetos de Pesquisa (SigPesq)`, `Ações/Projetos no SRC (Coordenador)`, `Participações no SRC`, `Orientações (Orientador)`, `Orientações (Orientando)`, `Produções Científicas (Lattes)`, `Grupos de Pesquisa (CNPq)`), **nunca misturando orientações na conta de projetos**.

---

## 3. Matriz Rígida de Cruzamento e Regras Transversais

| Dimensão de cruzamento | Chaves oficiais | Cuidado obrigatório |
|---|---|---|
| **Extensão Ação ↔ Participação** | `id_acao` | Agregar cada view em `CTE` antes de `JOIN`. |
| **Pessoa entre bases** | `LOWER(TRIM(col_nome))` (`coordenador_nome`, `nome_participante`, `nome_orientador`, `nome_autor`, `nome_membro`) | Agregar em `CTE` antes de `JOIN`; não existe `id_pessoa` unificado. |
| **Grande Área** | `grande_area` | Excluir `IS NULL OR TRIM(grande_area) = '' OR grande_area = 'Não Informada'` quando pedir área válida. |
| **Campus** | `campus` | Fora do SRC tem valor único (`campus LIKE 'Serra'`, sem `%`); no SRC Ações vem com `; ` (`LIKE '%Serra%'`). |
| **Ano** | `ano_cadastro` (SRC Ações), `ano_participacao` (SRC Part.), `ano_inicio` (Projetos), `ano` (Bolsas e Lattes), `ano_formacao` (CNPq) | Nunca fazer `JOIN` direto entre views fato sem `CTE` agregada (anti-*fan-out*). |

- **Proibição de cruzamento direto Projetos × Orientações:** nunca faça `JOIN` direto entre `vfact_projeto_pesquisa_resolved` e `vfact_orientacao_bolsa_resolved` sem `CTE` agregada nem some `id_orientacao` como se fosse projeto.
- **Filtro `"no IFES"` e `LIKE`:** nunca filtre `campus LIKE 'Ifes'` (a base inteira é do IFES; no Lattes use `campus NOT LIKE 'Externo%'`). O `LIKE` do Adito é case-insensitive e acento-insensível (`_` é curinga de 1 caractere).
- **Sinônimos e histórico:** *"parecer favorável"* → `flag_aprovado = 1`; *"softwares sem patente"* → `flag_software_sem_patente = 1`; *"grupos excluídos"* → `situacao_grupo = 'EXCLUIDO'`. `"já"` / `"ao todo"` trazem histórico completo; só filtre ativos (`flag_ativo = 1`, `flag_cancelado = 0`, `situacao_grupo <> 'EXCLUIDO'`) quando pedido explicitamente.
- **Rankings e datas:** exclua `'Sem Parceiro Demandante'` / `'Recurso Próprio / Sem Fomento'` em rankings de parceiros/fomentos; use `ORDER BY metrica DESC, nome ASC`; para `"ano passado"`, use `CAST(strftime('%Y','now') AS INTEGER) - 1`.
- **Valores ausentes (`NULL` real vs. texto padronizado):**
  - **Texto padronizado:** `grande_area`/`area_conhecimento` no SRC, `titulacao_coordenador` (Projetos), `titulacao_membro` (Grupos) = `'Não Informada'`; `orgao_fomento` = `'Recurso Próprio / Sem Fomento'`; `parceiros_demandantes` = `'Sem Parceiro Demandante'`; `programa_fomento` = `'Não Especificado'`; `titulo_edital` = `'Sem Edital Vinculado'`; `agencia_financiadora` = `'Recurso Institucional Ifes'`; `campus` = `'Não Informado'`, `'Campus Não Informado'` ou `'Externo / Não Vinculado'` (Lattes).
  - **`NULL` real:** Projetos (`coordenador_nome`, `natureza_projeto`, `parecer_diretoria`, datas/anos, `duracao_meses_prevista`, `grande_area`, `palavras_chave`); Bolsas (`titulacao_orientador`, `nivel_treinamento_aluno`, `curso_orientado`, `nome_cancelador`, `data_cancelado`); Produções (`ano`, `veiculo_publicacao`, `doi`, `issn_isbn`, `natureza_artigo`); Grupos (`sigla_grupo`, `grande_area`, `data_inicio`, `data_fim`, `tempo_participacao_dias`).
  - Para **"sem X informado"**, combine `col IS NULL OR TRIM(col) = ''` com o texto padronizado aplicável.
