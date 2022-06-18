TESTS = tests

VENV ?= .venv
CODE = tests exchange

PATH = bin

ifeq ($(OS), Windows_NT)
	PATH = Scripts
endif

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: venv
venv:
	python3.9 -m venv $(VENV)
	$(VENV)/$(PATH)/python -m pip install --upgrade pip
	$(VENV)/$(PATH)/python -m pip install poetry
	$(VENV)/$(PATH)/poetry install

.PHONY: test
test: ## Runs pytest
	$(VENV)/$(PATH)/pytest -v tests

.PHONY: lint
lint: ## Lint code
	$(VENV)/$(PATH)/flake8 --jobs 4 --statistics --show-source $(CODE)
	$(VENV)/$(PATH)/pylint --jobs 4 --rcfile=setup.cfg $(CODE)
	$(VENV)/$(PATH)/mypy $(CODE)
	$(VENV)/$(PATH)/black --skip-string-normalization --check $(CODE)

.PHONY: format
format: ## Formats all files
	$(VENV)/$(PATH)/isort $(CODE)
	$(VENV)/$(PATH)/black --skip-string-normalization $(CODE)
	$(VENV)/$(PATH)/autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	$(VENV)/$(PATH)/unify --in-place --recursive $(CODE)

.PHONY: ci
ci:	lint test ## Lint code then run tests

.PHONY: init_db
init_db:
	APP_CONFIG=config.ProductionConfig FLASK_APP=exchange FLASK_ENV=production $(VENV)/$(PATH)/flask init_db

.PHONY: up
up:
	APP_CONFIG=config.ProductionConfig FLASK_APP=exchange FLASK_ENV=production $(VENV)/$(PATH)/flask run
