.PHONY: setup up down migrate makemigrations test lint format shell prod-build prod-up prod-down prod-check frontend-build

setup:
	cp backend/.env.example backend/.env
	docker-compose up -d
	docker-compose exec web python manage.py migrate

down:
	docker-compose down

up:
	docker-compose up -d

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

test:
	docker-compose exec web python -m pytest tests/ -q --tb=short

lint:
	docker-compose exec web ruff check .

format:
	docker-compose exec web ruff format .
	docker-compose exec web ruff check . --fix

shell:
	docker-compose exec web python manage.py shell_plus

prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-check:
	curl -f http://localhost:8000/api/v1/health/ || exit 1
	docker-compose -f docker-compose.prod.yml exec web python manage.py check --deploy
	@echo "✅ Production build healthcheck passed"

frontend-build:
	cd frontend/merchant-portal && npm install && npm run build
