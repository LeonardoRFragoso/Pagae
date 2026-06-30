.PHONY: setup up down migrate makemigrations test lint format shell

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
