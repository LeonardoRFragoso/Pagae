.PHONY: help up down build restart logs shell migrate makemigrations test lint format install

DOCKER_COMPOSE = docker-compose
DJANGO = $(DOCKER_COMPOSE) exec web python manage.py

help:
	@echo "Available commands:"
	@echo "  make up            Start all services"
	@echo "  make down          Stop all services"
	@echo "  make build         Rebuild images"
	@echo "  make restart       Restart all services"
	@echo "  make logs          Tail all logs"
	@echo "  make shell         Open Django shell"
	@echo "  make migrate       Run database migrations"
	@echo "  make makemigrations name=<app> Make new migrations"
	@echo "  make createsuperuser Create a superuser"
	@echo "  make test          Run test suite"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run ruff linter"
	@echo "  make format        Run black formatter"
	@echo "  make install       Install pre-commit hooks"
	@echo "  make setup         First-time setup (copy .env, up, migrate)"

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

restart:
	$(DOCKER_COMPOSE) restart

logs:
	$(DOCKER_COMPOSE) logs -f

logs-web:
	$(DOCKER_COMPOSE) logs -f web

shell:
	$(DJANGO) shell_plus

migrate:
	$(DJANGO) migrate

makemigrations:
	$(DJANGO) makemigrations $(name)

createsuperuser:
	$(DJANGO) createsuperuser

test:
	$(DOCKER_COMPOSE) exec web pytest $(args)

test-cov:
	$(DOCKER_COMPOSE) exec web pytest --cov-report=html

lint:
	$(DOCKER_COMPOSE) exec web ruff check .

lint-fix:
	$(DOCKER_COMPOSE) exec web ruff check --fix .

format:
	$(DOCKER_COMPOSE) exec web black .

format-check:
	$(DOCKER_COMPOSE) exec web black --check .

install:
	pre-commit install
	pre-commit install --hook-type commit-msg

setup:
	@cp -n .env.example .env || true
	@echo "-> .env created from .env.example (edit it if needed)"
	$(DOCKER_COMPOSE) up -d postgres redis
	@sleep 3
	$(DOCKER_COMPOSE) up -d web celery
	$(DJANGO) migrate
	@echo "✅ Setup complete. Run 'make logs' to see the output."
