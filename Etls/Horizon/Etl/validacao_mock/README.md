# Validação do ETL do Horizon com dados mock (issue #5)

Kit para validar o pipeline PostgreSQL do Horizon (`src/core/logic/carga`) com
**300 registros fictícios**, sem acessar SigPesq, Lattes ou CNPq de verdade.

Coloque esta pasta em `Etls/Horizon/Etl/validacao_mock/`.

## Conteúdo

| Arquivo | Para quê |
|---|---|
| `gerar_mocks.py` | Gera os 300 registros (semente fixa) e o `gabarito.json` com o estado esperado do banco |
| `executar_etl_mock.py` | Roda `executar_carga` (mesmo núcleo do flow `horizon_postgres --sem-download`) com os mocks |
| `validar_carga.py` | Compara o banco com o gabarito, registro a registro (OK / FALHA / ALERTA) |
| `fake_cnpq/dgp_cnpq_lib.py` | Troca só a leitura do site do CNPq pela leitura de `dados/cnpq_espelhos/`; o `CnpqCrawlerAdapter` real continua sendo usado |
| `comum.py` | Normalizações compartilhadas (nomes, textos, datas) |
| `dados/` | Massa gerada: planilhas do SigPesq, JSONs do Lattes, espelhos do CNPq, `catalogo_registros.csv` e `gabarito.json` |
| `resultados/` | Saída das execuções e da validação |
| `RELATORIO_VALIDACAO.md` | Relatório da validação (texto para o comentário da issue) |

## Massa de dados

| Fonte | Formato | Válidos | Exceções | Total |
|---|---|---:|---:|---:|
| SigPesq – grupos | `sigpesq/research_group/*.xlsx` | 23 | 5 | 28 |
| SigPesq – projetos | `sigpesq/research_projects/*.xlsx` | 61 | 16 | 77 |
| SigPesq – bolsistas | `sigpesq/advisorships/<ano>/*.xlsx` (3 arquivos) | 96 | 24 | 120 |
| Lattes – currículos | `lattes_json/<nome>_<id>.json` | 40 | 10 | 50 |
| CNPq – espelhos de grupo | `cnpq_espelhos/*.json` | 20 | 5 | 25 |
| **Total** | | **240** | **60** | **300** |

O cenário de cada registro está em `dados/catalogo_registros.csv`. Nomes, e-mails
(`@ifes.mock`), IDs Lattes (começam com 9) e URLs são inventados.

## Atalhos no Makefile

Para ativar (rode **uma vez só**, na pasta `Etls/Horizon/Etl`):

```bash
cat validacao_mock/mock.mk >> Makefile
```

| Comando | O que faz |
|---|---|
| `make mock-carregar` | Sobe o banco, gera os 300 registros, carrega e valida |
| `make mock-psql` | Abre o psql já dentro do schema `mock_validacao` |
| `make mock-psql-sonda` | Abre o psql no schema `mock_completa` (carga interrompida pela L50) |
| `make mock-resumo` | Imprime contagens e os defeitos C1–C4 direto do banco (`consultas_mock.sql`) |

## Como rodar (passo a passo, sem os atalhos)

Pré-requisitos: dependências do ETL instaladas (`make setup`) e o PostgreSQL do
Horizon no ar (`make horizon-db-up`, porta 5434).

```bash
cd Etls/Horizon/Etl/validacao_mock
export HORIZON_DATABASE_URL=postgresql://horizon:horizon@localhost:5434/horizon

# 1. gerar a massa (já vem gerada; rode de novo para atualizar as datas esperadas)
../.venv/bin/python gerar_mocks.py --saida dados

# 2. carga principal (299 registros) no schema mock_validacao
../.venv/bin/python executar_etl_mock.py --schema mock_validacao

# 3. carga com o currículo-sonda (L50), que interrompe o Lattes, no schema mock_completa
../.venv/bin/python executar_etl_mock.py --schema mock_completa --com-sonda

# 4. validação
../.venv/bin/python validar_carga.py --schema mock_validacao --schema-sonda mock_completa
```

Os schemas `mock_validacao` e `mock_completa` são apagados e recriados a cada
execução; o schema `public` não é tocado.

**Datas:** a situação esperada (`em_andamento`/`concluida`) depende do dia em
que o gabarito foi gerado. Se for validar em outro dia, gere a massa de novo
(passo 1) — a semente fixa produz os mesmos registros.

## Como ler o resultado

* `resultados/resultado_validacao.csv` – uma linha por verificação, com registro,
  cenário, status, regra (`documentada` = docstrings do ETL; `negocio` = regra de
  negócio mais clara que o código) e causa (C1–C5).
* `resultados/resultado_validacao.json` – o mesmo, mais o resumo por registro.
* `resultados/execucao_*.json` – relatório da carga gerado pelo próprio ETL
  (`RelatorioCarga`), status da execução e traceback, se houver.
