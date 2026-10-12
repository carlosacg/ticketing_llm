.DEFAULT_GOAL := help
.PHONY: help install env run db-up up down build restart logs ps \
        test lint format format-check check migrate migration downgrade db-shell shell clean

# Avoid uv picking up a virtualenv activated for another project
unexport VIRTUAL_ENV

UV      := uv run
COMPOSE := docker compose

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

## --- Setup ---------------------------------------------------------------
install: ## Install dependencies (incl. dev) with uv
	uv sync

env: ## Create .env from .env.example if it does not exist
	@test -f .env && echo ".env already exists" || (cp .env.example .env && echo ".env created")

## --- Local development ---------------------------------------------------
run: db-up ## Run the API locally with reload (Postgres in Docker)
	$(UV) alembic upgrade head
	$(UV) uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

db-up: ## Start only the Postgres container
	$(COMPOSE) up -d --wait db

## --- Docker --------------------------------------------------------------
up: ## Build and start the full stack (api + db) in the background
	$(COMPOSE) up --build -d

down: ## Stop the stack
	$(COMPOSE) down

build: ## Rebuild the api image
	$(COMPOSE) build api

restart: ## Restart the api container (e.g. after editing .env)
	$(COMPOSE) up -d --force-recreate api

logs: ## Follow api logs
	$(COMPOSE) logs -f api

ps: ## Show container status
	$(COMPOSE) ps

## --- Quality -------------------------------------------------------------
test: ## Run tests (fake LLM + in-memory SQLite)
	$(UV) pytest

lint: ## Run ruff linter
	$(UV) ruff check .

format: ## Format code and apply lint autofixes
	$(UV) ruff check . --fix
	$(UV) ruff format .

format-check: ## Check formatting without modifying files
	$(UV) ruff format --check .

check: lint format-check test ## Lint, format check and tests (CI)

## --- Database ------------------------------------------------------------
migrate: ## Apply migrations against DATABASE_URL from .env
	$(UV) alembic upgrade head

migration: ## Create a migration: make migration m="add priority"
	@test -n "$(m)" || (echo 'Usage: make migration m="message"' && exit 1)
	$(UV) alembic revision --autogenerate -m "$(m)"

downgrade: ## Revert the last migration
	$(UV) alembic downgrade -1

db-shell: ## Open psql inside the db container
	$(COMPOSE) exec db psql -U ticketing -d ticketing

shell: ## Open a shell inside the api container
	$(COMPOSE) exec api sh

## --- Cleanup -------------------------------------------------------------
clean: ## Stop the stack, drop the DB volume and remove caches
	$(COMPOSE) down -v
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
