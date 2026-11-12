# Ambiente PostgreSQL — Modelo Unificado (Oraculo)

Este diretório contém a infraestrutura em Docker e os scripts SQL para provisionar o banco de dados PostgreSQL com o schema relacional unificado extraído do modelo de classes Astah (`ModeloClassesUnificado.asta`).

---

## 🚀 Como Subir o Banco

Na raiz deste diretório (`Adito/scripts/`):

### 1. Inicialização Automática e Validação
```bash
./recriar_banco.sh
```
O script:
1. Carrega o `.env` (porta padrão: `5435`).
2. Sobe o container `oraculo_postgres_unificado`.
3. Executa os scripts da pasta `sql/` na ordem correta (`00` a `99`).
4. Imprime o relatório de validação das tabelas e chaves criadas.

### 2. Ou via Docker Compose padrão
```bash
docker compose up -d
```

---

## 🔌 Conexão

| Parâmetro | Valor Padrão |
| :--- | :--- |
| **Host** | `localhost` |
| **Porta** | `5435` |
| **Database** | `oraculo_db` |
| **Usuário** | `oraculo` |
| **Senha** | `oraculo_password` |
| **Schema Padrão** | `unificado` |

Comando para conectar via `psql` direto no container:
```bash
docker compose exec -it oraculo-postgres psql -U oraculo -d oraculo_db
```

---

## 📁 Estrutura dos Scripts SQL

* `sql/00_schema.sql`: Cria o schema `unificado` e configura o `search_path`.
* `sql/01_tipos_e_dominios.sql`: Define os 16 tipos `ENUM` nativos e cria/popula as 14 tabelas de domínio.
* `sql/02_tabelas.sql`: Cria todas as tabelas de entidades de negócio, aplicando herança com chaves primárias e estrangeiras alinhadas.
* `sql/03_relacionamentos_e_juncoes.sql`: Cria classes associativas (com `id`), tabelas de junção N:N puras (sem `id`) e índices de alta performance em FKs.
* `sql/99_validacao.sql`: Consultas de auditoria (contagem de tabelas, colunas, enums e domínios).

---

## 📥 Popular com os dados do ETL do Adito

`popular_banco.py` (só Python padrão, sem dependências) lê a pasta `Adito/etl/`, com `brutos/` de cada fonte e `trabalho/pessoas.json` do cruzamento. Ele gera um SQL só de `INSERT`, numa transação, e executa esse SQL com o `psql` do container.

```bash
docker compose up -d                                  # banco vazio
python3 popular_banco.py                               # lê ../etl (Adito/etl)
python3 popular_banco.py --so-gerar                    # só gera o SQL e o relatório
```

- **Estrutura intacta:** não altera o banco (nada de CREATE, ALTER, DROP ou TRUNCATE). Se já houver dados, a carga para sem gravar nada; para recarregar, rode `./recriar_banco.sh` antes.
- **Tabelas de domínio:** as do `01_tipos_e_dominios.sql` não recebem linhas novas. Valor fora delas ou fora de um ENUM vira NULL e aparece no relatório.
- **Pessoas:** uma linha em `pessoa` por pessoa do cruzamento (nome normalizado, regras do horizon_etl). O banco não tem CPF nem e-mail de pessoa (colunas removidas do DDL); telefone e fax não vêm do ETL e ficam vazios; endereço profissional (Lattes, sem telefone) e o endereço do grupo (CNPq) entram. Sexo e data de nascimento não existem mais no banco. Antes de executar, o SQL é conferido contra e-mail e CPF.
- **`pessoa_lattes`:** além dos titulares de currículo, tem linhas sem dados para quem só aparece num currículo (integrante de projeto, orientando, aluno de banca), porque as tabelas do Lattes exigem `pessoa_lattes`.
- **Orientações sem projeto:** a orientação do SigPesq cujo projeto não está no relatório de projetos ganha um `projeto_pesquisa` mínimo (só título).
- **Onde ficam as saídas:** o SQL e o relatório (`carga_banco.sql`, `carga_banco_relatorio.json`) vão para `<etl>/saida/`, fora deste repositório, porque têm nomes de pessoas.
- **Ligações inferidas (documentadas):** a ação do SRC só traz a grande área, então `acao.id_area_conhecimento` aponta para uma área com o nome da grande área; o Ifes e seus campi, em qualquer grafia das fontes, viram uma única organização (campus com `id_organizacao_pai` = Ifes); líder de grupo do SigPesq ganha a unidade do grupo, coordenador de projeto o campus do projeto e orientado sem campus o campus de execução; o nível do bolsista sai do programa (Pibic-Jr/EM = ensino médio, demais = graduação) quando o CNPq não informa.
- **CNPq:** grupo no DGP (situação, datas, repercussões, endereço e site), membros ativos e egressos, líderes, linhas de pesquisa e grande área, para os grupos que também estão no SigPesq.

