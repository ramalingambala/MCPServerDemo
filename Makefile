.PHONY: install-hooks env-setup deps start-docker test-docker

install-hooks:
	@echo "Installing git hooks..."
	@./scripts/install-hooks.sh

env-setup:
	@echo "Copy .env.example to .env and edit values"
	@cp .env.example .env || true

deps:
	@python -m pip install -r requirements.txt

start-docker:
	@echo "Starting docker-compose services..."
	@docker-compose up -d

test-docker:
	@echo "Run docker-based tests"
	@python test_docker_sql.py
