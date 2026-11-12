.PHONY: install up down reset-db logs migrate migrations-check revision run test test-unit lint format typecheck check

install:
	uv sync

up:
	docker compose up -d --wait

down:
	docker compose down

# Deletes all local data, then recreates Postgres (including the test database) and Redis.
reset-db:
	docker compose down -v
	docker compose up -d --wait

logs:
	docker compose logs -f

migrate:
	uv run alembic upgrade head

# Fails if the models in db/models.py have changes that no migration covers.
migrations-check:
	uv run alembic check

# Usage: make revision m="add users table"
revision:
	uv run alembic revision --autogenerate -m "$(m)"

run:
	uv run uvicorn agent_runtime.api.app:create_app --factory --reload --host 127.0.0.1 --port 8000

test:
	uv run pytest

test-unit:
	uv run pytest -m "not integration"

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

check: lint typecheck test
