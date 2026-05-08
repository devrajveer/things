.PHONY: setup lint format test typecheck dev migrate seed reset clean ci obs-up

setup:
	@echo "Setting up local dev environment..."
	npm install -g pnpm
	pnpm install
	pip install pre-commit uv
	pre-commit install

lint:
	pre-commit run --all-files

format:
	ruff format .
	prettier --write .

test:
	pytest
	pnpm test

typecheck:
	mypy .
	pnpm --filter "*" exec tsc --noEmit

dev:
	docker-compose up -d
	pnpm dev

obs-up:
	docker-compose -f infra/local/observability/docker-compose.yml up -d

migrate:
	@echo "Running DB migrations..."

seed:
	@echo "Seeding DB..."

reset:
	docker-compose down -v
	$(MAKE) dev

clean:
	rm -rf node_modules dist build .next

ci: lint typecheck test
