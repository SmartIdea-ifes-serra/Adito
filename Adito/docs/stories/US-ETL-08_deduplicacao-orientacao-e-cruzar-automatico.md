# User Story: [US-ETL-08] Deduplicação de orientações na carga e `etl-cruzar` automático no `make db`

**Epic:** Refatoração de Carga ETL e das 6 Views Analíticas
**GitHub Epic Issue:** -
**GitHub US Issue:** #138
**Prioridade:** Alta
**Story Points:** 3
**Sprint:** 02
**Status:** Review
**Behavior Change Esperado:** YES

---

## Historia

**Como** mantenedor da base analítica do Adito
**Eu quero** que `popular_banco.py` deduplicar registros de `orientacao` por `id_origem` (preservando o estado do ano mais recente) e que `make db` execute `etl-cruzar` automaticamente sempre que houver arquivos em `brutos/` mais novos que `pessoas.json`
**Para que** o `dados.db` reflita 100% das extrações sem duplicar bolsas/investimentos nem descartar pessoas silenciosamente

### Contexto Adicional

- **Discovery:** `Adito/docs/discovery/refatoracao-etl-views-analiticas.md` (`PROBLEM_READY`)
- **Requirements:** `Adito/docs/requirements/refatoracao-etl-views-analiticas.md` (`REQUIREMENTS_READY` — `FR01`, `FR02`, `FR08`, `NFR02`, `NFR03`, `A02`, `KD01`)
- No SigPesq, bolsas que atravessam a virada do ano (ex.: set/2025 a ago/2026) aparecem nos dois arquivos anuais (`2025.json` e `2026.json`). Hoje `popular_banco.py` usa `self.novo("orientacao", ...)` sem deduplicar `id_origem`, duplicando linhas e valores de investimento.
- Hoje `make db` reaproveita `Adito/etl/trabalho/pessoas.json` se ele existir, mesmo quando há novas extrações em `Adito/etl/brutos/`, fazendo `popular_banco.py` descartar silenciosamente pessoas novas e seus registros.

### Pontos de Esclarecimento

Nenhum ponto pendente.

---

## Criterios de Aceitacao

- [ ] **Criterio 1:** Ao carregar múltiplos arquivos anuais de `brutos/sigpesq/orientacoes/` contendo o mesmo `Id`, a tabela `orientacao` no SQLite contém no máximo **1 linha por `id_origem`**, mantendo os campos atualizados (`cancelado`, `nome_cancelador`, `data_cancelado`, `relatorio_enviado`, etc.) da ocorrência mais recente (`FR01`, `KD01`).
- [ ] **Criterio 2:** A validação pós-carga em `popular_banco.py` (`validar_sanidade_banco`) garante que não há `id_origem` duplicado em `orientacao` quando `id_origem IS NOT NULL`.
- [ ] **Criterio 3:** No `Makefile`, `make db` executa `adito-etl cruzar` automaticamente quando `Adito/etl/trabalho/pessoas.json` não existe **ou** quando qualquer arquivo regular em `Adito/etl/brutos/` tem data de modificação mais recente que `pessoas.json`; caso contrário, reutiliza `pessoas.json` para carga rápida (`FR02`).
- [ ] **Criterio 4:** Existe teste automatizado cobrindo deduplicação de `orientacao` por `id_origem` (incluindo atualização de estado entre anos), e a validação com `brutos/` locais roda em banco temporário sem alterar `~/Downloads/dados.db` nem sobrescrever a cópia completa com Lattes em `Adito/app/data/dados.db` (`NFR01`, `NFR02`).

---

## Governanca e Rastreabilidade