---

## 📤 Exportar JSON para o DuckDB

`exportar_json.py` (apenas biblioteca padrão do Python 3.10+) lê o schema `unificado` do PostgreSQL em modo estritamente somente leitura (`BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY; ... ROLLBACK;`) e gera em `Adito/etl/saida/json/` um arquivo `<tabela>.json` por tabela usada pelas views analíticas de `Docs/Fatos/PropostaFatos.md`, além de `manifesto.json`.

### Por que exporta tabelas e não as views
O PostgreSQL continua sendo a base relacional oficial em 3ª Forma Normal (3FN). O aplicativo desktop ("Oráculo") consultará seis views analíticas desnormalizadas (`vfact_*_resolved`) em um **DuckDB embutido**, sem depender de servidor PostgreSQL. Por isso, `exportar_json.py` exporta uma fotografia consistente das **tabelas base** (com mesmas colunas, mesmos IDs e chaves estrangeiras coerentes entre si) e um manifesto de schema; as views serão recriadas diretamente no DuckDB de destino.

### Pré-requisitos e modos de execução
O banco `unificado` já deve estar criado (`./recriar_banco.sh`) e populado (`python3 popular_banco.py`). Se o banco estiver vazio ou faltar alguma tabela da lista, o script para e avisa sem criar nem alterar nada.

1. **Modo `docker` (padrão):** executa `docker compose exec -T <servico> psql ...` lendo serviço, banco e usuário de `Adito/scripts/docker-compose.yml` (e `.env` / `.env.example`):
   ```bash
   python3 Adito/scripts/exportar_json.py
   python3 Adito/scripts/exportar_json.py --forcar
   python3 Adito/scripts/exportar_json.py --tabelas pessoa,organizacao,acao --saida /caminho/saida/json
   ```
