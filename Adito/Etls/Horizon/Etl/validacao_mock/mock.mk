
# --- Validação com dados mock (issue #5) ---
# Acrescentado com: cat validacao_mock/mock.mk >> Makefile

MOCK_DIR ?= validacao_mock
MOCK_SCHEMA ?= mock_validacao
MOCK_SCHEMA_SONDA ?= mock_completa
HORIZON_DB_USER ?= horizon
HORIZON_DB_PASSWORD ?= horizon
HORIZON_DB_NAME ?= horizon
HORIZON_DB_PORT ?= 5434
MOCK_DB_URL ?= postgresql://$(HORIZON_DB_USER):$(HORIZON_DB_PASSWORD)@localhost:$(HORIZON_DB_PORT)/$(HORIZON_DB_NAME)
MOCK_PYTHON ?= HORIZON_DATABASE_URL=$(MOCK_DB_URL) $(abspath $(PYTHON_BIN))
MOCK_DB_UP ?= horizon-db-up
# psql dentro do container, já no schema dos dados falsos
MOCK_PSQL ?= $(DOCKER_COMPOSE) exec -e PGOPTIONS="-c search_path=$(MOCK_SCHEMA)" horizon-db psql -U $(HORIZON_DB_USER) -d $(HORIZON_DB_NAME)
MOCK_PSQL_SCRIPT ?= $(DOCKER_COMPOSE) exec -T -e PGOPTIONS="-c search_path=$(MOCK_SCHEMA)" horizon-db psql -U $(HORIZON_DB_USER) -d $(HORIZON_DB_NAME)

.PHONY: mock-carregar mock-psql mock-psql-sonda mock-resumo

mock-carregar: $(MOCK_DB_UP) ## Gera os 300 registros falsos, carrega no banco e valida (schemas mock_*)
	@cd $(MOCK_DIR) && $(MOCK_PYTHON) gerar_mocks.py --saida dados
	@cd $(MOCK_DIR) && $(MOCK_PYTHON) executar_etl_mock.py --schema $(MOCK_SCHEMA)
	@cd $(MOCK_DIR) && $(MOCK_PYTHON) executar_etl_mock.py --schema $(MOCK_SCHEMA_SONDA) --com-sonda
	@cd $(MOCK_DIR) && $(MOCK_PYTHON) validar_carga.py --schema $(MOCK_SCHEMA) --schema-sonda $(MOCK_SCHEMA_SONDA)
	@echo "Pronto. Abra o banco com: make mock-psql"

mock-psql: ## Abre o psql no schema com os dados falsos (rode make mock-carregar antes)
	@$(MOCK_PSQL)

mock-psql-sonda: ## Abre o psql no schema da carga interrompida pela sonda L50
	@$(MAKE) --no-print-directory mock-psql MOCK_SCHEMA=$(MOCK_SCHEMA_SONDA)

mock-resumo: ## Mostra um resumo dos dados falsos no banco (contagens e defeitos encontrados)
	@$(MOCK_PSQL_SCRIPT) < $(MOCK_DIR)/consultas_mock.sql