- **Nivel ScrumAIDev:** 1
- **Justificativa do nivel:** Altera comportamento observável da carga local de dados (`popular_banco.py` e `Makefile`), sem novo boundary de API HTTP/RPC externo.
- **US exige Spec governada?** Nao
- **Justificativa da Spec:** US nao exige Spec — regras determinísticas já estão documentadas em `Adito/docs/requirements/refatoracao-etl-views-analiticas.md`.
- **Spec prevista:** N/A
- **US exige Contract governado?** Nao
- **Justificativa do Contract:** US nao exige Contract — não altera contratos RPC/HTTP nem schemas de API externa.
- **Contract previsto:** N/A
- **Padrao de erro aplicavel:** N/A
- **BDD previsto:** N/A
- **Gates opcionais aplicaveis:** N/A
- **Touch List preliminar:** `Adito/scripts/popular_banco.py`, `Makefile`, `Adito/app/backend/nucleo/core/tests.py` (ou teste dedicado do ETL/carga)
- **Task Issues previstas:** #138

---

## Notas Tecnicas

### Arquitetura

- **Componentes afetados:** `Adito/scripts/popular_banco.py` (método `sigpesq` + `validar_sanidade_banco`), `Makefile` (alvo `db`), testes unitários.
- **APIs necessarias:** N/A
- **Database changes:** Sem alteração de schema de tabela base; correção de deduplicação na população da tabela `orientacao`.
- **Referencias do modelo de dados:** `Adito/scripts/sql/02_tabelas.sql`
- **Erros observaveis esperados:** `AssertionError` em `validar_sanidade_banco` caso surjam `id_origem` duplicados em `orientacao`.

### Dependencias

- [ ] Nenhuma dependência bloqueante externa (Lattes não é necessário para validar esta story).

### Consideracoes de Performance

- Verificação de timestamp com `find "$(ETL_DIR)/brutos" -type f -newer "$(ETL_DIR)/trabalho/pessoas.json" -print -quit` executa em poucos milissegundos.

---

## Plano de Testes

### Testes Unitarios
- [ ] Carregar dois arquivos anuais (`2025.json` e `2026.json`) com o mesmo `Id` de orientação (alterando `AvaliacaoRelatorio`/`Cancelado` no ano mais recente) e confirmar 1 único registro gravado com o estado mais recente.
- [ ] Carregar duas orientações com `Id` distintos no mesmo plano de trabalho e confirmar ambos os registros preservados.

### Testes de Integracao
- [ ] Executar `popular_banco.py --banco /tmp/dados_teste_etl.db` sobre `Adito/etl/brutos/` (após `etl-cruzar`) e confirmar `COUNT(*) == COUNT(DISTINCT id_origem)` em `orientacao` (0 duplicidades) e `PRAGMA foreign_key_check` limpo.
- [ ] Simular arquivo mais novo em `brutos/` (ou checar comando condicional do `Makefile`) confirmando disparo automático de `etl-cruzar`.

### Testes de Contract
- [ ] N/A

### Testes Manuais
- [ ] Confirmar que `~/Downloads/dados.db` não foi modificado.

---

## Tasks (Breakdown)

- [ ] **[TASK-ETL-08.1]** Implementar deduplicação de `orientacao` por `id_origem` (preservando estado mais recente) e guarda em `validar_sanidade_banco` em `Adito/scripts/popular_banco.py`.
- [ ] **[TASK-ETL-08.2]** Atualizar alvo `db` no `Makefile` para rodar `adito-etl cruzar` automaticamente quando `brutos/` tiver arquivos mais novos que `pessoas.json`.
- [ ] **[TASK-ETL-08.3]** Adicionar testes automatizados e validar em banco temporário.

---

## Definition of Done Checklist

- [ ] Codigo implementado conforme criterios de aceitacao
- [ ] Decisao sobre Spec governada foi registrada
- [ ] Decisao sobre Contract governado foi registrada
- [ ] Nivel ScrumAIDev foi registrado
- [ ] Testes unitarios com cobertura adequada
- [ ] Testes de integracao passando
- [ ] Documentacao atualizada
- [ ] `Behavior change` documentado no PR
