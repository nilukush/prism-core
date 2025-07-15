.PHONY: help install dev test lint format clean run migrate docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Start development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linters"
	@echo "  format      Format code"
	@echo "  clean       Clean up temporary files"
	@echo "  migrate     Run database migrations"
	@echo "  docker-up   Start all services with Docker"
	@echo "  docker-down Stop all Docker services"

install:
	poetry install

dev:
	poetry run uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=backend/src --cov-report=html --cov-report=term

lint:
	poetry run ruff check backend/
	poetry run mypy backend/

format:
	poetry run black backend/
	poetry run ruff check --fix backend/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/

migrate:
	poetry run alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build

docker-clean:
	docker compose down -v
	docker system prune -f

setup-hooks:
	poetry run pre-commit install