2. **Modo `conexao`:** usa um cliente `psql` local apontando para qualquer PostgreSQL com o schema `unificado`, configurado pelas variáveis padrão da `libpq` (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` e `.pgpass` / variável de ambiente de sessão):
   ```bash
   PGHOST=localhost PGPORT=5435 PGDATABASE=oraculo_db PGUSER=oraculo \
     python3 Adito/scripts/exportar_json.py --modo conexao --forcar
   ```
3. **Somente validação (`--so-validar`):** revalida uma pasta já exportada (JSON válido, contagens, ordem das colunas e integridade referencial das FKs) sem conectar ao PostgreSQL:
   ```bash
   python3 Adito/scripts/exportar_json.py --so-validar Adito/etl/saida/json
   ```

### Lista de tabelas (41 tabelas) e como atualizar
A lista de tabelas vem de `Docs/Fatos/PropostaFatos.md` (commit `c91761a`), agrupada na constante `TABELAS_POR_VIEW` em `exportar_json.py` (40 tabelas referenciadas nos blocos `CREATE OR REPLACE VIEW` mais `parceiro_demandante_projeto`, citada no texto da seção 3.3.3):

| View | Tabelas usadas |
| :--- | :--- |
| `vfact_extensao_acao_resolved` | `acao`, `acao_campus`, `area_conhecimento`, `atividade`, `fomento_acao`, `grande_area`, `iniciativa`, `natureza`, `organizacao`, `pessoa`, `tipo_acao` |
| `vfact_extensao_participacao_resolved` | `acao`, `acao_campus`, `atividade`, `iniciativa`, `organizacao`, `pessoa`, `registro_participante`, `situacao_participante`, `tipo_acao`, `tipo_atividade` |
| `vfact_projeto_pesquisa_resolved` | `area_conhecimento`, `grande_area`, `iniciativa`, `organizacao`, `parceiro_demandante_projeto`, `pesquisador`, `pessoa`, `plano_trabalho`, `projeto_pesquisa`, `titulacao` |
| `vfact_orientacao_bolsa_resolved` | `area_conhecimento`, `curso`, `edital`, `estudante`, `grande_area`, `iniciativa`, `nivel_treinamento`, `organizacao`, `orientacao`, `pesquisador`, `pessoa`, `plano_trabalho`, `programa`, `projeto_pesquisa`, `titulacao` |
| `vfact_producao_cientifica_resolved` | `artigo_trabalho_evento`, `autoria_producao`, `categoria_producao_tecnica`, `livro_capitulo`, `organizacao`, `patente_registro`, `pesquisador`, `pessoa`, `pessoa_lattes`, `producao`, `producao_tecnica_artistica_bibliografica`, `tipo_artigo_evento`, `tipo_livro_capitulo`, `tipo_patente_registro` |
| `vfact_grupo_pesquisa_membro_resolved` | `area_conhecimento`, `grande_area`, `grupo_pesquisa`, `grupo_pesquisa_cnpq`, `membro_grupo`, `membro_grupo_cnpq`, `organizacao`, `papel`, `pesquisador`, `pessoa`, `titulacao` |

Quando `Docs/Fatos/PropostaFatos.md` mudar, atualize `TABELAS_POR_VIEW` e `PROPOSTA_COMMIT` em `exportar_json.py`, confira as views com `BEGIN; ...; ROLLBACK;` e rode a suíte de testes (`cd Adito/etl && .venv/bin/python -m pytest`).

### Formato dos arquivos, do `manifesto.json` e conversão de tipos
- **`<saida>/<tabela>.json`:** lista JSON UTF-8 de objetos (`[{"id": 1, "nome": "Maria Exemplo"}, ...]`), ordenada pela chave primária descoberta em `pg_catalog` (ou por todas as colunas quando não há PK) e gravada atomicamente via arquivo temporário + rename. Tabela vazia sai como `[]`.
- **`<saida>/manifesto.json`:** registra `gerado_em` (ISO 8601), `commit` (`git rev-parse HEAD`), `proposta` (`arquivo` e `commit`), `postgres` (`SHOW server_version`), `schema` (`"unificado"`) e, para cada tabela exportada, `linhas`, `colunas` (`nome`, `tipo` de `format_type`, `anulavel` e `valores_enum` quando ENUM), `chave_primaria` e `chaves_estrangeiras` (`coluna`, `tabela_destino`, `coluna_destino` e `destino_exportado`).

| Tipo no PostgreSQL | No JSON (`json_agg`) |
| :--- | :--- |
| `text`, `varchar`, `ENUM` | string (o `ENUM` sai pelo rótulo, ex.: `"BOLSISTA"`) |
| `integer`, `bigint` | número inteiro |
| `numeric(12,2)` | número com as casas decimais do banco (ex.: `700.00`); o tipo exato vai no manifesto |
| `boolean` | `true` / `false` |
| `date` | string ISO `"YYYY-MM-DD"` |
| `timestamp` / `timestamptz` | string ISO 8601 |
| arrays (`text[]` etc.) | lista JSON |
| `NULL` | `null` |

### Aviso de LGPD
Os arquivos exportados contêm nomes de pessoas (`pessoa.json`, `orientacao.json`). **A saída nunca vai para o git:**
- Antes de gravar qualquer arquivo, `exportar_json.py` executa `git check-ignore -q <saida>/x.json` e aborta caso a pasta não esteja ignorada pelo git.
- Depois de gravar, o script varre todos os JSONs em busca de formatos de CPF ou e-mail; se encontrar qualquer ocorrência, apaga os arquivos gerados e aborta exibindo apenas o nome da tabela e da coluna (nunca o valor).

### Exemplo ilustrativo de leitura no DuckDB
De forma apenas ilustrativa, o DuckDB consegue ler diretamente cada arquivo exportado com `read_json`:

```sql
CREATE TABLE acao AS SELECT * FROM read_json('acao.json', format='array');
```

> **Nota:** o carregamento definitivo no pacote do DuckDB deve utilizar os tipos exatos, chaves primárias e chaves estrangeiras declarados em `manifesto.json` (especialmente para tabelas vazias como `patente_registro` e colunas `numeric`, `date` e `ENUM`), e não apenas a inferência automática do `read_json`.
