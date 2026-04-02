.PHONY: help install dev test coverage lint format typecheck check clean build docs shell

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install prollama
	pip install -e .

dev: ## Install with all dev dependencies
	pip install -e ".[dev,ast]"

test: ## Run tests
	python -m pytest tests/ -v

coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=prollama --cov-report=term-missing --cov-report=html

lint: ## Check code with ruff
	ruff check src/ tests/

format: ## Auto-fix lint issues
	ruff check --fix src/ tests/

typecheck: ## Run mypy type checking
	mypy src/prollama/ --ignore-missing-imports

check: lint typecheck test ## Run all checks (lint + typecheck + test)

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: clean ## Build package
	python -m build

shell: ## Start interactive prollama shell
	prollama shell

proxy: ## Start proxy server
	prollama start

demo: ## Run anonymization demo on example file
	@echo "=== Basic (regex only) ==="
	prollama anonymize examples/sample_code/fintech_app.py --level basic
	@echo ""
	@echo "=== Full (regex + NLP + AST) ==="
	prollama anonymize examples/sample_code/fintech_app.py --level full

docker-build: ## Build Docker image
	docker build -t prollama:latest .

docker-run: ## Run prollama in Docker
	docker run -it --rm -p 8741:8741 prollama:latest
